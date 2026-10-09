from copy import deepcopy
import unittest
from sdk.project import ProjectError
from sdk.scene_preview import actor_placement_proposal_view
import test_actor_placement_layout as fixture

class ActorPositionRotationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.ActorLayoutTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.p=self.fixture.p
    def test_native_rotation_fixed_anchor_height_and_atomic_history(self):
        p=self.p;p.command(dict(type='set_transform',entity_id=fixture.A,position=dict(x=640,z=512,y=-12)));p.command(dict(type='set_transform',entity_id=fixture.B,position=dict(x=512,z=512)));held=deepcopy(p.overrides);depth=len(p.undo_stack)
        ids=[fixture.A,fixture.B];op=dict(kind='rotate_angle',anchor_entity_id=fixture.B,angle_degrees=45);r=p.actor_placement_layout(ids,op);rows={row['entity_id']:row for row in r['targets']};self.assertEqual(rows[fixture.A]['proposed'],dict(x=576,z=576,y=-12));self.assertEqual(rows[fixture.B]['proposed'],rows[fixture.B]['effective'])
        view=actor_placement_proposal_view(p,r);self.assertEqual(view.overrides[fixture.A]['Transform']['position'],dict(x=576,z=576,y=-12));self.assertEqual(p.overrides,held)
        p.command(dict(type='layout_actor_placements',scene_id=r['scene_id'],actor_ids=ids,layout=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
        zero={**op,'angle_degrees':0};noop=p.actor_placement_layout(ids,zero);self.assertEqual(noop['changed_count'],0);p.command(dict(type='layout_actor_placements',scene_id=r['scene_id'],actor_ids=ids,layout=zero,review_key=noop['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
        p.undo();self.assertEqual(p.overrides,held)
        p.command(dict(type='set_transform',entity_id=fixture.A,position=dict(x=64,z=64)));held=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
        with self.assertRaises(ProjectError):p.actor_placement_layout(ids,dict(kind='rotate_angle',anchor_entity_id=fixture.A,angle_degrees=180))
        self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)
    def test_degrees_fields_and_selection(self):
        op=dict(kind='rotate_angle',anchor_entity_id=fixture.B,angle_degrees=45)
        for change in [dict(angle_degrees=True),dict(angle_degrees=45.5),dict(angle_degrees=-360),dict(angle_degrees=360),dict(anchor_entity_id='absent'),dict(axis='x')]:
            with self.assertRaises(ProjectError):self.p.actor_placement_layout([fixture.A,fixture.B],{**op,**change})
