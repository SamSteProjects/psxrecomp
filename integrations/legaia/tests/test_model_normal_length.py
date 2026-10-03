from hashlib import sha256
import struct
import unittest

from importer.core import ImportError
from importer.model_normal_length import rescale_normal, rescale_object_normals
from test_model_rotation import ModelRotationTests


class ModelNormalLengthTests(unittest.TestCase):
    def test_rounding_zero_extreme_and_source_byte_ownership(self):
        for vector,length,expected in [([3,4,0],10,[6,8,0]),([-3,-4,0],10,[-6,-8,0]),
                                      ([0,0,0],4096,[0,0,0]),([-32768,0,0],32767,[-32767,0,0]),
                                      ([1,1,1],1,[1,1,1])]:
            self.assertEqual(rescale_normal(vector,length),expected)
        original=bytearray(ModelRotationTests().source())
        normal=12+struct.unpack_from('<I',original,20)[0]
        struct.pack_into('<I',original,24,2)
        original.extend(struct.pack('<hhhh',0,0,0,321))
        original=bytes(original)
        effective=bytearray(original);vertex=12+struct.unpack_from('<I',original,12)[0]
        struct.pack_into('<h',effective,vertex,7);effective=bytes(effective)
        result=rescale_object_normals(original,effective,sha256(effective).hexdigest(),0,2048)
        self.assertNotEqual(result,effective)
        allowed=set(range(normal,normal+6))
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(effective,result)) if a!=b))
        self.assertEqual(result[normal+6:normal+16],effective[normal+6:normal+16])
        self.assertEqual(result[vertex:vertex+2],struct.pack('<h',7))

    def test_stale_domain_and_object_reject_before_replacement(self):
        source=ModelRotationTests().source();key=sha256(source).hexdigest()
        for obj,length in [(True,4096),(1,4096),(0,True),(0,0),(0,32768),(0,1.5)]:
            with self.assertRaises(ImportError):rescale_object_normals(source,source,key,obj,length)
        with self.assertRaises(ImportError):rescale_object_normals(source,source,'0'*64,0,4096)
