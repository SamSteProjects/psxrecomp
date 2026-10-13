import base64,json,os,struct,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources,current_preview,current_pose
from sdk.monster_model_authoring import export,review,apply,snapshot
from sdk.monster_models import path
from sdk.monster_palettes import inspect,review as palette_review,apply as palette_apply
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs
from importer.texture_png import decode_png,_encode_png
from test_monster_model_authoring import shifted_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterModelWorkflowTests(unittest.TestCase):
 def test_retained_history_current_pose_and_single_composed_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063';texture='texture://legaia/monster-archive/0063/pool';catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
   def context():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'])
   held=deepcopy(p._document());exports=[];plans=[]
   for n in range(2):
    e=export(p,**context());input_bytes=shifted_glb(base64.b64decode(e['glb_base64']));args=dict(context(),binding=e['binding'],glb_base64=base64.b64encode(input_bytes).decode());plan=review(p,**args)
    with self.assertRaises(ProjectError):apply(p,review_key='0'*64,**args)
    apply(p,review_key=plan['review_key'],**args);self.assertEqual(len(p.undo_stack),n+1);exports.append(e);plans.append(plan)
   after=deepcopy(p._document());p.undo();p.undo();self.assertEqual(p._document(),held);p.redo();p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
   receipt=p.monster_model_overrides[model]['inputs'][0];original_input=path(p,receipt['glb_sha256'],'glb').read_bytes();self.assertEqual(original_input,shifted_glb(base64.b64decode(exports[0]['glb_base64'])))
   fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=texture,palette_index=0);observed=inspect(p,**fresh);args=dict(fresh,entry_index=1,word=observed['preview']['words'][1]^1,expected_current_sha256=observed['current_pool_sha256']);proposal=palette_review(p,**args);palette_apply(p,review_key=proposal['review_key'],**args)
   from sdk.monster_png import download as png_download,review as png_review,apply as png_apply
   fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=texture,palette_index=0);observed=inspect(p,**fresh);png_args=dict(fresh,expected_current_sha256=observed['current_pool_sha256']);downloaded=png_download(p,**png_args);pixels=decode_png(base64.b64decode(downloaded['png_base64']));rgba=bytearray(pixels['rgba']);rgba[:4]=bytes([0,255,0,255]);edited=_encode_png(pixels['width'],pixels['height'],bytes(rgba));png_args.update(png_base64=base64.b64encode(edited).decode(),palette_mode='rebuild');image_plan=png_review(p,**png_args);png_apply(p,review_key=image_plan['review_key'],**png_args);self.assertIn('image_override',p.monster_palette_overrides[texture])
   v=current_preview(p,**context());self.assertEqual(base64.b64decode(v['source_tmd_base64']),base64.b64decode(plans[-1]['candidate_tmd_base64']));clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']);pose=current_pose(p,**context(),animation_id=clip['semantic_id'],frame_index=0);self.assertEqual(pose['base_preview']['model_binding'],p.monster_model_overrides[model])
   record,pool,original,current,raw,used=snapshot(p,**context());at=record['source_record']['byte_offset'];end=at+record['source_record']['byte_length'];pool_at=pool['source_record']['byte_offset'];expected=bytearray(original);expected[at:end]=base64.b64decode(plans[-1]['candidate_tmd_base64']);expected[pool_at:]=base64.b64decode(image_plan['candidate_pool_base64']);self.assertEqual(current,bytes(expected))
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));slots=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(slots),1)
   with zipfile.ZipFile(built['path']) as package:
    payload=package.read(slots[0]['file']);self.assertEqual(len(payload),used);self.assertEqual(decompress_lzs(payload,len(original))[0],current);self.assertEqual((Path(built['package_directory'])/slots[0]['file']).read_bytes(),payload)
   self.assertEqual(ProjectService.open(p.root)._document(),p._document());target=path(p,receipt['glb_sha256'],'glb');target.write_bytes(original_input[:-1])
   try:
    with self.assertRaises(ProjectError):ProjectService.open(p.root)
   finally:target.write_bytes(original_input)
   if os.getenv('LEGAIA_MONSTER_MODEL_WORKFLOW_CASES'):Path(os.environ['LEGAIA_MONSTER_MODEL_WORKFLOW_CASES']).write_text(json.dumps(dict(current=v,pose=pose,export=export(p,**context()),history=True,save_open=True,original_glb_retained=True,tampered_input_refused=True,model_texture_composition=True,one_slot_overlay=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
