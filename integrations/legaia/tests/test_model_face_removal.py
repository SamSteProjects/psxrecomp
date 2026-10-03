from hashlib import sha256
import struct
import unittest
from importer.core import ImportError
from importer.assets import decode_tmd
from importer.model_primitives import patch_model_primitives, inspect_model_primitives
from importer.model_face_removal import remove_faces, qualify_face_removal
from importer.model_authoring import preview_model_shape
from importer.animation import pose_vertices
from copy import deepcopy
from test_model_primitives import synthetic

class ModelFaceRemovalTests(unittest.TestCase):
    def test_posed_prefix_and_frame_geometry_retain_vertex_channels(self):
        original=synthetic(((0x22,),(0x14,)),count=2)
        candidate,_=remove_faces(original,original,[],[dict(object_index=0,primitive_index=0)])
        preview=decode_tmd(original);preview['objects']=preview['objects'][:1]
        count=preview['objects'][0]['vertex_count'];triangles=preview['objects'][0]['triangle_count']
        preview['vertices']=preview['vertices'][:count]
        for field in ['triangles','triangle_colors','triangle_uvs','triangle_materials','triangle_normals']:preview[field]=preview[field][:triangles]
        transforms=[dict(object_index=0,translation=[3,4,5],rotation_psx=[0,0,1024])]
        raw=deepcopy(preview['vertices']);preview.update(posed=True,pose={'object_transforms':transforms},frames=[dict(object_transforms=transforms,vertices=pose_vertices(raw,preview['objects'],transforms))])
        preview['vertices']=pose_vertices(raw,preview['objects'],transforms)
        baseline=deepcopy(preview)
        result=preview_model_shape(preview,candidate,{'format':'tmd-face-removal-v1'})
        self.assertEqual(preview,baseline);self.assertEqual(result['vertices'],preview['vertices'])
        self.assertEqual(result['frames'][0]['vertices'],preview['frames'][0]['vertices'])
        self.assertEqual(len(result['triangles']),2);self.assertEqual(result['objects'][0]['triangle_count'],2)

    def test_all_families_counts_vectors_and_cumulative_identity(self):
        for flags in range(0x10,0x28):
            with self.subTest(flags=flags):
                original=synthetic(((flags,flags),(flags,)),count=3)
                current=patch_model_primitives(original,sha256(original).hexdigest(),[dict(object_index=0,primitive_index=1,vertices=[4]*(4 if flags&2 else 3))])[0]
                candidate,removed=remove_faces(original,current,[],[dict(object_index=0,primitive_index=0)])
                self.assertEqual(removed,[dict(object_index=0,primitive_index=0)])
                shape=decode_tmd(candidate);before=decode_tmd(current)
                self.assertEqual(shape['vertices'],before['vertices']);self.assertEqual(len(candidate),len(original))
                rows=inspect_model_primitives(candidate)['objects'][0]['primitives']
                self.assertEqual(len(rows),5);self.assertEqual(rows[0]['vertices'],[4]*(4 if flags&2 else 3))
                candidate,next_removed=remove_faces(original,candidate,removed,[dict(object_index=0,primitive_index=0)])
                self.assertEqual(next_removed,[dict(object_index=0,primitive_index=0),dict(object_index=0,primitive_index=1)])
                qualify_face_removal(original,sha256(original).hexdigest(),candidate,next_removed)

    def test_empty_group_and_object(self):
        original=synthetic(((0x22,0x24),(0x14,)),count=1)
        candidate,removed=remove_faces(original,original,[],[dict(object_index=0,primitive_index=0),dict(object_index=0,primitive_index=1)])
        self.assertEqual(decode_tmd(candidate)['objects'][0]['triangle_count'],0)
        self.assertEqual(len(inspect_model_primitives(candidate)['objects'][1]['primitives']),1)
        self.assertEqual(remove_faces(original,candidate,removed,[]),(candidate,removed))

    def test_source_binding_opaque_and_domain_rejection(self):
        original=synthetic();selection=[dict(object_index=0,primitive_index=0)]
        candidate,removed=remove_faces(original,original,[],selection)
        with self.assertRaises(ImportError):qualify_face_removal(original,'0'*64,candidate,removed)
        for bad in [selection*2,[dict(object_index=True,primitive_index=0)],[dict(object_index=0,primitive_index=99)]]:
            with self.assertRaises(ImportError):remove_faces(original,original,[],bad)
        changed=bytearray(candidate);changed[-1]^=1
        with self.assertRaises(ImportError):qualify_face_removal(original,sha256(original).hexdigest(),bytes(changed),removed)
