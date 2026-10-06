from copy import deepcopy
import unittest
from sdk.project import ProjectError,ProjectService
from sdk.draft_donor_group import review,proposal_view
import test_draft_group as fixtures

class DonorGroupTests(fixtures.DraftGroupTests):
    def test_donor_group_atomic_noop_stale_bounds_and_persistence(self):
        p=self.p;donor=self.doc['actors'][0]['semantic_id'];ids=self.ids;before=deepcopy((p.actor_drafts,p.undo_stack,p.redo_stack));request=dict(entity_ids=ids,donor_entity_id=donor);report=review(p,request)
        self.assertEqual(report['changed_count'],0);p.command(dict(type='assign_actor_draft_donors',**request,review_key=report['review_key']));self.assertEqual((p.actor_drafts,p.undo_stack,p.redo_stack),before)
        for change in ({'donor_entity_id':'missing'},{'entity_ids':[ids[0]]},{'entity_ids':ids*2},{'extra':True}):
            with self.assertRaises(ProjectError):review(p,{**request,**change})
        second=deepcopy(self.doc['actors'][0]);second['semantic_id']=donor[:-4]+'0002';second['record_index']=2;p.imports[p.active_scene]['actors'].append(second)
        request['donor_entity_id']=second['semantic_id'];before=deepcopy(p.actor_drafts);imports=deepcopy(p.imports);depth=len(p.undo_stack);report=review(p,request);view=proposal_view(p,report);self.assertEqual(p.actor_drafts,before)
        self.assertTrue(all(view.actor_drafts[i]=={**before[i],'donor_entity_id':second['semantic_id']} for i in ids));p.command(dict(type='assign_actor_draft_donors',**request,review_key=report['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.imports,imports)
        p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)
        p.command(dict(type='rename_actor_draft',entity_id=ids[0],name='Changed'));unchanged=deepcopy((p.actor_drafts,p.undo_stack))
        with self.assertRaises(ProjectError):p.command(dict(type='assign_actor_draft_donors',**request,review_key=report['review_key']))
        self.assertEqual((p.actor_drafts,p.undo_stack),unchanged)

if __name__=='__main__':unittest.main()
