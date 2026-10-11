"""World channel HTTP envelopes match the bounded native authoring capacity."""
from copy import deepcopy
from hashlib import sha256
import json
from http.client import HTTPConnection
from pathlib import Path
import struct
import tempfile
from unittest import TestCase
from unittest.mock import patch
from importer.worldmap_animation_authoring import patch_world_animation_bank
from sdk.project import ProjectService
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldAnimationHttpBudgetTests(TestCase):
    def setUp(self):
        record=struct.pack('<4H',8,512,0x080c,2)+bytes([0,0,0,0,0xa0,0,0,0])*4096+bytes(8)
        self.bank=struct.pack('<2I',1,8)+record
        self.rows=[dict(frame_index=f,object_index=o,translation=dict(x=32,y=-32,z=16),rotation_psx=dict(x=16,y=32,z=48)) for f in range(512) for o in range(8)]
        self.body=dict(scene='map01',source_key='0'*64,entity_id='source-entity',frame_index=0,edits=self.rows,shared_record=True)
        self.assertGreater(len(json.dumps(self.body).encode()),32768)
        self.assertLess(len(json.dumps(self.body).encode()),1024*1024)

    def test_complete_native_capacity_reaches_review(self):
        calls=[]
        def review(project,scene,key,entity,frame,edits,shared):
            self.assertEqual((scene,key,entity,frame,shared),('map01','0'*64,'source-entity',0,True))
            proposed,audit=patch_world_animation_bank(self.bank,sha256(self.bank).hexdigest(),0,sha256(self.bank[8:]).hexdigest(),edits)
            # Independently packed XYZ and rotations, including every opaque nibble.
            self.assertEqual(proposed,self.bank[:16]+bytes([32,224,0xf0,16,0xa0,1,2,3])*4096+bytes(8))
            calls.append(len(edits));return dict(changed_bytes=len(audit['changed_bytes']),rows=len(edits))
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());held=deepcopy((p._document(),p.undo_stack))
            with patch('sdk.worldmap_animation_edit.review',side_effect=review),http_server(p) as (_,post):
                status,result=post('/api/worldmap-animation-edit-review',self.body)
                self.assertEqual(status,200);self.assertEqual(result['rows'],4096)
            self.assertEqual(calls,[4096]);self.assertEqual((p._document(),p.undo_stack),held)

    def test_dedicated_apply_keeps_exact_typed_command(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene())
            body=dict(self.body,review_key='1'*64)
            with http_server(p) as (server,post),patch.object(p,'command') as command,patch.object(server,'state',return_value=dict(project={'fixture':True},scene=None)):
                self.assertEqual(post('/api/worldmap-animation-edit-apply',body)[0],200)
                command.assert_called_once_with(dict(type='set_world_animation_channels',**body))
                command.reset_mock()
                for invalid in [self.body,dict(body,extra=True),dict(body,type='foreign')]:
                    self.assertEqual(post('/api/worldmap-animation-edit-apply',invalid)[0],400)
                command.assert_not_called()

    def test_route_limits_and_generic_command_limit_remain_bounded(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());held=deepcopy(p._document())
            with http_server(p) as (server,post),patch.object(p,'command') as command,patch('sdk.worldmap_animation_edit.review') as review:
                for route,limit in [('/api/worldmap-animation-edit-review',1024*1024),('/api/worldmap-animation-edit-apply',1024*1024),('/api/command',32768)]:
                    connection=HTTPConnection(*server.server_address,timeout=10)
                    try:
                        connection.request('POST',route,headers={'Content-Type':'application/json','Content-Length':str(limit+1)})
                        response=connection.getresponse();self.assertEqual(response.status,400);self.assertIn('error',json.loads(response.read()))
                    finally:connection.close()
                command.assert_not_called();review.assert_not_called()
            self.assertEqual(p._document(),held)
