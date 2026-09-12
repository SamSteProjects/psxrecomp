"""Ordered shape interchange never changes source topology or auxiliary bytes."""
from hashlib import sha256
import unittest

from importer.core import ImportError
from importer.model_obj import export_shape_obj, import_shape_obj
from test_importer_assets import model


class ModelObjTests(unittest.TestCase):
    def test_roundtrip_and_one_vertex_change(self):
        source = model(0x22)
        digest = sha256(source).hexdigest()
        obj = export_shape_obj(source)
        self.assertEqual(import_shape_obj(source, digest, obj), (source, []))
        # External tools emit decimals and optional texture/normal declarations.
        changed = obj.replace(b'v 0 0 0', b'v 20.000000 0.000000 0.000000', 1)
        result, audit = import_shape_obj(source, digest, b'\xef\xbb\xbf' + changed + b'vn 0 1 0\nmtllib ignored.mtl\n')
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]['after_value'], 20)
        allowed = {audit[0]['byte_offset'], audit[0]['byte_offset']+1}
        self.assertTrue(all(a == b or i in allowed for i,(a,b) in enumerate(zip(source,result))))

    def test_relative_indices_and_cyclic_faces_preserve_source(self):
        source = model(0x22)
        digest = sha256(source).hexdigest()
        obj = export_shape_obj(source)
        for face in (b'f -4 -3 -2', b'f 2 3 1', b'f -3 -2 -4'):
            self.assertEqual(import_shape_obj(source, digest, obj.replace(b'f 1 2 3', face)), (source, []))
        lines=obj.splitlines()
        faces=[line for line in lines if line.startswith(b'f ')]
        reordered=b'\n'.join([line for line in lines if not line.startswith(b'f ')]+list(reversed(faces)))+b'\n'
        self.assertEqual(import_shape_obj(source,digest,reordered),(source,[]))
        with self.assertRaises(ImportError):
            import_shape_obj(source,digest,reordered.replace(faces[1],faces[0]))
        for face in (b'f 0 2 3', b'f -5 -3 -2', b'f -2 -3 -4'):
            with self.assertRaises(ImportError):
                import_shape_obj(source, digest, obj.replace(b'f 1 2 3', face))

    def test_rejects_changed_order_counts_and_unrepresentable_positions(self):
        source = model(0x22)
        digest = sha256(source).hexdigest()
        obj = export_shape_obj(source)
        invalid = [obj.replace(b'f 1 2 3', b'f 2 1 3'), obj+b'v 1 2 3\n',
                   obj.replace(b'f 1 2 3', b'f -1 2 3'), obj+b'curv 1 2 3\n', b'\xff']
        invalid += [obj.replace(b'v 0 0 0', b'v '+v+b' 0 0', 1) for v in (b'0.5', b'nan', b'inf', b'32768')]
        for content in invalid:
            with self.subTest(content=content[:50]), self.assertRaises(ImportError):
                import_shape_obj(source, digest, content)
