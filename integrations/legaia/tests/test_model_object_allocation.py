"""Bounded native object growth preserves old bytes and allocates independent donors."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_object_allocation import allocate_model_objects,qualify_model_object_allocation
from importer.model_primitives import inspect_model_primitives,patch_model_primitives
from test_model_primitives import synthetic


def request(index,donor=0):
    return dict(object_id=f'object://authored/00000000-0000-4000-8000-{index:012x}',donor_object_index=donor)


class ModelObjectAllocationTests(unittest.TestCase):
    def test_native_families_independent_tables_and_exact_retained_suffix(self):
        for flags in range(0x10,0x28):
            with self.subTest(flags=flags):
                data=synthetic(((flags,flags),(flags,)),count=2)+b'UNOWNED-TAIL!?'
                requests=[request(1,1),request(2,0)];saved=deepcopy(requests)
                candidate,audit=allocate_model_objects(data,sha256(data).hexdigest(),requests)
                self.assertEqual(requests,saved)
                self.assertEqual(qualify_model_object_allocation(data,sha256(data).hexdigest(),candidate,requests),audit)
                old_end=12+2*28;growth=2*28
                self.assertEqual(candidate[old_end+growth:len(data)+growth],data[old_end:])
                before,after=(decode_tmd(blob) for blob in (data,candidate))
                self.assertEqual(after['vertices'][:len(before['vertices'])],before['vertices'])
                self.assertEqual(after['triangles'][:len(before['triangles'])],before['triangles'])
                for new in audit['new_objects']:
                    self.assertTrue(all(span['byte_offset']%4==0 for span in new['spans']))
                    donor,new_owner=new['donor_object_index'],new['object_index']
                    for span in new['spans']:
                        a,b,n=span['source_byte_offset'],span['byte_offset'],span['byte_length']
                        self.assertEqual(candidate[b:b+n],data[a:a+n])
                    old=inspect_model_primitives(data,include_normal_references=True)['objects'][donor]
                    added=inspect_model_primitives(candidate,include_normal_references=True)['objects'][new_owner]
                    for a,b in zip(old['primitives'],added['primitives']):
                        self.assertEqual({k:v for k,v in a.items() if k!='byte_offset'}, {k:v for k,v in b.items() if k!='byte_offset'})
                # Editing a new object's packet cannot mutate the donor allocation.
                edited,_=patch_model_primitives(candidate,sha256(candidate).hexdigest(),[dict(object_index=2,primitive_index=0,vertices=[2,1,0,3] if flags&2 else [2,1,0])])
                donor_span=audit['new_objects'][0]['spans'][0];at=donor_span['source_byte_offset']+growth;n=donor_span['byte_length']
                self.assertEqual(edited[at:at+n],candidate[at:at+n])

    def test_unused_pointer_repeated_donor_and_exact_qualification(self):
        raw=bytearray(synthetic(((0x20,),),count=1));struct.pack_into('<II',raw,20,0,0);data=bytes(raw)
        candidate,audit=allocate_model_objects(data,sha256(data).hexdigest(),[request(1),request(2)])
        self.assertEqual(struct.unpack_from('<I',candidate,20)[0],0)
        self.assertEqual([row['normal_count'] for row in audit['new_objects']],[0,0])
        self.assertEqual(struct.unpack_from('<I',candidate,48)[0],0)
        again,next_audit=allocate_model_objects(candidate,sha256(candidate).hexdigest(),[request(3,2)])
        self.assertEqual(next_audit['new_objects'][0]['object_index'],3)
        self.assertEqual(len(decode_tmd(again)['objects']),4)
        bad=bytearray(candidate);bad[-1]^=1
        with self.assertRaises(ImportError):qualify_model_object_allocation(data,sha256(data).hexdigest(),bytes(bad),[request(1),request(2)])

    def test_exact_requests_hash_ownership_and_budgets(self):
        data=synthetic();valid=request(1)
        for requests in ([],[valid]*2,[dict(valid,extra=True)],[dict(valid,donor_object_index=True)],
                         [dict(valid,donor_object_index=1)],[dict(valid,object_id='bad')], [request(i) for i in range(65)]):
            with self.assertRaises(ImportError):allocate_model_objects(data,sha256(data).hexdigest(),requests)
        with self.assertRaises(ImportError):allocate_model_objects(data,'0'*64,[valid])
        with patch('importer.model_object_allocation.MAX_MODEL_BYTES',len(data)+28):
            with self.assertRaises(ImportError):allocate_model_objects(data,sha256(data).hexdigest(),[valid])
        bad=bytearray(data);struct.pack_into('<I',bad,12,0)
        with self.assertRaises(ImportError):allocate_model_objects(bytes(bad),sha256(bad).hexdigest(),[valid])


if __name__=='__main__':unittest.main()
