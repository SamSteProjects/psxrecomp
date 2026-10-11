"""Selected model assignments preserve unselected donor descendants."""
from copy import deepcopy
from pathlib import Path
import base64, struct, tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation_binding import COMPONENT, owner
from sdk.worldmap_placement_model import review
from test_worldmap_decoration_group import group_fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationGroupModelTests(TestCase):
    def test_v1_v2_literal_model_words_descendants_http_and_history(self):
        for version_two in (False, True):
            with self.subTest(version_two=version_two), tempfile.TemporaryDirectory() as root:
                raw,floor,provenance,rows,current,binding=group_fixture(version_two)
                p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
                p.overrides[owner('map01')]={COMPONENT:binding};p.save()
                held=deepcopy(p._document());history=deepcopy(p.undo_stack)
                context=(raw,provenance,{},48,floor,None,raw,[])
                geometry=dict(scene_graph=dict(assets=[dict(asset_id=f'asset://map01/worldmap/models/{i:04d}',source_record=dict(slot=i),preview=dict(vertices=[[0,0,0]],triangles=[[0,0,0]])) for i in (1,2)]))
                with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_model.context',return_value=context),patch('sdk.worldmap_geometry.inspect',return_value=geometry):
                    ids=sorted(r['placement_id'] for r in rows[:2]);model=1 if version_two else 2;key=state_key(p)
                    receipt=review(p,'map01',key,ids,model)
                    self.assertEqual(receipt['schema_version'],'legaia.worldmap-decoration-model-review.v2')
                    expected=bytearray(current)
                    for row in rows[:2]:struct.pack_into('<H',expected,row['record_index']*32+16,model)
                    self.assertEqual(base64.b64decode(receipt['proposed_map_base64']),bytes(expected))
                    self.assertEqual(receipt['audit']['retained_child_models'],[dict(placement_id=rows[2]['placement_id'],model_pool_index=2 if version_two else 1)])
                    self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
                    for invalid in ([],ids[::-1],[ids[0],ids[0]],['foreign'],[True]):
                        with self.assertRaises(ProjectError):review(p,'map01',key,invalid,model)
                    command=dict(type='assign_worldmap_authored_models',scene='map01',source_key=key,placement_ids=ids,model_pool_index=model,review_key=receipt['review_key'])
                    with http_server(p) as (_,post):
                        body={k:v for k,v in command.items() if k not in ('type','review_key')}
                        self.assertEqual(post('/api/worldmap-decoration-model-review',body)[0],200)
                        self.assertEqual(post('/api/worldmap-decoration-model-review',{**body,'placement_ids':ids[0]})[0],400)
                        self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                        self.assertEqual(post('/api/command',command)[0],200)
                        self.assertEqual(post('/api/command',command)[0],400)
                    self.assertEqual(len(p.undo_stack),len(history)+1)
                    with self.assertRaises(ProjectError):review(p,'map01',state_key(p),ids,model)
                    # Mixed matching/changing members are valid; only one word changes.
                    mixed=review(p,'map01',state_key(p),sorted([ids[0],rows[2]['placement_id']]),model)
                    self.assertEqual(len(mixed['audit']['changed_bytes']),1)
                    applied=deepcopy(p._document());p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                    p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied);p.undo();self.assertEqual(p.undo_stack,history)
