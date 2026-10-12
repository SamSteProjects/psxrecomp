import os,json,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from sdk.project import ProjectService
from sdk.project_assets import source_key
from importer.pipeline import import_scene
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class SharedFieldEditorTests(unittest.TestCase):
 def test_resources_inspect_review_apply_history(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
   with http_server(p) as (_,post):
    status,report=post('/api/field-texture-resources',ctx());self.assertEqual(status,200,report);self.assertEqual(len(report['assets']),8);record=report['assets'][0];args=dict(ctx(),asset_id=record['semantic_id'],palette_index=0);status,inspection=post('/api/field-texture-inspect',args);self.assertEqual(status,200,inspection);word=inspection['palette']['words'][1]^1;body=dict(args,entry_index=1,word=word,expected_current_sha256=inspection['palette']['effective_sha256']);before=deepcopy((p._document(),p.undo_stack));status,r=post('/api/field-texture-review',body);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),before);self.assertEqual(post('/api/field-texture-apply',dict(body,review_key='0'*64))[0],400);status,result=post('/api/field-texture-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),1);self.assertEqual(post('/api/field-texture-apply',dict(body,review_key=r['review_key']))[0],400)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   if os.getenv('LEGAIA_FIELD_EDITOR_CASES'):Path(os.environ['LEGAIA_FIELD_EDITOR_CASES']).write_text(json.dumps(dict(report=report,record=dict(id=record['semantic_id'],data=record),inspection=inspection,review=r,entry=1,word=word,history=True,save_open=True,stale_apply_refused=True,gameplay_verified=False)),encoding='utf-8')
