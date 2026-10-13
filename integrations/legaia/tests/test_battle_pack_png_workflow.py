"""Real PNG HTTP Review/Apply/recovery and exact native package delivery."""
import os,base64,json,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources,animations
from sdk import battle_pack_current_actions as actions
from sdk import battle_pack_palettes as palettes,battle_pack_png as png_api,battle_pack_model_authoring as models
from sdk.battle_pack_png_inputs import prepare
from sdk.build import build_project
from importer.pipeline import _disc_context,import_scene
from importer.texture_png import decode_png
from importer.export import _png
from test_model_primitive_workflow import http_server
from test_monster_model_authoring import shifted_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPNGWorkflowTests(unittest.TestCase):
 def test_http_paired_ownership_original_recovery_history_and_complete_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];record=catalog['textures'][0]
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key'])
   observed=palettes.inspect(p,palette_index=0,**ctx());selection=dict(ctx(),expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256'])
   with http_server(p) as (_,post):
    status,download=post('/api/battle-pack-png-download',dict(selection,palette_index=0));self.assertEqual(status,200,download)
    original_png=base64.b64decode(download['png_base64']);original_mask=base64.b64decode(download['stp_base64']);shown=decode_png(original_png);rgba=bytearray(shown['rgba']);rgba[:4]=bytes([255,0,0,255]);edited=_png(256,256,bytes(rgba))
    args=dict(selection,palette_index=0,palette_mode='rebuild',png_base64=base64.b64encode(edited).decode(),stp_base64=download['stp_base64']);before=deepcopy((p._document(),p.undo_stack,p.redo_stack));status,review=post('/api/battle-pack-png-review',args);self.assertEqual(status,200,review);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before);self.assertFalse((p.root/'Authored'/'BattlePackTextureInputs').exists())
    for change in ({'png_base64':'foreign'},{'palette_index':True},{'palette_mode':'foreign'},{'expected_current_tim_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'extra':True}):self.assertEqual(post('/api/battle-pack-png-review',dict(args,**change))[0],400)
    self.assertEqual(post('/api/battle-pack-png-apply',dict(args,review_key='0'*64))[0],400);self.assertFalse((p.root/'Authored'/'BattlePackTextureInputs').exists());status,result=post('/api/battle-pack-png-apply',dict(args,review_key=review['review_key']));self.assertEqual(status,200,result);self.assertEqual(result['battle_pack_png_apply']['history_steps'],1)
    current=palettes.inspect(p,palette_index=0,**ctx());self.assertEqual(current['current_tim_base64'],review['candidate_tim_base64']);fresh=dict(ctx(),expected_current_tim_sha256=current['current_tim_sha256'],expected_current_entry_sha256=current['current_entry_sha256'])
    for kind,expected in [('png',edited),('stp',original_mask)]:
     status,value=post('/api/battle-pack-png-input-download',dict(fresh,kind=kind));self.assertEqual(status,200,value);self.assertEqual(base64.b64decode(value['png_base64']),expected)
   after=deepcopy(p._document());self.assertEqual(len(p.undo_stack),len(before[1])+1);p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   current=palettes.inspect(p,palette_index=0,**ctx());model=models.current(p,expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=catalog['models'][0]['semantic_id'],catalog_source_key=catalog['source_key']);self.assertEqual(model['palette_context']['image_owners'],p.battle_pack_image_overrides)
   # Native model inputs remain valid after independent indexed image edits.
   from importer import battle_pack_model_authoring as native_models
   with _disc_context(p.disc_path) as (_,_,_,archive):raw=archive.read_entry(archive.entry(1204))
   for m in catalog['models']:
    _,retail_binding=native_models.export(raw,m,catalog);exported=models.export(p,expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=m['semantic_id'],catalog_source_key=catalog['source_key']);self.assertEqual(exported['binding'],retail_binding)
   an=animations(p,expected_project_path=str(p.root),expected_source_key=source_key(p));clip=an['catalog']['clips'][0];sel=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model['record']['semantic_id'],catalog_source_key=catalog['source_key'],expected_current_tmd_sha256=model['current_tmd_sha256'],expected_current_entry_sha256=model['current_entry_sha256'],animation_id=clip['semantic_id'],animation_source_key=an['catalog']['source_key']);pose=actions.pose(p,frame_index=0,**sel);self.assertEqual(pose['geometry']['textures'],model['geometry']['textures'])
   for mode in ('object-local','pose','clip'):
    selected=dict(sel,mode=mode,frame_index=0 if mode=='pose' else None,fps=30 if mode=='clip' else None)
    if mode=='object-local':selected.update(animation_id=None,animation_source_key=None)
    self.assertEqual(actions.export(p,**selected)['current_entry_sha256'],model['current_entry_sha256'])
   retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   with _disc_context(p.disc_path) as (_,disc,_,archive):io,_=prepare(p,archive,disc);po,_=palettes.prepare(p,archive,disc);original=archive.read_entry(archive.entry(1204))
   rebuilt=bytearray(original)
   for o in io+po:at=o['source_record']['byte_offset'];rebuilt[at:at+o['size']]=o['payload']
   self.assertEqual(bytes(rebuilt),base64.b64decode(review['candidate_entry_base64']));built=build_project(p);directory=Path(built['package_directory'])
   with zipfile.ZipFile(built['path']) as package:
    files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(files),set(package.namelist()))
    for name,data in files.items():self.assertEqual(package.read(name),data)
    for o in io+po:self.assertEqual(package.read(o['file']),o['payload'])
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   if os.getenv('LEGAIA_PACK_PNG_CASES'):Path(os.environ['LEGAIA_PACK_PNG_CASES']).write_text(json.dumps(dict(inspection=observed,review=review,download=download,png_base64=args['png_base64'],stp_base64=args['stp_base64'],record=dict(id=record['semantic_id'],type='texture',data=record),report=dict(project_path=observed['project_path'],project_source_key=observed['project_source_key'],catalog=catalog),package_sha256=built['sha256'],complete_entry_directory_zip_exact=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
