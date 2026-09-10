from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.environment_authoring import patch_environment_transforms
from importer.core import ImportError


class EnvironmentAuthoringTests(unittest.TestCase):
    def source(self):
        data = bytearray(0x12000)
        data[5*32:6*32] = bytes(range(32))
        for cell in (1, 200):
            struct.pack_into('<H', data, 0x8000 + cell*2, 0x2005)
        return bytes(data)

    def test_exact_bytes_and_complete_shared_cell_audit(self):
        data = self.source()
        changed, audit = patch_environment_transforms(data, sha256(data).hexdigest(),
            [{'record_index':5, 'offset':{'z':-123}, 'rotation_psx':{'y':1024}}])
        expected = bytearray(data)
        struct.pack_into('<h', expected, 5*32+4, -123)
        struct.pack_into('<H', expected, 5*32+10, 1024)
        self.assertEqual(changed, bytes(expected))
        self.assertTrue(all(row['affected_grid_cells']==[1,200] for row in audit))
        same, no_changes = patch_environment_transforms(changed, sha256(changed).hexdigest(),
            [{'record_index':5, 'offset':{'z':-123}}])
        self.assertEqual(same, changed)
        self.assertEqual(no_changes, [])

    def test_invalid_edits_and_stale_source_rejected(self):
        data = self.source()
        for edits in ([{'record_index':5,'offset':{'x':True}}],
                      [{'record_index':5,'rotation_psx':{'y':4096}}],
                      [{'record_index':5,'offset':{'x':32768}}],
                      [{'record_index':6,'offset':{'x':1}}],
                      [{'record_index':5,'offset':{'w':1}}],
                      [{'record_index':5,'offset':{'x':1}}]*2):
            with self.assertRaises(ImportError):
                patch_environment_transforms(data, sha256(data).hexdigest(), edits)
        with self.assertRaises(ImportError):
            patch_environment_transforms(data, 'stale', [])


if __name__ == '__main__':
    unittest.main()
