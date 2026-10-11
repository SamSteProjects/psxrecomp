from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import tempfile
from urllib.request import urlopen
from sdk.project import ProjectService,ProjectError
from importer.core import ImportError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_script_operands import options,review,compose,inspection,owner,COMPONENT,LEGACY_COMPONENT,validate,FLAGS,patch_world_movement
from test_project_workflow import synthetic_scene
from test_effect_color_authoring import END
from test_model_primitive_workflow import http_server


def fixture(project):
    record=b'\0\0\x4c\x81\1\2\3\4\5\6\7\x34\x0f\1\2\3\4\0\xcc\x07\x50\x1c\0\x31\xe2\x2b\x10\x31\x08\x32\x0a\x51\x02\x71\x02\x02\0\xa3\x07\x60\x19'+END
    man=bytes(64)+record;script='script://map02/worldmap/man-p0/0000'
    provenance=dict(source_disc_sha256=next(iter(project.imports.values()))['source']['disc_identity'].removeprefix('sha256:'),source_man_sha256=sha256(man).hexdigest())
    carrier=b''.join(bytes([(1<<len(man[i:i+8]))-1])+man[i:i+8] for i in range(0,len(man),8))
    slot=dict(compressed_stream_offset=0,compressed_bytes_consumed=len(carrier))
    rows={script:dict(source_record=dict(sha256=sha256(record).hexdigest(),byte_offset=64,byte_length=len(record)),entry_pc=2,source_scene='map02',source_instance_ids=['scene://map02/worldmap/placements/0001','scene://map02/worldmap/placements/0002','scene://map02/worldmap/placements/0003'])}
    return script,(man,rows,provenance,245,0,slot,carrier)


