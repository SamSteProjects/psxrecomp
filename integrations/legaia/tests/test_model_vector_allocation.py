"""Native vector growth preserves bytes/indices and feeds actual face packets."""
from copy import deepcopy
from hashlib import sha256
import struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_vector_allocation import append_model_vectors,qualify_model_vector_allocation
from importer.model_face_addition import add_model_faces
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic


class VectorAllocationTests(unittest.TestCase):
    def test_four_adjacent_tables_preserve_every_existing_byte_except_owned_headers(self):
        original=synthetic(((0x16,),(0x22,)),count=2)
        requests=[dict(object_index=owner,kind=kind,vectors=[[100+owner,-200,32767],[-32768,0,300]])
                  for owner in (1,0) for kind in ('normals','vertices')]
        saved=deepcopy(requests)
        candidate,audit=append_model_vectors(original,sha256(original).hexdigest(),requests)
        self.assertEqual(requests,saved);self.assertEqual(audit['growth_bytes'],64)
        # Undo insertion spans, then only the qualified pointer/count words.
        recovered=bytearray(candidate)
        for row in sorted(audit['new_vectors'],key=lambda row:row['byte_offset'],reverse=True):
            at=row['byte_offset'];size=row['added_count']*8
            request=next(req for req in requests if req['object_index']==row['object_index'] and req['kind']==row['kind'])
            self.assertEqual(candidate[at:at+size],b''.join(struct.pack('<4h',*xyz,0) for xyz in request['vectors']))
            self.assertEqual(row['first_index'],5 if row['kind']=='vertices' else 4)
            del recovered[at:at+size]
        for owner in range(2):
            header=12+owner*28
            for field in (0,4,8,12,16):recovered[header+field:header+field+4]=original[header+field:header+field+4]
            self.assertEqual(struct.unpack_from('<I',candidate,header+4)[0],7)
            self.assertEqual(struct.unpack_from('<I',candidate,header+12)[0],6)
        self.assertEqual(bytes(recovered),original)
        before=inspect_model_primitives(original,include_normal_references=True)
        after=inspect_model_primitives(candidate,include_normal_references=True)
        for old,new in zip(before['objects'],after['objects']):
            for a,b in zip(old['primitives'],new['primitives']):
                for key in ('vertices','normal_indices','uvs','colors','flags','material'):self.assertEqual(a[key],b[key])
        self.assertEqual(qualify_model_vector_allocation(original,sha256(original).hexdigest(),candidate,requests),audit)
        with self.assertRaises(ImportError):qualify_model_vector_allocation(original,sha256(original).hexdigest(),candidate[:-1]+b'X',requests)

    def test_new_face_references_new_vertices_and_normals_without_renumbering_old_faces(self):
        original=synthetic(((0x16,),))
        requests=[dict(object_index=0,kind=kind,vectors=[[100,200,300],[400,500,600]]) for kind in ('vertices','normals')]
        current,_=append_model_vectors(original,sha256(original).hexdigest(),requests)
        candidate,_=add_model_faces(current,sha256(current).hexdigest(),[dict(
            face_id='face://authored/00000000-0000-4000-8000-000000000001',object_index=0,
            group_index=0,donor_primitive_index=0,fields=dict(vertices=[5,6,0,1],normal_indices=[4,5,4,5]))])
        rows=inspect_model_primitives(candidate,include_normal_references=True)['objects'][0]['primitives']
        self.assertEqual(rows[-1]['vertices'],[5,6,0,1]);self.assertEqual(rows[-1]['normal_indices'],[4,5,4,5])
        self.assertEqual(rows[0]['vertices'],[0,1,2,3])

    def test_allocates_unused_normal_table_at_owned_end_without_following_unused_pointer(self):
        source=bytearray(synthetic(((0x22,),)))
        struct.pack_into('<II',source,20,0,0)
        original=bytes(source)
        candidate,audit=append_model_vectors(original,sha256(original).hexdigest(),[
            dict(object_index=0,kind='normals',vectors=[[4096,0,-1]])])
        self.assertEqual(12+struct.unpack_from('<I',candidate,20)[0],len(original))
        self.assertEqual(struct.unpack_from('<I',candidate,24)[0],1)
        self.assertEqual(candidate[-8:],struct.pack('<4h',4096,0,-1,0))
        self.assertEqual(audit['new_vectors'][0]['first_index'],0)

    def test_native_address_boundary_metadata_and_byte_budgets_reject_transactionally(self):
        source=bytearray(synthetic(((0x22,),)))
        normal=12+struct.unpack_from('<I',source,20)[0]
        source[normal:normal]=bytes((8191-5)*8)
        struct.pack_into('<I',source,16,8191);struct.pack_into('<I',source,20,normal-12+(8191-5)*8)
        original=bytes(source);request=dict(object_index=0,kind='vertices',vectors=[[1,2,3]])
        candidate,_=append_model_vectors(original,sha256(original).hexdigest(),[request])
        self.assertEqual(struct.unpack_from('<I',candidate,16)[0],8192)
        face_model,_=add_model_faces(candidate,sha256(candidate).hexdigest(),[dict(
            face_id='face://authored/00000000-0000-4000-8000-000000000001',object_index=0,
            group_index=0,donor_primitive_index=0,fields=dict(vertices=[8191,0,1,2]))])
        self.assertEqual(inspect_model_primitives(face_model)['objects'][0]['primitives'][-1]['vertices'],[8191,0,1,2])
        with self.assertRaises(ImportError):append_model_vectors(candidate,sha256(candidate).hexdigest(),[request])
        for requests in ([],[request]*2,[{**request,'object_index':True}],[{**request,'kind':'other'}],
                         [{**request,'vectors':[[True,2,3]]}],[{**request,'vectors':[[32768,0,0]]}],
                         [{**request,'vectors':[[0,0]]}],[{**request,'padding':1}],
                         [{**request,'vectors':[[0,0,0]]*4097}]):
            saved=deepcopy(requests)
            with self.assertRaises(ImportError):append_model_vectors(original,sha256(original).hexdigest(),requests)
            self.assertEqual(requests,saved)
        with self.assertRaises(ImportError):append_model_vectors(original,'0'*64,[request])
        with patch('importer.model_vector_allocation.MAX_MODEL_BYTES',len(candidate)-1):
            with self.assertRaises(ImportError):append_model_vectors(original,sha256(original).hexdigest(),[request])


if __name__=='__main__':unittest.main()
