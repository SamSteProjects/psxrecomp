import os,tempfile,json,base64,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs,ImportError as NativeError
from importer.texture_png import decode_png,_encode_png
from importer.monster_png import export,convert
from test_model_primitive_workflow import http_server

class MonsterPngMaskTests(unittest.TestCase):
 def test_explicit_mask_preserves_native_layout_and_other_palettes(self):
  pool=bytes.fromhex('1f00')*240+bytes(128*128)
  png,mask,_=export(pool,128,4)
  self.assertEqual(convert(pool,128,4,png,'existing',mask)[0],pool)
  white=_encode_png(128,256,bytes([255,255,255,255])*(128*256))
  candidate,_=convert(pool,128,4,png,'rebuild',white)
  self.assertEqual(candidate[:128],pool[:128]);self.assertEqual(candidate[160:],pool[160:])
  from importer.monster_textures import pixels
  self.assertEqual(pixels(candidate,128,4)['stp'],bytes([1])*(128*256))
  invalid=_encode_png(128,256,bytes([127,127,127,255])*(128*256))
  with self.assertRaises(NativeError):convert(pool,128,4,png,'rebuild',invalid)

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterPngTests(unittest.TestCase):
 def test_original_png_native_image_and_history_delivery(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/monster-archive/0063/pool'
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0)
   with http_server(p) as (_,post):
    status,inspection=post('/api/monster-palette-inspect',ctx());self.assertEqual(status,200,inspection);args=dict(ctx(),expected_current_sha256=inspection['current_pool_sha256']);status,download=post('/api/monster-png-download',args);self.assertEqual(status,200,download);png=base64.b64decode(download['png_base64']);pixels=decode_png(png);self.assertEqual(pixels['rgba'],base64.b64decode(inspection['preview']['rgba_base64']));rgba=bytearray(pixels['rgba']);rgba[:4]=bytes([0,255,0,255]);edited=_encode_png(pixels['width'],pixels['height'],bytes(rgba));body=dict(args,png_base64=base64.b64encode(edited).decode(),palette_mode='rebuild',stp_base64=None);held=deepcopy((p._document(),p.undo_stack));status,r=post('/api/monster-png-review',body);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),held);self.assertEqual(post('/api/monster-png-apply',dict(body,review_key='0'*64))[0],400);status,result=post('/api/monster-png-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),1)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   from sdk.monster_palettes import snapshot
   from sdk.monster_png import validate_input,path
   _,record,original,current,_,used=snapshot(p,asset);binding=p.monster_palette_overrides[asset];receipt=binding['png_import'];self.assertEqual(validate_input(p,record,receipt)[0],edited);at=record['source_record']['byte_offset'];self.assertEqual(current[:at],original[:at]);self.assertEqual(current[at:],base64.b64decode(r['candidate_pool_base64']));self.assertIn('image_override',binding)
   from sdk.monster_palettes import review as palette_review,apply as palette_apply
   import struct
   palette_args=dict(ctx(),entry_index=1,word=struct.unpack_from('<H',current,at+2)[0]^1,expected_current_sha256=binding['current_pool_sha256'])
   palette_plan=palette_review(p,**palette_args);palette_apply(p,review_key=palette_plan['review_key'],**palette_args)
   composed=snapshot(p,asset)[3];self.assertEqual(composed[at+480:],current[at+480:]);self.assertEqual(p.monster_palette_overrides[asset]['png_import'],receipt)
   p.save();p=ProjectService.open(p.root);current=snapshot(p,asset)[3]
   image_receipt=p.monster_palette_overrides[asset]['image_override'];image_path=path(p,image_receipt['sha256'],'idx');image_bytes=image_path.read_bytes();image_path.write_bytes(image_bytes[:-1])
   try:
    with self.assertRaises(ProjectError):ProjectService.open(p.root)
   finally:image_path.write_bytes(image_bytes)
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
   with zipfile.ZipFile(built['path']) as package:
    overlay=next(o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_palette');self.assertEqual(len(package.read(overlay['file'])),used);self.assertEqual(decompress_lzs(package.read(overlay['file']),len(original))[0],current)
   target=path(p,receipt['png_sha256'],'png');original_input=target.read_bytes();target.write_bytes(original_input[:-1]+bytes([original_input[-1]^1]))
   try:
    with self.assertRaises(ProjectError):ProjectService.open(p.root)
   finally:target.write_bytes(original_input)
   if os.getenv('LEGAIA_MONSTER_PNG_CASES'):Path(os.environ['LEGAIA_MONSTER_PNG_CASES']).write_text(json.dumps(dict(inspection=inspection,download=download,review=r,input_png_base64=base64.b64encode(edited).decode(),exact_original_retention=True,image_indices_authored=True,protected_block_prefix=True,history=True,save_open=True,package_readback=True,tampered_original_refused=True,gameplay_verified=False)),encoding='utf-8')
