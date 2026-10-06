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
    def test_grid_row_major_atomic_history_persistence_and_pattern_binding(self):
        p=self.p;p.command({'type':'set_actor_draft_position','entity_id':self.original,'position':{'x':128,'z':1024}});before=deepcopy(p.actor_drafts);self.request.update(count=5,columns=3,step={'x':64,'z':-128})
        report=preview(p,self.request)
        self.assertEqual([r['draft']['position'] for r in report['copies']],
                         [{'x':192,'z':1024},{'x':256,'z':1024},{'x':128,'z':896},{'x':192,'z':896},{'x':256,'z':896}])
        line=preview(p,{k:v for k,v in self.request.items() if k!='columns'})
        self.assertNotEqual(line['review_key'],report['review_key'])
        stale={'type':'repeat_actor_draft',**self.request,'columns':2,'review_key':report['review_key']}
        with self.assertRaises(ProjectError):p.command(stale)
        self.assertEqual(p.actor_drafts,before)
        depth=len(p.undo_stack);p.command(self.command());self.assertEqual(len(p.undo_stack),depth+1)
        self.assertEqual(p.actor_drafts[self.original],before[self.original]);p.undo();self.assertEqual(p.actor_drafts,before)
        p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)

    def test_grid_validation_and_last_row_bounds_leave_project_unchanged(self):
        before=deepcopy((self.p.actor_drafts,self.p.undo_stack))
        for edits in ({'columns':True},{'columns':1},{'columns':5},{'columns':2.5},
                      {'columns':2,'step':{'x':0,'z':64}}, {'columns':2,'step':{'x':64,'z':0}},
                      {'columns':2,'step':{'x':64,'z':16320}}):
            with self.assertRaises((ProjectError,ValueError)):preview(self.p,{**self.request,**edits})
        self.assertEqual((self.p.actor_drafts,self.p.undo_stack),before)
        # One grid row requires no Z spacing; the original remains its first cell.
        self.p.command({'type':'set_actor_draft_position','entity_id':self.original,'position':{'x':384,'z':256}})
        row=preview(self.p,{**self.request,'columns':4,'step':{'x':-64,'z':0}})
        self.assertEqual([r['draft']['position']['x'] for r in row['copies']],[320,256,192])

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

    def test_owned_families_repeat_source_qualification_and_complete_project_freshness(self):
        from unittest.mock import patch
        from test_importer_dialogue_authoring import fixture
        from test_wait_authoring import END
        from importer.wait_authoring import WaitAuthoringContext
        from importer.movement_authoring import MovementAuthoringContext
        from sdk.draft_repeat_group import preview as group_preview
        context,_=fixture(b'\x4c\x51\0\x80\xab\x09\x4a\x0a\0\x1fHi\0'+END);p=self.p;donor=p.actor_drafts[self.original]['donor_entity_id'];waits=WaitAuthoringContext(context);movement=MovementAuthoringContext(context)
        run=context.options(donor)['runs'][0]['semantic_id'];wait=waits.options(donor)['targets'][0]['semantic_id'];target=movement.options(donor)['targets'][0]['semantic_id']
        owned=dict(dialogue=dict(donor_entity_id=donor,runs={run:'Yo'}),appearance=dict(script_donor_entity_id=donor,donor_entity_id=donor),waits=dict(donor_entity_id=donor,entries={wait:dict(duration_ticks=11)}),movement=dict(donor_entity_id=donor,entries={target:dict(x=128,move_id=10)}))
        p.actor_drafts[self.original].update(deepcopy(owned))
        with patch.object(ProjectService,'_dialogue_context',return_value=context),patch.object(ProjectService,'_wait_context',return_value=waits),patch.object(ProjectService,'_movement_context',return_value=movement),patch.object(ProjectService,'appearance_options',return_value={'options':[{'donor_entity_id':donor}]}):
            before=deepcopy(p.actor_drafts);report=preview(p,self.request)
            for row in report['copies']:
                self.assertEqual({k:row['draft'][k] for k in owned},owned)
                self.assertEqual(row['draft']['movement'],before[self.original]['movement'])
            detached=proposal_view(p,report);detached.actor_drafts[report['copies'][0]['entity_id']]['movement']['entries'][target]['x']=256;self.assertEqual(p.actor_drafts,before)
            p.command(dict(type='repeat_actor_draft',**self.request,review_key=report['review_key']));after=deepcopy(p.actor_drafts);p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,after);p.undo()
            p.command(dict(type='create_actor_draft',donor_entity_id=donor,name='Second',position=dict(x=512,z=640)));second=next(i for i in p.actor_drafts if i!=self.original);p.actor_drafts[second].update(deepcopy(owned));group_request=dict(entity_ids=sorted(p.actor_drafts),count=1,step=dict(x=64,z=64));group=group_preview(p,group_request)
            for row in group['copies']:self.assertEqual({k:row['draft'][k] for k in owned},owned)
            before=deepcopy(p.actor_drafts);p.command(dict(type='repeat_actor_drafts',**group_request,review_key=group['review_key']));p.undo();self.assertEqual(p.actor_drafts,before)
            report=preview(p,self.request);p.command(dict(type='create_npc_preset',entity_id=self.original,name='Library changed'));before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):p.command(dict(type='repeat_actor_draft',**self.request,review_key=report['review_key']))
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            with patch.object(ProjectService,'appearance_options',return_value={'options':[]}):
                with self.assertRaises(ProjectError):preview(p,self.request)
            p.actor_drafts[self.original]['movement']['entries']={target[:-4]+'ffff':dict(x=128)}
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):preview(p,self.request)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            p.mode='live'
            with self.assertRaises(ProjectError):preview(p,self.request)

if __name__=='__main__':unittest.main()
