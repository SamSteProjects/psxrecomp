from hashlib import sha256
import json,struct,unittest
from importer.core import ImportError
from importer.model_json import export_shape_json,scale_shape_object
import test_model_rotation

class ModelScaleTests(unittest.TestCase):
    def test_rounding_identity_normal_padding_and_other_spans(self):
        source=test_model_rotation.ModelRotationTests().source();data=bytearray(source);vert,count=struct.unpack_from('<II',data,12)
        struct.pack_into('<3h',data,12+vert,1,-1,3);source=bytes(data);digest=sha256(source).hexdigest()
        self.assertEqual(scale_shape_object(source,source,digest,0,100),source)
        before=json.loads(export_shape_json(source));changed=scale_shape_object(source,source,digest,0,50);after=json.loads(export_shape_json(changed))
        self.assertEqual(after['objects'][0]['vertices'][0],[1,-1,2])
        self.assertEqual(after['objects'][0]['normals'],before['objects'][0]['normals'])
        allowed={12+vert+n*8+a for n in range(count) for a in range(6)}
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(source,changed)) if a!=b))
        self.assertEqual(source,bytes(data))
    def test_stale_invalid_and_overflow_reject_atomically(self):
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        for obj,percent in ((True,100),(1,100),(0,True),(0,0),(0,1001),(0,1.5)):
            with self.assertRaises(ImportError):scale_shape_object(source,source,digest,obj,percent)
        with self.assertRaises(ImportError):scale_shape_object(source,source,'0'*64,0,100)
        data=bytearray(source);vert=struct.unpack_from('<I',data,12)[0];struct.pack_into('<h',data,12+vert,-32768);source=bytes(data)
        with self.assertRaises(ImportError):scale_shape_object(source,source,sha256(source).hexdigest(),0,101)
        self.assertEqual(scale_shape_object(source,source,sha256(source).hexdigest(),0,100),source)

if __name__=='__main__':unittest.main()
