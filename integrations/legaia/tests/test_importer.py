from __future__ import annotations

import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
from dataclasses import replace

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INTEGRATION_ROOT))

from importer.core import (  # noqa: E402
    ImportError,
    ManActor,
    ParsedMan,
    TmdRecord,
    canonical_json,
    claim,
    normalize_claims,
    parse_cdname,
    parse_man,
    parse_prot_bytes,
    parse_scene_table,
    scene_range,
    scan_tmds,
    stable_actor_id,
    stable_model_asset_id,
    validate_metadata_only,
    decompress_lzs,
)
from importer.pipeline import import_scene, project_metadata  # noqa: E402


def put_u24(buffer: bytearray, offset: int, value: int) -> None:
    buffer[offset : offset + 3] = value.to_bytes(3, "little")


def synthetic_man() -> bytes:
    counts = (1, 3, 0)  # one P0, P1 controller + two actors, no P2
    data_region = 0x2B + sum(counts) * 3
    section_relative = 40
    total_size = data_region + section_relative + 6 * 3
    data = bytearray(total_size)
    struct.pack_into("<hhh", data, 0x22, *counts)
    put_u24(data, 0x28, section_relative)
    for index, relative in enumerate((0, 8, 20, 32)):
        put_u24(data, 0x2B + index * 3, relative)
    # P1 record 1: one local, model 4, animation 2, X tile 5, Z tile 6 + half-tile bit.
    actor1 = data_region + 20
    data[actor1 : actor1 + 8] = bytes((1, 0, 0, 4, 2, 5, 0x86, 0))
    # P1 record 2: no locals, special model F1, no animation, X/Z tiles 1/2.
    actor2 = data_region + 32
    data[actor2 : actor2 + 8] = bytes((0, 0xF1, 0, 1, 2, 0, 0, 0))
    # Six empty, chained sections.
    section = data_region + section_relative
    for _ in range(6):
        put_u24(data, section, 0)
        section += 3
    return bytes(data)


def synthetic_prot() -> bytes:
    data = bytearray(10 * 0x800)
    # file_num_minus_1=1 -> one entry; one 0x800-byte header sector.
    struct.pack_into("<i", data, 4, 1)
    # TOC begins at +8; its first word is also header_sectors.
    toc = [1, 0, 2, 5, 0, 4]
    struct.pack_into(f"<{len(toc)}I", data, 8, *toc)
    return bytes(data)


def projected(parsed: ParsedMan | None = None) -> dict:
    parsed = parsed or parse_man(synthetic_man())
    scene_models = tuple(
        TmdRecord("scene_tmd", index, 4, "decoded_lzs_section", index * 100, 72, 1000, 1, 2, 64)
        for index in range(5)
    )
    global_models = tuple(
        TmdRecord("global_special", index, 874, "decoded_tmd_pack_slot", index * 80, 72, 500, 1, 0, 32, index, 72)
        for index in range(5)
    )
    return project_metadata(
        disc_digest="11" * 32,
        scene="town01",
        bundle_entry=3,
        table_offset=0,
        descriptor_index=1,
        descriptor_offset=128,
        descriptor_size=len(synthetic_man()),
        compressed_consumed=99,
        parsed_man=parsed,
        scene_models=scene_models,
        global_models=global_models,
    )


