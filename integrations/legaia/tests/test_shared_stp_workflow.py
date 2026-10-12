import os,base64,tempfile,json,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from importer.texture_png import decode_png,_encode_png
from importer.textures import parse_tim,decode_tim
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class SharedStpTests(unittest.TestCase):
 def test_explicit_flag_mask_and_review_identity(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/field-party/874/2/0'
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0)
   with http_server(p) as (_,post):
    _,report=post('/api/field-texture-resources',{k:v for k,v in ctx().items() if k not in ('asset_id','palette_index')});_,inspection=post('/api/field-texture-inspect',ctx());args=dict(ctx(),expected_current_sha256=inspection['palette']['effective_sha256']);_,e=post('/api/field-texture-png-download',args);rgba=decode_png(base64.b64decode(e['png_base64']));mask=decode_png(base64.b64decode(e['stp_png_base64']));data=bytearray(mask['rgba']);index=next(i for i in range(0,len(rgba['rgba']),4) if rgba['rgba'][i+3]==255 and any(rgba['rgba'][i:i+3]));new=0 if data[index] else 255;data[index:index+4]=bytes([new,new,new,255]);edited=_encode_png(mask['width'],mask['height'],bytes(data));body=dict(args,png_base64=e['png_base64'],stp_png_base64=base64.b64encode(edited).decode(),palette_mode='rebuild');held=deepcopy((p._document(),p.undo_stack));status,r=post('/api/field-texture-png-review',body);self.assertEqual(status,200,r);self.assertEqual((p._document(),p.undo_stack),held);self.assertEqual(r['stp_policy'],'explicit_mask_with_converter_transparent_black_rules');decoded=decode_tim(parse_tim(base64.b64decode(r['candidate_tim_base64'])),0);self.assertEqual(decoded['stp'][index//4],int(new!=0));self.assertGreater(r['quantization']['stp_changed_pixels'],0);self.assertEqual(post('/api/field-texture-png-apply',dict(body,stp_png_base64=e['stp_png_base64'],review_key=r['review_key']))[0],400);status,result=post('/api/field-texture-png-apply',dict(body,review_key=r['review_key']));self.assertEqual(status,200,result);self.assertEqual(len(p.undo_stack),1)
   after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   from sdk.field_texture_sources import validate,path
   receipt=p.texture_overrides[asset]['field_png_source']
   original_png,original_stp,baseline,candidate=validate(p,receipt)
   self.assertEqual(original_png,base64.b64decode(e['png_base64']))
   self.assertEqual(original_stp,edited)
   self.assertEqual(baseline,base64.b64decode(inspection['current_tim_base64']))
   self.assertEqual(candidate,base64.b64decode(r['candidate_tim_base64']))
   with http_server(p) as (_,post):
    current_sha=p.texture_overrides[asset]['asset_sha256']
    download_args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,expected_current_sha256=current_sha)
    status,retained_report=post('/api/field-texture-resources',{k:v for k,v in download_args.items() if k in ('expected_project_path','expected_source_key')})
    self.assertEqual(status,200,retained_report)
    self.assertEqual(len(retained_report['assets']),8);self.assertEqual(len(retained_report['retained_inputs']),2)
    self.assertEqual({row['kind'] for row in retained_report['retained_inputs']},{'png','stp'})
    for row in retained_report['retained_inputs']:
     self.assertEqual(row['references'],[asset]);self.assertEqual(row['source_record'],receipt)
     self.assertEqual(row['current_tim_sha256'],current_sha)
     self.assertEqual(row['layer'],'historical_authored_input')
     self.assertNotIn('png_base64',row)
    before_download=deepcopy((p._document(),p.undo_stack))
    input_downloads=[]
    for kind,expected in (('png',original_png),('stp',original_stp)):
     status,payload=post('/api/field-texture-input-download',dict(download_args,kind=kind))
     self.assertEqual(status,200,payload);self.assertEqual(base64.b64decode(payload['png_base64']),expected)
     input_downloads.append(payload)
     self.assertEqual(payload['retained_source'],receipt);self.assertEqual(payload['layer'],'historical_authored_input')
    self.assertEqual(post('/api/field-texture-input-download',dict(download_args,kind='png',expected_current_sha256='0'*64))[0],400)
    self.assertEqual(post('/api/field-texture-input-download',dict(download_args,kind='tim'))[0],400)
    self.assertEqual((p._document(),p.undo_stack),before_download)
   # Historical PNG provenance survives later native edits without claiming
   # that the uploaded image represents final Current pixels.
   later=bytearray(candidate);later[22]^=1
   p.set_texture_replacement(asset,bytes(later));p.save()
   p=ProjectService.open(p.root)
   self.assertEqual(p.texture_overrides[asset]['field_png_source'],receipt)
   self.assertEqual(p.read_texture_replacement(p.texture_overrides[asset]),bytes(later))
   for hash_key,size_key,suffix in (('png_sha256','png_byte_length','png'),('stp_sha256','stp_byte_length','png'),('tim_sha256','tim_byte_length','tim')):
    target=path(p,receipt[hash_key],suffix);original=target.read_bytes()
    damaged=bytearray(original);damaged[-1]^=1;target.write_bytes(damaged)
    try:
     with self.assertRaises(ProjectError):ProjectService.open(p.root)
     with self.assertRaises(ProjectError):p.read_texture_replacement(p.texture_overrides[asset])
    finally:target.write_bytes(original)
    target.unlink()
    try:
     with self.assertRaises(ProjectError):ProjectService.open(p.root)
    finally:target.write_bytes(original)
   from sdk.field_texture_authoring import validate as validate_owner
   wrong=deepcopy(p.texture_overrides[asset]);wrong['field_png_source']['asset_id']='texture://legaia/field-party/874/2/1'
   with self.assertRaises(ProjectError):validate_owner(p,wrong,asset)
   wrong['field_png_source']=[]
   with self.assertRaises(ProjectError):validate_owner(p,wrong,asset)
   if os.getenv('LEGAIA_SHARED_STP_CASES'):Path(os.environ['LEGAIA_SHARED_STP_CASES']).write_text(json.dumps(dict(retained_report=retained_report,input_downloads=input_downloads,report=report,inspection=inspection,review=r,png_base64=e['png_base64'],mask_base64=base64.b64encode(edited).decode(),original_mask_base64=e['stp_png_base64'],pixel_index=index//4,expected_stp=int(new!=0),history=True,save_open=True,changed_mask_apply_refused=True,gameplay_verified=False)),encoding='utf-8')
