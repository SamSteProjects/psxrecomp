"""Group alignment/distribution resolve effective source-grid placements atomically."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import actor_placement_proposal_view
import test_actor_placement_batch as fixture
A,B=fixture.A,fixture.B
C='scene://fixture/actors/man-p1/0003'
D='scene://fixture/actors/man-p1/0004'

class ActorLayoutTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        original=fixture.ActorPlacementBatchTests().project(self.directory.name)
        document=deepcopy(original.imports[original.active_scene])
        for identifier,x in [(C,192),(D,576)]:
            actor=deepcopy(document['actors'][0]);actor['semantic_id']=identifier;actor['imported_transform']['position'].update(x=x,z=256);document['actors'].append(actor)
        self.p=ProjectService(Path(self.directory.name)/'layout');self.p.import_metadata(document);self.ids=[A,B,C,D]
    def command(self,layout):
        r=self.p.actor_placement_layout(self.ids,layout)
        return dict(type='layout_actor_placements',scene_id=r['scene_id'],actor_ids=self.ids,layout=layout,review_key=r['review_key'])
    def test_align_detached_one_history_preserves_layers_and_persistence(self):
        p=self.p;p.command(dict(type='set_transform',entity_id=A,position={'x':192,'y':-12}))
        p.overrides[A]['Dialogue']={'runs':{'script://fixture/actors/man-p1/0001/dialogue/0000/run/0000':'Test'}};p.save();before=deepcopy(p.overrides);source=deepcopy(p.imports);depth=len(p.undo_stack)
        layout={'kind':'align','axis':'x','anchor_entity_id':B};report=p.actor_placement_layout(self.ids,layout)
        self.assertEqual(report['changed_count'],3);self.assertEqual(p.overrides,before)
        view=actor_placement_proposal_view(p,report);self.assertEqual(view.overrides[A]['Transform']['position'],{'x':512,'y':-12});self.assertEqual(p.overrides,before)
        p.command(self.command(layout));self.assertEqual(len(p.undo_stack),depth+1);self.assertNotIn(B,p.overrides)
        self.assertEqual(p.overrides[A]['Dialogue'],before[A]['Dialogue']);self.assertEqual(p.imports,source)
        p.undo();self.assertEqual(p.overrides,before);self.assertFalse(p.dirty);p.redo();self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)
        depth=len(p.undo_stack);p.command(self.command(layout));self.assertEqual(len(p.undo_stack),depth)
    def test_distribution_balanced_endpoints_deterministic_ties(self):
        p=self.p;p.command(dict(type='set_transform',entity_id=B,position={'x':192}))
        r=p.actor_placement_layout(list(reversed(self.ids)),{'kind':'distribute','axis':'x'})
        values={row['entity_id']:row['proposed']['x'] for row in r['targets']};self.assertEqual(values,{A:128,B:256,C:448,D:576})
        for row in r['targets']:self.assertEqual(row['effective']['z'],row['proposed']['z']);self.assertEqual(row['effective']['y'],row['proposed']['y'])
        self.assertEqual(r,p.actor_placement_layout(self.ids,{'kind':'distribute','axis':'x'}))
        p.command(self.command({'kind':'distribute','axis':'x'}));self.assertNotIn(D,p.overrides);self.assertNotIn(A,p.overrides)
    def test_invalid_insufficient_spacing_stale_replay_and_live_reject(self):
        p=self.p
        for layout in [{}, {'kind':'align','axis':'y','anchor_entity_id':A},{'kind':'align','axis':'x','anchor_entity_id':'other'},{'kind':'distribute','axis':'x','anchor_entity_id':A},{'kind':'align','axis':'x'}]:
            with self.assertRaises(ProjectError):p.actor_placement_layout(self.ids,layout)
        with self.assertRaises(ProjectError):p.actor_placement_layout([A,C,D],{'kind':'distribute','axis':'z'})
        cmd=self.command({'kind':'align','axis':'x','anchor_entity_id':B});p.command(dict(type='set_transform',entity_id=D,position={'z':320}));before=deepcopy(p.overrides);history=deepcopy(p.undo_stack)
        with self.assertRaises(ProjectError):p.command(cmd)
        self.assertEqual(p.overrides,before);self.assertEqual(p.undo_stack,history)
        fresh=self.command(cmd['layout']);p.command(fresh);before=deepcopy(p.overrides)
        with self.assertRaises(ProjectError):p.command(fresh)
        self.assertEqual(p.overrides,before);p.mode='live'
        with self.assertRaises(ProjectError):p.command(self.command(cmd['layout']))
    def test_http_layout_review_and_strict_requests(self):
        import json,threading
        from urllib.error import HTTPError
        from urllib.request import Request,urlopen
        from sdk.server import EditorServer
        p=self.p;server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def post(route,body):
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
        try:
            body={'actor_ids':self.ids,'layout':{'kind':'align','axis':'x','anchor_entity_id':B}}
            report=post('/api/actor-placement-layout',body);self.assertEqual(report['changed_count'],3)
            for route,bad in [('/api/actor-placement-layout',{**body,'delta':{'x':64}}),('/api/actor-placement-layout-scene',{**body,'review_key':'stale'}),('/api/command',{**self.command(body['layout']),'bytes':'00'})]:
                with self.assertRaises(HTTPError) as error:post(route,bad)
                self.assertEqual(error.exception.code,400);error.exception.close();self.assertFalse(p.overrides)
            post('/api/command',self.command(body['layout']));self.assertEqual(len(p.undo_stack),1);post('/api/undo',{});self.assertFalse(p.overrides)
        finally:server.shutdown();server.server_close();thread.join(timeout=5)

if __name__=='__main__':unittest.main()
