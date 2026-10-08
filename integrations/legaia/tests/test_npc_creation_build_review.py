from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.project_copy import source_key
from sdk.build import authored_state_key
from sdk.npc_creation_build_review import review
from test_project_workflow import synthetic_scene

class ProspectiveNpcBuildReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=ProjectService(Path(self.tmp.name));self.p.import_metadata(synthetic_scene());self.id=self.p.state()['scene']['entities'][0]['id']
 def request(self):return dict(donor_entity_id=self.id,name='Resident',position=dict(x=128,z=256),project_source_key=source_key(self.p))
 def test_complete_isolated_inputs_and_blocker_propagation(self):
  self.p.command(dict(type='set_transform',entity_id=self.id,position=dict(y=512)));self.p.command(dict(type='create_actor_draft',donor_entity_id=self.id,name='Existing',position=dict(x=64,z=128)))
  before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records))
  def assess(view):
   self.assertEqual(view.overrides,self.p.overrides);self.assertEqual(len(view.actor_drafts),2)
   for id,draft in self.p.actor_drafts.items():self.assertEqual(view.actor_drafts[id],draft)
   return dict(source_key=authored_state_key(view),included_npc_draft_count=2,read_only=True,status='blocked',normal_build_ready=False,blockers=[dict(message='Existing unsupported Y')])
  with patch('sdk.npc_creation_build_review.build_review',side_effect=assess):result=review(self.p,self.request())
  self.assertEqual(result['build_review']['blockers'][0]['message'],'Existing unsupported Y');self.assertEqual(result['existing_npc_draft_count'],1);self.assertEqual(result['proposed_npc_draft_count'],2);self.assertFalse(result['output_written']);self.assertNotIn(result['review']['preview_entity_id'],self.p.actor_drafts)
  self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack,self.p.imports,self.p.assets.records),before)
 def test_invalid_source_and_inconsistent_assessment_refuse(self):
  with self.assertRaises(ProjectError):review(self.p,{**self.request(),'project_source_key':'0'*64})
  with patch('sdk.npc_creation_build_review.build_review',return_value=dict(source_key='0'*64,included_npc_draft_count=1,read_only=True)):
   with self.assertRaises(ProjectError):review(self.p,self.request())