class WorldAnimationArgumentsTests(TestCase):
    def test_world_movement_does_not_expand_to_npc_run(self):
        with self.assertRaisesRegex(ImportError,'MOVE_TO'):
            patch_world_movement(b'\x4c\x51\x00\x80\xab\x09'+END,0,0,{'x':128,'z':64})
    def test_movement_grid_review_history_and_graph_composition(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                target=next(t for t in options(p,script,state_key(p))['targets'] if t['mnemonic']=='MOVE_TO')
                self.assertEqual(target['pc'],37);self.assertEqual(target['target_context'],7);self.assertEqual(target['retail_values'],{'x':12352,'z':3264})
                for values in ({'x':0,'z':64},{'x':65,'z':64},{'x':16448,'z':64},{'x':True,'z':64},{'x':64},{'x':64,'z':64,'move_id':1}):
                    with self.assertRaises((ProjectError,ImportError)):review(p,script,state_key(p),37,values,True)
                r,binding=review(p,script,state_key(p),37,{'x':64,'z':16384},True);candidate,audit=compose(source[0],source[1],binding)
                self.assertEqual(candidate,source[0][:103]+b'\0\xff'+source[0][105:]);self.assertEqual({a['scope'] for a in audit},{'world-script-movement-only'})
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=37,values={'x':64,'z':16384},shared=True,review_key=r['review_key']))
                snapshot=inspection(p,script,state_key(p));node=next(n for n in snapshot['current_graph']['instructions'] if n['pc']==37)
                self.assertEqual(node['operands']['target_position'],{'x':64,'y':None,'z':16384});self.assertEqual(node['target_context'],7)
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document());p.undo();self.assertEqual(p._document(),held);p.redo()
                reset,_=review(p,script,state_key(p),37,target['retail_values'],True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=37,values=target['retail_values'],shared=True,review_key=reset['review_key']))
                self.assertNotIn(owner('map02'),p.overrides)
    def test_current_graph_snapshot_is_read_only_and_source_bound(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p)
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                report,_=review(p,script,state_key(p),33,{'index':4095},True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=33,values={'index':4095},shared=True,review_key=report['review_key']))
                held=deepcopy(p._document());history=deepcopy(p.undo_stack);key=state_key(p)
                snapshot=inspection(p,script,key);self.assertEqual(snapshot['source']['source_key'],key)
                before=next(n for n in snapshot['retail_graph']['instructions'] if n['pc']==33);after=next(n for n in snapshot['current_graph']['instructions'] if n['pc']==33)
                self.assertEqual(before['operands']['index'],258);self.assertEqual(after['operands']['index'],4095)
                self.assertEqual(before['successors'],after['successors']);self.assertEqual(after['byte_offset'],97)
                self.assertEqual(snapshot['retail_graph']['opaque_regions'],snapshot['current_graph']['opaque_regions'])
                self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
                with self.assertRaises(ProjectError):inspection(p,script,'0'*64)
                p.mode='live'
                with self.assertRaises(ProjectError):inspection(p,script,key)
    def test_system_selectors_preserve_operation_and_test_delta(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                targets=[t for t in options(p,script,state_key(p))['targets'] if t['mnemonic'].startswith('SYSFLAG_')]
                self.assertEqual([(t['pc'],t['mnemonic']) for t in targets],[(31,'SYSFLAG_SET'),(33,'SYSFLAG_TEST')])
                for target in targets:
                    for index in (-1,4096,True):
                        with self.assertRaises((ProjectError,ImportError)):review(p,script,state_key(p),target['pc'],{'index':index},True)
                    report,_=review(p,script,state_key(p),target['pc'],{'index':4095},True)
                    p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=target['pc'],values={'index':4095},shared=True,review_key=report['review_key']))
                candidate,audit=compose(source[0],source[1],p.overrides[owner('map02')][COMPONENT])
                self.assertEqual(candidate,source[0][:95]+b'\x5f\xff\x7f\xff'+source[0][99:]);self.assertEqual(candidate[99:101],b'\2\0')
                self.assertEqual({c['scope'] for c in audit},{'world-script-system-flag-only'})
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();p.redo();self.assertEqual(next(t for t in options(p,script,state_key(p))['targets'] if t['pc']==33)['current_values'],{'index':4095})
                p.undo();p.undo();self.assertEqual(p._document(),held)

    def test_masked_flag_bits_and_unsupported_source_targets(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                v=options(p,script,state_key(p));flags=[t for t in v['targets'] if t['mnemonic'] in FLAGS]
                self.assertEqual(len(flags),1);target=flags[0];self.assertEqual(target['pc'],23)
                for bit in (-1,8,32,True):
                    with self.assertRaises((ProjectError,ImportError)):review(p,script,state_key(p),23,{'bit':bit},True)
                for pc in (25,27,29):
                    with self.assertRaises(ProjectError):review(p,script,state_key(p),pc,{'bit':3},True)
                r,binding=review(p,script,state_key(p),23,{'bit':3},True);candidate,audit=compose(source[0],source[1],binding)
                self.assertEqual(candidate,source[0][:88]+b'\xe3'+source[0][89:]);self.assertEqual(audit[0]['byte_length'],1)
                self.assertEqual(audit[0]['before_hex'],'e2');self.assertEqual(audit[0]['after_hex'],'e3')
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=23,values={'bit':3},shared=True,review_key=r['review_key']))
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();self.assertEqual(p._document(),held);p.redo()
                reset,_=review(p,script,state_key(p),23,{'bit':2},True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=23,values={'bit':2},shared=True,review_key=reset['review_key']))
                self.assertNotIn(owner('map02'),p.overrides)

    def test_model_selector_composes_with_animation_and_color(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                values=[dict(model_id=0x030201,animation_frame=0x0504,tween_frames=1),dict(red=255,green=0,blue=1,intensity=-32768),dict(model_selector_signed=-1),dict(bit=3),dict(index=4095)]
                targets=options(p,script,state_key(p))['targets'];self.assertEqual(targets[2]['target_context'],7)
                for target,wanted in zip(targets,values):
                    report,_=review(p,script,state_key(p),target['pc'],wanted,True)
                    p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=target['pc'],values=wanted,shared=True,review_key=report['review_key']))
                movement=next(t for t in targets if t['mnemonic']=='MOVE_TO');wanted={'x':128,'z':64}
                report,_=review(p,script,state_key(p),movement['pc'],wanted,True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=movement['pc'],values=wanted,shared=True,review_key=report['review_key']))
                binding=p.overrides[owner('map02')][COMPONENT];candidate,audit=compose(source[0],source[1],binding)
                self.assertEqual(candidate,source[0][:73]+b'\1\0'+source[0][75:77]+b'\xff\0\1\0\x80'+source[0][82:85]+b'\xff\xff'+source[0][87:88]+b'\xe3'+source[0][89:95]+b'\x5f\xff'+source[0][97:103]+b'\x80\0'+source[0][105:])
                self.assertEqual({c['scope'] for c in audit},{'world-script-animation-operands-only','world-script-effect-color-operands-only','world-script-model-selector-only','world-script-flag-bit-only','world-script-system-flag-only','world-script-movement-only'})
                with self.assertRaises(ProjectError):validate(p,owner('map02'),binding,LEGACY_COMPONENT)
                for bad in (True,-32769,32768):
                    with self.assertRaises((ProjectError,ImportError)):review(p,script,state_key(p),targets[2]['pc'],dict(model_selector_signed=bad),True)
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();p.redo();self.assertEqual(options(p,script,state_key(p))['targets'][2]['current_values'],values[2])
                for _ in range(6):p.undo()
                self.assertEqual(p._document(),held)

    def test_color_coauthor_legacy_migration_and_undo(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(document);script,source=fixture(p)
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                v=options(p,script,state_key(p));animation=v['targets'][0]
                _,legacy=review(p,script,state_key(p),animation['pc'],dict(animation['current_values'],tween_frames=1),True)
                p.overrides[owner('map02')]={LEGACY_COMPONENT:legacy};p.save()
                p=ProjectService.open(Path(root));held=deepcopy(p._document())
                color=next(t for t in options(p,script,state_key(p))['targets'] if t['mnemonic']=='EFFECT_COLOR_INTENSITY')
                values=dict(red=255,green=0,blue=1,intensity=-32768)
                for bad in (dict(values,red=True),dict(values,intensity=-32769),dict(values,intensity=32768)):
                    with self.assertRaises((ProjectError,ImportError)):review(p,script,state_key(p),color['pc'],bad,True)
                report,binding=review(p,script,state_key(p),color['pc'],values,True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=color['pc'],values=values,shared=True,review_key=report['review_key']))
                self.assertEqual(set(p.overrides[owner('map02')]),{COMPONENT})
                candidate,audit=compose(source[0],source[1],binding)
                self.assertEqual(candidate,source[0][:73]+b'\1\0'+source[0][75:77]+b'\xff\0\1\0\x80'+source[0][82:])
                self.assertEqual({c['scope'] for c in audit},{'world-script-animation-operands-only','world-script-effect-color-operands-only'})
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();self.assertEqual(p._document(),held);p.redo()
                current=options(p,script,state_key(p));self.assertEqual(current['targets'][1]['current_values'],values)
                reset,_=review(p,script,state_key(p),color['pc'],color['retail_values'],True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=color['pc'],values=color['retail_values'],shared=True,review_key=reset['review_key']))
                self.assertEqual(options(p,script,state_key(p))['targets'][0]['current_values']['tween_frames'],1)
                self.assertEqual(options(p,script,state_key(p))['targets'][1]['authored_values'],None)

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
                with urlopen(f'http://127.0.0.1:{server.server_port}/world-script-inspection.js') as response:self.assertIn(b'qualifyWorldScriptInspection',response.read())
                with urlopen(f'http://127.0.0.1:{server.server_port}/world-script-graph.js') as response:self.assertIn(b'qualifyWorldScriptGraph',response.read())
                with urlopen(f'http://127.0.0.1:{server.server_port}/world-script-branch-bytes.js') as response:self.assertIn(b'applyQualifiedWorldBranchBytes',response.read())
                for route in ('/api/world-script-animation-operands','/api/world-script-animation-review','/api/world-script-inspection'):
                    for body in ({},{'script_id':'foreign','source_key':'0'*64},{'script_id':'foreign','source_key':'0'*64,'extra':True}):self.assertEqual(post(route,body)[0],400)
            self.assertEqual(p._document(),held)
