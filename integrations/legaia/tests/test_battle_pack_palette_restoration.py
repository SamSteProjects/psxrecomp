"""Whole CLUT ownership restoration must preserve models and other complete TIMs."""
import os,base64,json,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources
from sdk import battle_pack_palettes as palettes,battle_pack_palette_restoration as restoration,battle_pack_model_authoring as models
from sdk.battle_pack_model_build import prepare as prepare_models
from sdk.build import build_project
from importer.pipeline import _disc_context,import_scene
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPaletteRestorationTests(unittest.TestCase):
 def test_all_six_owners_multi_palette_atomic_history_and_composed_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx(record):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key'])
   for record in catalog['textures'][:6]:
    for index in (0,15):
     observed=palettes.inspect(p,palette_index=index,**ctx(record));args=dict(ctx(record),palette_index=index,entry_index=0,word=observed['preview']['words'][0]^0x7FFF,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);review=palettes.review(p,**args);palettes.apply(p,review_key=review['review_key'],**args)
   model=catalog['models'][0];exported=models.export(p,**ctx(model));args=dict(ctx(model),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode(),expected_current_entry_sha256=exported['current_entry_sha256']);review=models.review(p,**args);models.apply(p,review_key=review['review_key'],**args);model_owners=deepcopy(p.battle_pack_model_overrides);retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};cases=[]
   for i,record in enumerate(catalog['textures'][:6]):
    observed=palettes.inspect(p,palette_index=15,**ctx(record));args=dict(ctx(record),palette_index=15,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);before=deepcopy((p._document(),p.undo_stack,p.redo_stack));owners=deepcopy(p.battle_pack_palette_overrides)
    if i==0:
     with http_server(p) as (_,post):
      status,review=post('/api/battle-pack-palette-restore-review',args);self.assertEqual(status,200,review);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
      for change in ({'expected_current_tim_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'palette_index':True},{'palette_index':16},{'extra':True}):self.assertEqual(post('/api/battle-pack-palette-restore-review',dict(args,**change))[0],400)
      self.assertEqual(post('/api/battle-pack-palette-restore-apply',dict(args,review_key='0'*64))[0],400)
      self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
      status,result=post('/api/battle-pack-palette-restore-apply',dict(args,review_key=review['review_key']));self.assertEqual(status,200,result)
    else:
     review=restoration.review(p,**args);restoration.apply(p,review_key=review['review_key'],**args)
    self.assertEqual(review['removed_word_count'],2);self.assertEqual(review['candidate_tim_base64'],observed['retail_tim_base64']);owners.pop(record['semantic_id']);self.assertEqual(p.battle_pack_palette_overrides,owners);self.assertEqual(p.battle_pack_model_overrides,model_owners);self.assertEqual(len(p.undo_stack),len(before[1])+1)
    after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),after);p.save();self.assertEqual(ProjectService.open(p.root)._document(),after)
    fresh=palettes.inspect(p,palette_index=15,**ctx(record));self.assertEqual(fresh['current_tim_base64'],observed['retail_tim_base64'])
    with self.assertRaises(ProjectError):restoration.review(p,**dict(ctx(record),palette_index=15,expected_current_tim_sha256=fresh['current_tim_sha256'],expected_current_entry_sha256=fresh['current_entry_sha256']))
    cases.append(dict(inspection=observed,review=review,report=dict(project_path=observed['project_path'],project_source_key=observed['project_source_key'],catalog=catalog),record=dict(id=record['semantic_id'],type='texture',data=record)))
    if i==0:
     p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
     with _disc_context(p.disc_path) as (_,disc,_,archive):po,_=palettes.prepare(p,archive,disc);mo,_=prepare_models(p,archive,disc);original=archive.read_entry(archive.entry(1204))
     self.assertEqual(len(po),5);self.assertEqual(len(mo),1);reconstructed=bytearray(original)
     for overlay in po+mo:at=overlay['source_record']['byte_offset'];reconstructed[at:at+overlay['size']]=overlay['payload']
     self.assertEqual(bytes(reconstructed),base64.b64decode(review['candidate_entry_base64']))
     built=build_project(p);directory=Path(built['package_directory'])
     with zipfile.ZipFile(built['path']) as package:
      files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(files),set(package.namelist()))
      for name,data in files.items():self.assertEqual(package.read(name),data)
      for overlay in po+mo:self.assertEqual(package.read(overlay['file']),overlay['payload'])
   self.assertEqual(p.battle_pack_palette_overrides,{})
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   if os.getenv('LEGAIA_PACK_PALETTE_RESTORE_CASES'):Path(os.environ['LEGAIA_PACK_PALETTE_RESTORE_CASES']).write_text(json.dumps(dict(cases=cases,package_sha256=built['sha256'],complete_entry_directory_zip_exact=True,model_owner_retained_files_exact=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
