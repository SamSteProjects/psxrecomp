import base64,json,os,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources,current_pose
from sdk.monster_motion_authoring import inspect,review,apply
from sdk.monster_model_authoring import export as model_export,review as model_review,apply as model_apply,snapshot as model_snapshot
from sdk.monster_palettes import inspect as palette_inspect,review as palette_review,apply as palette_apply
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs
from test_monster_model_authoring import shifted_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterMotionWorkflowTests(unittest.TestCase):
 def test_history_model_after_motion_and_composed_delivery(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063';catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']);held=deepcopy(p._document())
   def context():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'])
   selection=dict(animation_id=clip['semantic_id'],frame_index=0,part_index=0);observed=inspect(p,**context(),**selection);t=observed['channels']['translation'].copy();r=observed['channels']['rotation_psx'].copy();t[0]+=1;r[2]=(r[2]+1)%4096;args=dict(context(),**selection,expected_current_block_sha256=observed['current_block_sha256'],translation=t,rotation_psx=r);plan=review(p,**args)
   with self.assertRaises(ProjectError):apply(p,review_key='0'*64,**args)
   apply(p,review_key=plan['review_key'],**args);self.assertEqual(len(p.undo_stack),1);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after);again=inspect(p,**context(),**selection);self.assertEqual(again['channels']['translation'],t)
   e=model_export(p,**context());content=shifted_glb(base64.b64decode(e['glb_base64']));model_args=dict(context(),binding=e['binding'],glb_base64=base64.b64encode(content).decode());model_plan=model_review(p,**model_args);model_apply(p,review_key=model_plan['review_key'],**model_args);p.save();p=ProjectService.open(p.root)
   texture='texture://legaia/monster-archive/0063/pool';fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=texture,palette_index=0);v=palette_inspect(p,**fresh);palette_args=dict(fresh,entry_index=1,word=v['preview']['words'][1]^1,expected_current_sha256=v['current_pool_sha256']);q=palette_review(p,**palette_args);palette_apply(p,review_key=q['review_key'],**palette_args)
   pose=current_pose(p,**context(),animation_id=clip['semantic_id'],frame_index=0);self.assertEqual(pose['object_transforms'][0]['translation'],t);self.assertEqual(pose['object_transforms'][0]['rotation_psx'],r);record,_,original,current,_,used=model_snapshot(p,**context());self.assertEqual(current[clip['source_record']['byte_offset']:clip['source_record']['byte_offset']+clip['source_record']['byte_length']],base64.b64decode(plan['candidate_motion_base64']))
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),1)
   with zipfile.ZipFile(built['path']) as package:
    payload=package.read(overlays[0]['file']);self.assertEqual(len(payload),used);self.assertEqual(decompress_lzs(payload,len(original))[0],current)
   self.assertEqual(ProjectService.open(p.root)._document(),p._document())
   if os.getenv('LEGAIA_MONSTER_MOTION_WORKFLOW_CASES'):Path(os.environ['LEGAIA_MONSTER_MOTION_WORKFLOW_CASES']).write_text(json.dumps(dict(inspection=again,pose=pose,history=True,save_open=True,model_after_motion=True,model_texture_motion_composed=True,one_slot_overlay=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
