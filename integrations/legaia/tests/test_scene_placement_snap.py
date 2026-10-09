from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.scene_placement_group import layout_review, apply
from test_scene_placement_group import SCENE, MIXED, ACTOR
import test_scene_placement_group as fixture
from test_environment_group import source_map


class PlacementSnapTests(unittest.TestCase):
    def test_snap_axes_history_and_atomic_boundary_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            p=fixture.ScenePlacementGroupTests().project(directory)
            with patch.object(ProjectService,'_environment_source',return_value=source_map()):
                p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=192,y=77,z=320)))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                op=dict(kind='snap',axes=['x'],spacing=256);r=layout_review(p,SCENE,MIXED,op)
                actor=next(t for t in r['targets'] if t['kind']=='actor');self.assertEqual(actor['proposed'],dict(x=256,z=320));self.assertEqual(p.overrides,before)
                apply(p,dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']))
                self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR]['Transform']['position'],dict(x=256,y=77,z=320))
                after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after)
                noop=layout_review(p,SCENE,MIXED,op);self.assertFalse(noop['project_change']);held_depth=len(p.undo_stack)
                apply(p,dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=noop['review_key']));self.assertEqual(len(p.undo_stack),held_depth)
                p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=64)))
                held=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
                with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(kind='snap',axes=['x'],spacing=256))
                self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)

    def test_exact_operation_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            p=fixture.ScenePlacementGroupTests().project(directory)
            for op in [dict(kind='snap',axes=axes,spacing=spacing) for axes,spacing in [(['z','x'],256),([],256),(['x','x'],256),(['y'],256),(['x'],True),(['x'],65),(['x'],0),(['x'],4160),(['x'],256.0)]]+[dict(kind='snap',axes=['x'],spacing=256,anchor_entity_id=ACTOR)]:
                with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,op)
