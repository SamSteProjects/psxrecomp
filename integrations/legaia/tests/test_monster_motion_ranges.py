import base64,json,os,tempfile,unittest,zipfile
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from importer.monster_motion_authoring import patch_range
from importer.player_animation_authoring import _encode
from importer.player_battle import decode_part
from importer.core import ImportError as NativeError,decompress_lzs
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_motion_authoring import inspect,review,apply,proposed_pose
from sdk.monster_model_authoring import snapshot
from sdk.build import build_project
from importer.pipeline import import_scene


class MonsterRangeCodecTests(unittest.TestCase):
 def test_offset_preserves_motion_rotation_wrap_and_overflow_refusal(self):
  data=bytes(200)+bytes([1,3])+b''.join(_encode(t,r) for t,r in [([-10,0,0],[0,0,4095]),([0,1,0],[0,0,0]),([5,2,0],[0,0,1])])+bytes(20);stream=data[200:229];clip=dict(semantic_id='clip',preview_supported=True,frame_count=3,part_count=1,source_record=dict(byte_offset=200,byte_length=29,sha256=sha256(stream).hexdigest()));candidate,p=patch_range(data,data,clip,1,0,[3,1,0],[0,0,2],0,2,'offset');self.assertEqual([decode_part(candidate[202+i*9:211+i*9]) for i in range(3)],[dict(translation=t,rotation_psx=r) for t,r in [([-7,0,0],[0,0,1]),([3,1,0],[0,0,2]),([8,2,0],[0,0,3])]]);self.assertEqual(candidate[:202],data[:202]);self.assertEqual(candidate[229:],data[229:])
  with self.assertRaises(NativeError):patch_range(data,data,clip,1,0,[2047,1,0],[0,0,0],0,2,'offset')
  for start,end in ((2,1),(-1,1),(0,3)):
   with self.assertRaises(NativeError):patch_range(data,data,clip,1,0,[0,1,0],[0,0,0],start,end,'hold')


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterRangeWorkflowTests(unittest.TestCase):
 def test_hold_preview_history_offset_restore_and_native_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();model='asset://legaia/models/monster-archive/0063';catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported'] and c['frame_count']>=3)
   def context():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model,catalog_source_key=catalog['source_key'],animation_id=clip['semantic_id'],frame_index=1,part_index=0)
   observed=inspect(p,**context());t=observed['channels']['translation'].copy();t[0]+=3;args=dict(context(),expected_current_block_sha256=observed['current_block_sha256'],translation=t,rotation_psx=observed['channels']['rotation_psx'].copy(),frame_start=0,frame_end=2,range_operation='hold');plan=review(p,**args);held=deepcopy((p._document(),p.undo_stack));comparison=proposed_pose(p,review_key=plan['review_key'],**args);self.assertEqual((p._document(),p.undo_stack),held);apply(p,review_key=plan['review_key'],**args);self.assertEqual(len(p.undo_stack),1);p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(p.root);self.assertEqual(len(p.monster_motion_overrides[clip['semantic_id']]['edits']),3)
   current=inspect(p,**context());t=current['channels']['translation'].copy();t[2]+=2;offset_args=dict(context(),expected_current_block_sha256=current['current_block_sha256'],translation=t,rotation_psx=current['channels']['rotation_psx'].copy(),frame_start=0,frame_end=2,range_operation='offset');offset=review(p,**offset_args);apply(p,review_key=offset['review_key'],**offset_args)
   model_ctx={k:v for k,v in context().items() if k not in ('animation_id','frame_index','part_index')};record,_,original,block,_,used=snapshot(p,**model_ctx);p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),1)
   with zipfile.ZipFile(built['path']) as package:self.assertEqual(decompress_lzs(package.read(overlays[0]['file']),len(original))[0],block)
   current=inspect(p,**context());restore_args=dict(context(),expected_current_block_sha256=current['current_block_sha256'],translation=current['channels']['translation'],rotation_psx=current['channels']['rotation_psx'],frame_start=0,frame_end=2,range_operation='restore');restoration=review(p,**restore_args);apply(p,review_key=restoration['review_key'],**restore_args);self.assertEqual(p.monster_motion_overrides,{})
   if os.getenv('LEGAIA_MONSTER_RANGE_CASES'):Path(os.environ['LEGAIA_MONSTER_RANGE_CASES']).write_text(json.dumps(dict(inspection=observed,review=plan,comparison=comparison,translation=args['translation'],rotation_psx=args['rotation_psx'],range=dict(frame_start=0,frame_end=2,range_operation='hold'),offset_review=offset,restore_review=restoration,history=True,save_open=True,package_readback=True,package_sha256=built['sha256'],restored_owner=True,gameplay_verified=False)),encoding='utf-8')
