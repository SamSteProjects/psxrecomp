"""Synthetic placement coordinates plus opt-in retail reference examples."""
import os
from pathlib import Path
import struct
import sys
import unittest
from copy import deepcopy
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.environment import (decode_environment_placements, load_environment_placements,
                                  _prop_record, EnvironmentPreviewCatalog)


class EnvironmentPlacementTests(unittest.TestCase):
    def test_partition0_animation_header_and_truncation(self):
        man = bytearray(0x2B + 3)
        struct.pack_into("<h", man, 0x22, 1)
        man[0x28:0x2B] = (3).to_bytes(3, "little")
        man += bytes([0, 2, 0xFF]) + bytes(18)
        record = _prop_record(bytes(man), 0)
        self.assertEqual(record["animation_id"], 2)
        self.assertEqual(record["script_offset"], 2)
        self.assertEqual(record["byte_length"], 3)
        with self.assertRaises(ImportError):
            _prop_record(bytes(man), 1)
        man[0x2E] = 2  # local-name prefix would cross the next section
        with self.assertRaises(ImportError):
            _prop_record(bytes(man), 0)

    def test_prop_pose_and_unbound_raw_mesh_remain_separate(self):
        from test_importer_scene_animation import fixture
        catalog, _, asset, model = fixture()
        metadata = {"placements": [
            {"semantic_id": "environment://synthetic/animated", "model_asset_id": asset["semantic_id"], "animation_id": 1},
            {"semantic_id": "environment://synthetic/static", "model_asset_id": asset["semantic_id"], "animation_id": 0}]}
        env = EnvironmentPreviewCatalog("unused", metadata, [asset], catalog._body)
        with patch("importer.assets.load_model_preview", side_effect=lambda *args: deepcopy(model)):
            self.assertEqual(env.pose_preview("environment://synthetic/animated", 1)["vertices"], [[11, 2, 3]])
            self.assertEqual(env.pose_preview("environment://synthetic/static")["vertices"], model["vertices"])
            for identity, frame in (("missing", 0), ("environment://synthetic/animated", 2),
                                    ("environment://synthetic/static", 1), ("environment://synthetic/static", True)):
                with self.assertRaises(ImportError):
                    env.pose_preview(identity, frame)

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
