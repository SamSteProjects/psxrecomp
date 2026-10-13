"""Palette ownership must compose with retained models, actions and native delivery."""
import os,base64,json,tempfile,unittest,zipfile,struct,zlib
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources,animations
from sdk import battle_pack_palettes as palettes,battle_pack_model_authoring as models,battle_pack_current_actions as actions,battle_pack_model_restoration as restoration
from sdk.battle_pack_models import compose as model_entry
from sdk.battle_pack_model_build import prepare as prepare_models
from sdk.build import build_project
from importer.pipeline import _disc_context,import_scene
from test_monster_model_authoring import shifted_glb
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPaletteWorkflowTests(unittest.TestCase):
 def assert_current_pngs(self,content,geometry):
  doc,binary=parse_glb(content)
  for i,texture in enumerate(geometry['textures']):
   if texture['status']!='address_match':continue
   index=doc['materials'][i]['pbrMetallicRoughness']['baseColorTexture']['index'];image=doc['images'][doc['textures'][index]['source']];view=doc['bufferViews'][image['bufferView']];at=view.get('byteOffset',0);png=binary[at:at+view['byteLength']];self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n');cursor=8;compressed=b''
   while cursor<len(png):
    size=struct.unpack_from('>I',png,cursor)[0];kind=png[cursor+4:cursor+8];body=png[cursor+8:cursor+8+size];self.assertEqual(struct.unpack_from('>I',png,cursor+8+size)[0],zlib.crc32(kind+body))
    if kind==b'IHDR':self.assertEqual(struct.unpack('>2I5B',body),(texture['width'],texture['height'],8,6,0,0,0))
    if kind==b'IDAT':compressed+=body
    cursor+=size+12
   rows=zlib.decompress(compressed);stride=texture['width']*4+1;self.assertEqual(len(rows),stride*texture['height']);self.assertTrue(all(rows[y*stride]==0 for y in range(texture['height'])));rgba=b''.join(rows[y*stride+1:(y+1)*stride] for y in range(texture['height']));self.assertEqual(rgba,base64.b64decode(texture['rgba_base64']))

 def test_six_native_owners_current_geometry_interchange_restoration_history_and_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();self.assertNotIn('battle_pack_palette_overrides',p._document());self.assertEqual(ProjectService.open(p.root)._document(),p._document())
   catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def ctx(record):return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=catalog['source_key'])
   model=catalog['models'][0];initial=models.current(p,**ctx(model));baseline_export=models.export(p,**ctx(model))
   for record in catalog['textures'][:6]:
    observed=palettes.inspect(p,palette_index=0,**ctx(record));word=observed['preview']['words'][0]^0x7FFF;args=dict(ctx(record),palette_index=0,entry_index=0,word=word,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);plan=palettes.review(p,**args);before=deepcopy(p._document());palettes.apply(p,review_key=plan['review_key'],**args);self.assertNotEqual(p._document(),before)
   self.assertEqual(len(p.battle_pack_palette_overrides),6);saved=deepcopy(p._document());p.undo();self.assertEqual(len(p.battle_pack_palette_overrides),5);p.redo();self.assertEqual(p._document(),saved);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),saved)
   colored=models.current(p,**ctx(model));self.assertEqual(colored['current_tmd_sha256'],initial['current_tmd_sha256']);self.assertNotEqual(colored['current_entry_sha256'],initial['current_entry_sha256']);self.assertIn('palette_context',colored)
   # All palette entries receive new words in the codec oracle; here receipt and
   # image agreement matter even if a selected word is unused by this crop.
   exported=models.export(p,**ctx(model));self.assertEqual(exported['binding'],baseline_export['binding']);self.assert_current_pngs(base64.b64decode(exported['glb_base64']),colored['geometry'])
   args=dict(ctx(model),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode(),expected_current_entry_sha256=exported['current_entry_sha256']);plan=models.review(p,**args);models.apply(p,review_key=plan['review_key'],**args)
   current=models.current(p,**ctx(model));an=animations(p,expected_project_path=str(p.root),expected_source_key=source_key(p));clip=an['catalog']['clips'][0];selection=dict(ctx(model),animation_id=clip['semantic_id'],animation_source_key=an['catalog']['source_key'],expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256'])
   pose=actions.pose(p,frame_index=0,**selection);self.assertEqual(pose['geometry']['textures'],current['geometry']['textures'])
   for mode in ('object-local','pose','clip'):
    args=dict(selection,mode=mode,frame_index=0 if mode=='pose' else None,fps=30 if mode=='clip' else None)
    if mode=='object-local':args.update(animation_id=None,animation_source_key=None)
    result=actions.export(p,**args);self.assertEqual(result['current_entry_sha256'],current['current_entry_sha256']);self.assert_current_pngs(base64.b64decode(result['glb_base64']),current['geometry'])
   palette_owners=deepcopy(p.battle_pack_palette_overrides);retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};restore_args=dict(ctx(model),expected_current_tmd_sha256=current['current_tmd_sha256'],expected_current_entry_sha256=current['current_entry_sha256']);restored=restoration.review(p,**restore_args);self.assertEqual(restored['retail_geometry']['textures'],colored['geometry']['textures']);restoration.apply(p,review_key=restored['review_key'],**restore_args);self.assertEqual(p.battle_pack_palette_overrides,palette_owners)
   restored_current=models.current(p,**ctx(model));self.assertEqual(restored_current['current_tmd_sha256'],initial['current_tmd_sha256']);self.assertEqual(restored_current['current_entry_sha256'],colored['current_entry_sha256'])
   for file,data in retained.items():self.assertEqual(file.read_bytes(),data)
   record=catalog['textures'][0];observed=palettes.inspect(p,palette_index=0,**ctx(record));args=dict(ctx(record),palette_index=0,entry_index=0,word=observed['preview']['words'][0]^0x7FFF,expected_current_tim_sha256=observed['current_tim_sha256'],expected_current_entry_sha256=observed['current_entry_sha256']);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
   with http_server(p) as (_,post):
    status,review=post('/api/battle-pack-palette-review',args);self.assertEqual(status,200,review)
    for changed in ({'word':True},{'palette_index':16},{'entry_index':16},{'word':65536},{'expected_current_tim_sha256':'0'*64},{'expected_current_entry_sha256':'0'*64},{'extra':True}):self.assertEqual(post('/api/battle-pack-palette-review',dict(args,**changed))[0],400)
    self.assertEqual(post('/api/battle-pack-palette-apply',dict(args,review_key='0'*64))[0],400)
    self.assertEqual(post('/api/battle-pack-palette-inspect',dict(ctx(catalog['textures'][6]),palette_index=0))[0],400)
   self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
   palettes.apply(p,review_key=review['review_key'],**args);self.assertNotIn(record['semantic_id'],p.battle_pack_palette_overrides);p.undo();self.assertEqual(p._document(),before[0]);p.save();self.assertEqual(ProjectService.open(p.root)._document(),p._document())
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   with _disc_context(p.disc_path) as (_,disc,_,archive):
    overlays,_=palettes.prepare(p,archive,disc);original=archive.read_entry(archive.entry(1204));expected=palettes.compose(p,original,catalog,model_entry(p,original,catalog));mo,_=prepare_models(p,archive,disc)
   self.assertEqual(mo,[]);self.assertEqual(len(overlays),6);reconstructed=bytearray(original)
   for overlay in overlays:at=overlay['source_record']['byte_offset'];reconstructed[at:at+512]=overlay['payload']
   self.assertEqual(bytes(reconstructed),expected)
   built=build_project(p);directory=Path(built['package_directory'])
   with zipfile.ZipFile(built['path']) as package:
    files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(files),set(package.namelist()))
    for name,data in files.items():self.assertEqual(package.read(name),data)
    for overlay in overlays:self.assertEqual(package.read(overlay['file']),overlay['payload'])
   if os.getenv('LEGAIA_PACK_PALETTE_CASES'):Path(os.environ['LEGAIA_PACK_PALETTE_CASES']).write_text(json.dumps(dict(inspection=observed,review=review,model_current=current,animations=an,model_report=dict(project_path=current['project_path'],project_source_key=current['project_source_key'],catalog=catalog),pose=pose,restoration=restored,package_sha256=built['sha256'],complete_entry_and_directory_zip_exact=True,gameplay_verified=False)),encoding='utf-8')


if __name__=='__main__':unittest.main()
