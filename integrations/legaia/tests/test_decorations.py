import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.decorations import decode_field_decorations
from importer.core import ImportError


class DecorationTests(unittest.TestCase):
    def test_field_gate_excludes_placed_but_preserves_zero_mesh(self):
        data = bytearray(0x12000)
        for index, cell in enumerate((0x2005, 0x1005, 0x2006, 0x2007, 0x2001)):
            struct.pack_into('<H', data, 0x8000 + index * 2, cell)
        struct.pack_into('<H', data, 6 * 32 + 18, 4)
        rows = decode_field_decorations(bytes(data), [0] * 16, 'town01')['placements']
        self.assertEqual([p['object_record_index'] for p in rows], [5, 7, 1])
        self.assertEqual([p['pack_index'] for p in rows], [0, 0, None])

    def test_signed_transform_floor_mask_rotation_and_distinct_cells(self):
        data = bytearray(0x12000)
        struct.pack_into('<3h', data, 5 * 32, -64, -12, 56)
        struct.pack_into('<3H', data, 5 * 32 + 8, 1024, 2048, 3072)
        for index in (25 * 128 + 38, 25 * 128 + 39):
            struct.pack_into('<H', data, 0x8000 + index * 2, 0x2005)
            data[0x4000 + index] = 0xF1
        a, b = decode_field_decorations(bytes(data), [0, 64] + [0] * 14, 'town01')['placements']
        self.assertEqual(a['imported_transform']['position'], {'x':4864, 'y':-76, 'z':3208})
        self.assertEqual(a['imported_transform']['rotation_psx'], dict(x=1024,y=2048,z=3072))
        self.assertNotEqual(a['semantic_id'], b['semantic_id'])
        self.assertEqual(a['source_record']['object_sha256'], b['source_record']['object_sha256'])

    def test_invalid_source_bounds(self):
        for data, lut in ((b'', [0]*16), (bytes(0x12000), [0]*15),
                          (bytes(0x12000), [True]+[0]*15), (bytes(0x12000), [32768]+[0]*15)):
            with self.assertRaises(ImportError):
                decode_field_decorations(data, lut, 'town01')


if __name__ == '__main__':
    unittest.main()
