"""Reviewed model content composes through Project, HTTP and private Build."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from importer.assets import decode_tmd
from importer.core import ImportError as RetailImportError
from importer.model_authoring import preview_model_shape
from importer.model_json import export_shape_json
from importer.model_primitives import inspect_model_primitives
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import source_key
from sdk.server import EditorServer
from test_importer_assets import model
from test_project_workflow import synthetic_scene


ROOT = Path(__file__).resolve().parents[3]
ASSET = 'asset://fixture/model/0'
SCENE = 'scene://fixture'
ACTOR = 'scene://fixture/actors/man-p1/0001'


def digest(data):
    return sha256(data).hexdigest()


def face_edit(source):
    row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
    vertices, uvs, colors = (deepcopy(row[field]) for field in ('vertices', 'uvs', 'colors'))
    vertices[0], vertices[1] = vertices[1], vertices[0]
    uvs[0][0] = (uvs[0][0] + 1) % 256
    colors[0][0] = (colors[0][0] + 1) % 256
    return {'object_index': 0, 'primitive_index': 0,
            'vertices': vertices, 'uvs': uvs, 'colors': colors}


@contextmanager
def http_server(project):
    server = EditorServer(('127.0.0.1', 0), project)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def post(route, body):
        request = Request(f'http://127.0.0.1:{server.server_port}' + route,
                          data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)
    try:
        yield server, post
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise AssertionError('Owned HTTP server did not stop')


class ModelPrimitiveProjectWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='model-primitive-project-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = model(0x21)
        disc = self.root / 'fixture.bin'
        disc.write_bytes(b'synthetic source identity only')
        self.project = ProjectService(self.root)
        self.project.import_metadata(synthetic_scene(), str(disc))
        def source_lookup(project, asset_id, scene_id):
            document = project.imports.get(scene_id)
            if (not document or not project.disc_path or
                    not any(a['semantic_id'] == asset_id for a in document['assets']['models'])):
                raise ProjectError('Unknown imported model identity or active source')
            return self.source
        self.source_patch = patch.object(ProjectService, '_model_source', source_lookup)
        self.source_patch.start()
        self.addCleanup(self.source_patch.stop)
        self.project.save()
        self.imported = deepcopy(self.project.imports)

    def snapshot(self):
        return deepcopy((self.project.model_overrides, self.project.undo_stack, self.project.redo_stack)), {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in (self.root / 'Authored').rglob('*') if path.is_file()}

    def review(self, edits):
        current = self.project.model_primitive_source(ASSET)
        report = self.project.preview_model_primitives(ASSET, edits, current['effective_sha256'],
                                                        current['project_source_key'])
        return current, report

    def apply(self, edits):
        current, report = self.review(edits)
        self.project.set_model_primitives(ASSET, edits, current['effective_sha256'],
                                          current['project_source_key'], report['proposed_sha256'])
        return report

    def effective(self):
        binding = self.project.model_overrides.get(ASSET)
        return self.project.read_model_replacement(ASSET, binding) if binding else self.source

    def test_read_only_preview_noop_and_detached_source_layers(self):
        before = self.snapshot()
        current, noop = self.review([])
        self.assertEqual(current['schema_version'], 'legaia.model-primitives.v2')
        self.assertEqual(current['source_sha256'], digest(self.source))
        self.assertEqual(current['effective_sha256'], digest(self.source))
        self.assertEqual(current['project_source_key'], source_key(self.project))
        self.assertEqual(current['objects'], current['retail_objects'])
        self.assertEqual(noop['coordinate_changes'], [])
        self.assertEqual(noop['changes_from_current'], [])
        self.assertFalse(noop['project_changed'])
        self.project.set_model_primitives(ASSET, [], current['effective_sha256'],
                                          current['project_source_key'], noop['proposed_sha256'])
        changed = self.project.preview_model_primitives(ASSET, [face_edit(self.source)],
                                                        current['effective_sha256'], current['project_source_key'])
        self.assertEqual({c['field'] for c in changed['changes_from_current']}, {'vertex_index', 'uv', 'color'})
        self.assertEqual(changed['current_preview'], decode_tmd(self.source))
        self.assertNotEqual(changed['preview']['triangles'], changed['current_preview']['triangles'])
        current['objects'][0]['primitives'][0]['vertices'][0] = 999
        changed['preview']['vertices'][0][0] = 999
        self.assertEqual(self.project.model_primitive_source(ASSET)['objects'][0]['primitives'][0]['vertices'], [0, 1, 2])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.project.imports, self.imported)

    def test_rejected_and_stale_drafts_preserve_history_and_private_files(self):
        edits = [face_edit(self.source)]
        current, report = self.review(edits)
        before = self.snapshot()
        bad_edit = deepcopy(edits)
        bad_edit[0]['uvs'][0][0] = True
        cases = [
            lambda: self.project.preview_model_primitives(ASSET, bad_edit, current['effective_sha256'], current['project_source_key']),
            lambda: self.project.preview_model_primitives(ASSET, edits, '0' * 64, current['project_source_key']),
            lambda: self.project.preview_model_primitives(ASSET, edits, current['effective_sha256'], '0' * 64),
            lambda: self.project.preview_model_primitives('asset://foreign/model/0', edits, current['effective_sha256'], current['project_source_key']),
            lambda: self.project.set_model_primitives(ASSET, edits, current['effective_sha256'], current['project_source_key'], '0' * 64),
        ]
        for case in cases:
            with self.subTest(case=cases.index(case)), self.assertRaises((ProjectError, RetailImportError)):
                case()
            self.assertEqual(self.snapshot(), before)
        self.project.mode = 'live'
        with self.assertRaises(ProjectError):
            self.project.preview_model_primitives(ASSET, edits, current['effective_sha256'], current['project_source_key'])
        self.project.mode = 'edit'
        with patch('sdk.scene_preview.source_key', side_effect=[current['project_source_key'], 'f' * 64]):
            with self.assertRaisesRegex(ProjectError, 'during face inspection'):
                self.project.set_model_primitives(ASSET, edits, current['effective_sha256'],
                                                  current['project_source_key'], report['proposed_sha256'])
        self.assertEqual(self.snapshot(), before)
        self.project.set_model_vector(ASSET, 0, 'vertices', 0, [3, 4, 5], current['effective_sha256'])
        changed = self.snapshot()
        with self.assertRaises(ProjectError):
            self.project.set_model_primitives(ASSET, edits, current['effective_sha256'],
                                              current['project_source_key'], report['proposed_sha256'])
        self.assertEqual(self.snapshot(), changed)

    def test_composition_history_save_open_and_legacy_binding_guard(self):
        self.project.set_model_vector(ASSET, 0, 'vertices', 0, [3, 4, 5], digest(self.source))
        self.assertEqual(self.project.model_overrides[ASSET]['format'], 'tmd-shape')
        shape_only = self.effective()
        edits = [face_edit(self.source)]
        self.apply(edits)
        both = self.effective()
        binding = deepcopy(self.project.model_overrides[ASSET])
        self.assertEqual(binding['format'], 'tmd-content-v1')
        self.assertEqual(decode_tmd(both)['vertices'][0], [3, 4, 5])
        self.assertEqual(inspect_model_primitives(both)['objects'][0]['primitives'][0]['vertices'], edits[0]['vertices'])
        self.assertEqual(len(self.project.undo_stack), 2)
        self.project.undo()
        self.assertEqual(self.effective(), shape_only)
        self.project.redo()
        self.assertEqual(self.effective(), both)
        self.project.save()
        reopened = ProjectService.open(self.root)
        self.assertEqual(reopened.model_overrides, self.project.model_overrides)
        self.assertEqual(reopened.read_model_replacement(ASSET, reopened.model_overrides[ASSET]), both)
        self.assertEqual(reopened.imports, self.imported)
        unchanged = self.snapshot()
        self.apply(edits)
        self.assertEqual(self.snapshot(), unchanged)
        old_format = {**binding, 'format': 'tmd-shape'}
        with self.assertRaises(RetailImportError):
            self.project.read_model_replacement(ASSET, old_format)
        # Existing coordinate tools retain authored packet fields in both orders.
        self.project.set_model_vector(ASSET, 0, 'vertices', 1, [14, 5, 6], digest(both))
        self.project.translate_model_object(ASSET, 0, [1, 2, 3], digest(self.effective()))
        for operation, values in [('rotation', {'axis': 'z', 'quarter_turns': 1}),
                                  ('scale', {'percent': 125})]:
            effective = self.effective()
            report = self.project.preview_model_object(ASSET, 0, operation, values, digest(effective))
            if operation == 'rotation':
                self.project.rotate_model_object(ASSET, 0, values['axis'], values['quarter_turns'], digest(effective))
            else:
                self.project.scale_model_object(ASSET, 0, values['percent'], digest(effective))
            self.assertEqual(digest(self.effective()), report['proposed_sha256'])
        effective = self.effective()
        upload = json.loads(export_shape_json(self.source))
        upload['objects'][0]['vertices'][2] = [20, 30, 40]
        self.project.set_model_json(ASSET, json.dumps(upload).encode())
        final = self.project.model_primitive_source(ASSET)
        self.assertEqual(final['objects'][0]['primitives'][0]['vertices'], edits[0]['vertices'])
        self.assertEqual(final['objects'][0]['primitives'][0]['uvs'], edits[0]['uvs'])
        self.assertEqual(final['objects'][0]['primitives'][0]['colors'], edits[0]['colors'])
        self.assertEqual(final['retail_objects'], inspect_model_primitives(self.source, include_normal_references=True)['objects'])
        self.assertNotEqual(self.effective(), effective)
        self.assertEqual(decode_tmd(self.effective())['vertices'][2], [20, 30, 40])
        self.assertEqual(self.project.imports, self.imported)

    def test_http_review_apply_exact_envelopes_and_stale_repeat(self):
        with http_server(self.project) as (_server, post):
            status, source = post('/api/model-primitive-source', {'asset_id': ASSET})
            self.assertEqual(status, 200)
            body = dict(asset_id=ASSET, expected_sha256=source['effective_sha256'],
                        source_key=source['project_source_key'], edits=[face_edit(self.source)])
            before = self.snapshot()
            status, report = post('/api/model-primitive-preview', body)
            self.assertEqual(status, 200)
            self.assertEqual(report['preview']['textures'], [])
            self.assertEqual(self.snapshot(), before)
            for route, malformed in [('/api/model-primitive-source', {'asset_id': ASSET, 'bytes': []}),
                                     ('/api/model-primitives', {**body, 'proposed_sha256': '0' * 64}),
                                     ('/api/model-primitive-preview', {**body, 'extra': True})]:
                with self.subTest(route=route):
                    status, _ = post(route, malformed)
                    self.assertEqual(status, 400)
                    self.assertEqual(self.snapshot(), before)
            status, _ = post('/api/model-primitives', {**body, 'proposed_sha256': report['proposed_sha256']})
            self.assertEqual(status, 200)
            applied = self.snapshot()
            self.assertEqual(len(self.project.undo_stack), 1)
            status, _ = post('/api/model-primitives', {**body, 'proposed_sha256': report['proposed_sha256']})
            self.assertEqual(status, 400)
            self.assertEqual(self.snapshot(), applied)
            _, current = post('/api/model-primitive-source', {'asset_id': ASSET})
            self.assertNotEqual(current['effective_sha256'], source['effective_sha256'])
            self.assertNotEqual(current['project_source_key'], source['project_source_key'])
            self.assertEqual(current['retail_objects'], source['retail_objects'])
            _, _ = post('/api/undo', {})
            self.assertFalse(self.project.model_overrides)
            _, _ = post('/api/redo', {})
            self.assertEqual(self.snapshot()[0][0], applied[0][0])
        self.assertEqual(self.project.imports, self.imported)

    def test_posed_scene_proposal_refreshes_uv_crop_without_mutating_scene(self):
        from importer.animation import pose_vertices
        transforms = [dict(object_index=0, translation=[3, 4, 5], rotation_psx=[0, 0, 1024])]
        geometry = decode_tmd(self.source)
        geometry.update(posed=True, pose={'object_transforms': transforms},
                        frames=[{'object_transforms': transforms, 'vertices': deepcopy(geometry['vertices'])}],
                        textures=[{'status': 'resolved', 'bounds': [1, 2, 7, 8]}])
        scene = {'scene_id': SCENE,
                 'entities': [{'entity_id': ACTOR, 'asset_id': ASSET, 'renderable': True, 'geometry_key': 'pose'}],
                 'assets': [{'asset_id': ASSET, 'geometry_key': 'pose', 'preview': geometry}]}
        scene_before = deepcopy(scene)
        row = inspect_model_primitives(self.source, include_normal_references=True)['objects'][0]['primitives'][0]
        uvs = deepcopy(row['uvs'])
        uvs[0][0] = 100
        edits = [{'object_index': 0, 'primitive_index': 0, 'uvs': uvs}]
        source, report = self.review(edits)
        replacement, _ = self.project._prepare_model_primitives(ASSET, edits, source['effective_sha256'], source['project_source_key'])
        composed = preview_model_shape(geometry, replacement, {})
        self.assertEqual(composed['vertices'], pose_vertices(decode_tmd(replacement)['vertices'], geometry['objects'], transforms))
        self.assertEqual(composed['frames'][0]['vertices'], composed['vertices'])
        self.assertEqual(composed['triangle_uvs'], decode_tmd(replacement)['triangle_uvs'])
        catalog = SimpleNamespace(metadata=lambda: {}, textures=[])
        asset = self.project.assets.records[ASSET]
        asset['source_record']['prot_entry_name'] = 'fixture'
        def association(_catalog, _material, bounds):
            return {'status': 'resolved', 'bounds': list(bounds), 'rgba': bytes([0, 0, 0, 255]), 'stp': bytes([0])}
        with http_server(self.project) as (server, post):
            with patch.object(server.scene_previews, 'preview', return_value=scene), \
                    patch('importer.textures.load_scene_texture_catalog', return_value=catalog), \
                    patch('importer.textures.load_asset_texture_catalog', return_value=catalog), \
                    patch('importer.textures.associate_material', side_effect=association):
                body = dict(asset_id=ASSET, entity_id=ACTOR, all_instances=True, edits=edits,
                            expected_sha256=source['effective_sha256'], source_key=source['project_source_key'],
                            proposed_sha256=report['proposed_sha256'])
                for invalid in ({**body, 'all_instances': 1}, {**body, 'proposed_sha256': '0' * 64}):
                    status, _ = post('/api/model-primitive-scene-preview', invalid)
                    self.assertEqual(status, 400)
                    self.assertFalse(self.project.model_overrides)
                status, report = post('/api/model-primitive-scene-preview', body)
                self.assertEqual(status, 200)
            self.assertEqual(report['preview']['textures'][0]['bounds'], [4, 2, 100, 8])
            self.assertEqual(report['proposal_assets'][0]['preview']['textures'][0]['bounds'], [4, 2, 100, 8])
            self.assertEqual(report['preview']['vertices'], composed['vertices'])
            self.assertEqual(scene, scene_before)
            self.assertFalse(self.project.model_overrides)
            self.assertFalse(self.project.undo_stack)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class ModelPrimitiveRetailBuild(unittest.TestCase):
    def test_town01_normal_build_independent_member_decompression(self):
        from importer.core import decompress_lzs, parse_lzs_sections
        from importer.pipeline import _disc_context, import_scene
        from sdk.build import build_project
        disc = os.environ['LEGAIA_DISC_BIN']
        private = ROOT / 'local-output/sdk-20260909'
        private.mkdir(parents=True, exist_ok=True)
        with _disc_context(disc) as (_image, _disc_hash, _mapping, archive):
            document = import_scene(disc, 'town01')
            asset = next(a for a in document['assets']['models'] if a['semantic_id'].endswith('/scene-tmd/0000'))
            with tempfile.TemporaryDirectory(prefix='model-primitive-build-', dir=private) as raw:
                project = ProjectService(Path(raw))
                project.import_metadata(document, disc)
                original = project._model_source(asset['semantic_id'], project.active_scene)
                imported = deepcopy(project.imports)
                source = project.model_primitive_source(asset['semantic_id'])
                edits = [face_edit(original)]
                report = project.preview_model_primitives(asset['semantic_id'], edits, source['effective_sha256'], source['project_source_key'])
                project.set_model_primitives(asset['semantic_id'], edits, source['effective_sha256'],
                                              source['project_source_key'], report['proposed_sha256'])
                project.save()
                result = build_project(project)
                self.assertEqual(result['overlay_count'], 1)
                self.assertEqual(result['report']['validation']['live_runtime'], 'not_run')
                audit = json.loads(Path(result['audit']).read_text(encoding='utf-8'))
                edit = next(row for row in audit['edits'] if row['semantic_id'] == asset['semantic_id'])
                self.assertEqual(edit['scope'], 'TMD-existing-layout-content')
                self.assertEqual({row['field'] for row in edit['coordinate_changes']}, {'vertex_index', 'uv', 'color'})
                locator = asset['source_record']
                entry = archive.entry(locator['prot_entry_index'])
                body = archive.read_entry(entry)
                sections = parse_lzs_sections(body)
                section = sections[locator['container_section']]
                end = sections[locator['container_section'] + 1].stream_offset if locator['container_section'] + 1 < len(sections) else len(body)
                baseline, consumed = decompress_lzs(body[section.stream_offset:end], section.decoded_size)
                offset = (archive.node.extent_lba + entry.start_lba) * 2048 + section.stream_offset
                overlay = next(row for row in audit['overlays'] if row['offset'] == offset)
                with zipfile.ZipFile(result['path']) as package:
                    payload = package.read(overlay['file'])
                    self.assertIn(b'model faces, UVs and baked colors', package.read('manifest.toml'))
                    self.assertIn(b'Gameplay remains unverified', package.read('manifest.toml'))
                self.assertEqual(len(payload), consumed)
                decoded, read = decompress_lzs(payload, section.decoded_size)
                self.assertLessEqual(read, consumed)
                self.assertEqual(payload[read:], body[section.stream_offset + read:section.stream_offset + consumed])
                start, length = locator['byte_offset'], locator['byte_length']
                retail_member = baseline[start:start + length]
                authored_member = decoded[start:start + length]
                self.assertEqual(retail_member, original)
                # Independent known Town01 packet fields, not the writer's output.
                expected = bytearray(original)
                expected[48] = edits[0]['colors'][0][0]
                expected[52] = edits[0]['uvs'][0][0]
                struct.pack_into('<3H', expected, 62, *(value * 8 for value in edits[0]['vertices']))
                self.assertEqual(authored_member, bytes(expected))
                self.assertEqual(digest(authored_member), report['proposed_sha256'])
                self.assertEqual(decoded[:start], baseline[:start])
                self.assertEqual(decoded[start + length:], baseline[start + length:])
                self.assertEqual(project.imports, imported)
                self.assertEqual(project._model_source(asset['semantic_id'], project.active_scene), original)
                restored = ProjectService.open(project.root)
                self.assertEqual(restored.model_overrides, project.model_overrides)


if __name__ == '__main__':
    unittest.main()
