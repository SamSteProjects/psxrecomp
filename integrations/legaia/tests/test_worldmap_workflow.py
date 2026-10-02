"""Retail global landmark workflow and independent emitted SCUS data readback."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from importer.core import ImportError as RetailImportError
from importer.pipeline import import_scene, _disc_context
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import OWNER, COMPONENT, snapshot, review
from sdk.build import build_project
from sdk.build_review import review as build_review
from sdk.server import EditorServer, EditorHandler


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class WorldmapWorkflow(unittest.TestCase):
    def project(self, directory):
        p = ProjectService(Path(directory))
        p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
        p.save()
        return p

    def apply(self, p, identifier, values):
        result, _ = review(p, identifier, values)
        p.command(dict(type='set_worldmap_menu', entity_id=identifier, values=values,
                       review_key=result['review']['review_key']))
        return result

    def test_multiple_rows_history_persistence_build_and_exact_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            imported = deepcopy(p.imports)
            source = snapshot(p)
            self.assertEqual(len(source['placements']), 20)
            self.assertEqual(source['field_evidence']['menu_position'], 'reference_interpretation')
            a, b = source['placements'][0], source['placements'][1]
            values_a, values_b = deepcopy(a['retail_values']), deepcopy(b['retail_values'])
            values_a.update(name_index=1, discovery_flag_index=51)
            values_a['menu_position']['x'] = 97
            values_b['menu_position']['y'] += 1
            self.apply(p, a['semantic_id'], values_a)
            self.apply(p, b['semantic_id'], values_b)
            retained = deepcopy(p.overrides)
            p.undo(); self.assertEqual(len(p.overrides[OWNER][COMPONENT]['entries']), 1)
            p.redo(); self.assertEqual(p.overrides, retained)
            p.save(); q = ProjectService.open(p.root)
            self.assertEqual(q.overrides, retained)
            self.assertEqual(q.imports, imported)
            self.assertEqual(q.authored_assets()[0]['kind'], 'worldmap')
            assessment = build_review(q)
            self.assertTrue(assessment['normal_build_ready'], assessment['blockers'])
            built = build_project(q)
            self.assertEqual(assessment['assessment']['report'], built['report'])
            self.assertTrue(built['report']['validation']['worldmap_menu_round_trip'])
            with _disc_context(q.disc_path) as (image, _, _, _):
                exe = image.read_file(image.find('SCUS_942.54'))
            start = source['source_record']['table_file_offset']
            expected = bytearray(exe)
            for row, values in ((a, values_a), (b, values_b)):
                struct.pack_into('<BBHBB', expected, start + row['record_index'] * 6,
                    values['name_index'], values['discovery_flag_index'] - 32, values['destination_scene_id'],
                    values['menu_position']['x'], values['menu_position']['y'])
            with zipfile.ZipFile(built['path']) as package:
                payload = package.read('assets/worldmap-menu.bin')
            self.assertEqual(len(payload), 126)
            reopened = exe[:start] + payload + exe[start + len(payload):]
            self.assertEqual(reopened, bytes(expected))
            self.assertEqual(sha256(exe).hexdigest(), source['source_record']['sha256'])
            self.assertEqual(built['runtime_status'], 'package_built_not_launched')
            self.apply(q, a['semantic_id'], None)
            self.assertIn(b['semantic_id'], q.overrides[OWNER][COMPONENT]['entries'])
            self.apply(q, b['semantic_id'], None)
            self.assertNotIn(OWNER, q.overrides)
            self.assertEqual(build_project(q)['overlay_count'], 0)

    def test_review_noop_invalid_domains_and_stale_binding_preserve_state(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            row = snapshot(p)['placements'][0]
            saved = (p.root / 'project.legaia.json').read_bytes()
            state = deepcopy((p.imports, p.overrides, p.undo_stack, p.redo_stack))
            result, _ = review(p, row['semantic_id'], row['retail_values'])
            self.assertTrue(result['review']['no_op'])
            with self.assertRaises(ProjectError):
                p.command(dict(type='set_worldmap_menu', entity_id=row['semantic_id'], values=row['retail_values'],
                    review_key=result['review']['review_key']))
            for field, value in [('name_index', 255), ('name_index', True), ('discovery_flag_index', 31),
                                 ('destination_scene_id', 65535), ('menu_position', {'x': 256, 'y': 0})]:
                proposal = deepcopy(row['retail_values']); proposal[field] = value
                with self.subTest(field=field), self.assertRaises((ProjectError, RetailImportError)):
                    review(p, row['semantic_id'], proposal)
            self.assertEqual((p.imports, p.overrides, p.undo_stack, p.redo_stack), state)
            self.assertEqual((p.root / 'project.legaia.json').read_bytes(), saved)
            values = deepcopy(row['retail_values']); values['menu_position']['x'] += 1
            accepted, _ = review(p, row['semantic_id'], values)
            p.name += ' changed'
            with self.assertRaises(ProjectError):
                p.command(dict(type='set_worldmap_menu', entity_id=row['semantic_id'], values=values,
                    review_key=accepted['review']['review_key']))
            self.assertEqual((p.imports, p.overrides, p.undo_stack, p.redo_stack), state)
            p.mode = 'live'
            with self.assertRaises(ProjectError): review(p, row['semantic_id'], values)

    def test_global_menu_and_field_placement_compose_without_changing_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            imported = deepcopy(p.imports)
            row = snapshot(p)['placements'][0]
            values = deepcopy(row['retail_values']); values['menu_position']['x'] += 1
            self.apply(p, row['semantic_id'], values)
            from sdk.draft_build import prepare_draft_archive
            retained = deepcopy(p.overrides)
            with self.assertRaisesRegex(ProjectError, 'world-map landmarks; use normal Build'):
                prepare_draft_archive(p)
            self.assertEqual(p.overrides, retained)
            actor = p.imports['scene://town01']['actors'][0]
            x = actor['imported_transform']['position']['x']
            p.command(dict(type='set_transform', entity_id=actor['semantic_id'], position={'x': x + 64}))
            built = build_project(p)
            self.assertEqual(built['overlay_count'], 2)
            self.assertEqual({change['scope'] for change in built['report']['changes']},
                             {'worldmap-menu-record-only', 'initial-man-placement-only'})
            self.assertTrue(built['report']['validation']['worldmap_menu_round_trip'])
            self.assertEqual(p.imports, imported)
            with zipfile.ZipFile(built['path']) as package:
                self.assertEqual(len(package.read('assets/worldmap-menu.bin')), 126)

    def test_http_readonly_review_invalid_request_and_reviewed_apply(self):
        class QuietHandler(EditorHandler):
            def log_message(self, *args): pass
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            server = EditorServer(('127.0.0.1', 0), p)
            server.RequestHandlerClass = QuietHandler
            worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
            def post(route, body):
                request = Request(f'http://127.0.0.1:{server.server_port}' + route,
                                  json.dumps(body).encode(), {'Content-Type': 'application/json'})
                try:
                    with urlopen(request, timeout=20) as response: return response.status, json.load(response)
                except HTTPError as exc:
                    with exc: return exc.code, json.load(exc)
            try:
                saved = (p.root / 'project.legaia.json').read_bytes()
                code, report = post('/api/worldmap-authoring', {})
                self.assertEqual(code, 200)
                row = report['placements'][0]
                values = deepcopy(row['retail_values']); values['menu_position']['x'] += 1
                for body in ({}, {'entity_id': row['semantic_id'], 'values': values, 'extra': True},
                             {'entity_id': OWNER + '/placements/0063', 'values': values}):
                    self.assertEqual(post('/api/worldmap-authoring-review', body)[0], 400)
                code, inspected = post('/api/worldmap-authoring-review', {'entity_id': row['semantic_id'], 'values': values})
                self.assertEqual(code, 200)
                self.assertEqual(p.undo_stack, [])
                self.assertEqual((p.root / 'project.legaia.json').read_bytes(), saved)
                command = dict(type='set_worldmap_menu', entity_id=row['semantic_id'], values=values,
                               review_key=inspected['review']['review_key'])
                self.assertEqual(post('/api/command', {**command, 'review_key': '0' * 64})[0], 400)
                self.assertEqual(post('/api/command', command)[0], 200)
                self.assertEqual(post('/api/project/save', {})[0], 200)
                self.assertEqual(ProjectService.open(p.root).overrides, p.overrides)
                self.assertEqual(post('/api/command', command)[0], 400)
                self.assertEqual(len(p.undo_stack), 1)
            finally:
                server.shutdown(); server.server_close(); worker.join(5)
                self.assertFalse(worker.is_alive())


if __name__ == '__main__':
    unittest.main()
