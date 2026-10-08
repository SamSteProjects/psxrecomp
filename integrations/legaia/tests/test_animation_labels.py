from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from sdk.animation_labels import command,key,validate_collection
from sdk.project import ProjectError,digest

class AnimationLabels(TestCase):
 def setUp(self):
  self.asset='animation://fixture/authored-record/12345678-1234-4123-8123-123456789abc';self.scene='scene://fixture';self.source='a'*64
  self.p=SimpleNamespace(root=Path('private'),animation_labels={},imports={self.scene:{'retail':'immutable'}},overrides={self.scene:{'AnimationRecords':{'records':[{'record_id':self.asset.rsplit('/',1)[1]}]}}},active_scene=self.scene,mode='edit',undo_stack=[],redo_stack=[])
 def request(self,value='Walk'):
  return dict(type='set_animation_label',asset_id=self.asset,name=value,expected_source_key=self.source,expected_labels_key=key(self.p))
 @patch('sdk.animation_labels.source_key',return_value='a'*64)
 def test_exact_names_stale_noop_and_clear(self,_):
  p=self.p;retail=deepcopy((p.imports,p.overrides));stale=self.request();command(p,self.request('  Walk 🐾  '));self.assertEqual(p.animation_labels[self.asset]['name'],'Walk 🐾');self.assertEqual((p.imports,p.overrides),retail)
  before=deepcopy((p.animation_labels,p.undo_stack,p.redo_stack))
  for body in [stale,self.request(''),self.request('x'*81),self.request('bad\nname'),self.request('\ud800'),{**self.request(),'extra':True}]:
   with self.assertRaises(ProjectError):command(p,body)
   self.assertEqual((p.animation_labels,p.undo_stack,p.redo_stack),before)
  command(p,self.request('Walk 🐾'));self.assertEqual(len(p.undo_stack),1)
  body=self.request();body.pop('name');body['type']='clear_animation_label';command(p,body);self.assertEqual(p.animation_labels,{});self.assertEqual(len(p.undo_stack),2);self.assertEqual((p.imports,p.overrides),retail)
 @patch('sdk.animation_labels.source_key',return_value='a'*64)
 def test_foreign_source_live_orphan_and_forged_persistence(self,_):
  p=self.p
  for field,value in [('mode','live'),('active_scene','scene://other')]:
   old=getattr(p,field);setattr(p,field,value)
   with self.assertRaises(ProjectError):command(p,self.request())
   setattr(p,field,old)
  command(p,self.request());validate_collection(p)
  for field,value in [('scene_id','scene://other'),('import_sha256','0'*64),('name',' bad ')]:
   old=p.animation_labels[self.asset][field];p.animation_labels[self.asset][field]=value
   with self.assertRaises(ProjectError):validate_collection(p)
   p.animation_labels[self.asset][field]=old
  p.overrides.clear()
  with self.assertRaises(ProjectError):validate_collection(p)
