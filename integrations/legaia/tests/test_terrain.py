import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.terrain import decode_terrain
from sdk.scene_preview import sample_preview_ground


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
        self.assertEqual(g['vertex_floor_tiers'], [1,2,3,4])
        self.assertEqual(g['triangle_uvs'][0], [[224,255],[255,255],[224,224]])

    def test_border_clamps_height_and_missing_page_has_no_fallback(self):
        data = bytearray(0x12000)
        struct.pack_into("<H", data, 0xFFFE, 0x1000)
        data[0x7FFF] = 1
        g = decode_terrain(bytes(data), [0,64]+[0]*14)
        self.assertEqual([v[1] for v in g['vertices']], [-64]*4)
        self.assertEqual(g['vertex_floor_tiers'], [1]*4)
        self.assertFalse(g['materials'][0]['textured'])
        self.assertEqual(g['triangle_uvs'], [None,None])

    def test_ground_sampler_includes_outer_edges_without_extrapolation(self):
        data = bytearray(0x12000)
        struct.pack_into("<H", data, 0xFFFE, 0x1000)
        data[0x7FFF] = 1
        ground = decode_terrain(bytes(data), [0,64]+[0]*14)
        for x, z in ((16256,16256), (16384,16256), (16256,16384),
                     (16384,16384), (16384,16300), (16300,16384)):
            with self.subTest(x=x, z=z):
                sample = sample_preview_ground(ground, x, z)
                self.assertEqual(sample['y'], -64)
                self.assertEqual(sample['cell_index'], 16383)
        for x, z in ((16384.001,16384), (16384,16384.001), (-0.001,0),
                     (0,-0.001), (float('nan'),0), (0,float('inf')), (True,0)):
            with self.subTest(x=x, z=z):
                self.assertIsNone(sample_preview_ground(ground, x, z))
        self.assertIsNone(sample_preview_ground(ground, 0, 0))
        self.assertIsNone(sample_preview_ground({'cells': []}, 16384, 16384))

    def test_ground_sampler_uses_source_triangle_not_bilinear_height(self):
        ground = {'cells': [{'cell_index': 16383, 'vertex_start': 0}],
                  'vertices': [[16256,0,16256], [16384,128,16256],
                               [16256,256,16384], [16384,512,16384]]}
        for x, z, height in ((16288,16288,96), (16352,16352,352),
                             (16384,16320,320), (16320,16384,384)):
            with self.subTest(x=x, z=z):
                self.assertEqual(sample_preview_ground(ground, x, z)['y'], height)


if __name__ == '__main__':
    unittest.main()
