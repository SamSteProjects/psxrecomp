import os,base64,json,struct,tempfile,unittest,math
from pathlib import Path
from copy import deepcopy
from importer.monster_archive import discover,block
from importer.monster_motion import records,frame,ImportError
from importer.pipeline import _disc_context
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server

class MonsterMotionBoundsTests(unittest.TestCase):
 def test_unmatched_and_invalid_frame_refuse_before_source_read(self):
  clip=dict(preview_supported=False,frame_count=2)
  with self.assertRaises(ImportError):frame(b'',clip,0)
  clip['preview_supported']=True
  for index in (True,-1,2):
   with self.assertRaises(ImportError):frame(b'',clip,index)
  owner=dict(spell_entry_count=1)
  with self.assertRaises(ImportError):records(bytes(0x4c),owner,{})

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterMotionTests(unittest.TestCase):
 def test_source_entries_pose_and_mapping_refusals(self):
  disc=os.environ['LEGAIA_DISC_BIN'];catalog=discover(disc);clips=catalog['animations']
  self.assertEqual(len(clips),1811);self.assertEqual(sum(c['preview_supported'] for c in clips),1803)
  self.assertEqual({c['monster_id'] for c in clips if not c['preview_supported']},{182})
  with _disc_context(disc) as (_,_,_,archive):
   raw=archive.read_entry(archive.entry(867))
   for row in catalog['records']:
    data,_=block(raw,row['monster_id']);owned=[c for c in clips if c['monster_id']==row['monster_id']];self.assertEqual(len(owned),row['spell_entry_count'])
    for clip in owned:
     at=struct.unpack_from('<I',data,0x4c+clip['entry_index']*4)[0];self.assertEqual(clip['source_record']['byte_offset'],at+0x8c);self.assertEqual(clip['action_tag'],data[at]);self.assertEqual(clip['rate_byte'],data[at+0x78])
     if not clip['preview_supported']:
      with self.assertRaises(ImportError):frame(data,clip,0)
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=disc;p.save();context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));before=deepcopy((p._document(),p.undo_stack));poses=[]
   with http_server(p) as (_,post):
    status,report=post('/api/monster-resources',context);self.assertEqual(status,200,report)
    for identifier in (10,62,63):
     clip=next(c for c in clips if c['monster_id']==identifier and c['entry_index']==0)
     for index in (0,clip['frame_count']-1):
      body=dict(context,asset_id=clip['model_asset_id'],catalog_source_key=catalog['source_key'],animation_id=clip['semantic_id'],frame_index=index);status,v=post('/api/monster-pose',body);self.assertEqual(status,200,v);stream=base64.b64decode(v['source_motion_base64']);self.assertEqual(stream[:2],bytes([clip['part_count'],clip['frame_count']]))
      for part,t in enumerate(v['object_transforms']):
       b=stream[2+(index*clip['part_count']+part)*9:11+(index*clip['part_count']+part)*9];packed=int.from_bytes(b,'little')
       # Nibbles live between pairs rather than six contiguous 12-bit cells.
       values=[((packed>>low)&255)+((packed>>high)&15)*256 for low,high in ((0,16),(8,20),(24,40),(32,44),(48,64),(56,68))]
       self.assertEqual(t['translation'],[n-4096 if n>=2048 else n for n in values[:3]]);self.assertEqual(t['rotation_psx'],values[3:])
       o=v['base_preview']['geometry']['objects'][part];tx,ty,tz=t['translation'];rx,ry,rz=[n*math.pi/2048 for n in t['rotation_psx']];sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
       matrix=[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]]
       for vertex in range(o['vertex_start'],o['vertex_start']+o['vertex_count']):
        source=v['base_preview']['geometry']['vertices'][vertex];expected=[sum(matrix[a][k]*source[k] for k in range(3))+t['translation'][a] for a in range(3)]
        for actual,wanted in zip(v['geometry']['vertices'][vertex],expected):self.assertAlmostEqual(actual,wanted,places=7)
      self.assertNotIn('triangle_normals',v['geometry']);self.assertEqual(v['geometry']['textures'],v['base_preview']['geometry']['textures']);poses.append(v)
    body=dict(context,asset_id='asset://legaia/models/monster-archive/0010',catalog_source_key=catalog['source_key'],animation_id=clips[0]['semantic_id'],frame_index=0)
    self.assertEqual(post('/api/monster-pose',body)[0],400)
    self.assertEqual(post('/api/monster-pose',dict(body,expected_source_key='0'*64))[0],400)
   self.assertEqual((p._document(),p.undo_stack),before)
   if os.getenv('LEGAIA_MONSTER_MOTION_CASES'):Path(os.environ['LEGAIA_MONSTER_MOTION_CASES']).write_text(json.dumps(dict(report=report,poses=poses,all_entry_offsets=True,eight_unmatched_refused=True,source_channel_replay=True,independent_matrix_pose=True,unchanged=True,gameplay_verified=False)),encoding='utf-8')
