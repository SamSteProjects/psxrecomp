"""Selected field clip tracks replay independently decoded native poses."""
import base64,json,os,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from importer.pipeline import import_scene
from importer.animation import load_animation_preview
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.field_equipment import preview,export_clip
from test_importer_export import parse_glb
from test_animation_clip_export import values

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class FieldEquipmentClipExportTests(unittest.TestCase):
    def test_all_selected_native_frames(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));before=deepcopy((p._document(),p.undo_stack));cases=[];frames=corners=0
            for slot in range(3):
                for byte in (0,1):
                    for clip in ('idle','walk'):
                        ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=f'asset://legaia/models/global-special/{0xf0+slot:04x}',equipment_byte=byte,clip_id=clip,frame_index=0)
                        held=preview(p,**ctx);result=export_clip(p,17.5,**ctx);doc,binary=parse_glb(base64.b64decode(result['glb_base64']));native=load_animation_preview(p.disc_path,p.assets.records[ctx['asset_id']],clip,equipment_byte=byte);g=native['geometry'];animation=doc['animations'][0];self.assertEqual(len(animation['channels']),20);self.assertNotIn('skins',doc);frames+=len(native['frames'])
                        for n,node in enumerate(doc['nodes']):
                            o=g['objects'][n];samplers=[animation['samplers'][c['sampler']] for c in animation['channels'] if c['target']['node']==n];self.assertEqual(len(samplers),2)
                            ts,qs=[values(doc,binary,s['output']) for s in samplers];times=values(doc,binary,samplers[0]['input']);self.assertEqual(len(times),len(native['frames'])+1);self.assertEqual(ts[-1],ts[-2]);self.assertEqual(qs[-1],qs[-2]);self.assertTrue(all(s['interpolation']=='STEP' for s in samplers))
                            for i,t in enumerate(times):self.assertAlmostEqual(t[0],i/17.5,delta=.00001)
                            for i,frame in enumerate(native['frames']):
                                x,y,z,w=qs[i]
                                for vi in range(o['vertex_start'],o['vertex_start']+o['vertex_count']):
                                    v=g['vertices'][vi];v=[v[0],-v[1],v[2]];cross=[2*(y*v[2]-z*v[1]),2*(z*v[0]-x*v[2]),2*(x*v[1]-y*v[0])];actual=[v[0]+w*cross[0]+y*cross[2]-z*cross[1]+ts[i][0],v[1]+w*cross[1]+z*cross[0]-x*cross[2]+ts[i][1],v[2]+w*cross[2]+x*cross[1]-y*cross[0]+ts[i][2]];expected=frame['vertices'][vi];expected=[expected[0],-expected[1],expected[2]]
                                    for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,delta=.0002)
                                    corners+=1
                        cases.append(dict(context=dict(projectPath=str(p.root),sourceKey=source_key(p),assetId=ctx['asset_id'],equipmentByte=byte,clipId=clip,frameIndex=0,exportFps=17.5),held=held,value=result))
            for fps in (True,0,121,float('nan'),float('inf'),'30'):
                with self.assertRaises(ProjectError):export_clip(p,fps,**ctx)
            self.assertEqual((p._document(),p.undo_stack),before)
            output=os.getenv('LEGAIA_FIELD_CLIP_CASES')
            if output:Path(output).write_text(json.dumps(dict(cases=cases,frames=frames,vertices=corners)),encoding='utf-8')
