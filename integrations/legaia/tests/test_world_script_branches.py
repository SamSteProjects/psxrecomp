from pathlib import Path
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import tempfile
from urllib.request import urlopen
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_script_branches import options,review,owner,COMPONENT
from sdk.worldmap_script_operands import review as argument_review,context
from test_world_script_animation_operands import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server
from importer.core import ImportError
from hashlib import sha256
from types import SimpleNamespace

def jump_fixture(project):
    script,source=fixture(project);man,rows,provenance,index,offset,slot,carrier=deepcopy(source)
    record=man[64:];record=record[:2]+b'\x26\x02\0'+record[2:];man=bytes(64)+record
    rows[script]['source_record'].update(sha256=sha256(record).hexdigest(),byte_length=len(record));provenance['source_man_sha256']=sha256(man).hexdigest()
    carrier=b''.join(bytes([(1<<len(man[i:i+8]))-1])+man[i:i+8] for i in range(0,len(man),8));slot['compressed_bytes_consumed']=len(carrier)
    return script,(man,rows,provenance,index,offset,slot,carrier)

class WorldBranchProjectTests(TestCase):
    def project(self,root):
        p=ProjectService(Path(root));d=synthetic_scene();d['source']['disc_identity']='sha256:'+'a'*64;p.import_metadata(d);return p

    def test_shared_review_apply_history_save_reset_and_argument_coauthors(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);script,source=jump_fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                a,_=argument_review(p,script,state_key(p),40,{'x':64,'z':16384},True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=40,values={'x':64,'z':16384},shared=True,review_key=a['review_key']))
                baseline=deepcopy(p._document());v=options(p,script,state_key(p));self.assertEqual(v['branch_options']['targets'][0]['pc'],2)
                with self.assertRaises(ProjectError):review(p,script,state_key(p),2,{'target_pc':2},False)
                r,_=review(p,script,state_key(p),2,{'target_pc':2},True)
                self.assertEqual(p._document(),baseline);self.assertIn(40,r['candidate_graph']['unreachable_source_pcs'])
                p.command(dict(type='set_world_script_branches',script_id=script,source_key=state_key(p),pc=2,values={'target_pc':2},shared=True,review_key=r['review_key']))
                current=context(p,'map02')[8];self.assertEqual(current[67:69],b'\xff\xff');self.assertEqual(current[106:108],b'\0\xff')
                from sdk.worldmap_script_operands import options as argument_options
                witness=argument_options(p,script,state_key(p));self.assertEqual(witness['schema_version'],'legaia.world-script-operands.v2')
                self.assertEqual(witness['branch_changes'][0]['authored_target_pc'],2);self.assertEqual(witness['branch_source_graph']['instructions'][0]['byte_offset'],66)
                from sdk.worldmap_script_operands import inspection
                graph=inspection(p,script,state_key(p));self.assertEqual(graph['schema_version'],'legaia.world-script-inspection.v2')
                dormant=next(n for n in graph['current_graph']['unvisited_instructions'] if n['pc']==40)
                self.assertEqual(dormant['byte_offset'],104);self.assertEqual(dormant['operands']['target_position'],{'x':64,'y':None,'z':16384})
                rows=p.authored_assets();self.assertEqual(len(rows),1);self.assertEqual(set(rows[0]['authored']),{'WorldScriptOperands',COMPONENT})
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document());p.undo();self.assertEqual(p._document(),baseline);p.redo()
                # Fixed arguments can still be reviewed against immutable source
                # anchors after the branch makes them dormant; branches survive.
                a,_=argument_review(p,script,state_key(p),40,{'x':128,'z':64},True)
                p.command(dict(type='set_world_script_animation_operands',script_id=script,source_key=state_key(p),pc=40,values={'x':128,'z':64},shared=True,review_key=a['review_key']))
                self.assertEqual(context(p,'map02')[8][67:69],b'\xff\xff');self.assertEqual(context(p,'map02')[8][106:108],b'\x80\0');p.undo()
                reset,_=review(p,script,state_key(p),2,{'target_pc':5},True)
                p.command(dict(type='set_world_script_branches',script_id=script,source_key=state_key(p),pc=2,values={'target_pc':5},shared=True,review_key=reset['review_key']))
                self.assertNotIn(owner('map02'),p.overrides)
                p.undo();p.undo();p.undo();self.assertEqual(p._document(),held)

    def test_http_review_source_staleness_and_exact_command(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);script,source=fixture(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_script_operands.source',return_value=source),http_server(p) as (server,post):
                key=state_key(p);status,v=post('/api/world-script-branches',dict(script_id=script,source_key=key));self.assertEqual(status,200)
                body=dict(script_id=script,source_key=key,pc=33,values={'target_pc':33},shared=True)
                status,r=post('/api/world-script-branch-review',body);self.assertEqual(status,200)
                for changed in (dict(body,pc=True),dict(body,values={'target_pc':34}),dict(body,source_key='stale'),dict(body,extra=True)):
                    self.assertEqual(post('/api/world-script-branch-review',changed)[0],400)
                command=dict(type='set_world_script_branches',**body,review_key=r['review_key'])
                self.assertEqual(post('/api/command',dict(command,extra=True))[0],400)
                self.assertEqual(post('/api/command',dict(command,review_key='forged'))[0],400)
                self.assertEqual(p._document(),held);self.assertEqual(post('/api/command',command)[0],200)
                self.assertEqual(post('/api/command',command)[0],400);p.undo();self.assertEqual(p._document(),held)
                p.mode='live'
                with self.assertRaises(ProjectError):options(p,script,state_key(p))

    def test_saved_retail_branch_target_keeps_argument_v1_witness(self):
        from sdk.worldmap_script_operands import options as argument_options
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);script,source=jump_fixture(p)
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                _,binding=review(p,script,state_key(p),2,{'target_pc':2},True)
                binding['entries'][script]['branches']['0002']['target_pc']=5
                p.overrides[owner('map02')]={COMPONENT:binding}
                held=deepcopy(p._document());v=argument_options(p,script,state_key(p))
                self.assertEqual(v['schema_version'],'legaia.world-script-animation-operands.v1')
                self.assertEqual(v['record_base64'],v['current_record_base64'])
                self.assertNotIn('branch_changes',v);self.assertEqual(p._document(),held)

    def test_dormant_message_global_offsets_and_identity_are_retained(self):
        from sdk.worldmap_script_operands import inspection
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);script,source=jump_fixture(p)
            _,rows,provenance,index,offset,slot,_=deepcopy(source)
            record=bytes.fromhex('00002602001f410026f9ff');man=bytes(64)+record
            rows[script]['source_record'].update(sha256=sha256(record).hexdigest(),byte_length=len(record));provenance['source_man_sha256']=sha256(man).hexdigest()
            carrier=b''.join(bytes([(1<<len(man[i:i+8]))-1])+man[i:i+8] for i in range(0,len(man),8));slot['compressed_bytes_consumed']=len(carrier)
            with patch('sdk.worldmap_script_operands.source',return_value=(man,rows,provenance,index,offset,slot,carrier)):
                r,_=review(p,script,state_key(p),2,{'target_pc':2},True)
                p.command(dict(type='set_world_script_branches',script_id=script,source_key=state_key(p),pc=2,values={'target_pc':2},shared=True,review_key=r['review_key']))
                held=deepcopy(p._document());g=inspection(p,script,state_key(p))['current_graph']
                self.assertEqual(g['unreachable_source_pcs'],[5,8]);message=g['unvisited_dialogues'][0]
                self.assertEqual(message['semantic_id'],script+'/dialogue/0005');self.assertEqual(message['byte_offset'],69)
                self.assertEqual(message['tokens'][0]['byte_offset'],70);self.assertEqual(p._document(),held)

    def test_branch_only_owner_is_not_omitted_from_world_build(self):
        from sdk.worldmap_script_operands import build
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);script,source=fixture(p)
            with patch('sdk.worldmap_script_operands.source',return_value=source):
                r,_=review(p,script,state_key(p),33,{'target_pc':33},True)
                p.command(dict(type='set_world_script_branches',script_id=script,source_key=state_key(p),pc=33,values={'target_pc':33},shared=True,review_key=r['review_key']))
                archive=SimpleNamespace(node=SimpleNamespace(extent_lba=0),entry=lambda index:SimpleNamespace(start_lba=0))
                with patch('sdk.texture_build.archive_overlay_patches',return_value=([{'offset':1,'payload':b'x','expected_sha256':'a'*64}],[{'map_entry_index':245}])),patch('importer.prot_layout.locate_physical_span',return_value={'entry_index':245,'offset_within_span':0}):
                    overlays,audit=build(p,archive)
                self.assertEqual(len(overlays),1);self.assertEqual(overlays[0]['scene'],'map02');self.assertEqual(overlays[0]['file'],'assets/map02-world-script-man.lzs')
                self.assertEqual({row['scope'] for row in audit},{'world-script-branch-target-only'})
