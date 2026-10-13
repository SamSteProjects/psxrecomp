"""Active import recovery must preserve exact files and refuse stale or corrupt owners."""
import base64,json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources
from sdk import battle_pack_model_authoring as models
from sdk import battle_pack_model_inputs as inputs
from sdk.battle_pack_models import path
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackInputRecoveryTests(unittest.TestCase):
 def test_active_chain_exact_http_downloads_history_and_corrupt_files(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
   catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];originals=[]
   def ctx(i=0):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=catalog['models'][i]['semantic_id'],catalog_source_key=catalog['source_key'])
   def selection(i=0):
    current=models.current(p,**ctx(i))
    return current,dict(ctx(i),expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256'])
   for i in (0,0,1):
    exported=models.export(p,**ctx(i));content=shifted_glb(base64.b64decode(exported['glb_base64']));args=dict(ctx(i),binding=exported['binding'],glb_base64=base64.b64encode(content).decode(),expected_current_entry_sha256=exported['current_entry_sha256'])
    plan=models.review(p,**args);models.apply(p,review_key=plan['review_key'],**args)
    if i==0:originals.append(content)
   current,args=selection();before=deepcopy((p._document(),p.undo_stack,p.redo_stack));downloads=[]
   with http_server(p) as (_,post):
    status,library=post('/api/battle-pack-model-inputs',args);self.assertEqual(status,200,library)
    self.assertEqual(library['receipt_count'],2);self.assertEqual(library['distinct_glb_count'],2)
    self.assertEqual(library['registered_byte_length'],sum(map(len,originals)))
    self.assertEqual(library['model_binding'],current['model_binding'])
    for row,original in zip(library['imports'],originals):
     status,value=post('/api/battle-pack-model-input-download',dict(args,expected_library_key=library['library_key'],selected_receipt_key=row['receipt_key']))
     self.assertEqual(status,200,value);self.assertEqual(base64.b64decode(value['content_base64']),original);downloads.append(value)
    for extra in ({'expected_current_tmd_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'expected_source_key':'stale'},{'asset_id':'foreign'},{'extra':True}):
     self.assertEqual(post('/api/battle-pack-model-inputs',dict(args,**extra))[0],400)
    for extra in ({'expected_library_key':'0'*64},{'selected_receipt_key':'../original.glb'},{'selected_receipt_key':True},{'selected_receipt_key':downloads[0]['selected']['receipt_key']+'x'},{'extra':True}):
     body=dict(args,expected_library_key=library['library_key'],selected_receipt_key=library['imports'][0]['receipt_key']);body.update(extra)
     self.assertEqual(post('/api/battle-pack-model-input-download',body)[0],400)
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   p.save();opened=ProjectService.open(p.root);self.assertEqual(inputs.library(opened,**args),library)
   p.undo();p.undo();one_current,one_args=selection();one=inputs.library(p,**one_args);self.assertEqual(one['receipt_count'],1)
   with self.assertRaises(ProjectError):inputs.download(p,expected_library_key=library['library_key'],selected_receipt_key=library['imports'][1]['receipt_key'],**one_args)
   self.assertEqual(path(p,library['imports'][1]['receipt']['glb_sha256'],'glb').read_bytes(),originals[1])
   p.undo();empty_current,empty_args=selection();empty=inputs.library(p,**empty_args);self.assertEqual(empty['imports'],[])
   self.assertEqual(path(p,library['imports'][0]['receipt']['glb_sha256'],'glb').read_bytes(),originals[0])
   p.redo();p.redo();p.redo();self.assertEqual(inputs.library(p,**args),library)
   target=path(p,library['imports'][0]['receipt']['glb_sha256'],'glb');saved=target.read_bytes()
   target.write_bytes(saved[:-1])
   with self.assertRaises(ProjectError):inputs.library(p,**args)
   target.write_bytes(bytes([saved[0]^1])+saved[1:])
   with self.assertRaises(ProjectError):inputs.download(p,expected_library_key=library['library_key'],selected_receipt_key=library['imports'][0]['receipt_key'],**args)
   target.unlink()
   with self.assertRaises(ProjectError):inputs.library(p,**args)
   target.write_bytes(saved)
   self.assertEqual(inputs.library(p,**args),library)
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   if os.getenv('LEGAIA_PACK_INPUT_CASES'):
    Path(os.environ['LEGAIA_PACK_INPUT_CASES']).write_text(json.dumps(dict(report=dict(project_path=str(p.root),project_source_key=source_key(p),catalog=catalog),record=dict(id=ctx()['asset_id'],type='model',data=catalog['models'][0]),inspection=current,library=library,downloads=downloads,empty_inspection=empty_current,empty_library=empty,one_inspection=one_current,one_library=one)),encoding='utf-8')


if __name__=='__main__':unittest.main()
