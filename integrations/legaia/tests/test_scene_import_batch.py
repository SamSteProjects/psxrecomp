from copy import deepcopy
import json
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.scene_import_batch import review,apply,source_key
from test_project_workflow import synthetic_scene


def document(name):return json.loads(json.dumps(synthetic_scene()).replace('fixture',name))


class SceneImportBatch(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name))
  self.loader=patch('sdk.scene_import_batch.import_scene',side_effect=lambda disc,scene:document(scene));self.loader.start();self.addCleanup(self.loader.stop)
 def test_atomic_new_and_existing_project_history_save_open_and_noop(self):
  p=self.p;r=review(p,'private.bin',['aaa','bbb'],source_key(p));self.assertFalse(p.imports);self.assertFalse(r['project_changed']);self.assertEqual(r['active_scene'],'scene://aaa')
  body=dict(disc='private.bin',scenes=['aaa','bbb'],source_key=source_key(p),review_key=r['review_key']);apply(p,body);self.assertEqual(set(p.imports),{'scene://aaa','scene://bbb'});self.assertEqual(p.active_scene,'scene://aaa')
  p.command(dict(type='set_transform',entity_id=p.selected,position=dict(x=128)));p.save();self.assertFalse(p.dirty);held=deepcopy((p.overrides,p.undo_stack,p.redo_stack,p.active_scene,p.selected));r=review(p,'private.bin',['ccc'],source_key(p));apply(p,dict(disc='private.bin',scenes=['ccc'],source_key=source_key(p),review_key=r['review_key']));self.assertEqual((p.overrides,p.undo_stack,p.redo_stack,p.active_scene,p.selected),held);self.assertTrue(p.dirty)
  p.save();reopened=ProjectService.open(p.root);self.assertEqual(reopened.imports,p.imports);self.assertEqual(reopened.overrides,p.overrides)
  before=deepcopy((p._document(),p.undo_stack,p.redo_stack));r=review(p,'private.bin',['aaa','bbb','ccc'],source_key(p));self.assertTrue(r['no_op']);apply(p,dict(disc='private.bin',scenes=['aaa','bbb','ccc'],source_key=source_key(p),review_key=r['review_key']));self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
 def test_failure_and_stale_review_never_publish_partial_imports(self):
  p=self.p;p.import_metadata(document('aaa'));held=deepcopy((p._document(),p.assets.records,p.undo_stack,p.redo_stack,p.active_scene,p.selected))
  def bad(disc,scene):
   if scene=='ccc':raise ProjectError('unsupported source')
   return document(scene)
  with patch('sdk.scene_import_batch.import_scene',side_effect=bad):
   with self.assertRaisesRegex(ProjectError,'unsupported'):review(p,'private.bin',['bbb','ccc'],source_key(p))
  self.assertEqual((p._document(),p.assets.records,p.undo_stack,p.redo_stack,p.active_scene,p.selected),held)
  r=review(p,'private.bin',['bbb'],source_key(p))
  with self.assertRaises(ProjectError):apply(p,dict(disc='private.bin',scenes=['bbb'],source_key=source_key(p),review_key='f'*64))
  self.assertEqual((p._document(),p.assets.records,p.undo_stack,p.redo_stack,p.active_scene,p.selected),held)
  p.command(dict(type='set_transform',entity_id=p.selected,position=dict(x=128)))
  with self.assertRaises(ProjectError):apply(p,dict(disc='private.bin',scenes=['bbb'],source_key=r['source_key'],review_key=r['review_key']))
 def test_bounds_live_and_changed_authored_reimport_refuse(self):
  p=self.p
  for scenes in ([],['bbb','aaa'],['aaa','aaa'],['../aaa'],[None],['s'+str(i) for i in range(17)]):
   with self.assertRaises(ProjectError):review(p,'private.bin',scenes,source_key(p))
  p.mode='live'
  with self.assertRaises(ProjectError):review(p,'private.bin',['aaa'],source_key(p))
  p.mode='edit';p.import_metadata(document('aaa'));p.command(dict(type='set_transform',entity_id=p.selected,position=dict(x=128)));held=deepcopy(p._document())
  changed=document('aaa');changed['actors'][0]['imported_transform']['position']['x']=999
  with patch('sdk.scene_import_batch.import_scene',side_effect=lambda d,s:changed if s=='aaa' else document(s)):
   with self.assertRaises(ProjectError):review(p,'private.bin',['aaa','bbb'],source_key(p))
  self.assertEqual(p._document(),held)
  p.imports={'scene://e'+str(i):document('e'+str(i)) for i in range(64)}
  with self.assertRaisesRegex(ProjectError,'64 project scenes'):review(p,'private.bin',['new'],source_key(p))

if __name__=='__main__':unittest.main()
