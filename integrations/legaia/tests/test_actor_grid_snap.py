from copy import deepcopy
import unittest
from sdk.project import ProjectError
import test_actor_placement_layout as fixture
from sdk.scene_preview import actor_placement_proposal_view

class ActorGridSnapTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.ActorLayoutTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.p=self.fixture.p

    def test_single_axis_preservation_history_noop_and_boundary(self):
        p=self.p;p.command(dict(type='set_transform',entity_id=fixture.A,position=dict(x=192,y=-12,z=320)));held=deepcopy(p.overrides);depth=len(p.undo_stack)
        ids=[fixture.A,fixture.C];op=dict(kind='snap',axes=['x'],spacing=256);r=p.actor_placement_layout(ids,op);self.assertTrue(all(t['proposed']['x']==256 for t in r['targets']));self.assertEqual(p.overrides,held)
        view=actor_placement_proposal_view(p,r);self.assertEqual(view.overrides[fixture.A]['Transform']['position'],dict(x=256,y=-12,z=320));self.assertEqual(p.overrides,held)
        p.command(dict(type='layout_actor_placements',scene_id=r['scene_id'],actor_ids=ids,layout=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[fixture.A]['Transform']['position'],dict(x=256,y=-12,z=320))
        noop=p.actor_placement_layout(ids,op);self.assertEqual(noop['changed_count'],0);p.command(dict(type='layout_actor_placements',scene_id=r['scene_id'],actor_ids=ids,layout=op,review_key=noop['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
        p.undo();self.assertEqual(p.overrides,held);p.command(dict(type='set_transform',entity_id=fixture.A,position=dict(x=64)))
        held=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):p.actor_placement_layout(ids,op)
        self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)

    def test_strict_fields_axes_spacing(self):
        for op in [dict(kind='snap',axes=a,spacing=s) for a,s in [(['z','x'],256),(['x','x'],256),([],256),(['x'],True),(['x'],65),(['x'],0),(['x'],4160),(['x'],256.0)]]+[dict(kind='snap',axes=['x'],spacing=256,axis='x')]:
            with self.assertRaises(ProjectError):self.p.actor_placement_layout([fixture.A,fixture.C],op)
