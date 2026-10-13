"""Image-only and whole TIM restoration preserve unrelated native ownership."""
import os,base64,json,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources
from sdk import battle_pack_palettes as palettes,battle_pack_png as png,battle_pack_texture_restoration as restore,battle_pack_model_authoring as models
from sdk.battle_pack_png_inputs import prepare as images
from sdk.battle_pack_model_build import prepare as model_overlays
from sdk.build import build_project
from importer.pipeline import _disc_context,import_scene
from importer.export import _png
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackTextureRestoreTests(unittest.TestCase):
 def test_valid_ownership_only_image_restore(self):
  from sdk.battle_pack_png_inputs import retain_import
  from importer.battle_pack_png import export
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];record=catalog['textures'][0];png_bytes,mask,_=export(original,catalog,record,0);owner,_,_=retain_import(p,original,catalog,record,0,png_bytes,'existing',mask);p.battle_pack_image_overrides[record['semantic_id']]=owner;p.save()
   ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key']);observed=palettes.inspect(p,palette_index=0,**ctx);args=dict(ctx,scope='image',palette_index=0,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);review=restore.review(p,**args);self.assertEqual(review['byte_change_count'],0);self.assertFalse(review['native_content_changed']);self.assertTrue(review['ownership_changed']);restore.apply(p,review_key=review['review_key'],**args);self.assertEqual(p.battle_pack_image_overrides,{})
   if os.getenv('LEGAIA_TEXTURE_RESTORE_OWNERSHIP_CASES'):Path(os.environ['LEGAIA_TEXTURE_RESTORE_OWNERSHIP_CASES']).write_text(json.dumps(dict(inspection=observed,review=review,record=dict(id=record['semantic_id'],type='texture',data=record),report=dict(project_path=ctx['expected_project_path'],project_source_key=ctx['expected_source_key'],catalog=catalog))),encoding='utf-8')

 def test_both_restore_scopes_other_owners_history_recovery_and_complete_delivery(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx(record):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key'])
   for record in catalog['textures'][:2]:
    current=palettes.inspect(p,palette_index=0,**ctx(record));rgba=bytearray(base64.b64decode(current['preview']['rgba_base64']));rgba[:4]=bytes([255,0,0,255]);args=dict(ctx(record),palette_index=0,palette_mode='rebuild',png_base64=base64.b64encode(_png(256,256,bytes(rgba))).decode(),stp_base64=None,expected_current_tim_sha256=current['current_tim_sha256'],expected_current_entry_sha256=current['current_entry_sha256']);review=png.review(p,**args);png.apply(p,review_key=review['review_key'],**args)
   m=catalog['models'][0];exported=models.export(p,**ctx(m));args=dict(ctx(m),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode(),expected_current_entry_sha256=exported['current_entry_sha256']);review=models.review(p,**args);models.apply(p,review_key=review['review_key'],**args)
   record=catalog['textures'][0];cases=[];files={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};model_owners=deepcopy(p.battle_pack_model_overrides)
   for scope in ('image','texture'):
    observed=palettes.inspect(p,palette_index=0,**ctx(record));args=dict(ctx(record),scope=scope,palette_index=0,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);before=deepcopy((p._document(),p.undo_stack,p.redo_stack));other_image=deepcopy(p.battle_pack_image_overrides[catalog['textures'][1]['semantic_id']]);other_palette=deepcopy(p.battle_pack_palette_overrides.get(catalog['textures'][1]['semantic_id']))
    with http_server(p) as (_,post):
     status,review=post('/api/battle-pack-texture-restore-review',args);self.assertEqual(status,200,review);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
     for change in ({'scope':'foreign'},{'palette_index':True},{'expected_current_tim_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'extra':True}):self.assertEqual(post('/api/battle-pack-texture-restore-review',dict(args,**change))[0],400)
     self.assertEqual(post('/api/battle-pack-texture-restore-apply',dict(args,review_key='0'*64))[0],400);status,value=post('/api/battle-pack-texture-restore-apply',dict(args,review_key=review['review_key']));self.assertEqual(status,200,value)
    self.assertNotIn(record['semantic_id'],p.battle_pack_image_overrides);self.assertEqual(p.battle_pack_model_overrides,model_owners);self.assertEqual(p.battle_pack_image_overrides[catalog['textures'][1]['semantic_id']],other_image);self.assertEqual(p.battle_pack_palette_overrides.get(catalog['textures'][1]['semantic_id']),other_palette)
    if scope=='image':self.assertEqual(p.battle_pack_palette_overrides.get(record['semantic_id']),observed['binding'])
    else:self.assertNotIn(record['semantic_id'],p.battle_pack_palette_overrides)
    after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),after);p.save();self.assertEqual(ProjectService.open(p.root)._document(),after)
    cases.append(dict(inspection=observed,review=review,record=dict(id=record['semantic_id'],type='texture',data=record),report=dict(project_path=observed['project_path'],project_source_key=observed['project_source_key'],catalog=catalog)))
    if scope=='image':p.undo() # restore the authored baseline to qualify whole-texture scope
   for file,data in files.items():self.assertEqual(file.read_bytes(),data)
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   with _disc_context(p.disc_path) as (_,disc,_,archive):io,_=images(p,archive,disc);po,_=palettes.prepare(p,archive,disc);mo,_=model_overlays(p,archive,disc);original=archive.read_entry(archive.entry(1204))
   rebuilt=bytearray(original)
   for o in io+po+mo:at=o['source_record']['byte_offset'];rebuilt[at:at+o['size']]=o['payload']
   self.assertEqual(bytes(rebuilt),base64.b64decode(cases[-1]['review']['candidate_entry_base64']));built=build_project(p);directory=Path(built['package_directory'])
   with zipfile.ZipFile(built['path']) as package:
    disk={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(disk),set(package.namelist()))
    for name,data in disk.items():self.assertEqual(package.read(name),data)
    for o in io+po+mo:self.assertEqual(package.read(o['file']),o['payload'])
   if os.getenv('LEGAIA_TEXTURE_RESTORE_CASES'):Path(os.environ['LEGAIA_TEXTURE_RESTORE_CASES']).write_text(json.dumps(dict(cases=cases,package_sha256=built['sha256'],complete_entry_directory_zip_exact=True,retained_files_exact=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
