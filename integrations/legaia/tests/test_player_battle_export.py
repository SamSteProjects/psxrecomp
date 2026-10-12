import base64,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources,preview,pose
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values
from importer.texture_png import decode_png


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerBattleExportTests(unittest.TestCase):
    def test_three_modes_match_selected_geometry_textures_and_attachment_tracks(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));report=resources(p,**ctx);held=deepcopy((p._document(),p.undo_stack));files=0
            with http_server(p) as (_,post):
                for m in report['catalog']['models']:
                    ids=[next(d['item_id'] for d in m['descriptors'] if d['section_index']==i) for i in range(5)];raw=preview(p,**ctx,asset_id=m['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=ids);clip=m['actions'][0];last=clip['frame_count']-1
                    for mode in ('object-local','pose','clip'):
                        args=dict(ctx,asset_id=m['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=ids,mode=mode,action_slot=None if mode=='object-local' else 0,frame_index=last if mode=='pose' else None,fps=23.5 if mode=='clip' else None)
                        status,result=post('/api/player-battle-export',args);self.assertEqual(status,200,result);content=base64.b64decode(result['glb_base64']);doc,binary=parse_glb(content);self.assertEqual(doc['extras']['source_record']['player_assembly'],raw['assembly']);self.assertNotIn('skins',doc);files+=1
                        g=raw['geometry'];vertices=pose(p,**ctx,asset_id=m['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=ids,action_slot=0,frame_index=last)['geometry']['vertices'] if mode=='pose' else g['vertices']
                        corners=0
                        for node in doc['nodes']:
                            if 'mesh' not in node:continue
                            o=node['extras']['source_object']
                            for prim in doc['meshes'][node['mesh']]['primitives']:
                                positions=values(doc,binary,prim['attributes']['POSITION']);expected=[]
                                for t in range(o['triangle_start'],o['triangle_start']+o['triangle_count']):
                                    if g['triangle_materials'][t]!=prim['material']:continue
                                    for c in (0,2,1):x,y,z=vertices[g['triangles'][t][c]];expected.append((x,-y,z))
                                self.assertEqual(len(positions),len(expected));corners+=len(positions)
                                for actual,want in zip(positions,expected):
                                    for a,b in zip(actual,want):self.assertAlmostEqual(a,b,delta=.0002)
                        self.assertEqual(corners,len(g['triangles'])*3)
                        matched=[t for t in g['textures'] if t['status']=='address_match'];self.assertEqual(len(doc.get('images',[])),len(matched))
                        for image,t in zip(doc.get('images',[]),matched):
                            v=doc['bufferViews'][image['bufferView']];self.assertEqual(decode_png(binary[v['byteOffset']:v['byteOffset']+v['byteLength']])['rgba'],base64.b64decode(t['rgba_base64']))
                        if mode!='clip':self.assertNotIn('animations',doc);continue
                        animation=doc['animations'][0];self.assertEqual(len(animation['channels']),len(g['objects'])*2)
                        for f in (0,last):
                            native=pose(p,**ctx,asset_id=m['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=ids,action_slot=0,frame_index=f)
                            for i,tr in enumerate(native['object_transforms']):
                                channels={c['target']['path']:animation['samplers'][c['sampler']] for c in animation['channels'] if c['target']['node']==i};ts=values(doc,binary,channels['translation']['output']);qs=values(doc,binary,channels['rotation']['output']);self.assertEqual(ts[f],(tr['translation'][0],-tr['translation'][1],tr['translation'][2]));self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2]);self.assertEqual(channels['rotation']['interpolation'],'STEP')
                                qx,qy,qz,qw=qs[f];o=g['objects'][i];v=g['vertices'][o['vertex_start']];x,y,z=v[0],-v[1],v[2];cross=[2*(qy*z-qz*y),2*(qz*x-qx*z),2*(qx*y-qy*x)];actual=[x+qw*cross[0]+qy*cross[2]-qz*cross[1],y+qw*cross[1]+qz*cross[0]-qx*cross[2],z+qw*cross[2]+qx*cross[1]-qy*cross[0]];target=native['geometry']['vertices'][o['vertex_start']]
                                for a,b in zip([actual[j]+ts[f][j] for j in range(3)],[target[0],-target[1],target[2]]):self.assertAlmostEqual(a,b,delta=.0002)
                for change in [dict(mode='foreign'),dict(action_slot=6),dict(fps=True),dict(fps=0),dict(frame_index=0),dict(expected_source_key='0'*64),dict(catalog_source_key='0'*64),dict(extra=True)]:self.assertEqual(post('/api/player-battle-export',dict(args,**change))[0],400)
            self.assertEqual(files,12);self.assertEqual((p._document(),p.undo_stack),held)
