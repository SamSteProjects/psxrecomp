from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService,ProjectError
from sdk.draft_repeat import preview,proposal_view
from sdk.build import authored_state_key
from test_project_workflow import synthetic_scene

class DraftRepeatTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup);self.p=ProjectService(Path(self.directory.name));self.doc=synthetic_scene();self.p.import_metadata(self.doc)
        self.p.command({'type':'create_actor_draft','donor_entity_id':self.doc['actors'][0]['semantic_id'],'position':{'x':128,'z':256},'name':'Resident'});self.original=next(iter(self.p.actor_drafts));self.p.save()
        self.request={'entity_id':self.original,'count':3,'step':{'x':64,'z':128},'name':'Copy'}
    def command(self):
        report=preview(self.p,self.request);return {'type':'repeat_actor_draft',**self.request,'review_key':report['review_key']}
    def test_deterministic_detached_preview_one_history_persistence_and_independence(self):
        p=self.p;before=deepcopy(p.actor_drafts);source=deepcopy(p.imports);key=authored_state_key(p);depth=len(p.undo_stack)
        report=preview(p,self.request);self.assertEqual(report,preview(p,self.request));self.assertEqual([r['draft']['position']['x'] for r in report['copies']],[192,256,320]);self.assertEqual(p.actor_drafts,before)
        view=proposal_view(p,report);self.assertEqual(len(view.actor_drafts),4);view.actor_drafts[self.original]['name']='Detached';self.assertEqual(p.actor_drafts,before)
        p.command(self.command());self.assertEqual(len(p.undo_stack),depth+1);self.assertNotEqual(authored_state_key(p),key);self.assertEqual(p.actor_drafts[self.original],before[self.original]);self.assertEqual(p.imports,source)
        p.undo();self.assertEqual(p.actor_drafts,before);self.assertFalse(p.dirty);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)
        new=report['copies'][0]['entity_id'];p.command({'type':'set_actor_draft_position','entity_id':new,'position':{'x':384,'z':384}});self.assertEqual(p.actor_drafts[self.original],before[self.original]);self.assertEqual(p.actor_drafts[report['copies'][1]['entity_id']]['position'],{'x':256,'z':512})
    def test_last_copy_bounds_count_spacing_invalid_fields_fail_without_mutation(self):
        p=self.p;before=deepcopy(p.actor_drafts);history=deepcopy(p.undo_stack)
        for edits in [{'count':True},{'count':0},{'count':128},{'count':3,'step':{'x':8192,'z':0}},{'step':{'x':32,'z':0}},{'step':{'x':64,'y':0}},{'name':''},{'name':'x'*117},{'bytes':'00'}]:
            with self.assertRaises((ProjectError,ValueError)):preview(p,{**self.request,**edits})
        self.assertEqual(p.actor_drafts,before);self.assertEqual(p.undo_stack,history)
    def test_stale_source_replay_and_live_reject_atomic_group(self):
        p=self.p;cmd=self.command();p.command({'type':'rename_actor_draft','entity_id':self.original,'name':'Changed'});before=deepcopy(p.actor_drafts)
        with self.assertRaises(ProjectError):p.command(cmd)
        self.assertEqual(p.actor_drafts,before);fresh=self.command();p.command(fresh);before=deepcopy(p.actor_drafts)
        with self.assertRaises(ProjectError):p.command(fresh)
        self.assertEqual(p.actor_drafts,before);p.mode='live'
        with self.assertRaises(ProjectError):p.command(self.command())
    def test_preview_tampering_and_batch_history_source_reimport_guard(self):
        p=self.p;report=preview(p,self.request);report['copies'][-1]['draft']['position']['x']+=64
        with self.assertRaises(ProjectError):proposal_view(p,report)
        p.command(self.command());p.undo();p.actor_drafts.clear();p.undo_stack.clear()
        changed=deepcopy(self.doc);changed['actors'][0]['imported_transform']['position']['x']=192
        with self.assertRaisesRegex(ProjectError,'command history'):p.import_metadata(changed)

if __name__=='__main__':unittest.main()
