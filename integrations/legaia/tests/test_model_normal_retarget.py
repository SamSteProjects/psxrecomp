from hashlib import sha256
import struct
import unittest
from importer.core import ImportError
from importer.model_normal_retarget import retarget_object_normals
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic

class NormalRetargetTests(unittest.TestCase):
    def test_all_matching_flat_gouraud_operands_and_other_objects_preserved(self):
        source=synthetic(((0x12,0x14,0x16,0x20),(0x12,)),count=2)
        effective=bytearray(source);vertex=12+struct.unpack_from('<I',source,12)[0];struct.pack_into('<h',effective,vertex,37);effective=bytes(effective)
        obj=inspect_model_primitives(effective)['objects'][0]
        expected=bytearray(effective);changed=[]
        for row in obj['primitives']:
            if row['baked_colors']:continue
            relative=(18 if row['corner_count']==3 else 20) if row['gouraud'] else (12 if row['corner_count']==3 else 20)
            for corner in range(row['corner_count'] if row['gouraud'] else 1):
                at=row['byte_offset']+relative+corner*2
                if struct.unpack_from('<H',effective,at)[0]==0:struct.pack_into('<H',expected,at,24);changed.append(at)
        result=retarget_object_normals(source,effective,sha256(effective).hexdigest(),0,0,3)
        self.assertEqual(result,bytes(expected));self.assertEqual(len(changed),6)
        self.assertEqual(retarget_object_normals(source,result,sha256(result).hexdigest(),0,0,3),result)
        self.assertEqual(retarget_object_normals(source,result,sha256(result).hexdigest(),0,3,3),result)
    def test_stale_domain_and_unlit(self):
        source=synthetic(((0x14,),),count=1);key=sha256(source).hexdigest()
        for obj,old,new in [(True,0,1),(1,0,1),(0,True,1),(0,0,True),(0,0,4),(0,-1,1)]:
            with self.subTest(indices=(obj,old,new)),self.assertRaises(ImportError):retarget_object_normals(source,source,key,obj,old,new)
        with self.assertRaises(ImportError):retarget_object_normals(source,source,'0'*64,0,0,1)
        unlit=synthetic(((0x20,),),count=1);self.assertEqual(retarget_object_normals(unlit,unlit,sha256(unlit).hexdigest(),0,0,1),unlit)
