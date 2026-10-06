from copy import deepcopy
import unittest
from sdk.project import ProjectError,ProjectService
from sdk.draft_repeat_group import preview,proposal_view
from test_draft_repeat import DraftRepeatTests as Fixtures
class ArrangementTests(Fixtures):
    def test_arrangement_preserves_members_relative_positions_atomic_history_and_save(self):
        p=self.p;donor=self.doc['actors'][0]['semantic_id'];second=deepcopy(self.doc['actors'][0]);second['semantic_id']=donor[:-4]+'0002';second['record_index']=2;p.imports[p.active_scene]['actors'].append(second)
        p.command(dict(type='create_actor_draft',donor_entity_id=second['semantic_id'],position=dict(x=512,z=640),name='Other'))
        ids=sorted(p.actor_drafts);request=dict(entity_ids=ids,count=2,step=dict(x=128,z=-64));before=deepcopy(p.actor_drafts);imports=deepcopy(p.imports);depth=len(p.undo_stack)
        report=preview(p,request);self.assertEqual(report,preview(p,request));self.assertEqual(len(report['copies']),4);view=proposal_view(p,report);self.assertEqual(p.actor_drafts,before)
        for row in report['copies']:
            source=before[row['source_entity_id']];self.assertEqual(row['draft']['donor_entity_id'],source['donor_entity_id']);self.assertEqual(row['draft']['position'],{a:source['position'][a]+row['copy_index']*request['step'][a] for a in ('x','z')})
        grid=preview(p,{**request,'columns':2});self.assertEqual(len(grid['copies']),4)
        for row in grid['copies']:
            source=before[row['source_entity_id']];index=row['copy_index'];self.assertEqual(row['draft']['position'],dict(x=source['position']['x']+(index%2)*128,z=source['position']['z']+(index//2)*-64))
        p.command(dict(type='repeat_actor_drafts',**request,review_key=report['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.actor_drafts,view.actor_drafts);self.assertEqual(p.imports,imports)
        p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)
        stable=deepcopy((p.actor_drafts,p.undo_stack))
        with self.assertRaises(ProjectError):p.command(dict(type='repeat_actor_drafts',**request,review_key=report['review_key']))
        for edit in [dict(entity_ids=[ids[0]]),dict(entity_ids=ids*2),dict(count=True),dict(count=128),dict(step=dict(x=16320,z=0)),dict(extra=1)]:
            with self.assertRaises((ProjectError,ValueError)):preview(p,{**request,**edit})
        self.assertEqual((p.actor_drafts,p.undo_stack),stable)
if __name__=='__main__':unittest.main()
