"""Packet allocation shares exact operand checks and qualifies whole models once."""
from hashlib import sha256
import unittest
from unittest.mock import patch
from importer import model_primitives, model_face_addition, model_group_allocation
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from test_model_primitives import synthetic
from test_model_group_allocation import request


class PacketAllocationTests(unittest.TestCase):
    def test_all_layouts_match_existing_field_authoring_byte_for_byte(self):
        for flags in range(0x10,0x28):
            with self.subTest(flags=flags):
                original=synthetic(((flags,),),count=2);key=sha256(original).hexdigest()
                row=inspect_model_primitives(original,include_normal_references=True)['objects'][0]['primitives'][0]
                corners=row['corner_count'];stride=original[row['byte_offset']-3]*4
                fields={'vertices':list(reversed(range(corners)))}
                if row['uvs'] is not None:fields['uvs']=[[10+i,250-i] for i in range(corners)]
                if row['colors'] is not None:fields['colors']=[[11+i,127,253-i] for i in range(len(row['colors']))]
                if row['normal_indices'] is not None:fields['normal_indices']=list(reversed(row['normal_indices']))
                edited,_=patch_model_primitives(original,key,[dict(object_index=0,primitive_index=0,**fields)])
                expected=edited[row['byte_offset']:row['byte_offset']+stride]
                group=request(1,corners=corners);group['faces'][0]['fields']=fields
                grown,audit=model_group_allocation.allocate_model_groups(original,key,[group])
                at=audit['new_faces'][0]['byte_offset'];self.assertEqual(grown[at:at+stride],expected)
                addition=dict(face_id=group['faces'][0]['face_id'],object_index=0,group_index=0,donor_primitive_index=0,fields=fields)
                grown,audit=model_face_addition.add_model_faces(original,key,[addition])
                at=audit['new_faces'][0]['byte_offset'];self.assertEqual(grown[at:at+stride],expected)

    def test_full_source_and_final_qualification_do_not_scale_with_face_count(self):
        original=synthetic(((0x20,),),count=2);key=sha256(original).hexdigest()
        for count in (1,512):
            faces=[request(i)['faces'][0] for i in range(count)]
            group=request(900);group['faces']=faces
            additions=[dict(face_id=f['face_id'],object_index=0,group_index=0,donor_primitive_index=0,fields=f['fields']) for f in faces]
            for module,call,requests in ((model_face_addition,model_face_addition.add_model_faces,additions),
                                        (model_group_allocation,model_group_allocation.allocate_model_groups,[group])):
                with self.subTest(count=count,codec=module.__name__), \
                        patch.object(module,'inspect_model_primitives',wraps=inspect_model_primitives) as source, \
                        patch.object(module,'_qualified_model',wraps=model_primitives._qualified_model) as final:
                    call(original,key,requests)
                    self.assertEqual(source.call_count,1);self.assertEqual(final.call_count,1)


if __name__=='__main__':unittest.main()
