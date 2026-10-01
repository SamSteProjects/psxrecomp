"""Saved actor selections stay source-bound editor metadata across project history."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService,ProjectError,digest
from sdk.selection_sets import review_key
from sdk.build import authored_state_key
from sdk.scene_preview import source_key
import test_actor_placement_batch as fixture
A,B=fixture.A,fixture.B
C='scene://fixture/actors/man-p1/0003'

class SavedActorSelectionTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        p=fixture.ActorPlacementBatchTests().project(self.directory.name);doc=deepcopy(p.imports[p.active_scene]);actor=deepcopy(doc['actors'][0]);actor['semantic_id']=C;doc['actors'].append(actor)
        self.p=ProjectService(Path(self.directory.name)/'sets');self.p.import_metadata(doc);self.p.save()
    def create(self,name='Pair',ids=None):
        p=self.p;p.command(dict(type='create_actor_selection_set',scene_id=p.active_scene,import_sha256=digest(p.imports[p.active_scene]),name=name,actor_ids=ids or [B,A]))
        return next(value for value in p.actor_selection_sets.values() if value['name']==name.strip())
    def command(self,kind,value,**extra):
        return dict(type=kind,selection_set_id=value['id'],review_key=review_key(self.p,value),**extra)
    def test_source_undo_dirty_save_reopen_and_game_input_exclusion(self):
        p=self.p;imports=deepcopy(p.imports);overrides=deepcopy(p.overrides);build=authored_state_key(p);scene=source_key(p)
        value=self.create(' Pair ');self.assertEqual(value['actor_ids'],[A,B]);self.assertEqual(len(p.undo_stack),1);self.assertTrue(p.dirty);self.assertIn('Saved actor selections',p.unsaved_sections)
        self.assertEqual(p.overrides,overrides);self.assertEqual(p.imports,imports);self.assertEqual(authored_state_key(p),build);self.assertEqual(source_key(p),scene)
        p.undo();self.assertFalse(p.actor_selection_sets);self.assertFalse(p.dirty);p.redo();saved=p.save();opened=ProjectService.open(saved)
        self.assertEqual(opened.actor_selection_sets,p.actor_selection_sets);self.assertFalse(opened.dirty);self.assertEqual(opened.undo_stack,[])
    def test_rename_replace_delete_atomic_history_noop_and_stale_review(self):
        p=self.p;value=self.create();stale=self.command('rename_actor_selection_set',value,name='Old')
        p.command(self.command('rename_actor_selection_set',value,name='Renamed'));value=p.actor_selection_sets[value['id']]
        depth=len(p.undo_stack);p.command(self.command('rename_actor_selection_set',value,name='Renamed'));self.assertEqual(len(p.undo_stack),depth)
        before=deepcopy(p.actor_selection_sets)
        with self.assertRaises(ProjectError):p.command(stale)
        self.assertEqual(p.actor_selection_sets,before)
        p.command(self.command('update_actor_selection_set',value,actor_ids=[C,A]));self.assertEqual(p.actor_selection_sets[value['id']]['actor_ids'],[A,C]);p.undo();self.assertEqual(p.actor_selection_sets,before);p.redo()
        value=p.actor_selection_sets[value['id']];p.command(self.command('delete_actor_selection_set',value));self.assertFalse(p.actor_selection_sets);p.undo();self.assertEqual(p.actor_selection_sets[value['id']],value)
    def test_invalid_source_members_duplicate_names_live_and_extra_fields(self):
        p=self.p
        for updates in [{'actor_ids':[A,A]},{'actor_ids':[A]},{'actor_ids':[A,'other']},{'name':''},{'name':'x'*81},{'import_sha256':'stale'},{'bytes':'00'}]:
            cmd=dict(type='create_actor_selection_set',scene_id=p.active_scene,import_sha256=digest(p.imports[p.active_scene]),name='Pair',actor_ids=[A,B]);cmd.update(updates)
            with self.assertRaises(ProjectError):p.command(cmd)
            self.assertFalse(p.actor_selection_sets);self.assertFalse(p.undo_stack)
        value=self.create();before=deepcopy(p.actor_selection_sets)
        with self.assertRaises(ProjectError):self.create('pair')
        self.assertEqual(p.actor_selection_sets,before);p.mode='live'
        with self.assertRaises(ProjectError):p.command(self.command('delete_actor_selection_set',value))
    def test_changed_import_and_deleted_history_do_not_reinterpret_members(self):
        p=self.p;value=self.create();changed=deepcopy(p.imports[p.active_scene]);changed['actors'][0]['imported_transform']['position']['x']=192
        with self.assertRaisesRegex(ProjectError,'saved actor selections'):p.import_metadata(changed)
        p.command(self.command('delete_actor_selection_set',value));self.assertFalse(p.actor_selection_sets)
        with self.assertRaisesRegex(ProjectError,'command history'):p.import_metadata(changed)
        p.undo();self.assertEqual(p.actor_selection_sets[value['id']],value)
    def test_malformed_saved_collection_rejected_and_old_project_opens(self):
        import json
        p=self.p;path=p.save();raw=json.loads(path.read_text());self.assertNotIn('actor_selection_sets',raw);self.assertEqual(ProjectService.open(path).actor_selection_sets,{})
        value=self.create();p.save();raw=json.loads(path.read_text());raw['actor_selection_sets'][value['id']]['import_sha256']='stale';path.write_text(json.dumps(raw),encoding='utf-8')
        with self.assertRaises(ProjectError):ProjectService.open(path)

if __name__=='__main__':unittest.main()
