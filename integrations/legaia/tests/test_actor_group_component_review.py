"""Group component removal validates inherited and authored members before mutation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from sdk.project import ProjectError, ProjectService
from sdk.server import EditorServer
from test_project_workflow import synthetic_scene

IDS = [f'scene://fixture/actors/man-p1/{i:04}' for i in range(1,4)]

class ActorGroupComponentReviewTests(unittest.TestCase):
    def project(self, root):
        doc=synthetic_scene()
        for identifier in IDS[1:]:
            actor=deepcopy(doc['actors'][0]);actor['semantic_id']=identifier;doc['actors'].append(actor)
        p=ProjectService(Path(root));p.import_metadata(doc)
        p.overrides[IDS[0]]={'Transform':{'position':{'x':125}},'ScriptModelSelectors':{'entries':{'script://fixture/actors/man-p1/0001/model-selector/0000':{'model_selector_signed':240}}}}
        p.overrides[IDS[1]]={'Transform':{'position':{'z':250}}}
        return p

    def command(self,p):
        report=p.actor_component_batch(IDS,'Transform')
        return dict(type='revert_actor_group_component',scene_id=p.active_scene,actor_ids=IDS.copy(),component='Transform',review_key=report['review_key'])

    def test_review_detached_atomic_history_persistence_and_source(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);p.save();before=deepcopy(p.overrides);source=deepcopy(p.imports)
            report=p.actor_component_batch(IDS,'Transform');self.assertEqual(report['affected_count'],2);self.assertFalse(report['targets'][2]['has_authored'])
            report['targets'][0]['authored'].clear();self.assertEqual(p.overrides,before)
            p.command(self.command(p));self.assertNotIn('Transform',p.overrides[IDS[0]]);self.assertNotIn(IDS[1],p.overrides);self.assertNotIn(IDS[2],p.overrides)
            self.assertEqual(p.overrides[IDS[0]]['ScriptModelSelectors'],before[IDS[0]]['ScriptModelSelectors']);self.assertEqual(len(p.undo_stack),1)
            p.undo();self.assertEqual(p.overrides,before);self.assertFalse(p.dirty);p.redo()
            self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides);self.assertEqual(p.imports,source)

    def test_stale_last_or_inherited_member_source_root_and_shape_reject_atomically(self):
        with tempfile.TemporaryDirectory() as root:
            for kind in ('last','inherited','source','root','extra','duplicate','unknown','live'):
                p=self.project(Path(root)/kind);cmd=self.command(p)
                if kind=='last':p.overrides[IDS[1]]['Transform']['position']['z']=251
                if kind=='inherited':p.overrides[IDS[2]]={'Transform':{'position':{'x':50}}}
                if kind=='source':p.imports[p.active_scene]['actors'][0]['imported_transform']['position']['x']=101
                if kind=='root':p.root=Path(root)/'other'
                if kind=='extra':cmd['bytes']='00'
                if kind=='duplicate':cmd['actor_ids']=[IDS[0],IDS[0]]
                if kind=='unknown':cmd['component']='Retail'
                if kind=='live':p.mode='live'
                before=deepcopy(p.overrides)
                with self.assertRaises(ProjectError):p.command(cmd)
                self.assertEqual(p.overrides,before);self.assertFalse(p.undo_stack)

    def test_unrelated_component_preserved_replay_rejected_and_empty_noop(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);cmd=self.command(p);p.overrides[IDS[0]]['ScriptModelSelectors']['entries']['script://fixture/actors/man-p1/0001/model-selector/0000']['model_selector_signed']=239
            p.command(cmd);before=deepcopy(p.overrides)
            with self.assertRaises(ProjectError):p.command(cmd)
            self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),1)
            p.command(self.command(p));self.assertEqual(len(p.undo_stack),1)
            self.assertEqual(p.overrides[IDS[0]]['ScriptModelSelectors']['entries']['script://fixture/actors/man-p1/0001/model-selector/0000']['model_selector_signed'],239)

    def test_http_preview_shapes_and_group_revert(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(route,body):
                with urlopen(Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
            try:
                before=deepcopy(p.overrides);report=post('/api/actor-component-batch',{'actor_ids':IDS,'component':'Transform'});self.assertEqual(report['affected_count'],2);self.assertEqual(p.overrides,before)
                for route,body in [('/api/actor-component-batch',{'actor_ids':IDS,'component':'Transform','path':'other'}),('/api/command',{**self.command(p),'review_key':None}),('/api/command',{**self.command(p),'component':[]})]:
                    with self.assertRaises(HTTPError) as error:post(route,body)
                    self.assertEqual(error.exception.code,400);error.exception.close()
                result=post('/api/command',self.command(p));self.assertTrue(result['history']['can_undo']);post('/api/undo',{});self.assertEqual(p.overrides,before)
            finally:server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

if __name__=='__main__':unittest.main()
