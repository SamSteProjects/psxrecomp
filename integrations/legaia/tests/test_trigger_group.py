"""Atomic native trigger group history, source byte ownership and normal Build."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import json, os, tempfile, unittest, zipfile
from sdk.project import ProjectService, ProjectError
from sdk.trigger_group import review, apply
from importer.trigger_authoring import trigger_authoring_options
from test_trigger_cells import fixture, TRIGGER, OTHER
from test_project_workflow import synthetic_scene

def command(report):
    return dict(type='apply_trigger_group',scene_id=report['scene_id'],trigger_ids=report['trigger_ids'],
                delta=report['delta'],action=report['action'],review_key=report['review_key'])

class TriggerGroupTests(unittest.TestCase):
    def test_atomic_translation_retains_unselected_and_undo_retail_reset(self):
        with tempfile.TemporaryDirectory() as raw:
            p=ProjectService(Path(raw));p.import_metadata(synthetic_scene());original=fixture();scene=p.active_scene
            untouched='trigger://fixture/field-map/primary/kind-0/0001'
            with patch.object(p,'_environment_source',return_value=original):
                p.command(dict(type='set_trigger_cells',entity_id=scene,value=dict(source_sha256=sha256(original).hexdigest(),edits=[dict(trigger_id=untouched,tile_x=9,tile_z=9)])))
                before=deepcopy(p._document());report=review(p,scene,[OTHER,TRIGGER],dict(x=2,z=-1))
                self.assertEqual(p._document(),before);self.assertEqual(report['changed_cell_count'],2)
                apply(p,command(report));self.assertEqual(len(p.undo_stack),2)
                self.assertIn(dict(trigger_id=untouched,tile_x=9,tile_z=9),p.overrides[scene]['TriggerCells']['edits'])
                authored=deepcopy(p.overrides);p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p.overrides,authored)
                with self.assertRaises(ProjectError):apply(p,command(report))
                reset=review(p,scene,[TRIGGER,OTHER],dict(x=0,z=0),'retail');apply(p,command(reset))
                self.assertEqual(p.overrides[scene]['TriggerCells']['edits'],[dict(trigger_id=untouched,tile_x=9,tile_z=9)])
                p.undo();self.assertEqual(p.overrides,authored)
                noop=review(p,scene,[TRIGGER,OTHER],dict(x=0,z=0));count=len(p.undo_stack);apply(p,command(noop));self.assertEqual(len(p.undo_stack),count)

    def test_bad_selection_bounds_and_late_source_reject_without_partial_history(self):
        with tempfile.TemporaryDirectory() as raw:
            p=ProjectService(Path(raw));p.import_metadata(synthetic_scene());original=fixture();scene=p.active_scene
            with patch.object(p,'_environment_source',return_value=original):
                before=deepcopy(p._document())
                for ids,delta,action in [([],dict(x=1,z=0),'translate'),([TRIGGER,TRIGGER],dict(x=1,z=0),'translate'),([TRIGGER]*129,dict(x=1,z=0),'translate'),([TRIGGER,OTHER],dict(x=-3,z=0),'translate'),([TRIGGER],dict(x=True,z=0),'translate'),([TRIGGER],dict(x=1,z=0),'retail'),([TRIGGER.replace('/primary/','/fallback/')],dict(x=1,z=0),'translate')]:
                    with self.assertRaises(ProjectError):review(p,scene,ids,delta,action)
                    self.assertEqual(p._document(),before)
                report=review(p,scene,[TRIGGER],dict(x=1,z=0))
                with patch.object(p,'_environment_source',return_value=original+b'\0'):
                    with self.assertRaises(ProjectError):apply(p,command(report))
                self.assertEqual(p._document(),before)

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
    def test_native_http_save_build_composes_script_binding_and_preserves_payloads(self):
        from importer.pipeline import import_scene
        from sdk.trigger_scripts import review as script_review, apply as script_apply
        from sdk.build import build_project
        from test_model_primitive_workflow import http_server
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='trigger-group-',dir=private) as raw:
            p=ProjectService(Path(raw));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'vell'),os.environ['LEGAIA_DISC_BIN']);scene=p.active_scene;original=p._environment_source(scene)
            rows=trigger_authoring_options(original,'vell')['records'];selected=[r for r in rows if r['encoded']['tile_x']<255 and r['encoded']['tile_z']<255][:2]
            self.assertEqual(len(selected),2);gate=next(r for r in rows if r['table_kind']==1 and r['encoded']['gate']==1)
            available=script_review(p,gate['trigger_id']);target=next(t for t in available['targets'] if t['script_id']!=available['layers']['imported']);binding=script_review(p,gate['trigger_id'],target['script_id']);script_apply(p,dict(type='apply_trigger_scripts',trigger_id=gate['trigger_id'],script_id=target['script_id'],action='set',review_key=binding['review_key']))
            retained=deepcopy(p.overrides[scene]['TriggerScripts']);before=deepcopy(p._document())
            with http_server(p) as (_,post):
                status,report=post('/api/trigger-group-review',dict(scene_id=scene,trigger_ids=[r['trigger_id'] for r in selected],delta=dict(x=1,z=1),action='translate'));self.assertEqual(status,200,report);self.assertEqual(p._document(),before)
                status,state=post('/api/trigger-group-apply',command(report));self.assertEqual(status,200,state);self.assertEqual(len(p.undo_stack),2)
                status,_=post('/api/trigger-group-apply',command(report));self.assertEqual(status,400)
            self.assertEqual(p.overrides[scene]['TriggerScripts'],retained)
            reopened=ProjectService.open(p.save());state=deepcopy(reopened._document());result=build_project(reopened);audit=json.loads(Path(result['audit']).read_text());overlay=audit['overlays'][0];payload=(Path(result['package_directory'])/overlay['file']).read_bytes()
            expected={r['byte_offset']+delta for r in selected for delta in (0,1)}|{gate['byte_offset']+2}
            self.assertEqual({i for i,(a,b) in enumerate(zip(original,payload)) if a!=b},expected)
            for row in rows:self.assertEqual(payload[row['byte_offset']+3],original[row['byte_offset']+3])
            with zipfile.ZipFile(result['path']) as packed:self.assertEqual(packed.read(overlay['file']),payload)
            self.assertEqual(reopened._document(),state)
