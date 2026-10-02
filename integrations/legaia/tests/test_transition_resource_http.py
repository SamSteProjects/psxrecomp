"""Retail transition assets remain connected after qualified partial-script edits."""
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
class TransitionResourceHTTP(unittest.TestCase):
    def test_partial_source_entry_assets_history_save_and_graph(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='transition-assets-http-', dir=private) as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
            project.save()
            imports = deepcopy(project.imports)
            server = EditorServer(('127.0.0.1', 0), project)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def post(route, body=None):
                request = Request(f'http://127.0.0.1:{server.server_port}' + route,
                                  data=json.dumps(body or {}).encode(), headers={'Content-Type':'application/json'})
                with urlopen(request, timeout=30) as response:
                    return json.load(response)
            def get_state():
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/state', timeout=30) as response:
                    return json.load(response)
            try:
                state = get_state()
                catalog = post('/api/resource-catalog')
                asset = next(row for row in catalog['records'] if row['kind'] == 'transition')
                self.assertEqual(asset['script_status'], 'partial')
                self.assertEqual(asset['script_stop_count'], 0)
                self.assertIsNone(asset['trigger_position'])
                key = asset['entry_layers']['transition_id']
                owner = asset['owner_id']
                unchanged_source = state['scene_preview_source_key']
                original = asset['entry_layers']['imported']['entry_x_encoded']
                post('/api/command', dict(type='set_transition_entry', entity_id=owner, transition_id=key, values={'entry_x_encoded':128}))
                edited_state = get_state()
                self.assertEqual(edited_state['scene_preview_source_key'], unchanged_source)
                self.assertNotEqual(edited_state['scene_transition_state_key'], state['scene_transition_state_key'])
                changed = next(row for row in post('/api/resource-catalog')['records'] if row['kind'] == 'transition')
                self.assertEqual(changed['entry_layers']['imported']['entry_x_encoded'], original)
                self.assertEqual(changed['entry_layers']['effective']['entry_x_encoded'], 128)
                self.assertEqual(changed['arrival_layers']['effective']['x'], 128)
                graph = post('/api/asset-references', {'asset_id':asset['id']})
                self.assertEqual({edge['kind'] for edge in graph['incoming']}, {'script_transition_reference'})
                self.assertEqual({edge['kind'] for edge in graph['outgoing']}, {'transition_destination_source'})
                post('/api/undo')
                self.assertEqual(get_state()['scene_transition_state_key'], state['scene_transition_state_key'])
                post('/api/redo')
                post('/api/project/save')
                restored = ProjectService.open(project.root)
                self.assertEqual(restored.overrides, project.overrides)
                self.assertEqual(project.imports, imports)
                post('/api/command', dict(type='clear_transition_entry', entity_id=owner, transition_id=key))
                self.assertFalse(project.overrides)
                final = next(row for row in post('/api/resource-catalog')['records'] if row['kind'] == 'transition')
                self.assertEqual(final['entry_layers']['authored'], {})
                self.assertEqual(final['arrival_layers']['effective'], final['arrival_layers']['imported'])
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
