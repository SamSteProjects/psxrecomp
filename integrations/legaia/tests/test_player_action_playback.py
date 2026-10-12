import base64,json,os,struct,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.core import decompress_lzs
from importer.player_battle import _sources
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources,preview,pose
from sdk.player_model_authoring import export,review,apply,current,current_pose
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerActionPlaybackTests(unittest.TestCase):
    def test_original_action_bytes_bound_to_both_geometry_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];report=resources(p,str(p.root),source_key(p));_,sources=_sources(p.disc_path);cases=[]
            with http_server(p) as (_,post):
                for m in report['catalog']['models']:
                    ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=m['semantic_id'],catalog_source_key=report['catalog']['source_key'],equipped=[0]*5)
                    e=export(p,**ctx);doc,binary=_read_glb(base64.b64decode(e['glb_base64']));doc['nodes'][0]['translation']=[10,0,0];encoded=base64.b64encode(_write_glb(doc,binary)).decode();r=review(p,**ctx,binding=e['binding'],glb_base64=encoded);apply(p,**ctx,binding=e['binding'],glb_base64=encoded,review_key=r['review_key']);ctx['expected_source_key']=source_key(p)
                    native=sources[m['player_index']][3];desc,_,_,budget=struct.unpack_from('<4I',native);bank,_=decompress_lzs(native[16:desc],budget)
                    for layer in ('retail','current'):
                        raw=current(p,**ctx) if layer=='current' else preview(p,**ctx)
                        args=dict(ctx,layer=layer,expected_current_sha256=raw['effective_file_sha256'] if layer=='current' else None,action_slot=0);held=deepcopy((p._document(),p.undo_stack));status,value=post('/api/player-battle-playback',args);self.assertEqual(status,200,value)
                        source=m['actions'][0]['source_record'];self.assertEqual(base64.b64decode(value['action_base64']),bank[source['byte_offset']:source['byte_offset']+source['byte_length']]);self.assertEqual(value['assembly'],raw['assembly'])
                        frames=[]
                        for frame in (0,m['actions'][0]['frame_count']-1):
                            frames.append(current_pose(p,**ctx,expected_current_sha256=raw['effective_file_sha256'],action_slot=0,frame_index=frame) if layer=='current' else pose(p,**ctx,action_slot=0,frame_index=frame))
                        cases.append(dict(report=dict(report,project_source_key=ctx['expected_source_key']),raw=raw,value=value,frames=frames))
                        for change in (dict(layer='foreign'),dict(expected_current_sha256='0'*64),dict(action_slot=True),dict(action_slot=6),dict(extra=True)):
                            self.assertEqual(post('/api/player-battle-playback',dict(args,**change))[0],400)
                        self.assertEqual((p._document(),p.undo_stack),held)
            out=os.getenv('LEGAIA_PLAYER_PLAYBACK_CASES')
            if out:Path(out).write_text(json.dumps(cases),encoding='utf-8')
