from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from contextlib import nullcontext
from urllib.request import urlopen
import tempfile
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_behavior_resources import inspect
from test_model_primitive_workflow import http_server


class WorldBehaviorResourcesTests(TestCase):
    def test_request_scoped_shared_database_registration_and_immutability(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path='verified-local-disc'
            held=deepcopy(p._document());caches=deepcopy(vars(p.assets));history=deepcopy((p.undo_stack,p.redo_stack));key=state_key(p)
            def catalog(disc,scene):
                return dict(assets=[dict(semantic_id='script://'+scene+'/worldmap/man-p0/0000',asset_kind='script',kind='script')],limitations=['Bounded source only'],consumer={},unbound=[],unsupported_animation_bindings=[])
            with patch('sdk.worldmap_behavior_resources._disc_context',return_value=nullcontext()),patch('sdk.worldmap_behavior_resources.load_worldmap_behavior_catalog',side_effect=catalog):
                value=inspect(p,key)
            self.assertEqual(len(value['assets']),3)
            for row in value['assets']:
                self.assertEqual(row['id'],row['semantic_id']);self.assertEqual(row['layer'],'derived');self.assertIsNone(row['scene_id'])
                self.assertEqual(row['asset_registration'],'verified_world_behavior_catalog')
            self.assertEqual(p._document(),held);self.assertEqual(vars(p.assets),caches);self.assertEqual((p.undo_stack,p.redo_stack),history)
            with self.assertRaises(ProjectError):inspect(p,'0'*64)
            p.mode='live'
            with self.assertRaises(ProjectError):inspect(p,key)

    def test_http_exact_body_and_module_delivery(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));held=deepcopy(p._document())
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_port}/worldmap-behavior-resources.js') as response:
                    self.assertIn(b'decodeWorldmapBehaviorResources',response.read())
                for body in ({},{'source_key':'0'*64},{'source_key':'0'*64,'extra':True}):
                    self.assertEqual(post('/api/worldmap-behavior-resources',body)[0],400)
            self.assertEqual(p._document(),held)
