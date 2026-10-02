"""Primary region writes qualify source tables and preserve all opaque bytes."""
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, ProtEntry
from importer.field_map import _decode
from importer.region_authoring import (MAX_REGION_RECORDS, patch_field_regions,
                                       region_authoring_options)


SCENE = "fixture"
ROW_OFFSET = 0x10050


def source_map() -> bytes:
    data = bytearray((index * 37 + 11) & 255 for index in range(0x12000))
    for kind, offset, count in ((0, 0x40, 1), (1, 0x44, 1), (2, 0x48, 1), (3, 0x50, 4)):
        struct.pack_into("<hh", data, 0x10002 + 4 * kind, offset, count)
    rows = ([14, 19, 8, 3, 7, 0x91, 0xAB, 0xEF],
            [255, 0, 255, 0, 255, 2, 3, 4],
            [0, 255, 0, 255, 0, 5, 6, 7],
            [4, 5, 9, 10, 1, 0xFE, 0x80, 0xC0])
    for index, row in enumerate(rows):
        data[ROW_OFFSET + 8 * index:ROW_OFFSET + 8 * index + 8] = bytes(row)
    return bytes(data)


def corners(index=0, **values):
    encoded = region_authoring_options(source_map(), SCENE)["records"][index]["encoded"]
    return {"region_id": f"region://{SCENE}/field-map/primary/{index:04d}",
            **{key: encoded[key] for key in ("x0", "z0", "x1", "z1")}, **values}


