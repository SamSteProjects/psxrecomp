from hashlib import sha256
import struct,unittest
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_face_addition import add_model_faces,qualify_model_face_additions,MAX_NEW_FACES
from importer.model_primitives import inspect_model_primitives
from importer.model_face_removal import _groups
from test_model_primitives import synthetic

def face(index,owner=0,group=0,donor=0,corners=3):
    return dict(face_id=f'face://authored/00000000-0000-4000-8000-{index:012x}',object_index=owner,group_index=group,donor_primitive_index=donor,fields={'vertices':list(reversed(range(corners)))})
class ModelFaceAdditionTests(unittest.TestCase):
    def test_native_families_rebase_vectors_preserve_footer_and_source_faces(self):
        for flags in range(0x10,0x28):
            data=synthetic(((flags,flags),(flags,)),count=2);corners=4 if flags&2 else 3
            additions=[face(1,corners=corners),face(2,0,1,2,corners),face(3,1,0,0,corners)]
            candidate,audit=add_model_faces(data,sha256(data).hexdigest(),additions)
            before,after=(decode_tmd(value) for value in (data,candidate))
            self.assertEqual(before['vertices'],after['vertices'])
            self.assertEqual(len(after['triangles'])-len(before['triangles']),3*(2 if corners==4 else 1))
            self.assertEqual(audit['growth_bytes'],len(candidate)-len(data));self.assertEqual(len(audit['retained_faces']),6)
            old=inspect_model_primitives(data);new=inspect_model_primitives(candidate)
            old_groups=list(_groups(data,old));new_groups=list(_groups(candidate,new))
            for (_,start,count,stride,_),(_,now,more,_,_) in zip(old_groups,new_groups):
                self.assertEqual(candidate[now+8+more*stride:now+8+(more+1)*stride],data[start+8+count*stride:start+8+(count+1)*stride])
                self.assertEqual(candidate[now+2:now+8],data[start+2:start+8])
            for mapping in audit['retained_faces']:
                owner=mapping['object_index'];a=old['objects'][owner]['primitives'][mapping['source_primitive_index']];b=new['objects'][owner]['primitives'][mapping['current_primitive_index']]
                self.assertEqual(a['vertices'],b['vertices']);self.assertEqual(a['uvs'],b['uvs']);self.assertEqual(a['colors'],b['colors'])
            for row in audit['new_faces']:
                self.assertEqual(new['objects'][row['object_index']]['primitives'][row['current_primitive_index']]['vertices'],list(reversed(range(corners))))
            self.assertEqual(qualify_model_face_additions(data,sha256(data).hexdigest(),candidate,additions),audit)
    def test_multiple_same_group_ids_and_typed_attributes(self):
        data=synthetic(((0x24,),),count=2);a=face(1);b=face(2)
        a['fields'].update(uvs=[[1,2],[3,4],[5,6]],colors=[[7,8,9]]*3)
        candidate,audit=add_model_faces(data,sha256(data).hexdigest(),[a,b])
        self.assertEqual([r['current_primitive_index'] for r in audit['new_faces']],[2,3])
        row=inspect_model_primitives(candidate)['objects'][0]['primitives'][2]
        self.assertEqual(row['uvs'],a['fields']['uvs']);self.assertEqual(row['colors'],a['fields']['colors'])
        self.assertEqual(data,synthetic(((0x24,),),count=2))
    def test_identity_domain_source_and_unowned_mutations_reject(self):
        data=synthetic(((0x20,0x22),),count=2);valid=face(1)
        invalid=[[],[valid,valid],[face(1,group=1,donor=0)], [face(1,owner=True)], [dict(valid,face_id='retail/0')], [dict(valid,fields={})], [dict(valid,fields={'vertices':[99]*3})], [dict(valid,extra=True)]]
        for rows in invalid:
            with self.assertRaises(ImportError):add_model_faces(data,sha256(data).hexdigest(),rows)
        with self.assertRaises(ImportError):add_model_faces(data,'stale',[valid])
        candidate,_=add_model_faces(data,sha256(data).hexdigest(),[valid]);tampered=bytearray(candidate);tampered[-1]^=1
        with self.assertRaises(ImportError):qualify_model_face_additions(data,sha256(data).hexdigest(),bytes(tampered),[valid])
        with self.assertRaises(ImportError):add_model_faces(data,sha256(data).hexdigest(),[face(i) for i in range(MAX_NEW_FACES+1)])
    def test_lit_face_normal_reference_is_typed_and_source_remains_unchanged(self):
        data=synthetic(((0x10,),),count=2);addition=face(1)
        addition['fields']['normal_indices']=[3]
        candidate,_=add_model_faces(data,sha256(data).hexdigest(),[addition])
        before=inspect_model_primitives(data,include_normal_references=True)
        after=inspect_model_primitives(candidate,include_normal_references=True)
        self.assertEqual(after['objects'][0]['primitives'][2]['normal_indices'],[3])
        self.assertEqual(after['objects'][0]['primitives'][0]['normal_indices'],before['objects'][0]['primitives'][0]['normal_indices'])
        addition['fields']['normal_indices']=[4]
        with self.assertRaises(ImportError):add_model_faces(data,sha256(data).hexdigest(),[addition])
    def test_unused_normal_pointer_is_not_reinterpreted(self):
        original=synthetic(((0x20,),),count=2);data=bytearray(original);struct.pack_into('<II',data,20,len(original)-12,0);data=bytes(data)
        candidate,_=add_model_faces(data,sha256(data).hexdigest(),[face(1)])
        self.assertEqual(struct.unpack_from('<I',candidate,20)[0],len(original)-12)
if __name__=='__main__':unittest.main()
