import base64,json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.monster_archive import resources
from sdk.monster_motion_authoring import inspect,review
from importer.monster_motion_authoring import patch
from importer.core import ImportError as NativeError


class MonsterMotionCodecTests(unittest.TestCase):
 def test_nine_byte_boundaries_and_refusals(self):
  from hashlib import sha256
  data=bytes(200)+bytes([1,1])+bytes(9)+bytes(20);stream=data[200:211];clip=dict(semantic_id='clip',preview_supported=True,frame_count=1,part_count=1,source_record=dict(byte_offset=200,byte_length=11,sha256=sha256(stream).hexdigest()))
  candidate,p=patch(data,clip,0,0,[-2048,2047,-1],[4095,2048,1]);self.assertEqual(candidate[:202],data[:202]);self.assertEqual(candidate[211:],data[211:]);self.assertEqual(candidate[202:211],bytes([0,255,120,255,255,255,0,1,8]));self.assertEqual(p['after']['translation'],[-2048,2047,-1])
  for values in ([True,0,0],[-2049,0,0],[2048,0,0],[0,0],[0.1,0,0]):
   with self.assertRaises(NativeError):patch(data,clip,0,0,values,[0,0,0])
  for value in (-1,4096,True):
   with self.assertRaises(NativeError):patch(data,clip,0,0,[0,0,0],[value,0,0])


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterMotionReviewTests(unittest.TestCase):
 def test_native_frame_review_and_protected_project(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));catalog=resources(p,**fresh)['catalog'];clips=[next(c for c in catalog['animations'] if c['monster_id']==i and c['preview_supported']) for i in (10,62,63)];held=deepcopy((p._document(),p.undo_stack));cases=[]
   for clip in clips:
    ctx=dict(fresh,asset_id=clip['model_asset_id'],catalog_source_key=catalog['source_key'],animation_id=clip['semantic_id'],frame_index=clip['frame_count']-1,part_index=clip['part_count']-1);v=inspect(p,**ctx);translation=v['channels']['translation'].copy();translation[0]=translation[0]+1 if translation[0]<2047 else translation[0]-1;rotation=v['channels']['rotation_psx'].copy();rotation[2]=(rotation[2]+1)%4096;args=dict(ctx,expected_current_block_sha256=v['current_block_sha256'],translation=translation,rotation_psx=rotation);plan=review(p,**args);raw=base64.b64decode(v['source_motion_base64']);candidate=base64.b64decode(plan['candidate_motion_base64']);at=2+(ctx['frame_index']*clip['part_count']+ctx['part_index'])*9;self.assertEqual(raw[:at],candidate[:at]);self.assertEqual(raw[at+9:],candidate[at+9:]);self.assertEqual(plan['persistence'],'not_applied')
    with self.assertRaises(ProjectError):review(p,**dict(args,expected_current_block_sha256='0'*64))
    cases.append(dict(inspection=v,review=plan,translation=translation,rotation_psx=rotation))
   self.assertEqual((p._document(),p.undo_stack),held)
   if os.getenv('LEGAIA_MONSTER_FRAME_CASES'):Path(os.environ['LEGAIA_MONSTER_FRAME_CASES']).write_text(json.dumps(dict(cases=cases,history_unchanged=True,document_unchanged=True,gameplay_verified=False)),encoding='utf-8')
