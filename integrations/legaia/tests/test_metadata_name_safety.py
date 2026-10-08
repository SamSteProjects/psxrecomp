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
  for value in [None,False,'','  ','🐾'*81,'bad\x00name','bad\nname','bad\x7fname','\nName','Name\t','\ud800','\udfff','\ud83d\udc3e']:
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

 def test_draft_and_template_names_reject_before_history_and_persist(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ActorPlacementBatchTests().project(directory)
   p.command(dict(type='set_transform',entity_id=A,position=dict(x=192)))
   draft_create=dict(type='create_actor_draft',donor_entity_id=A,position=dict(x=128,z=256))
   template_create=dict(type='create_actor_template',entity_id=A)
   for create in [draft_create,template_create]:
    before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
    for name in ['\ud800','\udfff','bad\nname','bad\x7fname','\nName','Name\t']:
     with self.assertRaises(ProjectError):p.command({**create,'name':name})
     self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   p.command({**draft_create,'name':'  道路 🐾  '})
   draft_id=next(iter(p.actor_drafts))
   before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
   for name in ['\ud800','bad\nname','\nName','Name\t']:
    with self.assertRaises(ProjectError):p.command(dict(type='create_npc_preset',entity_id=draft_id,name=name))
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   p.command({**template_create,'name':' 道路 🐾 '})
   template_id=next(iter(p.actor_templates))
   for command in [dict(type='rename_actor_draft',entity_id=draft_id),dict(type='duplicate_actor_draft',entity_id=draft_id),dict(type='rename_actor_template',template_id=template_id)]:
    before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
    for name in ['\ud800','bad\x00name','bad\nname','\nName','Name\t']:
     with self.assertRaises(ProjectError):p.command({**command,'name':name})
     self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   for command,name in [(dict(type='rename_actor_draft',entity_id=draft_id),'🐾'*120),(dict(type='rename_actor_template',template_id=template_id),'🐾'*80)]:
    p.command({**command,'name':name});after=deepcopy(p._document());p.undo();p.redo();self.assertEqual(p._document(),after)
   opened=ProjectService.open(p.save())
   self.assertEqual(opened.actor_drafts,p.actor_drafts);self.assertEqual(opened.actor_templates,p.actor_templates)
   for field,identifier in [('actor_drafts',draft_id),('actor_templates',template_id)]:
    document=deepcopy(p._document());document[field][identifier]['name']='\ud800'
    path=Path(directory)/'invalid-name.json';path.write_text(json.dumps(document,ensure_ascii=True),encoding='utf-8')
    with self.assertRaises(ProjectError):ProjectService.open(path)

 def test_save_guard_preserves_files_for_bypassed_name_mutation(self):
  for family in ['draft','template','header']:
   with self.subTest(family=family),tempfile.TemporaryDirectory() as directory:
    p=ActorPlacementBatchTests().project(directory)
    p.command(dict(type='create_actor_draft',donor_entity_id=A,position=dict(x=128,z=256),name='Safe NPC'))
    p.command(dict(type='set_transform',entity_id=A,position=dict(x=192)))
    p.command(dict(type='create_actor_template',entity_id=A,name='Safe Template'));p.save()
    files={str(path.relative_to(p.root)):path.read_bytes() for path in p.root.rglob('*') if path.is_file()}
    if family=='header':p.name='\ud800'
    else:next(iter((p.actor_drafts if family=='draft' else p.actor_templates).values()))['name']='\ud800'
    before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
    with self.assertRaises(ProjectError):p.save()
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
    self.assertEqual({str(path.relative_to(p.root)):path.read_bytes() for path in p.root.rglob('*') if path.is_file()},files)

 def test_project_header_constructor_and_open_unicode_safety(self):
  with tempfile.TemporaryDirectory() as directory:
   for name in ['\ud800','bad\nname','\nName','Name\t','🐾'*129]:
    with self.assertRaises(ProjectError):ProjectService(Path(directory),name)
   p=ProjectService(Path(directory),'🐾'*128);self.assertEqual(ProjectService.open(p.save()).name,p.name)
   p.name='  Existing padded name  ';self.assertEqual(ProjectService.open(p.save()).name,p.name)
   document=p._document();document['name']='\ud800'
   path=Path(directory)/'invalid-name.json';path.write_text(json.dumps(document,ensure_ascii=True),encoding='utf-8')
   with self.assertRaises(ProjectError):ProjectService.open(path)

if __name__=='__main__':unittest.main()
