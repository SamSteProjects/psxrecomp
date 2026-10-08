from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from sdk.project import ProjectService,ProjectError
from sdk.project_copy import source_key
from sdk.actor_position_preview import review,proposal_view,qualify_instances
from test_project_workflow import synthetic_scene

class ActorPositionPreviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=ProjectService(Path(self.tmp.name));self.p.import_metadata(synthetic_scene());self.id=self.p.state()['scene']['entities'][0]['id']
 def request(self,id=None):return dict(entity_id=id or self.id,position=dict(x=128,z=256),project_source_key=source_key(self.p))
 def test_actor_detached_projection_preserves_y_history_and_imports(self):
  self.p.command(dict(type='set_transform',entity_id=self.id,position=dict(y=512)))
  before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records))
  report=review(self.p,self.request());view=proposal_view(self.p,report)
  self.assertEqual(report['proposed_position'],dict(x=128,y=512,z=256));self.assertEqual(view.overrides[self.id]['Transform']['position'],dict(x=128,y=512,z=256))
  self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records),before)
 def test_npc_detached_projection_retains_donor_and_fields(self):
  self.p.command(dict(type='create_actor_draft',donor_entity_id=self.id,position=dict(x=64,z=128),name='Resident'));id=next(iter(self.p.actor_drafts));before=deepcopy(self.p.actor_drafts)
  report=review(self.p,self.request(id));view=proposal_view(self.p,report)
  self.assertEqual(report['kind'],'npc');self.assertEqual(view.actor_drafts[id],{**before[id],'position':dict(x=128,z=256)});self.assertEqual(self.p.actor_drafts,before)
 def test_stale_forged_unsupported_and_unknown_refuse_without_changes(self):
  before=deepcopy((self.p._document(),self.p.undo_stack));request=self.request()
  for changed in [{**request,'project_source_key':'0'*64},{**request,'entity_id':'missing'},{**request,'position':dict(x=65,z=256)},{**request,'position':dict(x=128,z=256,y=0)},{**request,'position':dict(x=True,z=256)}]:
   with self.assertRaises(ProjectError):review(self.p,changed)
  report=review(self.p,request);report['proposed_position']['y']=999
  with self.assertRaises(ProjectError):proposal_view(self.p,report)
  self.assertEqual((self.p._document(),self.p.undo_stack),before)
 def test_complete_projection_qualification_rejects_ownership_rotation_and_neighbors(self):
  report=review(self.p,self.request());matrix=[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]
  row=dict(entity_id=self.id,asset_id='model',position=report['current_position'],model_to_scene=matrix,evidence=dict(runtime='unknown',height='unknown'))
  current=dict(schema='legaia.scene-preview.v1',coordinate_system='editor_field_y_up_source_units',source_key=report['scene_preview_source_key'],scene_id=self.p.active_scene,assets=[dict(id='geometry')],position_to_display=matrix,entities=[row,dict(entity_id='neighbor',value=1)])
  proposed=deepcopy(current);proposed['entities'][0]['position']=report['proposed_position']
  self.assertFalse(qualify_instances(current,proposed,report)['project_changed'])
  for mutate in [lambda d:d['assets'].append({}),lambda d:d['entities'][1].update(value=2),lambda d:d['entities'][0].update(asset_id='other'),lambda d:d['entities'][0]['model_to_scene'].__setitem__(0,2),lambda d:d['entities'][0]['evidence'].update(runtime='confirmed')]:
   changed=deepcopy(proposed);mutate(changed)
   with self.assertRaises(ProjectError):qualify_instances(current,changed,report)
