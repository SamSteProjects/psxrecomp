import os,json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_motion_authoring import inspect,review,proposed_pose


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterMotionProposedTests(unittest.TestCase):
 def test_exact_review_unsaved_pose_and_stale_refusal(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**fresh)['catalog'];model='asset://legaia/models/monster-archive/0063';clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported']);context=dict(fresh,asset_id=model,catalog_source_key=catalog['source_key'],animation_id=clip['semantic_id'],frame_index=0,part_index=0);observed=inspect(p,**context);t=observed['channels']['translation'].copy();t[0]+=128;args=dict(context,expected_current_block_sha256=observed['current_block_sha256'],translation=t,rotation_psx=observed['channels']['rotation_psx'].copy());plan=review(p,**args);held=deepcopy((p._document(),p.undo_stack))
   with self.assertRaises(ProjectError):proposed_pose(p,review_key='0'*64,**args)
   proposed=proposed_pose(p,review_key=plan['review_key'],**args);self.assertEqual(proposed['review'],plan);before=proposed['current_pose']['geometry'];after=proposed['proposed_pose']['geometry'];obj=before['objects'][0];affected=range(obj['vertex_start'],obj['vertex_start']+obj['vertex_count'])
   for i,(a,b) in enumerate(zip(before['vertices'],after['vertices'])):
    self.assertEqual(b,[a[0]+128,a[1],a[2]] if i in affected else a)
   for field in ('triangles','triangle_uvs','triangle_materials','textures','objects'):self.assertEqual(before[field],after[field])
   self.assertEqual((p._document(),p.undo_stack),held)
   if os.getenv('LEGAIA_MONSTER_MOTION_PROPOSED_CASES'):Path(os.environ['LEGAIA_MONSTER_MOTION_PROPOSED_CASES']).write_text(json.dumps(dict(inspection=observed,review=plan,comparison=proposed,source_model=catalog['models'][next(i for i,m in enumerate(catalog['models']) if m['semantic_id']==model)],vertex_delta_exact=True,unselected_parts_unchanged=True,history_unchanged=True,gameplay_verified=False)),encoding='utf-8')
