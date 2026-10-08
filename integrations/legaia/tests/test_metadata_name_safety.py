"""Display metadata names must fail before mutation and remain UTF-8 portable."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from hashlib import sha256
from sdk.project import ProjectError,ProjectService,digest
from sdk.metadata_text import metadata_name
from sdk.build import authored_state_key
from sdk.scene_preview import source_key
from sdk.selection_sets import review_key as actor_key
from sdk.scene_selection_sets import review_key as selection_key
from sdk.scene_views import review_key as view_key
from sdk.script_bookmarks import review_key as bookmark_key
from test_actor_placement_batch import ActorPlacementBatchTests,A,B
from test_scene_views import DISPLAY

class MetadataNameSafety(unittest.TestCase):
 def test_scalar_unicode_bounds_and_controls(self):
  self.assertEqual(metadata_name('  道路 🐾  ','Name'),'道路 🐾')
  self.assertEqual(metadata_name('🐾'*80,'Name'),'🐾'*80)
  for value in [None,False,'','  ','🐾'*81,'bad\x00name','bad\nname','bad\x7fname','\ud800','\udfff','\ud83d\udc3e']:
   with self.subTest(value=repr(value)),self.assertRaises(ProjectError):metadata_name(value,'Name')
 def test_command_and_persisted_names_across_navigation_metadata(self):
  for family in ['actor_selection_sets','scene_selection_sets','scene_views','script_bookmarks']:
   with self.subTest(family=family),tempfile.TemporaryDirectory() as directory:
    p=ActorPlacementBatchTests().project(directory);p.save();scene=p.active_scene;source=digest(p.imports[scene]);sha=sha256(b'original script witness').hexdigest()
    settings={
     'actor_selection_sets':(dict(type='create_actor_selection_set',scene_id=scene,import_sha256=source,actor_ids=[A,B]),'rename_actor_selection_set','selection_set_id',actor_key),
     'scene_selection_sets':(dict(type='create_scene_selection_set',scene_id=scene,import_sha256=source,map_sha256=None,entity_ids=[A]),'rename_scene_selection_set','selection_set_id',selection_key),
     'scene_views':(dict(type='create_scene_view',scene_id=scene,import_sha256=source,display=deepcopy(DISPLAY)),'rename_scene_view','view_id',view_key),
     'script_bookmarks':(dict(type='create_script_bookmark',owner_id=A,pc=10,source_record_sha256=sha),'rename_script_bookmark','bookmark_id',bookmark_key)}
    create,rename,field,key=settings[family]
    inspection=dict(record=dict(sha256=sha),instructions=[dict(pc=10,mnemonic='WAIT')],dialogues=[])
    inputs=deepcopy((p.imports,p.overrides,authored_state_key(p),source_key(p)))
    with patch('sdk.script_bookmarks._inspection',return_value=inspection):
     before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
     for value in ['\ud800','\udfff','bad\x00name','bad\nname','bad\x7fname']:
      with self.assertRaises(ProjectError):p.command({**create,'name':value})
      self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
     p.command({**create,'name':' Safe 🐾 '});row=next(iter(getattr(p,family).values()));self.assertEqual(row['name'],'Safe 🐾')
     before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
     for value in ['\ud800','\udfff','bad\x00name','bad\nname','bad\x7fname']:
      with self.assertRaises(ProjectError):p.command(dict(type=rename,**{field:row['id']},review_key=key(p,row),name=value))
      self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
     p.command(dict(type=rename,**{field:row['id']},review_key=key(p,row),name='🐾'*80));self.assertEqual(getattr(p,family)[row['id']]['name'],'🐾'*80)
     p.undo();self.assertEqual(getattr(p,family)[row['id']]['name'],'Safe 🐾');p.redo()
     opened=ProjectService.open(p.save());self.assertEqual(getattr(opened,family),getattr(p,family));self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),inputs)
     for invalid in ['\ud800','bad\nname']:
      document=deepcopy(p._document());document[family][row['id']]['name']=invalid;path=Path(directory)/'invalid-name.json';path.write_text(json.dumps(document,ensure_ascii=True),encoding='utf-8')
      with self.assertRaises(ProjectError):ProjectService.open(path)

if __name__=='__main__':unittest.main()
