"""Synthetic placement coordinates plus opt-in retail reference examples."""
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.environment import decode_environment_placements, load_environment_placements


class EnvironmentPlacementTests(unittest.TestCase):
    def test_signed_offsets_floor_cell_rotation_and_distinct_instances(self):
        data, man = bytearray(0x12000), bytearray(0x2B + 6 * 3)
        struct.pack_into("<16h", man, 2, 0, 64, *([0] * 14))
        struct.pack_into("<hhhbb3HbbHH", data, 137 * 32,
                         -64, -12, 56, 1, -1, 1024, 2048, 3072, 0, 0, 7, 6)
        for col in (38, 40):
            struct.pack_into("<H", data, 0x8000 + (25 * 128 + col) * 2, 137)
            data[0x4000 + 25 * 128 + col] = 1
            struct.pack_into("<H", data, 0x8000 + (24 * 128 + col + 1) * 2, 0x400)
        result = decode_environment_placements(bytes(data), bytes(man), "synthetic")
        a, b = result["placements"]
        self.assertNotEqual(a["semantic_id"], b["semantic_id"])
        self.assertEqual(a["imported_transform"]["position"], {"x": 4864, "y": -76, "z": 3208})
        self.assertEqual(a["imported_transform"]["rotation_psx"], {"x": 1024, "y": 2048, "z": 3072})
        self.assertEqual(a["pack_index"], 7)
        self.assertTrue(a["footprint_anchor"]["bind_owned"])
        self.assertEqual(a["floor"]["tier"], 1)  # anchor tier is zero

    def test_offgrid_anchor_and_nonplaced_records_do_not_spawn(self):
        data, man = bytearray(0x12000), bytes(0x2B + 6 * 3)
        struct.pack_into("<H", data, 0x8000, 4)
        struct.pack_into("<b", data, 4 * 32 + 6, -1)
        struct.pack_into("<H", data, 4 * 32 + 18, 4)
        result = decode_environment_placements(bytes(data), man, "synthetic")
        self.assertEqual(result["placements"], [])
        self.assertEqual(len(result["excluded"]), 1)
        with self.assertRaises(ImportError):
            decode_environment_placements(bytes(data[:-1]), man, "synthetic")
        with self.assertRaises(ImportError):
            decode_environment_placements(bytes(data), man[:20], "synthetic")

    @unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
    def test_town01_reference_placements_house_and_unbound_cave(self):
        result = load_environment_placements(os.environ["LEGAIA_DISC_BIN"], "town01")
        self.assertEqual(len(result["placements"]), 46)
        self.assertEqual(result["excluded"], [])
        by_record = {p["object_record_index"]: p for p in result["placements"]}
        self.assertEqual(by_record[137]["imported_transform"]["position"], {"x": 4864, "y": -192, "z": 3208})
        self.assertEqual(by_record[168]["tile"], {"x": 32, "z": 93})
        self.assertFalse(by_record[168]["footprint_anchor"]["bind_owned"])
        self.assertEqual(sum(p["footprint_anchor"]["bind_owned"] for p in result["placements"]), 37)


if __name__ == "__main__":
    unittest.main()
