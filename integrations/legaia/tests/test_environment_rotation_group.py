"""Bounded quarter-turn scenery contracts and independent MAP byte readback."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.environment_authoring import patch_environment_overrides
from sdk.project import ProjectService, ProjectError
from sdk.environment_rotation_group import review, apply
from test_environment_group import SCENE, IDS, identity, source_map
from test_project_workflow import synthetic_scene


class EnvironmentRotationGroupTests(unittest.TestCase):
    def project(self, root):
        p=ProjectService(Path(root));p.import_metadata(synthetic_scene());return p

    def command(self, report):
        return dict(type='apply_environment_rotation_group',entity_id=SCENE,
                    entity_ids=report['entity_ids'],operation=report['operation'],review_key=report['review_key'])

    def test_inherited_yaw_pivot_direction_source_bytes_and_atomic_history(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map();h=sha256(source).hexdigest()
            binding=dict(source_sha256=h,edits=[dict(record_index=4,offset=dict(x=40,y=50,z=60),rotation_psx=dict(y=4000))],
                         instances=[dict(cell_index=129,offset=dict(x=70,y=80),rotation_psx=dict(y=777)),dict(cell_index=387,offset=dict(z=120))])
            with patch.object(ProjectService,'_environment_source',return_value=source):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                p.command(dict(type='set_collision_walls',entity_id=SCENE,value=dict(source_sha256=h,edits=[dict(row=1,column=0,quadrant=0,blocked=True)])))
                p.save();before=deepcopy(p.overrides);depth=len(p.undo_stack)
                r=review(p,SCENE,IDS[::-1],dict(anchor_id=IDS[0],quarter_turns=1))
                self.assertEqual(r['schema_version'],'legaia.environment-rotation-group-review.v1')
                self.assertEqual(r['scope'],'static-decoration-instance-layout-and-yaw-only')
                self.assertEqual(r['entity_ids'],IDS)
                self.assertEqual([t['current'] for t in r['targets']],[dict(x=262,z=132,yaw=777),dict(x=360,z=260,yaw=4000)])
                self.assertEqual([t['proposed'] for t in r['targets']],[dict(x=262,z=132,yaw=1801),dict(x=390,z=34,yaw=928)])
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
                apply(p,self.command(r));self.assertEqual(len(p.undo_stack),depth+1)
                value=p.overrides[SCENE]['Environment'];candidate,_=patch_environment_overrides(source,value)
                self.assertEqual(value['edits'],binding['edits']);self.assertEqual(value['instances'][-1],binding['instances'][-1])
                self.assertEqual(p.overrides[SCENE]['Collision'],before[SCENE]['Collision'])
                for cell,expected in [(129,(70,80,60,100,1801,300)),(258,(70,50,286,100,928,300))]:
                    word=struct.unpack_from('<H',candidate,0x8000+cell*2)[0];record=word&511
                    self.assertEqual(word&~511,0x2000)
                    self.assertEqual(struct.unpack_from('<3h',candidate,record*32),expected[:3])
                    self.assertEqual(struct.unpack_from('<3H',candidate,record*32+8),expected[3:])
                    self.assertEqual(candidate[record*32+14:record*32+32],source[4*32+14:5*32])
                self.assertEqual(candidate[0x4000:0x8000],source[0x4000:0x8000])
                p.undo();self.assertEqual(p.overrides,before);p.redo()
                self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)

    def test_all_quarter_turns_and_angle_normalization(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=bytearray(source_map());struct.pack_into('<H',source,4*32+10,65535)
            with patch.object(p,'_environment_source',return_value=bytes(source)):
                expected=[(330,290),(330,34),(74,34),(74,290)]
                for q,(x,z) in enumerate(expected):
                    r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=q))
                    self.assertEqual(r['targets'][1]['proposed'],dict(x=x,z=z,yaw=(4095+1024*q)&4095))
                    self.assertEqual(r['targets'][0]['proposed']['x'],202)
                    self.assertEqual(r['targets'][0]['proposed']['z'],162)

    def test_zero_turn_preserves_redundant_binding_and_history(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                b=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=258,rotation_psx=dict(y=200)),dict(cell_index=129,offset=dict(x=10))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=b));p.save();before=deepcopy(p.overrides);depth=len(p.undo_stack)
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[1],quarter_turns=0))
                self.assertFalse(r['project_change']);self.assertEqual(r['value'],b)
                apply(p,self.command(r));self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth);self.assertFalse(p.dirty)

    def test_invalid_selection_operation_and_exact_apply_contract(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root)
            with patch.object(p,'_environment_source',return_value=source_map()):
                for op in [None,{},dict(anchor_id=IDS[0],quarter_turns=True),dict(anchor_id=IDS[0],quarter_turns=-1),dict(anchor_id=IDS[0],quarter_turns=4),dict(anchor_id=IDS[0],quarter_turns=1.0),dict(anchor_id=identity(387),quarter_turns=1),dict(anchor_id=IDS[0],quarter_turns=1,extra=True)]:
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,op)
                for ids in [IDS[:1],IDS*2,[IDS[0],identity(0)],[IDS[0],IDS[1].replace('fixture','other')]]:
                    with self.assertRaises(ProjectError):review(p,SCENE,ids,dict(anchor_id=IDS[0],quarter_turns=1))
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=1));cmd=self.command(r)
                for changed in [{**cmd,'extra':True},{**cmd,'type':'other'},{**cmd,'operation':dict(anchor_id=IDS[0],quarter_turns=2)}]:
                    with self.assertRaises(ProjectError):apply(p,changed)
                self.assertEqual(p.undo_stack,[])

    def test_stale_project_source_and_unselected_change_reject(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                r=review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=1));p.name='Changed'
                with self.assertRaises(ProjectError):apply(p,self.command(r))
                r=review(p,SCENE,IDS,r['operation'])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=387,rotation_psx=dict(y=1000))])))
                with self.assertRaises(ProjectError):apply(p,self.command(r))
                p.undo();r=review(p,SCENE,IDS,r['operation'])
            changed=bytearray(source);changed[4*32+31]=1
            with patch.object(p,'_environment_source',return_value=bytes(changed)):
                with self.assertRaises(ProjectError):apply(p,self.command(r))
            self.assertEqual(p.undo_stack,[]);self.assertEqual(p.overrides,{})

    def test_capacity_and_signed_offset_failure_are_atomic(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);source=bytearray(source_map())
            for record in range(5,512):source[record*32+31]=1
            with patch.object(p,'_environment_source',return_value=bytes(source)):
                with self.assertRaisesRegex(ImportError,'No unused'):review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=1))
            source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=258,offset=dict(x=32767))])))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                with self.assertRaisesRegex(ProjectError,'signed'):review(p,SCENE,IDS,dict(anchor_id=IDS[0],quarter_turns=1))
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)

    def test_http_review_read_only_exact_fields_apply_and_stale_key(self):
        import json, threading
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        from sdk.server import EditorServer
        with tempfile.TemporaryDirectory() as root:
            p=self.project(root);saved=p.save();saved_bytes=saved.read_bytes();before=deepcopy(p._document())
            with patch.object(ProjectService,'_environment_source',return_value=source_map()):
                server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever);thread.start()
                try:
                    def post(route,body):
                        request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                        try:
                            with urlopen(request,timeout=10) as response:return response.status,json.load(response)
                        except HTTPError as error:
                            with error:return error.code,json.load(error)
                    body=dict(entity_id=SCENE,entity_ids=IDS,operation=dict(anchor_id=IDS[0],quarter_turns=1))
                    for bad in [{},{**body,'extra':True},{**body,'operation':dict(anchor_id=IDS[0],quarter_turns=True)}]:
                        self.assertEqual(post('/api/environment-rotation-group-review',bad)[0],400)
                    code,r=post('/api/environment-rotation-group-review',body);self.assertEqual(code,200,r)
                    self.assertEqual(p._document(),before);self.assertEqual(p.undo_stack,[])
                    self.assertEqual(post('/api/command',{**self.command(r),'extra':True})[0],400)
                    self.assertEqual(post('/api/command',self.command(r))[0],200);self.assertEqual(len(p.undo_stack),1)
                    after=deepcopy(p._document());self.assertEqual(post('/api/command',self.command(r))[0],400)
                    self.assertEqual(p._document(),after);self.assertEqual(saved.read_bytes(),saved_bytes)
                    self.assertEqual(post('/api/undo',{})[0],200);self.assertEqual(p._document(),before)
                    self.assertEqual(post('/api/redo',{})[0],200);self.assertEqual(p._document(),after)
                finally:
                    server.shutdown();server.server_close();thread.join(timeout=5)
                self.assertFalse(thread.is_alive())


if __name__=='__main__':unittest.main()
