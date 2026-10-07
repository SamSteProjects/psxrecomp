"""A declared GLB pose stays atomic across mapped native sections."""
from copy import deepcopy
import base64, unittest
from unittest.mock import patch
from sdk import model_mesh_append,model_mesh_batch,model_face_addition
from sdk.model_mesh_sources import read_source,validate
from sdk.project import ProjectError,digest
from test_model_mesh_animation_pose import animated,pose
from test_model_mesh_primitive_selection import sections
import test_model_mesh_append_normals as normal_fixtures
from test_model_primitive_workflow import http_server

class AnimationBatchTests(unittest.TestCase):
 def fixture(self):
  helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups)
  p,asset,donor=helper.fixture(0x14)
  self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
  self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
  source=model_mesh_append.source(p,asset,'a'*64)
  mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
  content=animated(sections(),[(0,'translation','LINEAR',[[0,0,0],[10,20,30]])])
  return p,asset,source,mappings,content
 def test_complete_static_oracle_retention_history_and_replay(self):
  for replace in (False,True):
   with self.subTest(replace_objects=replace):
    p,asset,source,mappings,content=self.fixture();before=deepcopy(p._document())
    original,_,base,*_=model_face_addition._context(p,asset,'a'*64)
    args=(asset,content,mappings,source['effective_sha256'],'a'*64)
    candidate,_,r=model_mesh_batch.prepare(p,*args,animation_pose=pose(),replace_objects=replace)
    literal=sections(dict(translation=[5,10,15]))
    expected,_,_=model_mesh_batch.prepare(p,asset,literal,mappings,source['effective_sha256'],'a'*64,replace_objects=replace)
    self.assertEqual(candidate,expected);self.assertEqual(p._document(),before)
    self.assertTrue(all(s['review']['animation_pose']==pose() for s in r['steps']))
    with self.assertRaises(ProjectError):model_mesh_batch.apply(p,*args,review_key=r['review_key'],animation_pose=pose(.25),replace_objects=replace)
    self.assertEqual(p._document(),before);depth=len(p.undo_stack)
    model_mesh_batch.apply(p,*args,review_key=r['review_key'],animation_pose=pose(),replace_objects=replace)
    record=p.model_overrides[asset]['mesh_imports'][-1]
    self.assertEqual(record['recipe']['animation_pose'],pose());self.assertEqual(read_source(p,record),content)
    self.assertEqual(len(p.undo_stack),depth+1)
    self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),expected)
    held=deepcopy(p._document());binding=p.model_overrides[asset]
    validate(p,asset,binding,base,original,digest(p.imports[binding['source_scene_id']]))
    self.assertEqual(p._document(),held);p.undo();self.assertEqual(p._document(),before)
    p.redo();self.assertEqual(p._document(),held)
 def test_http_pose_and_changed_time_refusal(self):
  p,asset,source,mappings,content=self.fixture();before=deepcopy(p._document())
  body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,animation_pose=pose())
  with http_server(p) as (_,post):
   status,r=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,r)
   self.assertEqual(r['animation_pose'],pose());self.assertEqual(p._document(),before)
   status,_=post('/api/model-mesh-batch',dict(body,review_key=r['review_key'],animation_pose=pose(.25)))
   self.assertEqual(status,400);self.assertEqual(p._document(),before)
   status,_=post('/api/model-mesh-batch-preview',dict(body,animation_pose=dict(animation_index=True,time_seconds=.5)))
   self.assertEqual(status,400);self.assertEqual(p._document(),before)
   status,state=post('/api/model-mesh-batch',dict(body,review_key=r['review_key']));self.assertEqual(status,200,state)
  self.assertEqual(p.model_overrides[asset]['mesh_imports'][-1]['recipe']['animation_pose'],pose())
