"""Reviewed source trigger HTTP actions, cache keys and preserved source layers."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.server import EditorServer

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class TriggerCellsHTTP(unittest.TestCase):
    def test_review_apply_history_source_layers_and_stale_rejection(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='trigger-http-', dir=private) as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
            project.save()
            imported = deepcopy(project.imports)
            server = EditorServer(('127.0.0.1', 0), project)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def post(route, body=None):
                request = Request(f'http://127.0.0.1:{server.server_port}' + route,
                    data=json.dumps(body or {}).encode(), headers={'Content-Type':'application/json'})
                try:
                    with urlopen(request, timeout=60) as response:return response.status, json.load(response)
                except HTTPError as error:
                    with error:return error.code, json.load(error)
            def ok(route, body=None):
                status, value = post(route, body)
                self.assertEqual(status, 200, value)
                return value
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/trigger-cells.js') as response:
                    self.assertIn(b'openTriggerCells', response.read())
                initial = server.state()
                catalog = ok('/api/resource-catalog')
                initial_preview = ok('/api/field-map-preview', {'asset_id':'collision://town01/field-map'})
                self.assertEqual(initial_preview['trigger_cells'], [])
                trigger = next(row for row in catalog['records'] if row['kind']=='trigger' and '/primary/' in row['id'])
                body = dict(trigger_id=trigger['id'], values=None, action='set')
                report = ok('/api/trigger-cells-review', body)
                self.assertFalse(project.dirty)
                self.assertEqual(project.undo_stack, [])
                values = {**report['values_layers']['current'], 'tile_x': report['values_layers']['current']['tile_x'] + 1}
                proposal = ok('/api/trigger-cells-review', {**body, 'values':values})
                command = dict(type='apply_trigger_cells', trigger_id=trigger['id'], values=values,
                               action='set', review_key=proposal['review_key'])
                self.assertEqual(post('/api/trigger-cells-apply', {**command, 'values':{**values,'tile_x':values['tile_x']+1}})[0], 400)
                self.assertFalse(project.overrides)
                applied = ok('/api/trigger-cells-apply', command)
                self.assertEqual(len(project.undo_stack), 1)
                self.assertTrue(project.dirty)
                self.assertNotEqual(applied['scene_trigger_state_key'], initial['scene_trigger_state_key'])
                self.assertEqual(applied['scene_preview_source_key'], initial['scene_preview_source_key'])
                self.assertEqual(ok('/api/resource-catalog')['trigger_state_key'], applied['scene_trigger_state_key'])
                for layer in ('imported', 'effective'):
                    preview = ok('/api/field-map-preview', {'asset_id':'collision://town01/field-map','layer':layer})
                    self.assertEqual(preview['spatial'], initial_preview['spatial'])
                    self.assertEqual(len(preview['trigger_cells']), 1)
                    annotation = preview['trigger_cells'][0]
                    self.assertEqual(annotation['row_sha256'], trigger['source_record']['sha256'])
                    self.assertEqual(annotation['world_bounds_layers']['effective'], proposal['world_bounds_layers']['proposed'])
                before = deepcopy((project.overrides, project.undo_stack, project.redo_stack))
                self.assertEqual(post('/api/trigger-cells-apply', command)[0], 400)
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack), before)
                ok('/api/undo')
                self.assertFalse(project.overrides)
                self.assertFalse(project.dirty)
                ok('/api/redo')
                project.save()
                reopened = ProjectService.open(project.root)
                self.assertEqual(reopened.overrides, project.overrides)
                self.assertEqual(project.imports, imported)
                clear = ok('/api/trigger-cells-review', {**body,'action':'clear'})
                ok('/api/trigger-cells-apply', dict(type='apply_trigger_cells',trigger_id=trigger['id'],
                    values=None,action='clear',review_key=clear['review_key']))
                self.assertFalse(project.overrides)
                self.assertEqual(ok('/api/field-map-preview', {'asset_id':'collision://town01/field-map'})['trigger_cells'], [])
                for invalid in ({}, {**body,'path':'x'}, {**body,'values':{**values,'tile_x':True}}):
                    self.assertEqual(post('/api/trigger-cells-review', invalid)[0], 400)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
