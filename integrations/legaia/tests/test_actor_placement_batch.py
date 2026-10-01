"""Atomic group placement commands validate all actors before publishing changes."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService, ProjectError
from test_project_workflow import synthetic_scene

A = 'scene://fixture/actors/man-p1/0001'
B = 'scene://fixture/actors/man-p1/0002'


class ActorPlacementBatchTests(unittest.TestCase):
    def project(self, root):
        document = synthetic_scene()
        document['actors'][0]['imported_transform']['position'].update(x=128, z=256)
        other = deepcopy(document['actors'][0]); other['semantic_id'] = B
        other['imported_transform']['position'].update(x=512, z=1024)
        document['actors'].append(other)
        p = ProjectService(Path(root)); p.import_metadata(document)
        return p

    def command(self, p, delta):
        preview = p.actor_placement_batch([B, A], delta)
        return dict(type='offset_actor_placements', scene_id=p.active_scene,
                    actor_ids=[B, A], delta=delta, review_key=preview['review_key'])

    def test_group_history_layers_persistence_and_unrelated_components(self):
        with tempfile.TemporaryDirectory() as root:
            p = self.project(root)
            p.command(dict(type='set_transform', entity_id=A, position={'x':192}))
            p.overrides[A]['ScriptWaits']={'entries':{'script://fixture/actors/man-p1/0001/wait/0000':{'duration_ticks':3}}}
            p.save(); before=deepcopy(p.overrides); source=deepcopy(p.imports); depth=len(p.undo_stack)
            report=p.actor_placement_batch([B,A], {'x':64, 'z':-64})
            self.assertEqual(p.overrides,before);self.assertFalse(p.dirty)
            self.assertEqual(report['targets'][0]['retail']['x'],128)
            self.assertEqual(report['targets'][0]['effective']['x'],192)
            self.assertEqual(report['targets'][0]['proposed']['x'],256)
            p.command(self.command(p,{'x':64,'z':-64}))
            self.assertEqual(len(p.undo_stack),depth+1)
            self.assertEqual(p.overrides[A]['Transform']['position'],{'x':256,'z':192})
            self.assertEqual(p.overrides[B]['Transform']['position'],{'x':576,'z':960})
            self.assertEqual(p.overrides[A]['ScriptWaits'],before[A]['ScriptWaits'])
            p.undo();self.assertEqual(p.overrides,before);self.assertFalse(p.dirty)
            p.redo();self.assertTrue(p.dirty)
            self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)
            self.assertEqual(p.imports,source)

    def test_last_actor_invalid_rejects_whole_group_and_preserves_redo(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root)
            cmd=self.command(p,{'x':64})
            p.command(dict(type='set_transform',entity_id=B,position={'x':16384}));p.undo();p.redo()
            before=deepcopy(p.overrides);history=deepcopy(p.undo_stack)
            with self.assertRaises(ProjectError):p.command(cmd)
            self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)
            for ids,delta in (([A,A],{'x':64}),([A],{'x':64}),([A,B],{'y':64}),([A,B],{'x':True}),([A,B],{'x':32}),([A,B],{'x':64.0}),([A,B],{'x':float('nan')}),([A,'other'],{'x':64})):
                with self.assertRaises(ProjectError):p.actor_placement_batch(ids,delta)
            self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)

    def test_stale_source_project_scene_and_extra_fields_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for kind in ('source','root','scene','extra','live'):
                p=self.project(Path(root)/kind);cmd=self.command(p,{'z':64})
                if kind=='source':p.imports[p.active_scene]['actors'][0]['imported_transform']['position']['z']=320
                if kind=='root':p.root=Path(root)/'other'
                if kind=='scene':cmd['scene_id']='scene://other'
                if kind=='extra':cmd['source_offset']=0
                if kind=='live':p.mode='live'
                with self.assertRaises(ProjectError):p.command(cmd)
                self.assertFalse(p.overrides);self.assertFalse(p.undo_stack)

    def test_changed_effective_actor_and_replayed_group_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);cmd=self.command(p,{'x':64})
            p.command(dict(type='set_transform',entity_id=B,position={'x':576}))
            before=deepcopy(p.overrides);history=deepcopy(p.undo_stack)
            with self.assertRaisesRegex(ProjectError,'changed since preview'):p.command(cmd)
            self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)
            current=self.command(p,{'x':64});p.command(current)
            before=deepcopy(p.overrides);history=deepcopy(p.undo_stack)
            with self.assertRaisesRegex(ProjectError,'changed since preview'):p.command(current)
            self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)

    def test_noop_and_group_redo_prevent_changed_source_reimport(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);p.command(self.command(p,{'x':0,'z':0}))
            self.assertFalse(p.overrides);self.assertFalse(p.undo_stack)
            p.command(self.command(p,{'x':64}));p.undo()
            self.assertFalse(p.overrides)
            changed=deepcopy(p.imports[p.active_scene]);changed['actors'][1]['imported_transform']['position']['x']=576
            with self.assertRaisesRegex(ProjectError,'command history'):p.import_metadata(changed)
            p.redo();self.assertEqual(p.overrides[B]['Transform']['position']['x'],576)


if __name__=='__main__':unittest.main()
