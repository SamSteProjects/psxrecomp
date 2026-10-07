"""A sampled external pose respects one/all native scene inspection scope."""
from copy import deepcopy
import base64,unittest
from unittest.mock import patch
from sdk import model_mesh_append
from sdk.scene_preview import preview_shape_instance,preview_shape_instances
from test_model_primitive_workflow import http_server
from test_model_mesh_animation_pose import animated,pose
from test_model_mesh_append import glb
import test_model_mesh_scene_preview as fixtures

class MeshSceneScopeTests(unittest.TestCase):
 def test_sampled_pose_single_all_geometry_and_refusals_are_read_only(self):
  helper=fixtures.MeshScenePreviewTests();self.addCleanup(helper.doCleanups)
  p,asset,donor,_,scene=helper.fixture()
  source=model_mesh_append.source(p,asset,'a'*64)
  content=animated(glb(),[(0,'translation','LINEAR',[[0,0,0],[10,20,30]])])
  candidate,binding,r=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,animation_pose=pose())
  literal=glb(lambda doc:doc['nodes'][0].update(translation=[5,10,15]))
  expected,_,_=model_mesh_append.prepare(p,asset,literal,donor,source['effective_sha256'],'a'*64)
  self.assertEqual(candidate,expected)
  body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,review_key=r['review_key'],proposed_sha256=r['proposed_sha256'],animation_pose=pose(),entity_id='posed',all_instances=False)
  before=deepcopy((p._document(),p.undo_stack,p.redo_stack,scene))
  with http_server(p) as (server,post),patch.dict(p.assets.records,{asset:dict(id=asset)}),patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(server.scene_previews,'preview',return_value=scene),patch.object(server,'model_preview',side_effect=lambda asset,**kw:kw['prepared']):
   status,single=post('/api/model-mesh-append-scene-preview',body);self.assertEqual(status,200,single)
   self.assertNotIn('proposal_instances',single);self.assertEqual(single['preview'],preview_shape_instance(scene,asset,'posed',expected,binding))
   status,all_=post('/api/model-mesh-append-scene-preview',{**body,'all_instances':True});self.assertEqual(status,200,all_)
   oracle=preview_shape_instances(scene,asset,expected,binding)
   for key in oracle:self.assertEqual(all_[key],oracle[key])
   self.assertEqual([row['entity_id'] for row in all_['proposal_instances']],['one','two','posed'])
   for changed in [dict(animation_pose=pose(.25)),dict(entity_id='missing'),dict(entity_id='wrong'),dict(all_instances=1),dict(proposed_sha256='0'*64)]:
    self.assertEqual(post('/api/model-mesh-append-scene-preview',{**body,**changed})[0],400)
  self.assertEqual((p._document(),p.undo_stack,p.redo_stack,scene),before)
