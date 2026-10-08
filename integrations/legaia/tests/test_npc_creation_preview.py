from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from sdk.project import ProjectService,ProjectError
from sdk.project_copy import source_key
from sdk.npc_creation_preview import review,proposal_view,qualify_instances
from test_project_workflow import synthetic_scene

class NpcCreationPreviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=ProjectService(Path(self.tmp.name));self.p.import_metadata(synthetic_scene());self.id=self.p.state()['scene']['entities'][0]['id']
 def request(self):return dict(donor_entity_id=self.id,name='Prospective resident',position=dict(x=128,z=256),project_source_key=source_key(self.p))
 def test_detached_creation_and_deterministic_temporary_identity(self):
  self.p.command(dict(type='create_actor_draft',donor_entity_id=self.id,name='Existing',position=dict(x=64,z=128)))
  before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records));report=review(self.p,self.request());view=proposal_view(self.p,report)
  self.assertEqual(view.actor_drafts[report['preview_entity_id']],report['draft']);self.assertEqual(len(view.actor_drafts),len(self.p.actor_drafts)+1);self.assertEqual(report,review(self.p,self.request()))
  self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records),before)
  self.p.command(report['command']);self.assertNotIn(report['preview_entity_id'],self.p.actor_drafts);self.p.undo();self.assertEqual(self.p._document(),before[0])
 def test_invalid_stale_forged_and_capacity_refuse(self):
  request=self.request();before=deepcopy(self.p._document())
  for bad in [{**request,'project_source_key':'0'*64},{**request,'donor_entity_id':'unknown'},{**request,'name':' '},{**request,'position':dict(x=65,z=256)},{**request,'position':dict(x=True,z=256)},{**request,'position':dict(x=128,z=256,y=0)}]:
   with self.assertRaises(ProjectError):review(self.p,bad)
  report=review(self.p,request);report['draft']['name']='forged'
  with self.assertRaises(ProjectError):proposal_view(self.p,report)
  self.assertEqual(self.p._document(),before)
  for index in range(128):self.p.command(dict(type='create_actor_draft',donor_entity_id=self.id,name='Resident '+str(index),position=dict(x=64,z=128)))
  with self.assertRaises(ProjectError):review(self.p,self.request())
 def test_complete_scene_qualification_retains_existing_owners_and_geometry(self):
  report=review(self.p,self.request());matrix=[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]
  current=dict(schema='legaia.scene-preview.v1',coordinate_system='editor_field_y_up_source_units',scene_id=self.p.active_scene,source_key=report['scene_preview_source_key'],assets=[dict(geometry_key='mesh')],position_to_display=matrix,entities=[dict(entity_id=self.id,owner=1)])
  target=dict(entity_id=report['preview_entity_id'],kind='actor_draft',name=report['draft']['name'],donor_entity_id=self.id,source_actor_id=self.id,position=dict(x=128,z=256,y=None),geometry_key='mesh',renderable=True)
  proposed=deepcopy(current);proposed['entities'].append(target);self.assertFalse(qualify_instances(current,proposed,report)['project_changed'])
  for change in [lambda d:d['assets'].append(dict(geometry_key='other')),lambda d:d['entities'][0].update(owner=2),lambda d:d['entities'][-1].update(source_actor_id='other'),lambda d:d['entities'][-1]['position'].update(y=0),lambda d:d['entities'][-1].update(renderable=False),lambda d:d['entities'].append(deepcopy(target))]:
   bad=deepcopy(proposed);change(bad)
   with self.assertRaises(ProjectError):qualify_instances(current,bad,report)
