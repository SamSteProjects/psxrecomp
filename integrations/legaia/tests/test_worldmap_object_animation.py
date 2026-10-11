from copy import deepcopy
import struct
from unittest import TestCase
from pathlib import Path
import tempfile
from urllib.request import urlopen
from importer.core import ImportError
from importer.worldmap_object_animation import resolve_object_animation


def fixture():
    record=struct.pack('<4H',1,2,0x080c,2)+bytes([1,0,0,0,0,0,0,0])+bytes([3,0,0,0,0,0,0,0])+bytes(8)
    bank=struct.pack('<2I',1,8)+record
    geometry=dict(vertices=[[10,20,30]],objects=[dict(object_index=0,vertex_start=0,vertex_count=1)])
    bind=dict(status='resolved_source_header',encoded_animation_selector=1)
    return bind,bank,geometry


class WorldObjectAnimationTests(TestCase):
    def test_editor_module_route_and_exact_frame_request(self):
        from sdk.project import ProjectService
        from test_project_workflow import synthetic_scene
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());held=deepcopy(p._document())
            with http_server(p) as (server,post):
                with urlopen(f'http://127.0.0.1:{server.server_address[1]}/worldmap-object-animation.js') as response:
                    self.assertIn(b'qualifyWorldObjectAnimation',response.read())
                body=dict(scene='map01',source_key='0'*64,entity_id='foreign',frame_index=True)
                for invalid in ({},{**body,'extra':True},body):
                    self.assertEqual(post('/api/worldmap-object-animation',invalid)[0],400)
            self.assertEqual(p._document(),held)

    def test_rotated_normals_preserve_record_span_and_translation_independence(self):
        bind,bank,geometry=fixture();data=bytearray(bank);data[8+8+8+6]=64
        geometry.update(vertices=[[10,20,30],[0,0,0],[1,1,1]],triangles=[[0,1,2]],
            triangle_normals=[[[1,0,0]]*3],normal_preview=dict(status='source_unposed',coordinate_system='retail_tmd_object_local'))
        geometry['objects'][0].update(vertex_count=3,triangle_start=0,triangle_count=1)
        held=deepcopy(geometry);r=resolve_object_animation(bind,bytes(data),geometry,1)
        self.assertEqual(r['byte_offset'],8);self.assertEqual(r['byte_length'],32)
        self.assertEqual(r['normal_pose'],'rigid_rotation_only')
        vector=r['geometry']['triangle_normals'][0][0]
        self.assertAlmostEqual(vector[0],0);self.assertAlmostEqual(vector[1],0);self.assertAlmostEqual(vector[2],-1)
        self.assertEqual(geometry,held)

    def test_two_frames_native_selector_and_immutable_model(self):
        bind,bank,geometry=fixture();held=deepcopy(geometry)
        for frame,x in ((0,11),(1,13)):
            result=resolve_object_animation(bind,bank,geometry,frame)
            self.assertEqual(result['geometry']['vertices'],[[x,20,30]])
            self.assertEqual(result['record_index'],0)
            self.assertEqual(result['frame_count'],2)
            self.assertEqual(result['runtime_state'],'not_observed')
            self.assertEqual(result['normal_pose'],'unavailable')
        self.assertEqual(geometry,held)

    def test_absent_zero_out_of_bank_and_incompatible_model_refuse(self):
        bind,bank,geometry=fixture()
        for selector in (None,0,2,True,256):
            with self.subTest(selector=selector),self.assertRaises(ImportError):
                resolve_object_animation({**bind,'encoded_animation_selector':selector},bank,geometry,0)
        with self.assertRaises(ImportError):resolve_object_animation({**bind,'status':'no_source_bind'},bank,geometry,0)
        with self.assertRaises(ImportError):resolve_object_animation(bind,bank,{**geometry,'objects':[]},0)
        for frame in (-1,2,512,True,0.5):
            with self.subTest(frame=frame),self.assertRaises(ImportError):resolve_object_animation(bind,bank,geometry,frame)
