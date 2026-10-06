from copy import deepcopy
from pathlib import Path
import tempfile, unittest
from sdk.project import ProjectService,ProjectError
from sdk.draft_group import review,proposal_view
from test_project_workflow import synthetic_scene

class DraftGroupTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.doc=synthetic_scene();self.p.import_metadata(self.doc)
        for i in range(3):self.p.command(dict(type='create_actor_draft',donor_entity_id=self.doc['actors'][0]['semantic_id'],position={'x':128+i*64,'z':512},name=f'Draft{i}'))
        self.p.save();self.ids=sorted(self.p.actor_drafts)[:2];self.request=dict(entity_ids=self.ids,delta={'x':64,'z':-128})
    def command(self,report=None):
        result=report or review(self.p,self.request)
        return dict(type='offset_actor_drafts',**self.request,review_key=result['review_key'])
    def test_detached_exact_selected_group_atomic_history_and_persistence(self):
        p=self.p;before=deepcopy(p.actor_drafts);imports=deepcopy(p.imports);depth=len(p.undo_stack)
        result=review(p,self.request);self.assertEqual(result,review(p,{**self.request,'entity_ids':list(reversed(self.ids))}))
        view=proposal_view(p,result)
        for i in self.ids:self.assertEqual(view.actor_drafts[i]['position'],{a:before[i]['position'][a]+self.request['delta'][a] for a in ('x','z')})
        self.assertEqual(p.actor_drafts,before);p.command(self.command(result));self.assertEqual(len(p.undo_stack),depth+1)
        for i in set(before)-set(self.ids):self.assertEqual(p.actor_drafts[i],before[i])
        self.assertEqual(p.imports,imports);p.undo();self.assertEqual(p.actor_drafts,before);self.assertFalse(p.dirty)
        p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)
    def test_stale_invalid_last_target_tampered_scene_and_live_reject(self):
        p=self.p;before=deepcopy((p.actor_drafts,p.undo_stack,p.redo_stack));old=self.command()
        for change in ({'entity_ids':self.ids[:1]},{'entity_ids':self.ids*2},{'entity_ids':[self.ids[0],'missing']},
                       {'delta':{'x':32,'z':0}},{'delta':{'x':True,'z':0}},{'delta':{'x':16320,'z':0}},{'extra':0}):
            with self.assertRaises((ProjectError,ValueError)):review(p,{**self.request,**change})
        self.assertEqual((p.actor_drafts,p.undo_stack,p.redo_stack),before)
        report=review(p,self.request);report['targets'][-1]['proposed']['x']+=64
        with self.assertRaises(ProjectError):proposal_view(p,report)
        p.command(dict(type='rename_actor_draft',entity_id=self.ids[0],name='Changed'))
        with self.assertRaises(ProjectError):p.command(old)
        report=review(p,{**self.request,'delta':{'x':0,'z':0}});depth=len(p.undo_stack)
        p.command(dict(type='offset_actor_drafts',**report['request'],review_key=report['review_key']));self.assertEqual(len(p.undo_stack),depth)
        p.mode='live'
        with self.assertRaises(ProjectError):review(p,self.request)
        with self.assertRaises(ProjectError):p.command(old)

if __name__=='__main__':unittest.main()
