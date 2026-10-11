from base64 import b64decode
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.request import urlopen
import tempfile
from sdk.project import ProjectService,ProjectError,atomic_write
from sdk.worldmap_authoring import state_key
from sdk.worldmap_current_map import inspect
from sdk.worldmap_scripted_placement_binding import owner,COMPONENT,base_path
from test_worldmap_scripted_placement_binding import ledger
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class CurrentWorldMapTests(TestCase):
    def test_editor_binding_snapshot_is_scoped_fresh_and_detached(self):
        from sdk.worldmap_edit_state import snapshot
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene())
            p.overrides={'scene://map01':{'FloorHeights':{'heights':{'0':123}},'Dialogue':{'private':True}},
                         'worldmap://map02/script-operands':{'WorldScriptOperands':{'entries':{}},'Unsupported':{}},
                         'worldmap://map03/scripted-placement-allocations':{'WorldMapScriptedPlacementAllocations':{'scene':'map03','operations':[]}},
                         'scene://town01':{'Unrelated':{'private':True}},
                         'actor://other':{'Transform':{'x':9}}}
            before=deepcopy(p._document());key=state_key(p)
            expected={'scene://map01':{'FloorHeights':{'heights':{'0':123}}},
                      'worldmap://map02/script-operands':deepcopy(p.overrides['worldmap://map02/script-operands']),
                      'worldmap://map03/scripted-placement-allocations':deepcopy(p.overrides['worldmap://map03/scripted-placement-allocations'])}
            self.assertEqual(snapshot(p),expected)
            detached=snapshot(p);detached['scene://map01']['FloorHeights']['heights']['0']=999
            self.assertEqual(snapshot(p),expected)
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/state') as response:
                    import json
                    state=json.load(response)
                self.assertEqual(state['worldmap_edit_bindings'],expected)
                self.assertEqual(state['worldmap_authoring_state_key'],key)
                p.overrides['scene://map01']['FloorHeights']['heights']['0']=124
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/state') as response:changed=json.load(response)
                self.assertNotEqual(changed['worldmap_authoring_state_key'],key)
                self.assertEqual(changed['worldmap_edit_bindings']['scene://map01']['FloorHeights']['heights']['0'],124)
                p.overrides['scene://map01']['FloorHeights']['heights']['0']=123
            self.assertEqual(p._document(),before)

    def test_complete_scripted_map_http_and_stale_refusal(self):
        base,fallback,man,floor,binding,expected,_=ledger();provenance={k:binding[k] for k in ('scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256')}
        inputs=(base,provenance,floor,base,[],fallback,man,man,{},[])
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
            p.overrides[owner('map01')]={COMPONENT:binding};atomic_write(base_path(p,binding),base);key=state_key(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_current_map._inputs',return_value=inputs):
                value=inspect(p,'map01',key);self.assertEqual(b64decode(value['current_map_base64']),expected);self.assertEqual(b64decode(value['normal_map_base64']),base)
                with http_server(p) as (server,post):
                    status,actual=post('/api/worldmap-current-map',dict(scene='map01',source_key=key));self.assertEqual(status,200,actual);self.assertEqual(actual,value)
                    self.assertEqual(post('/api/worldmap-current-map',dict(scene='map01',source_key=key,extra=True))[0],400)
                    with urlopen(f'http://127.0.0.1:{server.server_port}/worldmap-current-map.js') as response:self.assertIn(b'qualifyCurrentWorldMap',response.read())
                    with urlopen(f'http://127.0.0.1:{server.server_port}/worldmap-scripted-placement-scene.js') as response:self.assertIn(b'qualifyScriptedWorldScene',response.read())
                    for filename in ('worldmap-scripted-creation-state.js','worldmap-scripted-creation-editor.js'):
                        with urlopen(f'http://127.0.0.1:{server.server_port}/{filename}') as response:self.assertIn(b'Scripted',response.read())
            with patch('sdk.worldmap_current_map._inputs',side_effect=AssertionError('stale must refuse before reading')):
                with self.assertRaises(ProjectError):inspect(p,'map01','0'*64)
            self.assertEqual(p._document(),held)
