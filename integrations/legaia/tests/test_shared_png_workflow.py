import os,base64,tempfile,unittest,json
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from importer.texture_png import decode_png,_encode_png
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class SharedPngTests(unittest.TestCase):
 def test_export_quantization_review_native_retention(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/field-party/874/2/0'
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0)
   with http_server(p) as (_,post):
    _,report=post('/api/field-texture-resources',{k:v for k,v in ctx().items() if k not in ('asset_id','palette_index')});_,inspection=post('/api/field-texture-inspect',ctx());body=dict(ctx(),expected_current_sha256=inspection['palette']['effective_sha256']);status,export=post('/api/field-texture-png-download',body);self.assertEqual(status,200,export);original=base64.b64decode(export['png_base64']);pixels=decode_png(original);self.assertEqual(pixels['rgba'],base64.b64decode(inspection['rgba_base64']));rgba=bytearray(pixels['rgba']);rgba[:4]=bytes([255,0,0,255]);edited=_encode_png(pixels['width'],pixels['height'],bytes(rgba));args=dict(body,png_base64=base64.b64encode(edited).decode(),palette_mode='rebuild');held=deepcopy((p._document(),p.undo_stack));status,r=post('/api/field-texture-png-review',args);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),held);self.assertGreater(r['changes']['total_change_count'],0);self.assertEqual(post('/api/field-texture-png-apply',dict(args,review_key='0'*64))[0],400);status,result=post('/api/field-texture-png-apply',dict(args,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.read_texture_replacement(p.texture_overrides[asset]),base64.b64decode(r['candidate_tim_base64']));self.assertEqual(post('/api/field-texture-png-apply',dict(args,review_key=r['review_key']))[0],400)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   from sdk.field_texture_authoring import resources
   retained_report=resources(p,str(p.root),source_key(p))
   self.assertEqual(len(retained_report['retained_inputs']),1)
   self.assertEqual(retained_report['retained_inputs'][0]['kind'],'png')
   from sdk.field_texture_sources import validate,path
   from sdk.build import build_project
   from importer.pipeline import import_scene
   from importer.core import decompress_lzs
   import zipfile
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save()
   self.assertEqual(validate(p,p.texture_overrides[asset]['field_png_source'])[0],edited)
   built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
   with zipfile.ZipFile(built['path']) as package:
    overlay=next(o for o in audit['overlays'] if o.get('carrier_kind')=='lzs_shared_field_texture_pack')
    options=p._texture_context(asset).options(asset)
    bank=decompress_lzs(package.read(overlay['file']),options['carrier']['decoded_size'])[0]
    offset=options['source_record']['byte_offset'];expected=base64.b64decode(r['candidate_tim_base64'])
    self.assertEqual(bank[offset:offset+len(expected)],expected)
   receipt=p.texture_overrides[asset]['field_png_source'];target=path(p,receipt['png_sha256'],'png');original=target.read_bytes();target.unlink()
   try:
    from sdk.project import ProjectError
    with self.assertRaises(ProjectError):build_project(p)
   finally:target.write_bytes(original)
   if os.getenv('LEGAIA_SHARED_PNG_CASES'):Path(os.environ['LEGAIA_SHARED_PNG_CASES']).write_text(json.dumps(dict(report=report,inspection=inspection,exported=export,review=r,input_base64=base64.b64encode(edited).decode(),history=True,save_open=True,retained_native_exact=True,gameplay_verified=False)),encoding='utf-8')
