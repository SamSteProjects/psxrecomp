import base64,json,os,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from sdk import player_art_animation as arts
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from test_importer_export import parse_glb
from test_animation_clip_export import values
from importer.texture_png import decode_png

@unittest.skipUnless(os.getenv('PLAYER_ART_EXPORT_FIXTURES'),'Private qualified art fixtures required')
class PlayerArtExportTests(unittest.TestCase):
    def test_all_layers_archives_pose_clip_vectors_pixels_and_tracks(self):
        cases=json.loads(Path(os.environ['PLAYER_ART_EXPORT_FIXTURES']).read_text(encoding='utf-8'))['cases']
        files=0
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.getenv('LEGAIA_DISC_BIN','private-fixture.bin');p.save();context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            for c in cases:
                receipt=c['playback'];g=receipt['base_inspection']['geometry'];last=c['poses'][-1]['frame_index']
                with patch.object(arts,'playback',return_value=deepcopy(receipt)):
                    for mode in ('pose','clip'):
                        result=arts.export(p,mode,last if mode=='pose' else None,None if mode=='pose' else 23.5,**context)
                        doc,binary=parse_glb(base64.b64decode(result['glb_base64']));files+=1
                        self.assertEqual(doc['extras']['source_record']['stream'],receipt['stream']['source_record']);self.assertNotIn('skins',doc)
                        vertices=c['poses'][-1]['geometry']['vertices'] if mode=='pose' else g['vertices'];corners=0
                        for node in doc['nodes']:
                            if 'mesh' not in node:continue
                            o=node['extras']['source_object']
                            for prim in doc['meshes'][node['mesh']]['primitives']:
                                positions=values(doc,binary,prim['attributes']['POSITION']);expected=[]
                                for t in range(o['triangle_start'],o['triangle_start']+o['triangle_count']):
                                    if g['triangle_materials'][t]!=prim['material']:continue
                                    for k in (0,2,1):x,y,z=vertices[g['triangles'][t][k]];expected.append((x,-y,z))
                                self.assertEqual(len(positions),len(expected));corners+=len(positions)
                                for actual,want in zip(positions,expected):
                                    for a,b in zip(actual,want):self.assertAlmostEqual(a,b,delta=.0003)
                        self.assertEqual(corners,len(g['triangles'])*3)
                        matched=[t for t in g['textures'] if t['status']=='address_match'];self.assertEqual(len(doc.get('images',[])),len(matched))
                        for image,t in zip(doc.get('images',[]),matched):
                            v=doc['bufferViews'][image['bufferView']];self.assertEqual(decode_png(binary[v['byteOffset']:v['byteOffset']+v['byteLength']])['rgba'],base64.b64decode(t['rgba_base64']))
                        if mode=='pose':self.assertNotIn('animations',doc);continue
                        animation=doc['animations'][0];self.assertEqual(len(animation['channels']),len(g['objects'])*2)
                        for pose in c['poses']:
                            f=pose['frame_index']
                            for i,tr in enumerate(pose['object_transforms']):
                                channels={v['target']['path']:animation['samplers'][v['sampler']] for v in animation['channels'] if v['target']['node']==i};ts=values(doc,binary,channels['translation']['output']);qs=values(doc,binary,channels['rotation']['output']);times=values(doc,binary,channels['translation']['input'])
                                self.assertEqual(len(ts),receipt['stream']['frame_count']+1);self.assertAlmostEqual(times[f][0],f/23.5,delta=.00001);self.assertEqual(ts[f],(tr['translation'][0],-tr['translation'][1],tr['translation'][2]));self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2]);self.assertEqual(channels['rotation']['interpolation'],'STEP')
                                qx,qy,qz,qw=qs[f];o=g['objects'][i]
                                for j in range(o['vertex_start'],o['vertex_start']+o['vertex_count']):
                                    v=g['vertices'][j];x,y,z=v[0],-v[1],v[2];cross=[2*(qy*z-qz*y),2*(qz*x-qx*z),2*(qx*y-qy*x)];actual=[x+qw*cross[0]+qy*cross[2]-qz*cross[1],y+qw*cross[1]+qz*cross[0]-qx*cross[2],z+qw*cross[2]+qx*cross[1]-qy*cross[0]];target=pose['geometry']['vertices'][j]
                                    for a,b in zip([actual[k]+ts[f][k] for k in range(3)],[target[0],-target[1],target[2]]):self.assertAlmostEqual(a,b,delta=.001)
                    for mode,frame,fps in [('foreign',None,None),('pose',True,None),('pose',0,12),('pose',last+1,None),('clip',0,12),('clip',None,True),('clip',None,float('nan')),('clip',None,0),('clip',None,121)]:
                        with self.assertRaises(ProjectError):arts.export(p,mode,frame,fps,**context)
            self.assertEqual(files,32);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private retail disc required')
class PlayerArtExportHTTPTests(unittest.TestCase):
    def test_fresh_retail_current_and_exact_route_guards(self):
        from sdk.player_battle import resources as models
        from sdk.player_model_authoring import current
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
            m=models(p,**ctx);catalog=arts.resources(p,**ctx)['catalog'];model=m['catalog']['models'][0];ctx.update(asset_id=model['semantic_id'],catalog_source_key=m['catalog']['source_key'],equipped=[0]*5)
            saved=current(p,**ctx);held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with http_server(p) as (_,post):
                for role in ('main','base'):
                    stream=next(v for v in catalog['streams'] if v['player_index']==0 and v['archive_role']==role)
                    for layer in ('retail','current'):
                        args=dict(ctx,art_source_key=catalog['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer=layer,expected_current_sha256=saved['effective_file_sha256'] if layer=='current' else None,mode='clip',frame_index=None,fps=23.5)
                        status,result=post('/api/player-art-export',args);self.assertEqual(status,200,result);doc,_=parse_glb(base64.b64decode(result['glb_base64']));self.assertEqual(doc['extras']['frame_count'],stream['frame_count']);self.assertEqual(result['playback']['stream'],stream)
                for change in [dict(extra=True),dict(fps=True),dict(frame_index=0),dict(mode='foreign'),dict(expected_current_sha256='stale'),dict(art_source_key='stale')]:
                    self.assertEqual(post('/api/player-art-export',dict(args,**change))[0],400)
                status,result=post('/api/player-art-export',dict(args,mode='pose',frame_index=0,fps=None));self.assertEqual(status,200,result);self.assertTrue(result['audit']['posed'])
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)

if __name__=='__main__':unittest.main()
