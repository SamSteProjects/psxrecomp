import os,math,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from importer.player_battle import discover,preview,pose,_sources
from importer.core import decompress_lzs,ImportError
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerBattlePoseTests(unittest.TestCase):
    def test_all_stored_actions_first_last_and_attachment_channels(self):
        disc=os.environ['LEGAIA_DISC_BIN'];catalog=discover(disc);_,sources=_sources(disc);count=empty=vertices=0
        for m in catalog['models']:
            raw=sources[m['player_index']][3];desc,_,_,budget=struct.unpack_from('<4I',raw);bank,_=decompress_lzs(raw[16:desc],budget);_,_,base,assembly=preview(disc,m['semantic_id'],catalog['source_key'],[0]*5)
            for clip in m['actions']:
                if not clip['preview_supported']:
                    empty+=1
                    with self.assertRaises(ImportError):pose(disc,m['semantic_id'],catalog['source_key'],[0]*5,clip['action_slot'],0)
                    continue
                for frame in [0,clip['frame_count']-1]:
                    _,_,g,a,c,transforms=pose(disc,m['semantic_id'],catalog['source_key'],[0]*5,clip['action_slot'],frame);self.assertEqual(a,assembly);self.assertEqual(c,clip);self.assertNotIn('triangle_normals',g)
                    for obj,tr,part in zip(base['objects'],transforms,assembly['animation_part_indices']):
                        at=clip['source_record']['byte_offset']+2+(frame*clip['part_count']+part)*9;b=bank[at:at+9];signed=lambda v:v-4096 if v&2048 else v
                        t=[signed(b[0]|((b[2]&15)<<8)),signed(b[1]|((b[2]>>4)<<8)),signed(b[3]|((b[5]&15)<<8))];angles=[b[4]|((b[5]>>4)<<8),b[6]|((b[8]&15)<<8),b[7]|((b[8]>>4)<<8)];self.assertEqual(tr['translation'],t);self.assertEqual(tr['rotation_psx'],angles);self.assertEqual(tr['part_index'],part)
                        rx,ry,rz=[v*math.pi/2048 for v in angles];sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
                        # Independent full homogeneous rotation matrix, including extras.
                        matrix=[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]]
                        for i in range(obj['vertex_start'],obj['vertex_start']+obj['vertex_count']):
                            v=base['vertices'][i];expected=[sum(row[j]*v[j] for j in range(3))+t[k] for k,row in enumerate(matrix)]
                            for actual,want in zip(g['vertices'][i],expected):self.assertAlmostEqual(actual,want,places=7)
                            vertices+=1
                    count+=1
        self.assertEqual((count,empty),(76,10));self.assertEqual(vertices,49700)

    def test_pose_http_rejects_empty_foreign_and_invalid_frames(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];held=deepcopy((p._document(),p.undo_stack));catalog=discover(p.disc_path);args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=catalog['models'][0]['semantic_id'],catalog_source_key=catalog['source_key'],equipped=[0]*5,action_slot=0,frame_index=0)
            with http_server(p) as (_,post):
                self.assertEqual(post('/api/player-battle-pose',args)[0],200)
                for change in [dict(action_slot=6),dict(action_slot=True),dict(frame_index=True),dict(frame_index=999),dict(asset_id='foreign'),dict(catalog_source_key='0'*64),dict(expected_source_key='0'*64),dict(equipped=[True]*5),dict(extra=True)]:self.assertEqual(post('/api/player-battle-pose',dict(args,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),held)
