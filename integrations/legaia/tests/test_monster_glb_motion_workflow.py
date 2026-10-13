import base64,json,os,tempfile,unittest,zipfile
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources,current_pose
from sdk.monster_motion_authoring import inspect,review as numeric_review,apply as numeric_apply
from sdk.monster_motion_glb import review,apply,proposed_pose,validate_input,path
from sdk.monster_model_authoring import snapshot
from sdk.build import build_project
from importer.pipeline import import_scene
from importer.core import decompress_lzs


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN') and os.getenv('LEGAIA_MONSTER_EDITED_GLB'),'Private edited native fixture is required')
class MonsterGlbMotionWorkflowTests(unittest.TestCase):
 def test_retained_glb_pose_history_numeric_composition_and_delivery(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();content=Path(os.environ['LEGAIA_MONSTER_EDITED_GLB']).read_bytes();model='asset://legaia/models/monster-archive/0063';catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['entry_index']==0)
   def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'])
   i=inspect(p,**ctx(),animation_id=clip['semantic_id'],frame_index=0,part_index=0);args=dict(ctx(),animation_id=clip['semantic_id'],expected_current_block_sha256=i['current_block_sha256'],glb_base64=base64.b64encode(content).decode(),fps=24,animation_index=None,object_node_indices=None);v=review(p,**args);held=deepcopy((p._document(),p.undo_stack));pose=proposed_pose(p,review_key=v['review_key'],frame_index=0,**args);self.assertEqual((p._document(),p.undo_stack),held)
   with self.assertRaises(ProjectError):apply(p,review_key='0'*64,**args)
   apply(p,review_key=v['review_key'],**args);self.assertEqual(len(p.undo_stack),1);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after);receipt=deepcopy(p.monster_motion_overrides[clip['semantic_id']]['glb_import']);record,_,original,current,_,used=snapshot(p,**ctx());self.assertEqual(validate_input(p,original,clip,receipt)[0],content)
   i=inspect(p,**ctx(),animation_id=clip['semantic_id'],frame_index=0,part_index=0);t=i['channels']['translation'].copy();t[2]+=1;n=dict(ctx(),animation_id=clip['semantic_id'],frame_index=0,part_index=0,expected_current_block_sha256=i['current_block_sha256'],translation=t,rotation_psx=i['channels']['rotation_psx']);plan=numeric_review(p,**n);numeric_apply(p,review_key=plan['review_key'],**n);self.assertEqual(p.monster_motion_overrides[clip['semantic_id']]['glb_import'],receipt);p.save();p=ProjectService.open(p.root);current=snapshot(p,**ctx())[3]
   p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),1)
   with zipfile.ZipFile(built['path']) as package:self.assertEqual(decompress_lzs(package.read(overlays[0]['file']),len(original))[0],current)
   target=path(p,receipt['glb_sha256'],'glb');target.write_bytes(content[:-1])
   try:
    with self.assertRaises(ProjectError):ProjectService.open(p.root)
   finally:target.write_bytes(content)
   if os.getenv('LEGAIA_MONSTER_GLB_WORKFLOW_CASES'):Path(os.environ['LEGAIA_MONSTER_GLB_WORKFLOW_CASES']).write_text(json.dumps(dict(review=v,comparison=pose,history=True,save_open=True,exact_original_retention=True,numeric_composition=True,tamper_refused=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')
