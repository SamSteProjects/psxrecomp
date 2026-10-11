from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import os,struct,tempfile,unittest,math
from importer.battle_pack_animation import record,discover,pose
from importer.battle_character_catalog import discover as models,preview
from importer.core import ImportError

class BattlePackAnimationTests(unittest.TestCase):
 def test_record_modes_and_extents(self):
  raw=struct.pack('<4H',0x101,2,0x080c,0x401)+bytes(24);self.assertEqual(record(raw)['frame_count'],2)
  for offset,value in [(1,0),(4,0),(7,0),(len(raw)-1,1)]:
   bad=bytearray(raw);bad[offset]=value
   with self.subTest(offset=offset),self.assertRaises(ImportError):record(bytes(bad))
  with self.assertRaises(ImportError):record(raw[:-1])
 @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
 def test_retail_catalogue_pose_and_refusals(self):
  disc=os.environ['LEGAIA_DISC_BIN'];m=models(disc);a=discover(disc);self.assertEqual(len(a['clips']),30);self.assertEqual(sum(c['model_asset_id'] is not None for c in a['clips']),27);held=deepcopy(a)
  for slot,index in [(0,0),(1,9),(2,18)]:
   asset=m['models'][slot];_,_,raw=preview(disc,asset['semantic_id'],m['source_key']);clip=a['clips'][index]
   for frame in [0,clip['frame_count']-1]:
    _,_,_,_,geometry,transforms=pose(disc,asset['semantic_id'],clip['semantic_id'],m['source_key'],a['source_key'],frame)
    # Independent homogeneous matrix for a native vertex from each object.
    for obj,t in zip(raw['objects'],transforms):
     if not obj['vertex_count']:continue
     at=obj['vertex_start'];x,y,z=raw['vertices'][at];rx,ry,rz=[v*math.tau/4096 for v in t['rotation_psx']];sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
     matrix=[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]]
     for axis in range(3):self.assertAlmostEqual(geometry['vertices'][at][axis],sum(matrix[axis][i]*[x,y,z][i] for i in range(3))+t['translation'][axis],places=7)
    self.assertTrue(geometry['posed']);self.assertNotIn('triangle_normals',geometry)
  for model_id,clip_id,frame in [(m['models'][3]['semantic_id'],a['clips'][0]['semantic_id'],0),(m['models'][0]['semantic_id'],a['clips'][9]['semantic_id'],0),(m['models'][0]['semantic_id'],a['clips'][0]['semantic_id'],True),(m['models'][0]['semantic_id'],a['clips'][0]['semantic_id'],512)]:
   with self.assertRaises(ImportError):pose(disc,model_id,clip_id,m['source_key'],a['source_key'],frame)
  self.assertEqual(a,held)
