import os,base64,struct,tempfile,json,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs
from importer.texture_authoring import inspect_tim_pixel_index
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class SharedTimFileTests(unittest.TestCase):
 def test_download_review_exact_retention_and_history(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/field-party/874/2/0'
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset)
   with http_server(p) as (_,post):
    _,report=post('/api/field-texture-resources',{k:v for k,v in ctx().items() if k!='asset_id'});_,inspection=post('/api/field-texture-inspect',dict(ctx(),palette_index=0));raw=base64.b64decode(inspection['current_tim_base64']);candidate=bytearray(raw);pixel=inspect_tim_pixel_index(raw,0,0);candidate[pixel['byte_offset']]^=1;struct.pack_into('<H',candidate,22,struct.unpack_from('<H',raw,22)[0]^1);candidate=bytes(candidate)
    for layer in ('retail','current'):
     status,r=post('/api/field-texture-download',dict(ctx(),layer=layer,expected_current_sha256=inspection['palette']['effective_sha256']));self.assertEqual(status,200,r);self.assertEqual(base64.b64decode(r['tim_base64']),raw)
    args=dict(ctx(),palette_index=0,tim_base64=base64.b64encode(candidate).decode(),expected_current_sha256=inspection['palette']['effective_sha256']);before=deepcopy((p._document(),p.undo_stack));status,r=post('/api/field-texture-file-review',args);self.assertEqual(status,200,r);self.assertEqual(base64.b64decode(r['candidate_tim_base64']),candidate);self.assertEqual((p._document(),p.undo_stack),before);self.assertGreater(r['changes']['pixel_indices_changed'],0);self.assertGreater(r['changes']['palette_words_changed'],0);self.assertEqual(post('/api/field-texture-file-apply',dict(args,review_key='0'*64))[0],400);status,result=post('/api/field-texture-file-apply',dict(args,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.read_texture_replacement(p.texture_overrides[asset]),candidate);self.assertEqual(post('/api/field-texture-file-apply',dict(args,review_key=r['review_key']))[0],400)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after);self.assertEqual(p.read_texture_replacement(p.texture_overrides[asset]),candidate)
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
   with zipfile.ZipFile(built['path']) as package:
    overlay=next(o for o in audit['overlays'] if o.get('carrier_kind')=='lzs_shared_field_texture_pack');bank=decompress_lzs(package.read(overlay['file']),overlay['source_record'].get('decoded_size',p._texture_context(asset).options(asset)['carrier']['decoded_size']))[0];offset=p._texture_context(asset).options(asset)['source_record']['byte_offset'];self.assertEqual(bank[offset:offset+len(candidate)],candidate)
   if os.getenv('LEGAIA_SHARED_TIM_FILE_CASES'):Path(os.environ['LEGAIA_SHARED_TIM_FILE_CASES']).write_text(json.dumps(dict(report=report,inspection=inspection,review=r,input_base64=base64.b64encode(candidate).decode(),history=True,save_open=True,retained_exact=True,package_sha256=built['sha256'],package_tim_readback=True,gameplay_verified=False)),encoding='utf-8')