class ImporterUnitTests(unittest.TestCase):
    def test_stable_semantic_actor_id(self) -> None:
        self.assertEqual(stable_actor_id("town01", 1, 7), "scene://town01/actors/man-p1/0007")
        self.assertEqual(stable_actor_id("town01", 1, 7), stable_actor_id("town01", 1, 7))
        with self.assertRaises(ImportError):
            stable_actor_id("Town 01", 1, 7)

    def test_stable_semantic_model_asset_id(self) -> None:
        self.assertEqual(
            stable_model_asset_id("town01", "scene_tmd", 4),
            "asset://town01/models/scene-tmd/0004",
        )
        self.assertEqual(
            stable_model_asset_id("town01", "global_special", 1),
            "asset://legaia/models/global-special/00f1",
        )
        with self.assertRaises(ImportError):
            stable_model_asset_id("town01", "global_special", 16)

    def test_claim_serialization_round_trip(self) -> None:
        item = claim("x", {"n": 3}, "confirmed", [{"kind": "parser_span"}], {"record": 1}, "synthetic")
        self.assertEqual(json.loads(canonical_json(item)), item)

    def test_deterministic_json(self) -> None:
        first = canonical_json(projected(), pretty=True)
        second = canonical_json(projected(), pretty=True)
        self.assertEqual(first, second)
        self.assertNotIn("timestamp", first.lower())

    def test_asset_order_shared_references_and_unused_assets(self) -> None:
        base = parse_man(synthetic_man())
        shared = ParsedMan(base.partition_counts, (base.actors[0], replace(base.actors[1], model_index=4)))
        output = projected(shared)
        model_ids = [model["semantic_id"] for model in output["assets"]["models"]]
        self.assertEqual(model_ids[:2], [
            "asset://town01/models/scene-tmd/0000",
            "asset://town01/models/scene-tmd/0001",
        ])
        self.assertEqual(model_ids[-1], "asset://legaia/models/global-special/00f4")
        refs = [actor["model_reference"]["asset_semantic_id"] for actor in output["actors"]]
        self.assertEqual(refs, ["asset://town01/models/scene-tmd/0004"] * 2)
        self.assertEqual(len(set(model_ids) - set(refs)), 9)
        self.assertTrue(all(model["aliases"] == [] for model in output["assets"]["models"]))

    def test_unknown_out_of_range_special_model_is_not_fabricated(self) -> None:
        base = parse_man(synthetic_man())
        invalid = ParsedMan(base.partition_counts, (replace(base.actors[0], model_index=0xFF),))
        actor = projected(invalid)["actors"][0]
        self.assertEqual(actor["model_reference"]["normalized_pool_index"], 15)
        self.assertIsNone(actor["model_reference"]["asset_semantic_id"])
        self.assertEqual(actor["model_reference"]["resolution_status"], "pool_index_out_of_bounds")
        claim_by_property = {item["property"]: item for item in actor["claims"]}
        self.assertEqual(claim_by_property["model_reference.referenced_asset_record"]["confidence"], "unknown")

    def test_synthetic_prot_table(self) -> None:
        entries = parse_prot_bytes(synthetic_prot())
        self.assertEqual(len(entries), 1)
        self.assertEqual((entries[0].index, entries[0].start_lba, entries[0].size_sectors), (0, 2, 3))

    def test_cdname_scene_resolution(self) -> None:
        mapping = parse_cdname("// synthetic\n#define town01 5\n#define next_scene 9\n")
        self.assertEqual(scene_range(mapping, "town01"), (3, 7))
        with self.assertRaisesRegex(ImportError, "absent scene"):
            scene_range(mapping, "missing")

    def test_synthetic_man_actor_records(self) -> None:
        parsed = parse_man(synthetic_man())
        self.assertEqual(parsed.partition_counts, (1, 3, 0))
        self.assertEqual(len(parsed.actors), 2)
        self.assertEqual(parsed.actors[0].model_index, 4)
        self.assertEqual((parsed.actors[0].world_x, parsed.actors[0].world_z), (704, 896))
        self.assertEqual(parsed.actors[1].model_index, 0xF1)

    def test_scene_table_and_lzs_use_synthetic_data(self) -> None:
        table = bytearray(0x90)
        struct.pack_into("<II", table, 0, 6, 0)
        types = (2, 3, 4, 5, 6, 7)
        for index, type_byte in enumerate(types):
            offset = 0x38 if index == 0 else 0x40 + index * 8
            struct.pack_into("<II", table, 8 + index * 8, type_byte << 24 | 8, offset)
        parsed = parse_scene_table(bytes(table), 3)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.descriptors[1].type_byte, 3)
        # One all-literal control byte followed by eight non-proprietary bytes.
        decoded, consumed = decompress_lzs(b"\xffSYNTHETC", 8)
        self.assertEqual(decoded, b"SYNTHETC")
        self.assertEqual(consumed, 9)

    def test_synthetic_tmd_scan_is_bounded(self) -> None:
        tmd = bytearray(72)
        struct.pack_into("<III", tmd, 0, 0x80000002, 0, 1)
        struct.pack_into("<IIIIIII", tmd, 12, 28, 4, 0, 0, 28, 0, 0x00808080)
        hits = scan_tmds(bytes(tmd))
        self.assertEqual(hits, ((0, 72, 1),))
        self.assertEqual(scan_tmds(bytes(tmd[:-1])), ())

    def test_truncated_man_and_invalid_offsets(self) -> None:
        with self.assertRaisesRegex(ImportError, "header is truncated"):
            parse_man(b"\0" * 10)
        damaged = bytearray(synthetic_man())
        data_region = 0x2B + 4 * 3
        put_u24(damaged, 0x2B + 2 * 3, len(damaged) + 10 - data_region)
        with self.assertRaisesRegex(ImportError, "record 1 exceeds"):
            parse_man(bytes(damaged))

    def test_unsupported_scene_and_disc(self) -> None:
        with self.assertRaisesRegex(ImportError, "currently supports only town01"):
            import_scene("does-not-matter.bin", "town02")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not-a-disc.bin"
            path.write_bytes(b"synthetic")
            with self.assertRaisesRegex(ImportError, "Mode 2/2352"):
                import_scene(path, "town01")

    def test_duplicate_and_contradictory_claims(self) -> None:
        one = claim("position", 1, "confirmed", [], {}, "one")
        same = dict(one)
        other = claim("position", 2, "tentative", [], {}, "two")
        normalized = normalize_claims([one, same, other])
        self.assertEqual(len(normalized), 2)
        self.assertEqual({item["confidence"] for item in normalized}, {"contradictory"})
        model_one = claim("model_asset.source_record", {"record": 1}, "confirmed", [], {}, "one")
        model_other = claim("model_asset.source_record", {"record": 2}, "tentative", [], {}, "two")
        model_claims = normalize_claims([model_one, model_other])
        self.assertEqual({item["confidence"] for item in model_claims}, {"contradictory"})

    def test_metadata_only_output(self) -> None:
        output = projected()
        validate_metadata_only(output)
        self.assertTrue(output["actors"])
        self.assertEqual(output["schema_version"], "legaia.scene-import.v2")
        self.assertEqual(len(output["assets"]["models"]), 10)
        self.assertEqual(
            output["actors"][0]["model_reference"]["asset_semantic_id"],
            "asset://town01/models/scene-tmd/0004",
        )
        self.assertEqual(
            output["actors"][1]["model_reference"]["asset_semantic_id"],
            "asset://legaia/models/global-special/00f1",
        )
        with self.assertRaisesRegex(ImportError, "forbidden field"):
            validate_metadata_only({"payload": "not allowed"})
        with self.assertRaisesRegex(ImportError, "binary value"):
            validate_metadata_only({"safe": b"binary"})

    def test_v2_schema_accepts_projected_metadata(self) -> None:
        schema_path = INTEGRATION_ROOT / "schemas" / "town01-import.v2.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(projected(), schema)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "LEGAIA_DISC_BIN is not set")
