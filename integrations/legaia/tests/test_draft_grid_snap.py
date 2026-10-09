from copy import deepcopy
import unittest
from sdk.project import ProjectError
from sdk.draft_group import review,proposal_view
import test_draft_group as fixture

class DraftGridSnapTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.DraftGroupTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.p=self.fixture.p;self.ids=self.fixture.ids
    def test_complete_axes_donor_metadata_history_and_boundary(self):
        p=self.p;held=deepcopy(p.actor_drafts);depth=len(p.undo_stack);request=dict(entity_ids=self.ids,layout=dict(kind='snap',axes=['x'],spacing=256));r=review(p,request)
        view=proposal_view(p,r);self.assertEqual(p.actor_drafts,held)
        for identifier in self.ids:
            self.assertEqual(view.actor_drafts[identifier]['position'],dict(x=256,z=held[identifier]['position']['z']))
        p.command(dict(type='layout_actor_drafts',**request,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
        noop=review(p,request);self.assertEqual(noop['changed_count'],0);p.command(dict(type='layout_actor_drafts',**request,review_key=noop['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
        for identifier in self.ids:
            for key,value in held[identifier].items():
                if key!='position':self.assertEqual(p.actor_drafts[identifier][key],value)
        for identifier in set(held)-set(self.ids):self.assertEqual(p.actor_drafts[identifier],held[identifier])
        p.undo();self.assertEqual(p.actor_drafts,held)
        p.actor_drafts[self.ids[0]]['position']['x']=64;held=deepcopy((p.actor_drafts,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):review(p,request)
        self.assertEqual((p.actor_drafts,p.undo_stack,p.redo_stack),held)
    def test_strict_fields_spacing_and_axes(self):
        for axes,spacing in [(['z','x'],256),(['x','x'],256),([],256),(['x'],True),(['x'],65),(['x'],0),(['x'],4160)]:
            with self.assertRaises(ProjectError):review(self.p,dict(entity_ids=self.ids,layout=dict(kind='snap',axes=axes,spacing=spacing)))
