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