class Town01DiscIntegrationTests(unittest.TestCase):
    def test_town01_metadata_is_stable_and_bounded(self) -> None:
        path = Path(os.environ["LEGAIA_DISC_BIN"])
        first = import_scene(path, "town01")
        second = import_scene(path, "town01")
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertGreater(len(first["actors"]), 0)
        ids = [actor["semantic_id"] for actor in first["actors"]]
        self.assertEqual(len(ids), len(set(ids)))
        model_ids = [asset["semantic_id"] for asset in first["assets"]["models"]]
        self.assertEqual(len(model_ids), len(set(model_ids)))
        for actor in first["actors"]:
            source = actor["source_record"]
            self.assertGreater(source["byte_length"], 0)
            self.assertLessEqual(source["byte_offset"] + source["byte_length"], source["containing_decoded_size"])
            self.assertEqual(actor["model_reference"]["resolution_status"], "resolved")
            self.assertIn(actor["model_reference"]["asset_semantic_id"], model_ids)
        for asset in first["assets"]["models"]:
            source = asset["source_record"]
            self.assertGreater(source["byte_length"], 0)
            self.assertLessEqual(source["byte_offset"] + source["byte_length"], source["containing_size"])
        validate_metadata_only(first)


if __name__ == "__main__":
    unittest.main()
