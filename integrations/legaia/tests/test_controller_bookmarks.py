from copy import deepcopy
from contextlib import nullcontext
from unittest.mock import patch
import test_script_bookmarks as base
from sdk.project import ProjectError
from sdk.script_bookmarks import _inspection
class ControllerBookmarkTests(base.ScriptBookmarkTests):
 def setUp(self):
  super().setUp();self.owner=self.p.active_scene+'/controllers/man-p1/0000'
 def test_exact_controller_owner_only(self):
  for owner in [self.owner[:-1]+'1',self.owner+'/extra','scene://foreign/controllers/man-p1/0000','script://'+self.owner[8:]]:
   before=deepcopy((self.p._document(),self.p.undo_stack))
   with self.assertRaises(ProjectError):self.p.command(dict(type='create_script_bookmark',owner_id=owner,pc=10,source_record_sha256=self.sha,name='Foreign'))
   self.assertEqual(before,(self.p._document(),self.p.undo_stack))
 def test_duplicate_decoded_boundary_refused(self):
  with patch('sdk.script_bookmarks._inspection',return_value={'record':{'sha256':self.sha},'instructions':[{'pc':10,'mnemonic':'A'},{'pc':10,'mnemonic':'B'}],'dialogues':[]}):
   with self.assertRaisesRegex(ProjectError,'unique'):self.create()
 def test_fresh_controller_inspection_owner(self):
  document=self.p.imports[self.p.active_scene];self.p.disc_path='fixture.bin';raw={'semantic_id':self.owner.replace('scene://','script://'),'scene_id':self.p.active_scene,'read_only':True,'record':{'local_count':0},'source_record':{'sha256':self.sha},'instructions':[],'dialogues':[]}
  from sdk import script_bookmarks
  with patch('importer.pipeline._disc_context',return_value=nullcontext()),patch('importer.pipeline.import_scene',return_value=document),patch('importer.scene_controller.inspect_scene_controller',return_value=raw):
   # The inherited setup patches _inspection; exercise its real implementation separately.
   result=self.real_inspection(self.p,self.owner,document);self.assertEqual(result['record']['sha256'],self.sha);self.assertNotIn('sha256',raw['record'])
  with patch('importer.pipeline._disc_context',return_value=nullcontext()),patch('importer.pipeline.import_scene',return_value=document),patch('importer.scene_controller.inspect_scene_controller',return_value={**raw,'semantic_id':'foreign'}):
   with self.assertRaises(ProjectError):self.real_inspection(self.p,self.owner,document)
 real_inspection=staticmethod(_inspection)
