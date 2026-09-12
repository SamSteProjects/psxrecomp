"""Authored draft lifecycle preserves donor evidence and build freshness."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from test_project_workflow import synthetic_scene
from sdk.project import ProjectService, ProjectError
from sdk.build import authored_state_key, _build_project, BuildError


class ActorDraftTests(unittest.TestCase):
    def test_donor_change_preserves_identity_position_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));scene=synthetic_scene()
            second=deepcopy(scene['actors'][0]);second['semantic_id']='scene://fixture/actors/man-p1/0002'
            scene['actors'].append(second);p.import_metadata(scene)
            p.command({'type':'create_actor_draft','donor_entity_id':scene['actors'][0]['semantic_id'],
                       'position':{'x':128,'z':256},'name':'Resident'})
            identifier=next(iter(p.actor_drafts));before=deepcopy(p.actor_drafts[identifier])
            p.command({'type':'set_actor_draft_donor','entity_id':identifier,'donor_entity_id':second['semantic_id']})
            self.assertEqual(p.actor_drafts[identifier],{**before,'donor_entity_id':second['semantic_id']})
            p.undo();self.assertEqual(p.actor_drafts[identifier],before)
            p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)
            history=len(p.undo_stack)
            with self.assertRaises(ValueError):
                p.command({'type':'set_actor_draft_donor','entity_id':identifier,'donor_entity_id':'scene://other/actor'})
            self.assertEqual(len(p.undo_stack),history)
            self.assertEqual(p.imports[scene['scene']['semantic_id']],scene)

    def test_rename_duplicate_independence_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));scene=synthetic_scene();p.import_metadata(scene)
            p.command({'type':'create_actor_draft','donor_entity_id':scene['actors'][0]['semantic_id'],
                       'position':{'x':128,'z':256},'name':'Resident'})
            original=next(iter(p.actor_drafts))
            p.command({'type':'rename_actor_draft','entity_id':original,'name':'North resident'})
            count=len(p.undo_stack)
            p.command({'type':'rename_actor_draft','entity_id':original,'name':'North resident'})
            self.assertEqual(len(p.undo_stack),count)
            p.command({'type':'duplicate_actor_draft','entity_id':original,'name':'South resident'})
            duplicate=next(key for key in p.actor_drafts if key!=original)
            p.command({'type':'set_actor_draft_position','entity_id':duplicate,'position':{'x':192,'z':256}})
            self.assertEqual(p.actor_drafts[original]['position']['x'],128)
            p.undo();p.undo();self.assertNotIn(duplicate,p.actor_drafts)
            p.redo();self.assertEqual(p.actor_drafts[duplicate]['name'],'South resident')
            saved=p.save();q=ProjectService.open(saved)
            self.assertEqual(q.actor_drafts,p.actor_drafts)
            before=deepcopy(p._document());history=len(p.undo_stack)
            for name in ('',None,'x'*121):
                with self.assertRaises(ValueError):
                    p.command({'type':'rename_actor_draft','entity_id':original,'name':name})
            self.assertEqual(p._document(),before);self.assertEqual(len(p.undo_stack),history)

    def test_lifecycle_persistence_and_build_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory)); original=synthetic_scene()
            p.import_metadata(original);p.save();baseline=authored_state_key(p)
            p.command({'type':'create_actor_draft','donor_entity_id':original['actors'][0]['semantic_id'],
                       'position':{'x':128,'z':256},'name':'New NPC'})
            identifier=next(iter(p.actor_drafts))
            self.assertIn('New NPC drafts',p.unsaved_sections)
            self.assertNotEqual(authored_state_key(p),baseline)
            p.undo();self.assertFalse(p.dirty);self.assertEqual(authored_state_key(p),baseline)
            p.redo();self.assertIn(identifier,p.actor_drafts)
            p.command({'type':'set_actor_draft_position','entity_id':identifier,'position':{'x':192,'z':256}})
            p.save();q=ProjectService.open(p.root)
            self.assertEqual(q.actor_drafts,p.actor_drafts);self.assertFalse(q.dirty)
            self.assertEqual(q.imports[original['scene']['semantic_id']],original)
            with self.assertRaisesRegex(BuildError,'drafts'):
                _build_project(q,None)
            q.command({'type':'delete_actor_draft','entity_id':identifier})
            self.assertFalse(q.actor_drafts);q.undo();self.assertIn(identifier,q.actor_drafts)

    def test_invalid_donor_and_position_do_not_mutate_history(self):
        p=ProjectService(Path('.'));original=synthetic_scene();p.import_metadata(original)
        before=deepcopy(p._document());history=deepcopy(p.undo_stack)
        for donor,position in [('missing',{'x':128,'z':256}),
                               (original['actors'][0]['semantic_id'],{'x':128,'y':0,'z':256})]:
            with self.assertRaises(ValueError):
                p.command({'type':'create_actor_draft','donor_entity_id':donor,'position':position,'name':'Draft'})
            self.assertEqual(p._document(),before);self.assertEqual(p.undo_stack,history)


if __name__=='__main__':
    unittest.main()
