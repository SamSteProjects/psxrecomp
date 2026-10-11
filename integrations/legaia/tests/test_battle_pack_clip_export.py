"""Complete pack clip channels checked against original eight-byte records."""
import base64,math,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from importer.pipeline import _disc_context
from importer.core import decode_lzs_sections
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.battle_character_resources import resources,animations,preview
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class BattlePackClipExportTests(unittest.TestCase):
    def test_complete_native_channels_and_http_guards(self):
        disc=os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_,_,_,archive):bank=decode_lzs_sections(archive.read_entry(archive.entry(1203)))[2][1]
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=disc;context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));r=resources(p,**context);an=animations(p,**context);held=deepcopy((p._document(),p.undo_stack));samples=0
            with http_server(p) as (_,post):
                for slot,index in enumerate([8,17,26]):
                    clip=an['catalog']['clips'][index];model=r['catalog']['models'][slot];rate=[23.5,30,12][slot];args=dict(context,model_id=model['semantic_id'],model_source_key=r['catalog']['source_key'],animation_id=clip['semantic_id'],animation_source_key=an['catalog']['source_key'],fps=rate)
                    status,value=post('/api/battle-pack-clip-export',args);self.assertEqual(status,200,value);doc,binary=parse_glb(base64.b64decode(value['glb_base64']));a=doc['animations'][0];self.assertEqual(len(a['channels']),clip['bone_count']*2);self.assertNotIn('skins',doc)
                    raw=preview(p,**context,asset_id=model['semantic_id'],catalog_source_key=r['catalog']['source_key'],palette_index=0)['preview']
                    for bone,obj in enumerate(raw['objects']):
                        tracks={c['target']['path']:a['samplers'][c['sampler']] for c in a['channels'] if c['target']['node']==bone};ts=values(doc,binary,tracks['translation']['output']);qs=values(doc,binary,tracks['rotation']['output']);times=values(doc,binary,tracks['translation']['input'])
                        self.assertEqual(len(ts),clip['frame_count']+1);self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2]);self.assertEqual(tracks['rotation']['interpolation'],'STEP')
                        for frame in range(clip['frame_count']):
                            self.assertAlmostEqual(times[frame][0],frame/rate,places=6);offset=clip['source_record']['byte_offset']+8+(frame*clip['bone_count']+bone)*8;b=bank[offset:offset+8]
                            signed=lambda n:n-4096 if n&2048 else n
                            t=[signed(b[0]|((b[2]&15)<<8)),signed(b[1]|((b[2]>>4)<<8)),signed(b[3]|((b[4]&15)<<8))];self.assertEqual(ts[frame],(t[0],-t[1],t[2]))
                            rx,ry,rz=[v*math.pi/128 for v in b[5:8]];sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
                            for x,y,z in [[1,0,0],[0,1,0],[0,0,1]]:
                                original=[x,-y,z];y,z=y*cx-z*sx,y*sx+z*cx;x,z=x*cy+z*sy,-x*sy+z*cy;x,y=x*cz-y*sz,x*sz+y*cz
                                qx,qy,qz,qw=qs[frame];vx,vy,vz=original;cross=[2*(qy*vz-qz*vy),2*(qz*vx-qx*vz),2*(qx*vy-qy*vx)];actual=[vx+qw*cross[0]+qy*cross[2]-qz*cross[1],vy+qw*cross[1]+qz*cross[0]-qx*cross[2],vz+qw*cross[2]+qx*cross[1]-qy*cross[0]]
                                for actual_axis,expected_axis in zip(actual,[x,-y,z]):self.assertAlmostEqual(actual_axis,expected_axis,places=6)
                            samples+=1
                        self.assertAlmostEqual(times[-1][0],clip['frame_count']/rate,places=6)
                for change in [dict(fps=True),dict(fps=0),dict(fps=121),dict(fps='30'),dict(extra=True),dict(model_source_key='0'*64),dict(animation_source_key='0'*64),dict(animation_id=an['catalog']['clips'][0]['semantic_id'])]:self.assertEqual(post('/api/battle-pack-clip-export',dict(args,**change))[0],400)
            self.assertEqual(samples,2018);self.assertEqual((p._document(),p.undo_stack),held)
