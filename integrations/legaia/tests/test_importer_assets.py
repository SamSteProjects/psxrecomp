"""Synthetic primitive-layout and model-source guards; no retail fixtures."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.assets import decode_tmd, load_model_preview
from importer.core import ImportError


def model(flags=0x18, *, invalid_vertex=False):
    corners = 4 if flags & 2 else 3
    textured = flags >= 0x20
    vertex_offset = (16 if corners == 4 else 14) if textured else 4
    stride = ((vertex_offset + corners * 2 + 3) // 4) * 4
    body = bytearray(stride)
    body[:4] = bytes([64, 96, 128, 0])
    if textured:
        body[4:14] = bytes([1, 2, 3, 0, 4, 5, 6, 0, 7, 8])
        if corners == 4:
            body[14:16] = bytes([9, 10])
    struct.pack_into(f"<{corners}H", body, vertex_offset,
                     *([0, 8, 7 if invalid_vertex else 16, 24][:corners]))
    group = struct.pack("<HH4B", 1, flags, 0, stride // 4, 0, 0x24 if textured else 0x20)
    primitives = group + body + bytes(stride) + bytes(4)
    vertex_start = 40 + len(primitives)
    header = struct.pack("<III7I", 0x80000002, 0, 1,
                         vertex_start - 12, 4, 0, 0, 28, 1, 0x00808080)
    vectors = b"".join(struct.pack("<hhhh", *v, 0)
                       for v in [(0, 0, 0), (10, 0, 0), (0, 10, 0), (10, 10, 0)])
    return header + primitives + vectors


class ModelPreviewTests(unittest.TestCase):
    def test_triangle_and_quad_topology_preserve_color_and_bounds(self):
        tri = decode_tmd(model())
        self.assertEqual(tri["triangles"], [[0, 1, 2]])
        self.assertEqual(tri["triangle_colors"], [[[64, 96, 128]] * 3])
        self.assertEqual(tri["bounds"], {"min": [0, 0, 0], "max": [10, 10, 0]})
        self.assertIsNone(tri["objects"][0]["transform"])
        self.assertFalse(tri["posed"])
        quad = decode_tmd(model(0x1A))
        self.assertEqual(quad["triangles"], [[0, 1, 2], [1, 3, 2]])

    def test_texture_fields_and_quad_corner_order(self):
        tri = decode_tmd(model(0x20))
        self.assertEqual(tri["triangle_uvs"], [[[1, 2], [4, 5], [7, 8]]])
        self.assertEqual(tri["materials"][0]["clut"], 3)
        self.assertEqual(tri["materials"][0]["tpage"], 6)
        quad = decode_tmd(model(0x22))
        self.assertEqual(quad["triangle_uvs"][1], [[4, 5], [9, 10], [7, 8]])

    def test_malformed_geometry_and_unknown_modes_fail_explicitly(self):
        with self.assertRaisesRegex(ImportError, "invalid vertex offsets"):
            decode_tmd(model(invalid_vertex=True))
        with self.assertRaisesRegex(ImportError, "unsupported ETMD/primitive"):
            decode_tmd(model(0x28))
        with self.assertRaisesRegex(ImportError, "exceeds model size"):
            decode_tmd(model()[:-1])
        absolute = bytearray(model())
        struct.pack_into("<I", absolute, 0, 0x41)
        with self.assertRaisesRegex(ImportError, "unsupported TMD/ETMD header"):
            decode_tmd(bytes(absolute))

    def test_source_locator_rejected_before_disc_access(self):
        for asset in [None, {}, {"asset_kind": "tmd_model", "source_record": []}]:
            with self.assertRaises(ImportError):
                load_model_preview("not-a-disc.bin", asset)


if __name__ == "__main__":
    unittest.main()
