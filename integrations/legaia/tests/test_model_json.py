"""Readable vector interchange preserves opaque TMD bytes and exact source binding."""
from copy import deepcopy
from hashlib import sha256
import json
import struct
import unittest
from test_importer_assets import model
from importer.core import ImportError
from importer.model_json import export_shape_json, import_shape_json

class ModelJsonTests(unittest.TestCase):
    def test_vectors_padding_and_invalid_bindings(self):
        data=bytearray(model(0x22)); normal=len(data)
        struct.pack_into('<II',data,20,normal-12,1)
        data.extend(struct.pack('<hhhh',0,4096,0,123));source=bytes(data);digest=sha256(source).hexdigest()
        encoded=export_shape_json(source)
        self.assertEqual(import_shape_json(source,digest,encoded),(source,[]))
        doc=json.loads(encoded);doc['objects'][0]['normals'][0]=[4096,0,0]
        changed,audit=import_shape_json(source,digest,json.dumps(doc).encode())
        self.assertEqual(len(audit),2);self.assertTrue(all(row['kind']=='normal' for row in audit))
        self.assertEqual(changed[:normal],source[:normal]);self.assertEqual(changed[normal+6:],source[normal+6:])
        invalid=[]
        for field,value in [('source_sha256','0'*64),('coordinate_system','y_up'),('objects',[])]:
            bad=deepcopy(doc);bad[field]=value;invalid.append(json.dumps(bad).encode())
        for vector in ([True,0,0],[32768,0,0],[1.5,0,0],[0,0],None):
            bad=deepcopy(doc);bad['objects'][0]['normals'][0]=vector;invalid.append(json.dumps(bad).encode())
        invalid.append(encoded.replace(b'"objects":',b'"objects": [], "objects":',1))
        for content in invalid:
            with self.assertRaises(ImportError):import_shape_json(source,digest,content)
