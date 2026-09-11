"""Shape byte protection and rigid-pose preservation, using synthetic TMDs."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from test_importer_assets import model
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_authoring import replace_model_shape, preview_model_shape


class ModelShapeTests(unittest.TestCase):
    def test_coordinate_bytes_only_including_normals(self):
        data = bytearray(model(0x22))
        normal = len(data)
        struct.pack_into('<II', data, 20, normal-12, 1)
        data.extend(struct.pack('<hhhh', 0, 4096, 0, 123))
        source = bytes(data)
        start = 12 + struct.unpack_from('<I', source, 12)[0]
        allowed = {start+n*8+a for n in range(4) for a in range(6)} | set(range(normal,normal+6))
        for offset in range(len(source)):
            changed = bytearray(source); changed[offset] ^= 1
            if offset in allowed:
                _, audit = replace_model_shape(source, sha256(source).hexdigest(), bytes(changed))
                self.assertEqual(len(audit), 1)
            else:
                with self.assertRaises(ImportError):
                    replace_model_shape(source, sha256(source).hexdigest(), bytes(changed))
        self.assertEqual(replace_model_shape(source, sha256(source).hexdigest(), source), (source, []))
        struct.pack_into('<I', data, 20, start-12)
        with self.assertRaisesRegex(ImportError, 'aliased'):
            replace_model_shape(bytes(data), sha256(data).hexdigest(), bytes(data))

    def test_pose_applies_rotation_and_preserves_input(self):
        source = model()
        edited = bytearray(source)
        start = 12 + struct.unpack_from('<I', source, 12)[0]
        struct.pack_into('<h', edited, start, 20)
        preview = decode_tmd(source)
        transforms = [dict(object_index=0, translation=[3,4,5], rotation_psx=[0,0,1024])]
        preview.update(posed=True, pose={'object_transforms':transforms})
        baseline = deepcopy(preview)
        result = preview_model_shape(preview, bytes(edited), {'source_sha256':sha256(source).hexdigest()})
        for actual, expected in zip(result['vertices'][0], [3,24,5]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(preview, baseline)
        self.assertEqual(result['triangles'], preview['triangles'])
        preview['pose'] = {}
        with self.assertRaisesRegex(ImportError, 'explicit pose'):
            preview_model_shape(preview, bytes(edited), {})
