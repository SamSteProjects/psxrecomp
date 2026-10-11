from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import tempfile
from urllib.request import urlopen
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_script_operands import options,review,compose,owner,COMPONENT
from test_project_workflow import synthetic_scene
from test_effect_color_authoring import END
from test_model_primitive_workflow import http_server


def fixture(project):
    record=b'\0\0\x4c\x81\1\2\3\4\5\6\7'+END
    man=bytes(64)+record;script='script://map02/worldmap/man-p0/0000'
    provenance=dict(source_disc_sha256=next(iter(project.imports.values()))['source']['disc_identity'].removeprefix('sha256:'),source_man_sha256=sha256(man).hexdigest())
    carrier=b''.join(bytes([(1<<len(man[i:i+8]))-1])+man[i:i+8] for i in range(0,len(man),8))
    slot=dict(compressed_stream_offset=0,compressed_bytes_consumed=len(carrier))
    rows={script:dict(source_record=dict(sha256=sha256(record).hexdigest(),byte_offset=64,byte_length=len(record)),entry_pc=2,source_scene='map02',source_instance_ids=['scene://map02/worldmap/placements/0001','scene://map02/worldmap/placements/0002','scene://map02/worldmap/placements/0003'])}
    return script,(man,rows,provenance,245,0,slot,carrier)


class WorldAnimationArgumentsTests(TestCase):
    def test_source_composition_shared_review_history_and_persistence(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p);held=deepcopy(p._document());history=deepcopy(p.undo_stack);key=state_key(p)
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                v=options(p,script,key);t=v['targets'][0];values=dict(t['current_values'],tween_frames=1)
                with self.assertRaises(ProjectError):review(p,script,key,t['pc'],values,False)
                r,binding=review(p,script,key,t['pc'],values,True);self.assertEqual(p._document(),held)
                bad=deepcopy(binding);bad['entries'][script]['shared_record']=False
                with self.assertRaises(ProjectError):compose(source[0],source[1],bad)
                bad=deepcopy(binding);bad['entries'][script]['source_record_sha256']='0'*64
                with self.assertRaises(ProjectError):compose(source[0],source[1],bad)
                result,audit=compose(source[0],source[1],binding)
                # Only the literal operand bytes change; all three source owners remain explicit.
                self.assertEqual(result,source[0][:73]+b'\1\0'+source[0][75:]);self.assertEqual(len(audit),1)
                command=dict(type='set_world_script_animation_operands',script_id=script,source_key=key,pc=t['pc'],values=values,shared=True,review_key=r['review_key'])
                with self.assertRaises(ProjectError):p.command(dict(command,review_key='0'*64))
                self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
                p.command(command);self.assertEqual(options(p,script,state_key(p))['targets'][0]['current_values'],values)
                self.assertEqual(p.authored_assets()[0]['script_id'],script)
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertIn(COMPONENT,p.overrides[owner('map02')])
                revert,_=review(p,script,state_key(p),t['pc'],t['retail_values'],True)
                p.command(dict(command,source_key=state_key(p),values=t['retail_values'],review_key=revert['review_key']))
                self.assertNotIn(owner('map02'),p.overrides)

    def test_http_exact_scope_and_module(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));held=deepcopy(p._document())
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_port}/world-script-animation-operands.js') as response:self.assertIn(b'qualifyWorldScriptOperands',response.read())
                for route in ('/api/world-script-animation-operands','/api/world-script-animation-review'):
                    for body in ({},{'script_id':'foreign','source_key':'0'*64},{'script_id':'foreign','source_key':'0'*64,'extra':True}):self.assertEqual(post(route,body)[0],400)
            self.assertEqual(p._document(),held)
