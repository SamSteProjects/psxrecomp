from hashlib import sha256
import json,struct,unittest
from importer.core import ImportError
from importer.model_json import export_shape_json,rotate_shape_object
from test_importer_assets import model

class ModelRotationTests(unittest.TestCase):
    def source(self):
        data=bytearray(model(0x22));normal=len(data);struct.pack_into('<II',data,20,normal-12,1);data.extend(struct.pack('<hhhh',123,4096,-456,789));return bytes(data)
    def test_axes_inverse_four_turns_and_opaque_preservation(self):
        source=self.source();before=json.loads(export_shape_json(source));digest=sha256(source).hexdigest()
        for axis in ('x','y','z'):
            changed=rotate_shape_object(source,source,digest,0,axis,1)
            restored=rotate_shape_object(source,changed,sha256(changed).hexdigest(),0,axis,-1)
            self.assertEqual(restored,source)
            effective=source
            for _ in range(4):effective=rotate_shape_object(source,effective,sha256(effective).hexdigest(),0,axis,1)
            self.assertEqual(effective,source)
            after=json.loads(export_shape_json(changed))
            for kind in ('vertices','normals'):
                for old,new in zip(before['objects'][0][kind],after['objects'][0][kind]):
                    x,y,z=old;self.assertEqual(new,[x,-z,y] if axis=='x' else [z,y,-x] if axis=='y' else [-y,x,z])
                    self.assertEqual(sum(v*v for v in old),sum(v*v for v in new))
            vert,count,normal,normals=struct.unpack_from('<4I',source,12)
            allowed={12+offset+n*8+a for offset,size in [(vert,count),(normal,normals)] for n in range(size) for a in range(6)}
            self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(source,changed)) if a!=b))
            self.assertEqual(rotate_shape_object(source,source,digest,0,axis,2),rotate_shape_object(source,changed,sha256(changed).hexdigest(),0,axis,1))
    def test_stale_bounds_types_and_negative_limit_reject(self):
        source=self.source();digest=sha256(source).hexdigest()
        for obj,axis,turn in [(True,'x',1),(1,'x',1),(0,'unknown',1),(0,'x',True),(0,'x',0),(0,'x',4)]:
            with self.assertRaises(ImportError):rotate_shape_object(source,source,digest,obj,axis,turn)
        with self.assertRaises(ImportError):rotate_shape_object(source,source,'0'*64,0,'x',1)
        data=bytearray(source);vert=struct.unpack_from('<I',data,12)[0];struct.pack_into('<h',data,12+vert,-32768);source=bytes(data)
        with self.assertRaises(ImportError):rotate_shape_object(source,source,sha256(source).hexdigest(),0,'y',1)
