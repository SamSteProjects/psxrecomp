"""Imported actor spacing arithmetic and one-command source-preserving history."""
from copy import deepcopy
import unittest
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import actor_placement_proposal_view
import test_actor_placement_layout as fixture


class ActorSpacingLayoutTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.ActorLayoutTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.p = self.fixture.p
        self.ids = [fixture.A, fixture.B]
        self.p.command(dict(type='set_transform', entity_id=fixture.A, position=dict(x=640, z=576, y=-12)))
        self.p.command(dict(type='set_transform', entity_id=fixture.B, position=dict(x=512, z=512)))

    def test_scale_rounding_coincidence_and_mirror_axes(self):
        for layout, expected in (
                (dict(kind='scale', percent=50), dict(x=576, z=576, y=-12)),
                (dict(kind='scale', percent=200), dict(x=768, z=640, y=-12)),
                (dict(kind='scale', percent=1), dict(x=512, z=512, y=-12)),
                (dict(kind='mirror', axis='x'), dict(x=384, z=576, y=-12)),
                (dict(kind='mirror', axis='z'), dict(x=640, z=448, y=-12))):
            layout['anchor_entity_id'] = fixture.B
            with self.subTest(layout=layout):
                report = self.p.actor_placement_layout(self.ids, layout)
                rows = {row['entity_id']: row for row in report['targets']}
                self.assertEqual(rows[fixture.A]['proposed'], expected)
                self.assertEqual(rows[fixture.B]['proposed'], rows[fixture.B]['effective'])
                self.assertEqual(report['changed_count'], 1)
                self.assertEqual(report, self.p.actor_placement_layout(self.ids[::-1], layout))

    def test_detached_preview_history_persistence_and_stale_refusal(self):
        self.p.save()
        held = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        for layout in (dict(kind='scale', percent=200, anchor_entity_id=fixture.B),
                       dict(kind='mirror', axis='z', anchor_entity_id=fixture.B)):
            report = self.p.actor_placement_layout(self.ids, layout)
            detached = actor_placement_proposal_view(self.p, report)
            for row in report['targets']:
                self.assertEqual({**row['retail'], **detached.overrides[row['entity_id']]['Transform']['position']}, row['proposed'])
            self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), held)
            command = dict(type='layout_actor_placements', scene_id=report['scene_id'], actor_ids=self.ids,
                           layout=layout, review_key=report['review_key'])
            self.p.command(command)
            applied = deepcopy(self.p._document())
            self.assertEqual(len(self.p.undo_stack), len(held[1])+1)
            with self.assertRaises(ProjectError):
                self.p.command(command)
            self.p.save()
            self.assertEqual(ProjectService.open(self.p.root)._document(), applied)
            self.p.undo()
            self.assertEqual(self.p._document(), held[0])
            self.p.redo()
            self.assertEqual(self.p._document(), applied)
            self.p.undo()
            self.p.save()
            self.assertEqual(self.p.undo_stack, held[1])
            # Undo intentionally retains a redo entry; clear it before the next independent workflow.
            self.p.redo_stack.clear()

    def test_invalid_fields_anchor_bounds_and_atomic_failure(self):
        held = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        for layout in (dict(kind='scale', percent=True, anchor_entity_id=fixture.B),
                       dict(kind='scale', percent=50.5, anchor_entity_id=fixture.B),
                       dict(kind='scale', percent=0, anchor_entity_id=fixture.B),
                       dict(kind='scale', percent=1001, anchor_entity_id=fixture.B),
                       dict(kind='scale', percent=50, anchor_entity_id=fixture.C),
                       dict(kind='scale', percent=50, anchor_entity_id=fixture.B, axis='x'),
                       dict(kind='mirror', axis='y', anchor_entity_id=fixture.B),
                       dict(kind='mirror', axis='x', anchor_entity_id=fixture.C)):
            with self.subTest(layout=layout), self.assertRaises(ProjectError):
                self.p.actor_placement_layout(self.ids, layout)
            self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), held)
        self.p.command(dict(type='set_transform', entity_id=fixture.A, position=dict(x=16384, z=16384)))
        held = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        for layout in (dict(kind='scale', percent=1000, anchor_entity_id=fixture.B),
                       dict(kind='mirror', axis='x', anchor_entity_id=fixture.B)):
            with self.assertRaises(ProjectError):
                self.p.actor_placement_layout(self.ids, layout)
            self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), held)
        # Earlier selected members fit, but a later member exceeds the native range.
        self.p.command(dict(type='set_transform', entity_id=fixture.A, position=dict(x=640, z=576)))
        self.p.command(dict(type='set_transform', entity_id=fixture.C, position=dict(x=16384, z=512)))
        held = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        with self.assertRaises(ProjectError):
            self.p.actor_placement_layout([*self.ids, fixture.C], dict(kind='scale', percent=1000, anchor_entity_id=fixture.B))
        self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), held)

    def test_identity_scale_is_noop(self):
        report = self.p.actor_placement_layout(self.ids, dict(kind='scale', percent=100, anchor_entity_id=fixture.B))
        held = deepcopy((self.p._document(), self.p.undo_stack, self.p.redo_stack))
        self.assertEqual(report['changed_count'], 0)
        self.p.command(dict(type='layout_actor_placements', scene_id=report['scene_id'], actor_ids=self.ids,
                            layout=report['layout'], review_key=report['review_key']))
        self.assertEqual((self.p._document(), self.p.undo_stack, self.p.redo_stack), held)
