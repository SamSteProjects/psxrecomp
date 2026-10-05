from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import json
import tempfile
import unittest
import uuid
from sdk.project import ProjectService, ProjectError
from sdk.script_bookmarks import review_key
from sdk.build import authored_state_key
from sdk.scene_preview import source_key
import test_actor_placement_batch as fixture

class ScriptBookmarkTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=fixture.ActorPlacementBatchTests().project(self.directory.name);self.p.save()
        self.owner=self.p.state()['scene']['entities'][0]['id'];self.record=b'original script witness';self.sha=sha256(self.record).hexdigest()
        mock=patch('sdk.script_bookmarks._inspection',return_value=dict(record=dict(sha256=self.sha),instructions=[dict(pc=10,mnemonic='WAIT'),dict(pc=12,mnemonic='RETURN')],dialogues=[dict(pc=20)]));mock.start();self.addCleanup(mock.stop)
    def create(self,**values):
        self.p.command(dict(type='create_script_bookmark',owner_id=self.owner,pc=10,source_record_sha256=self.sha,name='Greeting',**values))
        return next(iter(self.p.script_bookmarks.values()))
    def cmd(self,kind,row,**fields):
        return dict(type=kind,bookmark_id=row['id'],review_key=review_key(self.p,row),**fields)
    def test_history_portability_and_game_input_separation(self):
        p=self.p;before=deepcopy(p.imports),deepcopy(p.overrides),authored_state_key(p),source_key(p)
        row=self.create();self.assertIn('Saved script bookmarks',p.unsaved_sections);self.assertTrue(p.dirty)
        self.assertEqual(p.state()['script_bookmarks'][0]['review_key'],review_key(p,row));self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),before)
        p.undo();self.assertFalse(p.script_bookmarks);self.assertFalse(p.dirty);p.redo()
        reopened=ProjectService.open(p.save());self.assertEqual(reopened.script_bookmarks,p.script_bookmarks);self.assertFalse(reopened.dirty)
        reopened.disc_path=None;self.assertEqual(ProjectService.open(reopened.save()).script_bookmarks,p.script_bookmarks)
    def test_update_rename_delete_and_stale_noop(self):
        p=self.p;row=self.create();stale=self.cmd('delete_script_bookmark',row)
        p.command(self.cmd('update_script_bookmark',row,pc=20,source_record_sha256=self.sha));row=p.script_bookmarks[row['id']];self.assertEqual(row['mnemonic'],'DIALOGUE_SEGMENT')
        before=deepcopy(p._document()),deepcopy(p.undo_stack),deepcopy(p.redo_stack)
        with self.assertRaises(ProjectError):p.command(stale)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        p.command(self.cmd('rename_script_bookmark',row,name=' Other '));row=p.script_bookmarks[row['id']];self.assertEqual(row['name'],'Other')
        depth=len(p.undo_stack);p.command(self.cmd('rename_script_bookmark',row,name='Other'));self.assertEqual(len(p.undo_stack),depth)
        p.command(self.cmd('delete_script_bookmark',row));self.assertFalse(p.script_bookmarks);p.undo();self.assertEqual(p.script_bookmarks[row['id']],row)
    def test_source_bounds_duplicate_names_and_edit_guard_are_atomic(self):
        p=self.p;self.create()
        valid=dict(type='create_script_bookmark',owner_id=self.owner,pc=12,source_record_sha256=self.sha,name='Other')
        for changed in [dict(pc=True),dict(pc=11),dict(pc=-1),dict(pc=65536),dict(source_record_sha256='0'*64),dict(name='greeting'),dict(name=''),dict(extra=True)]:
            before=deepcopy(p._document()),deepcopy(p.undo_stack)
            with self.assertRaises(ProjectError):p.command(valid|changed)
            self.assertEqual((p._document(),p.undo_stack),before)
        p.mode='observe'
        with self.assertRaises(ProjectError):p.command(valid)
        p.mode='edit';original=next(iter(p.script_bookmarks.values()))
        for index in range(255):
            identifier='bookmark://'+str(uuid.uuid4());p.script_bookmarks[identifier]=dict(original,id=identifier,name=f'Bookmark {index}')
        before=deepcopy(p._document()),deepcopy(p.undo_stack)
        with self.assertRaisesRegex(ProjectError,'256'):p.command(valid)
        self.assertEqual((p._document(),p.undo_stack),before)
    def test_open_rejects_forged_metadata_and_duplicate_names(self):
        p=self.p;row=self.create();p.save();path=p.root/'project.legaia.json';original=json.loads(path.read_text())
        for field,value in [('pc',True),('source_record_sha256','bad'),('owner_id','scene://other/actors/man-p1/0001'),('import_sha256','0'*64)]:
            raw=deepcopy(original);raw['script_bookmarks'][row['id']][field]=value;path.write_text(json.dumps(raw))
            with self.assertRaises(ProjectError):ProjectService.open(p.root)
        raw=deepcopy(original);other='bookmark://'+str(uuid.uuid4());raw['script_bookmarks'][other]=dict(row,id=other);path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ProjectError,'Duplicate'):ProjectService.open(p.root)
        path.write_text(json.dumps(original))
    def test_reimport_cannot_reinterpret_live_or_deleted_bookmark_history(self):
        p=self.p;row=self.create();changed=deepcopy(p.imports[p.active_scene]);changed['source']['extra']='changed'
        for delete in (False,True):
            if delete:p.command(self.cmd('delete_script_bookmark',row))
            with self.assertRaisesRegex(ProjectError,'bookmarks'):p.import_metadata(changed)

if __name__=='__main__':unittest.main()
