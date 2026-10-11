from base64 import b64encode
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import tempfile
from urllib.request import urlopen
from importer.worldmap_placements import decode_worldmap_placements
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_scene import inspect
from test_worldmap_scripted_placement_binding import ledger
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedSceneTests(TestCase):
    def test_current_native_membership_stable_identity_http_and_refusals(self):
        raw,fallback,man,floor,binding,current,audit=ledger()
        seeds=decode_worldmap_placements(raw,floor,scene='map01')['placements']
        provenance={k:binding[k] for k in ('scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256')}
        receipt=dict(source_record=provenance,current_map_base64=b64encode(current).decode(),floor_lut=floor,
            authored_decorations=[],authored_scripted_placements=deepcopy(audit['allocations']))
        asset='asset://map01/worldmap/models/0001'
        geometry=dict(scene='map01',source_record=dict(disc_sha256='b'*64,map_sha256=binding['source_map_sha256'],floor_lut_sha256=binding['source_floor_lut_sha256']),
            scene_graph=dict(assets=[dict(asset_id='ground',preview=dict(triangles=[[0,1,2]])),dict(asset_id=asset,preview=dict(vertices=[[0,0,0]],triangles=[[0,0,0]]))],
                entities=[dict(entity_id='ground',placement_scope='source_ground',asset_id='ground')]+[dict(s,asset_id=asset,renderable=True) for s in seeds],metrics={},coverage={},limitations=[]))
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());key=state_key(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_scripted_placement_scene.source',return_value=receipt),patch('sdk.worldmap_scripted_placement_scene.inspect_geometry',side_effect=lambda *a,**k:deepcopy(geometry)):
                result=inspect(p,'map01',key);graph=result['scene_graph'];allocation=audit['allocations'][0]
                authored=next(e for e in graph['entities'] if e.get('authored_placement_kind')=='scripted')
                self.assertEqual(authored['entity_id'],'scene://map01/worldmap/authored-placements/'+allocation['placement_id'].rsplit('/',1)[1])
                self.assertEqual(authored['source_position'],allocation['native_seed']['source_position'])
                self.assertEqual(authored['native_entity_id'],allocation['native_seed']['entity_id'])
                self.assertIsNone(authored['retail_seed']);self.assertEqual(graph['metrics']['entity_count'],len(seeds)+2)
                self.assertTrue(result['authored_geometry']);self.assertEqual(result['authored_entity_count'],1)
                unbound=deepcopy(receipt);unbound.update(current_map_base64=b64encode(raw).decode(),remaining_creation_capacity=32,authored_scripted_placements=[])
                review=dict(review_key='a'*64,proposed_map_base64=b64encode(current).decode(),proposed_map_sha256=binding['operations'][0]['proposed_map_sha256'],binding=binding,audit=audit)
                proposal=dict(requests=binding['operations'][0]['requests'],review_key='a'*64)
                with patch('sdk.worldmap_scripted_placement_scene.source',return_value=unbound),patch('sdk.worldmap_scripted_placement_scene._prepare',return_value=(raw,review)):
                    proposed=inspect(p,'map01',key,proposal)
                    self.assertEqual(proposed['representation'],'proposed-scripted-placement-source')
                    self.assertEqual(proposed['placement_layer'],'proposed');self.assertEqual(proposed['scene_graph']['entities'],result['scene_graph']['entities'])
                    self.assertEqual(proposed['scripted_proposal'],review)
                    with self.assertRaises(ProjectError):inspect(p,'map01',key,dict(proposal,review_key='0'*64))
                    with self.assertRaises(ProjectError):inspect(p,'map01',key,dict(proposal,extra=True))
                raised=deepcopy(receipt);raised['floor_lut']=[v+20 for v in floor]
                raised_seeds={s['entity_id']:s for s in decode_worldmap_placements(current,raised['floor_lut'],scene='map01')['placements']}
                for a in raised['authored_scripted_placements']:a['native_seed']=raised_seeds[a['native_seed']['entity_id']]
                with patch('sdk.worldmap_scripted_placement_scene.source',return_value=raised):
                    high=inspect(p,'map01',key)
                high_authored=next(e for e in high['scene_graph']['entities'] if e.get('authored_placement_kind')=='scripted')
                self.assertEqual(high_authored['source_position']['y'],authored['source_position']['y']-20)
                self.assertEqual(high['ground_layer'],'retail')
                original_entity=next(e for e in high['scene_graph']['entities'] if e.get('retail_seed'))
                self.assertEqual(original_entity['source_position']['y'],original_entity['retail_seed']['source_position']['y']-20)
                with http_server(p) as (server,post):
                    with urlopen(f'http://127.0.0.1:{server.server_port}/worldmap-scripted-placement-replay.js') as response:
                        self.assertIn(b'export async function replayScriptedWorldPlacements',response.read())
                    status,actual=post('/api/worldmap-scripted-placement-scene',dict(scene='map01',source_key=key))
                    self.assertEqual(status,200,actual);self.assertEqual(actual,result)
                    self.assertEqual(post('/api/worldmap-scripted-placement-scene',dict(scene='map01',source_key=key,extra=True))[0],400)
                    self.assertEqual(post('/api/worldmap-scripted-placement-scene',dict(scene='map01',source_key=key,scripted_proposal=None))[0],400)
                for bad in ('provenance','model','allocation'):
                    g=deepcopy(geometry);r=deepcopy(receipt)
                    if bad=='provenance':g['source_record']['map_sha256']='0'*64
                    if bad=='model':g['scene_graph']['assets'][1]['preview']['vertices']=[]
                    if bad=='allocation':r['authored_scripted_placements'][0]['native_seed']['source_position']['x']+=1
                    with patch('sdk.worldmap_scripted_placement_scene.source',return_value=r),patch('sdk.worldmap_scripted_placement_scene.inspect_geometry',return_value=g),self.subTest(bad=bad),self.assertRaises(ProjectError):inspect(p,'map01',key)
            with patch('sdk.worldmap_scripted_placement_scene.source',side_effect=AssertionError('stale must refuse before reading')):
                with self.assertRaises(ProjectError):inspect(p,'map01','0'*64)
                p.mode='live'
                with self.assertRaises(ProjectError):inspect(p,'map01',state_key(p))
                p.mode='edit'
            self.assertEqual(p._document(),held)