class RegionAuthoringTests(unittest.TestCase):
    def test_metadata_matches_importer_and_is_detached_without_payload(self):
        source = source_map()
        options = region_authoring_options(source, SCENE)
        self.assertEqual(options["source_sha256"], sha256(source).hexdigest())
        imported = _decode(SCENE, "0" * 64, ProtEntry(1, 100, 8, 36), source, None)[0]
        regions = [row for row in imported["assets"] if row["asset_kind"] == "region"]
        self.assertEqual(len(options["records"]), 4)
        for row, imported_row in zip(options["records"], regions):
            self.assertEqual(row["region_id"], imported_row["semantic_id"])
            self.assertEqual(row["encoded"], imported_row["encoded"])
            self.assertEqual(row["tile_bounds"], imported_row["tile_bounds"])
            self.assertEqual(row["byte_offset"], imported_row["source_record"]["byte_offset"])
            self.assertEqual(row["sha256"], imported_row["source_record"]["sha256"])
            self.assertEqual(row["byte_length"], 8)
        json.dumps(options)
        self.assertNotIn("raw", options)
        self.assertEqual(set(options["records"][0]),
                         {"region_id", "record_index", "byte_offset", "byte_length",
                          "sha256", "encoded", "tile_bounds"})
        options["records"][0]["encoded"]["x0"] = 99
        options["records"][0]["tile_bounds"]["x_min"] = 99
        self.assertEqual(region_authoring_options(source, SCENE)["records"][0]["encoded"]["x0"], 14)
        self.assertEqual(region_authoring_options(source, SCENE)["records"][0]["tile_bounds"]["x_min"], 8)

    def test_unchanged_empty_and_inherited_corners_are_byte_identical(self):
        source = source_map()
        digest = sha256(source).hexdigest()
        self.assertEqual(patch_field_regions(source, digest, SCENE, []), (source, []))
        self.assertEqual(patch_field_regions(source, digest, SCENE,
                         [corners(index) for index in range(4)]), (source, []))
        empty = bytearray(source)
        struct.pack_into("<hh", empty, 0x1000E, 0, 0)
        empty = bytes(empty)
        self.assertEqual(region_authoring_options(empty, SCENE)["records"], [])
        self.assertEqual(patch_field_regions(empty, sha256(empty).hexdigest(), SCENE, []), (empty, []))

    def test_only_four_corners_change_with_exact_complete_audit(self):
        source = source_map()
        edit = corners(x0=1, z0=2, x1=3, z1=4)
        result, audit = patch_field_regions(source, sha256(source).hexdigest(), SCENE, [edit])
        expected = bytearray(source)
        expected[ROW_OFFSET:ROW_OFFSET + 4] = bytes([1, 2, 3, 4])
        self.assertEqual(result, bytes(expected))
        self.assertEqual(len(result), len(source))
        self.assertEqual(result[ROW_OFFSET + 4:ROW_OFFSET + 8], bytes([7, 0x91, 0xAB, 0xEF]))
        self.assertEqual(audit, [
            {"region_id": edit["region_id"], "record_index": 0, "field": f"region.{field}",
             "byte_offset": ROW_OFFSET + delta, "before_value": source[ROW_OFFSET + delta],
             "after_value": edit[field], "scope": "source-MAP-region-bounds-only"}
            for delta, field in enumerate(("x0", "z0", "x1", "z1"))])
        self.assertEqual(patch_field_regions(result, sha256(result).hexdigest(), SCENE, [edit]), (result, []))
        restore = corners()
        self.assertEqual(patch_field_regions(result, sha256(result).hexdigest(), SCENE, [restore])[0], source)
        edits = [corners(3, x0=255, z1=0), edit]
        self.assertEqual(patch_field_regions(source, sha256(source).hexdigest(), SCENE, edits),
                         patch_field_regions(source, sha256(source).hexdigest(), SCENE, edits[::-1]))

    def test_reversed_and_degenerate_corners_preserve_source_order_and_widening(self):
        source = source_map()
        rows = region_authoring_options(source, SCENE)["records"]
        self.assertEqual(rows[0]["tile_bounds"], {"x_min": 8, "x_max": 14, "z_min": 3, "z_max": 19})
        self.assertEqual(rows[1]["tile_bounds"], {"x_min": 255, "x_max": 257, "z_min": -2, "z_max": 0})
        self.assertEqual(rows[2]["tile_bounds"], {"x_min": 0, "x_max": 2, "z_min": 253, "z_max": 255})
        edited, _ = patch_field_regions(source, sha256(source).hexdigest(), SCENE,
                                       [corners(x0=255, z0=0, x1=255, z1=0)])
        row = region_authoring_options(edited, SCENE)["records"][0]
        self.assertEqual(row["encoded"], {"x0": 255, "z0": 0, "x1": 255, "z1": 0, "type": 7})
        self.assertEqual(row["tile_bounds"], rows[1]["tile_bounds"])

    def test_invalid_edits_identity_shape_values_and_stale_hash_fail_closed(self):
        source, edit = source_map(), corners()
        digest = sha256(source).hexdigest()
        invalid = [None, {}, [None], [edit, edit], [edit] * (MAX_REGION_RECORDS + 1),
                   [{**edit, "extra": 0}], [{k: v for k, v in edit.items() if k != "x1"}]]
        for identity in (None, {}, "region://other/field-map/primary/0000",
                         "region://fixture/field-map/fallback/0000",
                         "region://fixture/field-map/primary/0", "region://fixture/field-map/primary/0004",
                         "region://fixture/field-map/primary/0000/", "trigger://fixture/field-map/primary/0000"):
            invalid.append([{**edit, "region_id": identity}])
        for field in ("x0", "z0", "x1", "z1"):
            for value in (True, -1, 256, 1.0, "1", None):
                invalid.append([{**edit, field: value}])
        for edits in invalid:
            with self.subTest(edits=str(edits)[:90]), self.assertRaises(ImportError):
                patch_field_regions(source, digest, SCENE, edits)
        for stale in (None, {}, "0" * 64, digest.upper(), digest[:-1]):
            with self.subTest(hash=stale), self.assertRaises(ImportError):
                patch_field_regions(source, stale, SCENE, [])
        for scene in (None, "", "../fixture", "é", "fixture/primary"):
            with self.subTest(scene=scene), self.assertRaises(ImportError):
                region_authoring_options(source, scene)

    def test_malformed_or_overlapping_known_tables_and_footprints_fail_closed(self):
        source = source_map()
        for invalid in (None, bytearray(source), source[:-1], source + b"\0"):
            with self.subTest(source_type=type(invalid)), self.assertRaises(ImportError):
                region_authoring_options(invalid, SCENE)
        for kind in range(4):
            for offset, count in ((-1, 0), (0, -1), (17, 1), (0x1FFF, 1), (0x20, 32767)):
                malformed = bytearray(source)
                struct.pack_into("<hh", malformed, 0x10002 + 4 * kind, offset, count)
                malformed = bytes(malformed)
                with self.subTest(kind=kind, bounds=(offset, count)), self.assertRaises(ImportError):
                    region_authoring_options(malformed, SCENE)
                with self.assertRaises(ImportError):
                    patch_field_regions(malformed, sha256(malformed).hexdigest(), SCENE, [])
        for kind in range(3):
            ambiguous = bytearray(source)
            struct.pack_into("<hh", ambiguous, 0x10002 + 4 * kind, 0x50, 1)
            with self.subTest(overlapping_kind=kind), self.assertRaisesRegex(ImportError, "overlap"):
                region_authoring_options(bytes(ambiguous), SCENE)
        # Even two unexposed non-region tables must be mutually disjoint.
        ambiguous = bytearray(source)
        struct.pack_into("<hh", ambiguous, 0x1000A, 0x44, 1)
        with self.assertRaisesRegex(ImportError, "overlap"):
            region_authoring_options(bytes(ambiguous), SCENE)

    def test_physical_row_limit_is_accepted_without_truncation(self):
        source = bytearray(0x12000)
        struct.pack_into("<hh", source, 0x1000E, 18, MAX_REGION_RECORDS)
        source = bytes(source)
        options = region_authoring_options(source, SCENE)
        self.assertEqual(len(options["records"]), MAX_REGION_RECORDS)
        last = options["records"][-1]
        edit = {"region_id": last["region_id"], "x0": 255, "z0": 0, "x1": 255, "z1": 0}
        result, audit = patch_field_regions(source, options["source_sha256"], SCENE, [edit])
        self.assertEqual([row["byte_offset"] for row in audit], [last["byte_offset"], last["byte_offset"] + 2])
        self.assertEqual(len(result), 0x12000)
        overflow = bytearray(source)
        struct.pack_into("<h", overflow, 0x10010, MAX_REGION_RECORDS + 1)
        with self.assertRaises(ImportError):
            region_authoring_options(bytes(overflow), SCENE)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailRegionAuthoringTests(unittest.TestCase):
    def test_town01_fresh_source_and_one_corner_only(self):
        from importer.field_map import load_field_map_catalog
        from importer.pipeline import _bounded_scene_range, _disc_context
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc) as (_, _, mapping, archive):
            start, _ = _bounded_scene_range(archive, mapping, "town01")
            source = archive.read_entry(archive.entry(start), extended=True)
            catalog = load_field_map_catalog(disc, "town01")
        options = region_authoring_options(source, "town01")
        imported = [row for row in catalog["assets"] if row["asset_kind"] == "region"]
        self.assertEqual(len(options["records"]), 14)
        self.assertEqual(len(imported), 14)
        for row, imported_row in zip(options["records"], imported):
            self.assertEqual(row["region_id"], imported_row["semantic_id"])
            self.assertEqual(row["sha256"], imported_row["source_record"]["sha256"])
            self.assertEqual(row["encoded"], imported_row["encoded"])
            self.assertEqual(row["tile_bounds"], imported_row["tile_bounds"])
        row = options["records"][0]
        edit = {"region_id": row["region_id"],
                **{key: row["encoded"][key] for key in ("x0", "z0", "x1", "z1")}}
        self.assertEqual(patch_field_regions(source, options["source_sha256"], "town01", [edit]), (source, []))
        edit["x0"] = (edit["x0"] + 1) % 256
        result, audit = patch_field_regions(source, options["source_sha256"], "town01", [edit])
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["byte_offset"], row["byte_offset"])
        self.assertEqual([index for index, pair in enumerate(zip(source, result)) if pair[0] != pair[1]],
                         [row["byte_offset"]])


if __name__ == "__main__":
    unittest.main()
