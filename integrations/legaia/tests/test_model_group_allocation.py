"""New native groups preserve qualified descriptors, footer and table ownership."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_face_addition import add_model_faces
from importer.model_face_removal import _groups
from importer.model_group_allocation import allocate_model_groups, qualify_model_group_allocation
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic


def request(index, owner=0, donor=0, primitive=0, corners=3):
    return dict(group_id=f'group://authored/00000000-0000-4000-8000-{index:012x}',
        object_index=owner, donor_group_index=donor, faces=[dict(
            face_id=f'face://authored/00000000-0000-4000-8000-{index:012x}',
            donor_primitive_index=primitive, fields={'vertices':list(reversed(range(corners)))})])


class ModelGroupAllocationTests(unittest.TestCase):
    def test_all_packet_families_multiple_objects_and_exact_unowned_bytes(self):
        for flags in range(0x10,0x28):
            with self.subTest(flags=flags):
                data=synthetic(((flags,flags),(flags,)),count=2)
                corners=4 if flags&2 else 3
                requests=[request(1,corners=corners),request(2,1,0,1,corners),request(3,0,1,3,corners)]
                original=deepcopy(requests)
                candidate,audit=allocate_model_groups(data,sha256(data).hexdigest(),requests)
                self.assertEqual(requests,original)
                self.assertEqual(qualify_model_group_allocation(data,sha256(data).hexdigest(),candidate,requests),audit)
                before,after=(decode_tmd(b) for b in (data,candidate))
                self.assertEqual(before['vertices'],after['vertices'])
                self.assertEqual(len(after['triangles'])-len(before['triangles']),3*(2 if corners==4 else 1))
                old=inspect_model_primitives(data,include_normal_references=True)
                new=inspect_model_primitives(candidate,include_normal_references=True)
                old_groups={}
                for owner,start,count,stride,first in _groups(data,old):
                    old_groups.setdefault(owner,[]).append((start,count,stride,first))
                for mapping in audit['retained_faces']:
                    owner=mapping['object_index']
                    a=old['objects'][owner]['primitives'][mapping['source_primitive_index']]
                    b=new['objects'][owner]['primitives'][mapping['current_primitive_index']]
                    astart,bstart=a['byte_offset'],b['byte_offset']
                    stride=old_groups[owner][a['group_index']][2]
                    self.assertEqual(candidate[bstart:bstart+stride],data[astart:astart+stride])
                for row in audit['new_groups']:
                    start,count,stride,_=old_groups[row['object_index']][row['donor_group_index']]
                    at=row['byte_offset'];stop=at+row['byte_length']
                    self.assertEqual(candidate[at+2:at+8],data[start+2:start+8])
                    self.assertEqual(candidate[stop-stride:stop],data[start+8+count*stride:start+8+(count+1)*stride])
                for row in audit['new_faces']:
                    packet=new['objects'][row['object_index']]['primitives'][row['current_primitive_index']]
                    self.assertEqual(packet['vertices'],list(reversed(range(corners))))
                # Remove only inserted groups and restore qualified header fields.
                unallocated=bytearray(candidate)
                for row in sorted(audit['new_groups'],key=lambda r:r['byte_offset'],reverse=True):
                    del unallocated[row['byte_offset']:row['byte_offset']+row['byte_length']]
                for owner in range(2):unallocated[12+owner*28:12+(owner+1)*28]=data[12+owner*28:12+(owner+1)*28]
                self.assertEqual(bytes(unallocated),data)
                self.assertEqual(audit['growth_bytes'],len(candidate)-len(data))

    def test_multiple_typed_packets_and_successive_new_group_donor(self):
        data=synthetic(((0x24,),),count=2)
        group=request(1)
        group['faces'][0]['fields'].update(uvs=[[1,2],[3,4],[5,6]],colors=[[7,8,9],[10,11,12],[13,14,15]])
        group['faces'].append(dict(face_id='face://authored/00000000-0000-4000-8000-000000000002',
            donor_primitive_index=1,fields={'vertices':[1,2,3]}))
        candidate,audit=allocate_model_groups(data,sha256(data).hexdigest(),[group])
        packets=inspect_model_primitives(candidate)['objects'][0]['primitives']
        self.assertEqual([r['current_primitive_index'] for r in audit['new_faces']],[2,3])
        self.assertEqual(packets[2]['uvs'],group['faces'][0]['fields']['uvs'])
        self.assertEqual(packets[2]['colors'],group['faces'][0]['fields']['colors'])
        second,review=allocate_model_groups(candidate,sha256(candidate).hexdigest(),[request(3,donor=1,primitive=2)])
        self.assertEqual(review['new_groups'][0]['group_index'],2)
        self.assertEqual(review['new_faces'][0]['current_primitive_index'],4)
        third,_=add_model_faces(second,sha256(second).hexdigest(),[dict(
            face_id='face://authored/00000000-0000-4000-8000-000000000004',object_index=0,
            group_index=2,donor_primitive_index=4,fields={'vertices':[2,1,0]})])
        self.assertEqual(len(inspect_model_primitives(third)['objects'][0]['primitives']),6)

    def test_lit_normals_and_unused_pointer_ownership(self):
        data=synthetic(((0x14,),),count=2);group=request(1)
        group['faces'][0]['fields']['normal_indices']=[3,2,1]
        candidate,_=allocate_model_groups(data,sha256(data).hexdigest(),[group])
        self.assertEqual(inspect_model_primitives(candidate,include_normal_references=True)['objects'][0]['primitives'][2]['normal_indices'],[3,2,1])
        group['faces'][0]['fields']['normal_indices']=[4,2,1]
        with self.assertRaises(ImportError):allocate_model_groups(data,sha256(data).hexdigest(),[group])
        original=synthetic(((0x20,),),count=2);data=bytearray(original)
        struct.pack_into('<II',data,20,len(original)-12,0);data=bytes(data)
        candidate,_=allocate_model_groups(data,sha256(data).hexdigest(),[request(1)])
        self.assertEqual(struct.unpack_from('<I',candidate,20)[0],len(original)-12)

    def test_identity_domains_budgets_and_exact_candidate_qualification(self):
        data=synthetic(((0x20,0x22),),count=2);valid=request(1)
        malformed=[[],[valid,valid],[dict(valid,extra=True)],[dict(valid,object_index=True)],
            [dict(valid,donor_group_index=True)],[dict(valid,donor_group_index=8)],
            [dict(valid,group_id='retail/0')],[dict(valid,faces=[])]]
        for field,value in [('face_id','bad'),('donor_primitive_index',True),('donor_primitive_index',2),('fields',{}),('fields',{'vertices':[99]*3})]:
            altered=deepcopy(valid);altered['faces'][0][field]=value;malformed.append([altered])
        duplicate=deepcopy(valid);duplicate['faces']*=2;malformed.append([duplicate])
        for requests in malformed:
            with self.subTest(requests=requests),self.assertRaises(ImportError):
                allocate_model_groups(data,sha256(data).hexdigest(),requests)
        with self.assertRaises(ImportError):allocate_model_groups(data,'stale',[valid])
        with self.assertRaises(ImportError):allocate_model_groups(data,sha256(data).hexdigest(),[request(i) for i in range(65)])
        oversized=deepcopy(valid);oversized['faces']=[request(i)['faces'][0] for i in range(513)]
        with self.assertRaises(ImportError):allocate_model_groups(data,sha256(data).hexdigest(),[oversized])
        with patch('importer.model_group_allocation.MAX_MODEL_BYTES',len(data)):
            with self.assertRaises(ImportError):allocate_model_groups(data,sha256(data).hexdigest(),[valid])
        candidate,_=allocate_model_groups(data,sha256(data).hexdigest(),[valid])
        for offset in (0,len(candidate)-1):
            tampered=bytearray(candidate);tampered[offset]^=1
            with self.assertRaises(ImportError):qualify_model_group_allocation(data,sha256(data).hexdigest(),bytes(tampered),[valid])


if __name__=='__main__':unittest.main()
