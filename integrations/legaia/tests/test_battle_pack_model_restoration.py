"""Whole pack restoration preserves other owners, historical files and exact delivery."""
import base64,json,os,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources
from sdk import battle_pack_model_authoring as models
from sdk import battle_pack_model_restoration as restoration
from sdk.battle_pack_models import path
from sdk.battle_pack_model_build import prepare
from sdk.build import build_project
from importer.pipeline import _disc_context,import_scene
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackModelRestorationTests(unittest.TestCase):
 def test_all_five_sources_restore_only_the_selected_complete_span(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
   catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx(record):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key'])
   for record in catalog['models']:
    exported=models.export(p,**ctx(record));args=dict(ctx(record),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode(),expected_current_entry_sha256=exported['current_entry_sha256'])
    plan=models.review(p,**args);models.apply(p,review_key=plan['review_key'],**args)
   retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};reviews=[]
   for record in catalog['models']:
    current=models.current(p,**ctx(record));args=dict(ctx(record),expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256']);owners=deepcopy(p.battle_pack_model_overrides)
    review=restoration.review(p,**args);self.assertEqual(p.battle_pack_model_overrides,owners)
    before=base64.b64decode(review['current_entry_base64']);after=base64.b64decode(review['candidate_entry_base64']);at=record['source_record']['byte_offset'];end=at+record['source_record']['byte_length']
    self.assertEqual(before[:at],after[:at]);self.assertEqual(before[end:],after[end:]);self.assertEqual(after[at:end],base64.b64decode(current['retail_tmd_base64']))
    restoration.apply(p,review_key=review['review_key'],**args);owners.pop(record['semantic_id']);self.assertEqual(p.battle_pack_model_overrides,owners);reviews.append(dict(record=dict(id=record['semantic_id'],type='model',data=record),inspection=current,review=review))
   self.assertEqual(p.battle_pack_model_overrides,{})
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   if os.getenv('LEGAIA_PACK_RESTORE_ALL_CASES'):Path(os.environ['LEGAIA_PACK_RESTORE_ALL_CASES']).write_text(json.dumps(dict(catalog=catalog,cases=reviews)),encoding='utf-8')

 def test_whole_owner_http_history_persistence_and_complete_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
   catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx(i=0):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=catalog['models'][i]['semantic_id'],catalog_source_key=catalog['source_key'])
   for i in (0,0,1):
    exported=models.export(p,**ctx(i));args=dict(ctx(i),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode(),expected_current_entry_sha256=exported['current_entry_sha256'])
    plan=models.review(p,**args);models.apply(p,review_key=plan['review_key'],**args)
   current=models.current(p,**ctx());args=dict(ctx(),expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256'])
   before=deepcopy((p._document(),p.undo_stack,p.redo_stack));retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};other=deepcopy(p.battle_pack_model_overrides[catalog['models'][1]['semantic_id']])
   with http_server(p) as (_,post):
    status,review=post('/api/battle-pack-model-restore-review',args);self.assertEqual(status,200,review);self.assertEqual(review['current_preview'],current);self.assertEqual(len(review['removed_active_inputs']),2)
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
    for changes in ({'extra':True},{'expected_current_tmd_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'asset_id':'foreign'}):self.assertEqual(post('/api/battle-pack-model-restore-review',dict(args,**changes))[0],400)
    self.assertEqual(post('/api/battle-pack-model-restore-apply',dict(args,review_key='0'*64))[0],400)
    target=path(p,review['removed_active_inputs'][0]['glb_sha256'],'glb');saved=target.read_bytes();target.write_bytes(saved[:-1])
    try:self.assertEqual(post('/api/battle-pack-model-restore-apply',dict(args,review_key=review['review_key']))[0],400)
    finally:target.write_bytes(saved)
    self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
    status,result=post('/api/battle-pack-model-restore-apply',dict(args,review_key=review['review_key']));self.assertEqual(status,200,result);self.assertEqual(result['battle_pack_model_restore']['history_steps'],1)
   self.assertEqual(len(p.undo_stack),len(before[1])+1);self.assertNotIn(catalog['models'][0]['semantic_id'],p.battle_pack_model_overrides);self.assertEqual(p.battle_pack_model_overrides[catalog['models'][1]['semantic_id']],other)
   after=deepcopy(p._document());p.undo();self.assertEqual((p._document(),p.undo_stack),before[:2]);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   fresh=models.current(p,**ctx());self.assertEqual(fresh['current_tmd_base64'],current['retail_tmd_base64']);self.assertEqual(fresh['current_entry_sha256'],review['candidate_entry_sha256'])
   with self.assertRaises(ProjectError):restoration.review(p,**dict(ctx(),expected_current_tmd_sha256=fresh['current_tmd_sha256'],expected_current_entry_sha256=fresh['current_entry_sha256']))
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   with _disc_context(p.disc_path) as (_,disc,_,archive):
    overlays,_=prepare(p,archive,disc);original=archive.read_entry(archive.entry(1204))
   self.assertEqual(len(overlays),1);self.assertEqual(overlays[0]['source_record'],catalog['models'][1]['source_record'])
   reconstructed=bytearray(original)
   for overlay in overlays:at=overlay['source_record']['byte_offset'];reconstructed[at:at+overlay['size']]=overlay['payload']
   self.assertEqual(bytes(reconstructed),base64.b64decode(review['candidate_entry_base64']))
   built=build_project(p);directory=Path(built['package_directory'])
   with zipfile.ZipFile(built['path']) as package:
    files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(files),set(package.namelist()))
    for name,data in files.items():self.assertEqual(package.read(name),data)
    for overlay in overlays:self.assertEqual(package.read(overlay['file']),overlay['payload']);self.assertEqual(files[overlay['file']],overlay['payload'])
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   if os.getenv('LEGAIA_PACK_RESTORE_CASES'):
    Path(os.environ['LEGAIA_PACK_RESTORE_CASES']).write_text(json.dumps(dict(report=dict(project_path=review['project_path'],project_source_key=review['project_source_key'],catalog=catalog),record=dict(id=catalog['models'][0]['semantic_id'],type='model',data=catalog['models'][0]),inspection=current,review=review,package_sha256=built['sha256'],whole_directory_zip_exact=True,complete_pack_entry_exact=True,retained_files_exact=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
