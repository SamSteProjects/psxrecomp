"""Focused gate-1 target-byte ownership, reviewed history and actual private Build."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import json
import os
import tempfile
import unittest
import zipfile

from importer.core import ImportError
from importer.trigger_authoring import patch_field_triggers, trigger_authoring_options
from importer.trigger_script_authoring import patch_trigger_scripts
from sdk.build import BuildError, _merge_trigger_script_patch, build_project, package_change_kinds
from sdk.project import ProjectError, ProjectService
from sdk.trigger_scripts import review, apply, targets
from test_field_spatial import table
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server

ID='trigger://fixture/field-map/primary/kind-1/0000'
TARGET='script://fixture/scripts/man-p2/0002'

def source():
    return bytes(0x10000)+table({1:[(8,9,0,1),(1,2,4,0),(4,3,8,7)]})

def binding(data):
    return dict(source_sha256=sha256(data).hexdigest(),edits=[dict(trigger_id=ID,script_id=TARGET,script_sha256='a'*64)])

def command(report):
    return dict(type='apply_trigger_scripts',trigger_id=report['trigger_id'],script_id=report['requested_script_id'],action=report['action'],review_key=report['review_key'])

class TriggerScriptAuthoring(unittest.TestCase):
    def test_exact_index_byte_and_composition_reject_false_audits(self):
        data=source();value=binding(data);changed,audit=patch_trigger_scripts(data,value['source_sha256'],'fixture',value['edits'])
        offset=trigger_authoring_options(data,'fixture')['records'][0]['byte_offset']
        self.assertEqual([i for i,(a,b) in enumerate(zip(data,changed)) if a!=b],[offset+2])
        cells,_=patch_field_triggers(data,value['source_sha256'],'fixture',[dict(trigger_id=ID,tile_x=3,tile_z=9)])
        merged=_merge_trigger_script_patch(data,cells,changed,audit,'fixture',value)
        self.assertEqual(merged[offset:offset+4],bytes([3,9,2,1]))
        for bad in ([],audit+audit,[{**audit[0],'target_script_sha256':'b'*64}]):
            with self.assertRaises(BuildError):_merge_trigger_script_patch(data,data,changed,bad,'fixture',value)
        bad=bytearray(changed);bad[offset+3]=0
        with self.assertRaises(BuildError):_merge_trigger_script_patch(data,data,bytes(bad),audit,'fixture',value)
        with self.assertRaises(BuildError):_merge_trigger_script_patch(data,changed,changed,audit,'fixture',value)
        for edit in ({**value['edits'][0],'trigger_id':ID[:-1]+'1'}, {**value['edits'][0],'script_id':'script://other/scripts/man-p2/0002'}, {**value['edits'][0],'script_id':'script://fixture/scripts/man-p2/0256'}, {**value['edits'][0],'gate':1}):
            with self.assertRaises(ImportError):patch_trigger_scripts(data,value['source_sha256'],'fixture',[edit])

    def test_review_history_reset_and_late_target_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            p=ProjectService(Path(raw));p.import_metadata(synthetic_scene());original=deepcopy(p.imports)
            available={TARGET:dict(script_id=TARGET,source_sha256='a'*64,record_index=2)}
            with patch.object(p,'_environment_source',return_value=source()),patch('sdk.trigger_scripts.targets',return_value=available):
                report=review(p,ID,TARGET);self.assertEqual(p.overrides,{});self.assertTrue(report['project_change'])
                apply(p,command(report));self.assertEqual(len(p.undo_stack),1)
                with self.assertRaises(ProjectError):apply(p,command(report))
                p.undo();self.assertEqual(p.overrides,{});p.redo();p.save()
                with patch.object(ProjectService,'_environment_source',return_value=source()):
                    reopened=ProjectService.open(p.root)
                self.assertEqual(reopened.overrides,p.overrides)
                reset=review(p,ID,action='clear');apply(p,command(reset));self.assertEqual(p.overrides,{})
                fresh=review(p,ID,TARGET)
                with patch('sdk.trigger_scripts.targets',return_value={TARGET:dict(script_id=TARGET,source_sha256='b'*64,record_index=2)}):
                    with self.assertRaises(ProjectError):apply(p,command(fresh))
                self.assertEqual(p.overrides,{})
                for bad in ([],{},1,'script://fixture/actors/man-p1/0002'):
                    with self.assertRaises(ProjectError):review(p,ID,bad)
            self.assertEqual(p.imports,original)

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
    def test_retail_vell_http_save_build_and_exact_packed_map(self):
        from importer.pipeline import import_scene
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='trigger-script-build-',dir=private) as raw:
            p=ProjectService(Path(raw));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'vell'),os.environ['LEGAIA_DISC_BIN']);p.save()
            original=p._environment_source(p.active_scene);imports=deepcopy(p.imports)
            row=next(r for r in trigger_authoring_options(original,'vell')['records'] if r['table_kind']==1 and r['encoded']['gate']==1)
            target=next(r for r in targets(p,p.active_scene).values() if r['record_index']!=row['encoded']['record_index'])
            with http_server(p) as (_,post):
                status,report=post('/api/trigger-scripts-review',dict(trigger_id=row['trigger_id'],script_id=target['script_id'],action='set'))
                self.assertEqual(status,200,report);self.assertFalse(p.dirty);self.assertEqual(p.overrides,{})
                status,state=post('/api/trigger-scripts-apply',command(report));self.assertEqual(status,200,state)
                self.assertEqual(len(p.undo_stack),1)
                status,_=post('/api/trigger-scripts-apply',command(report));self.assertEqual(status,400)
            p.command(dict(type='set_trigger_cells',entity_id=p.active_scene,value=dict(source_sha256=sha256(original).hexdigest(),edits=[dict(trigger_id=row['trigger_id'],tile_x=(row['encoded']['tile_x']+1)%256,tile_z=row['encoded']['tile_z'])])))
            reopened=ProjectService.open(p.save());before=deepcopy(reopened._document());result=build_project(reopened)
            audit=json.loads(Path(result['audit']).read_text(encoding='utf-8'));overlay=audit['overlays'][0];payload=(Path(result['package_directory'])/overlay['file']).read_bytes();offset=row['byte_offset']
            self.assertEqual([i for i,(a,b) in enumerate(zip(original,payload)) if a!=b],[offset,offset+2])
            self.assertEqual(payload[offset+3],1);self.assertEqual(payload[offset+2],target['record_index']);self.assertEqual(len(audit['overlays']),1)
            self.assertIn('trigger script bindings',package_change_kinds(audit['edits']))
            with zipfile.ZipFile(result['path']) as packed:self.assertEqual(packed.read(overlay['file']),payload)
            self.assertEqual(reopened._document(),before);self.assertEqual(reopened.imports,imports)
