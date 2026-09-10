import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.terrain import decode_terrain


class TerrainTests(unittest.TestCase):
    def test_corner_heights_quad_order_and_flipped_atlas_v(self):
        data = bytearray(0x12000)
        struct.pack_into("<H", data, 0x8000, 0x1004)
        data[4 * 32 + 20:4 * 32 + 24] = bytes([63, 12, 0, 125])
        for index, tier in ((0, 1), (1, 2), (128, 3), (129, 4)):
            data[0x4000 + index] = tier
        g = decode_terrain(bytes(data), [i * 16 for i in range(16)])
        self.assertEqual(g['vertices'], [[0,-16,0],[128,-32,0],[0,-48,128],[128,-64,128]])
        self.assertEqual(g['triangles'], [[0,1,2],[1,3,2]])
        self.assertEqual(g['triangle_uvs'][0], [[224,255],[255,255],[224,224]])

    def test_border_clamps_height_and_missing_page_has_no_fallback(self):
        data = bytearray(0x12000)
        struct.pack_into("<H", data, 0xFFFE, 0x1000)
        data[0x7FFF] = 1
        g = decode_terrain(bytes(data), [0,64]+[0]*14)
        self.assertEqual([v[1] for v in g['vertices']], [-64]*4)
        self.assertFalse(g['materials'][0]['textured'])
        self.assertEqual(g['triangle_uvs'], [None,None])


if __name__ == '__main__':
    unittest.main()
