from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from sdk.project import ProjectService,ProjectError
from sdk.npc_script_reset import source,review
from test_project_workflow import synthetic_scene

class NpcScriptReset(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene())
        donor='scene://fixture/actors/man-p1/0001';self.p.command(dict(type='create_actor_draft',name='NPC',donor_entity_id=donor,position=dict(x=128,z=256)))
        self.id=next(iter(self.p.actor_drafts));draft=self.p.actor_drafts[self.id];prefix='script://fixture/actors/man-p1/0001/'
        draft['waits']=dict(donor_entity_id=donor,entries={prefix+'wait/0001':dict(duration_ticks=12)})
        draft['facing']=dict(donor_entity_id=donor,entries={prefix+'facing/0002':dict(sector=4)})
        draft['effect_colors']=dict(donor_entity_id=donor,entries={prefix+'effect-color/0003':dict(red=1,green=2,blue=3,intensity=-4)})
        self.p._validate_actor_draft(self.id,draft)

    def test_atomic_selected_reset_history_and_persistence(self):
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));request=dict(entity_id=self.id,families=['waits','facing'])
        report=review(self.p,request);self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.redo_stack))
        self.assertEqual([r['id'] for r in report['removed']],['waits','facing']);self.assertFalse(report['native_byte_preview'])
        expected=deepcopy(self.p.actor_drafts[self.id]);expected.pop('waits');expected.pop('facing')
        self.p.command(dict(type='reset_actor_draft_script',**request,review_key=report['review_key']))
        self.assertEqual(self.p.actor_drafts[self.id],expected);self.assertEqual(len(self.p.undo_stack),len(before[1])+1)
        self.p.undo();self.assertEqual(self.p._document(),before[0]);self.p.redo()
        self.p.save();opened=ProjectService.open(self.p.root);self.assertEqual(opened.actor_drafts,self.p.actor_drafts)

    def test_stale_unknown_unowned_order_mode_and_wrong_owner_refuse(self):
        request=dict(entity_id=self.id,families=['waits','facing']);report=review(self.p,request)
        for selected in [[],['appearance'],['movement'],['waits','waits'],['facing','waits'],[True],None]:
            before=deepcopy((self.p._document(),self.p.undo_stack))
            with self.assertRaises(ProjectError):review(self.p,dict(request,families=selected))
            self.assertEqual(before,(self.p._document(),self.p.undo_stack))
        self.p.command(dict(type='rename_actor_draft',entity_id=self.id,name='Changed'));before=deepcopy((self.p._document(),self.p.undo_stack))
        with self.assertRaises(ProjectError):self.p.command(dict(type='reset_actor_draft_script',**request,review_key=report['review_key']))
        self.assertEqual(before,(self.p._document(),self.p.undo_stack))
        self.p.mode='live'
        with self.assertRaises(ProjectError):source(self.p,self.id)
        self.p.mode='edit';self.p.active_scene='scene://other'
        with self.assertRaises(ProjectError):source(self.p,self.id)
