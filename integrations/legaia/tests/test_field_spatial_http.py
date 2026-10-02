"""Retail source cells and trigger references remain private read-only views."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.server import EditorServer


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class FieldSpatialHTTP(unittest.TestCase):
    def test_fresh_source_cells_graph_and_persistence_do_not_author_project_data(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='field-spatial-http-', dir=private) as raw:
            project = ProjectService(Path(raw))
            disc = os.environ['LEGAIA_DISC_BIN']
            for name in ('town01', 'dolk2'):
                project.import_metadata(import_scene(disc, name), disc)
            project.set_scene('scene://town01')
            project.save()
            before = deepcopy(project._document())
            server = EditorServer(('127.0.0.1', 0), project)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def post(route, body=None):
                request = Request(f'http://127.0.0.1:{server.server_port}' + route,
                                  data=json.dumps(body or {}).encode(),
                                  headers={'Content-Type': 'application/json'})
                with urlopen(request, timeout=60) as response:
                    return json.load(response)

            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/field-spatial.js', timeout=5) as response:
                    self.assertIn(b'decodeFieldSpatial', response.read())
                catalog = post('/api/resource-catalog')
                preview = post('/api/field-map-preview', {'asset_id': 'collision://town01/field-map'})
                spatial = preview['spatial']
                self.assertEqual(spatial['scene_id'], 'scene://town01')
                self.assertEqual(spatial['height_status'], 'unknown')
                self.assertEqual(len(spatial['records']), 113)
                self.assertEqual(sum(row['kind'] == 'trigger' for row in spatial['records']), 99)
                self.assertEqual(sum(row['kind'] == 'region' for row in spatial['records']), 14)
                by_id = {row['semantic_id']: row for row in catalog['records']}
                for row in spatial['records']:
                    self.assertEqual(row['source_record'], by_id[row['id']]['source_record'])
                    self.assertEqual(row['activation'], 'not_evaluated')
                    self.assertEqual(row['world_center']['y'], 0)
                    bias = 64 if row['kind'] == 'region' else 0
                    self.assertEqual(row['world_bounds'], {key: value * 128 + bias
                                                          for key, value in row['source_tile_bounds'].items()})
                eligible = [row for row in catalog['records'] if row['kind'] == 'trigger'
                            and row.get('encoded', {}).get('gate') == 1]
                self.assertEqual(len(eligible), 51)
                trigger = eligible[0]
                target = f"script://town01/scripts/man-p2/{trigger['encoded']['record_index']:04d}"
                report = post('/api/trigger-script', {'asset_id': trigger['id']})
                self.assertEqual(report['script_id'], target)
                self.assertEqual(report['trigger_source_record'], trigger['source_record'])
                self.assertEqual(report['source_record']['sha256'], by_id[target]['source_record']['sha256'])
                for scope in ('active', 'project'):
                    graph = post('/api/asset-references', {'asset_id': trigger['id'], 'scope': scope})
                    links = [edge for edge in graph['outgoing'] if edge['kind'] == 'field_trigger_script_reference']
                    self.assertEqual(len(links), 1)
                    self.assertEqual(links[0]['target_id'], target)
                    self.assertEqual(links[0]['trigger_reference_evidence']['reachability'], 'not_evaluated')
                    self.assertEqual(links[0]['runtime_binding'], 'not_asserted')
                effective = post('/api/field-map-preview', {'asset_id': 'collision://town01/field-map', 'layer': 'effective'})
                self.assertEqual(effective['spatial'], spatial)
                self.assertEqual(project._document(), before)
                self.assertFalse(project.dirty)
                self.assertFalse(project.overrides)
                self.assertFalse(project.undo_stack)
                project.save()
                self.assertEqual(ProjectService.open(project.root)._document(), before)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
