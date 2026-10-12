import base64, json, os, tempfile, unittest
from copy import deepcopy
from pathlib import Path
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.player_battle import resources, pose as retail_pose
from sdk.player_model_authoring import export, review, apply, current, current_export
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc is private')
class PlayerCurrentActionsTests(unittest.TestCase):
    def test_export_rejects_invalid_mode_and_rate_before_source_work(self):
        valid=dict(expected_current_sha256='0'*64,mode='clip',action_slot=0,frame_index=None,fps=30)
        for change in (dict(mode='foreign'),dict(fps=True),dict(fps=0),dict(fps=121),dict(fps=float('nan')),dict(frame_index=0),dict(mode='object-local'),dict(mode='pose',fps=30)):
            with self.assertRaises(ProjectError):current_export(None,**dict(valid,**change))

    def test_current_poses_and_all_export_modes_use_authored_vertices(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN']
            report=resources(p,str(p.root),source_key(p));cases=[];corners=0
            with http_server(p) as (_,post):
                for record in report['catalog']['models']:
                    ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=record['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=[0]*5)
                    exported=export(p,**ctx);doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));doc['nodes'][0]['translation']=[10,0,0];payload=base64.b64encode(_write_glb(doc,binary)).decode();r=review(p,**ctx,binding=exported['binding'],glb_base64=payload);apply(p,**ctx,binding=exported['binding'],glb_base64=payload,review_key=r['review_key'])
                    ctx['expected_source_key']=source_key(p);raw=current(p,**ctx);before=deepcopy((p._document(),p.undo_stack));expected_current_sha256=raw['effective_file_sha256'];args=dict(ctx,expected_current_sha256=expected_current_sha256,action_slot=0,frame_index=record['actions'][0]['frame_count']-1)
                    status,posed=post('/api/player-model-current-pose',args);self.assertEqual(status,200,posed)
                    retail=retail_pose(p,**ctx,action_slot=args['action_slot'],frame_index=args['frame_index']);self.assertEqual(posed['object_transforms'],retail['object_transforms']);self.assertNotEqual(posed['geometry']['vertices'],retail['geometry']['vertices'])
                    exports=[]
                    for mode in ('object-local','pose','clip'):
                        selection=dict(mode=mode,action_slot=None if mode=='object-local' else 0,frame_index=args['frame_index'] if mode=='pose' else None,fps=23.5 if mode=='clip' else None)
                        status,result=post('/api/player-model-current-export',dict(ctx,expected_current_sha256=expected_current_sha256,**selection));self.assertEqual(status,200,result);exports.append(dict(selection=selection,result=result))
                        glb,buf=parse_glb(base64.b64decode(result['glb_base64']));g=raw['geometry'];verts=posed['geometry']['vertices'] if mode=='pose' else g['vertices'];self.assertEqual(glb['extras']['source_record']['current_sha256'],expected_current_sha256)
                        for node in glb['nodes']:
                            if 'mesh' not in node:continue
                            obj=node['extras']['source_object']
                            for primitive in glb['meshes'][node['mesh']]['primitives']:
                                expected=[]
                                for t in range(obj['triangle_start'],obj['triangle_start']+obj['triangle_count']):
                                    if g['triangle_materials'][t]!=primitive['material']:continue
                                    for c in (0,2,1):x,y,z=verts[g['triangles'][t][c]];expected.append((x,-y,z))
                                actual=values(glb,buf,primitive['attributes']['POSITION']);self.assertEqual(len(actual),len(expected));corners+=len(actual)
                                for a,b in zip(actual,expected):
                                    for v,w in zip(a,b):self.assertAlmostEqual(v,w,delta=.0002)
                        if mode=='clip':
                            tracks=glb['animations'][0];self.assertEqual(len(tracks['channels']),len(g['objects'])*2)
                            for i,tr in enumerate(posed['object_transforms']):
                                channel=next(c for c in tracks['channels'] if c['target']==dict(node=i,path='translation'));sampler=tracks['samplers'][channel['sampler']];samples=values(glb,buf,sampler['output']);self.assertEqual(samples[-2],(tr['translation'][0],-tr['translation'][1],tr['translation'][2]));self.assertEqual(samples[-1],samples[-2])
                    for mutation in (dict(expected_current_sha256='0'*64),dict(frame_index=True),dict(action_slot=6),dict(extra=True)):
                        self.assertEqual(post('/api/player-model-current-pose',dict(args,**mutation))[0],400)
                    self.assertEqual((p._document(),p.undo_stack),before)
                    cases.append(dict(raw=raw,posed=posed,exports=exports))
            evidence=os.getenv('LEGAIA_PLAYER_CURRENT_CASES')
            if evidence:Path(evidence).write_text(json.dumps(dict(report=report,cases=cases,corners=corners)),encoding='utf-8')
