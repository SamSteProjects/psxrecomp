"""Metadata-only resource identities and conservative scoped script references."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, validate_metadata_only
from importer.script_catalog import _catalog, load_script_asset_catalog
from integrations.legaia.tests.test_importer_dialogue_authoring import fixture


def forbidden_fields(value):
    """The generic metadata validator alone also permits text/hex strings."""
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"text", "raw_hex", "encoded_hex", "tokens", "scene_name_bytes_hex",
                       "rgba", "stp", "payload", "raw_bytes"}:
                found.add(key)
            found.update(forbidden_fields(child))
    elif isinstance(value, list):
        for child in value:
            found.update(forbidden_fields(child))
    return found


def catalog(script):
    _, man = fixture(script)
    return _catalog(man, "fixture", {"synthetic": True}, {"town02"})


class ScriptAssetCatalogTests(unittest.TestCase):
    def test_flag_word_branches_join_evidenced_banks_without_live_values(self):
        result = catalog(b"\x4c\xa0\x03\x0a\0\x4c\xa1\xf3\x0f\0\x4c\xa2\x05\x14\0")
        refs = result["assets"][0]["flag_references"]
        self.assertEqual([r["bank"] for r in refs], ["context", "local", "global"])
        self.assertEqual([r["index"] for r in refs], [3, 19, 5])
        self.assertEqual(refs[1]["status"], "bank_width_unresolved")
        self.assertTrue(all(r["operation"] == "test" and r["runtime_value"] is None for r in refs))
        self.assertEqual(result["flag_reference_count"], 3)

    def test_menu_metadata_has_no_labels_and_preserves_bounded_source(self):
        result = catalog(b"\x27\x10\0\x20\0\x1fPrivateOne\0\x1fPrivateTwo\0")
        script = next(a for a in result["assets"] if a["asset_kind"] == "script" and a["menu_count"])
        self.assertEqual(script["menu_count"], 1)
        menu = script["menus"][0]
        self.assertEqual(menu["option_count"], 2)
        self.assertEqual(menu["pc"], 5)
        self.assertEqual(len(menu["sha256"]), 64)
        self.assertNotIn('PrivateOne', json.dumps(result))
        self.assertNotIn('PrivateTwo', json.dumps(result))
        self.assertEqual(forbidden_fields(result), set())
        self.assertEqual(script["status"], "partial")

    def test_partition_two_source_bounds_and_unknown_tail_are_preserved(self):
        _, original = fixture()
        region = 0x2B + 12
        section = int.from_bytes(original[0x28:0x2B], "little")
        # Separate P2 record, with a real prefix and a known MES before a halt.
        record = bytes(4) + b"\x1fHi\0\x2a\x2b\x01"
        man = bytearray(original[:region + section] + record + original[region + section:])
        man[0x34:0x37] = section.to_bytes(3, "little")
        man[0x28:0x2B] = (section + len(record)).to_bytes(3, "little")
        result = _catalog(bytes(man), "fixture", {"synthetic": True}, set())
        p2 = next(a for a in result["assets"] if a["asset_kind"] == "script" and a["partition"] == 2)
        self.assertEqual(p2["source_record"]["byte_offset"], region + section)
        self.assertEqual(p2["source_record"]["byte_length"], len(record))
        self.assertEqual(p2["entry_pc"], 4)
        self.assertEqual((p2["status"], p2["dialogue_count"]), ("partial", 1))
        self.assertEqual(p2["flag_references"], [])
        self.assertEqual(p2["stops"][0]["kind"], "known_instruction_unresolved_control_flow")
        self.assertEqual(forbidden_fields(result), set())

    def test_extended_context_width_system_selector_and_extra_flags_remain_scoped(self):
        # LFLAG ordinary / extended; GFLAG; extended CFLAG; ordinary/extended
        # system selectors; extra-flags conditional with both successors equal.
        result = catalog(b"\x2b\x02\xab\x07\x12\x2e\x03\xb1\x08\x05"
                         b"\x51\x23\xd0\x09\x44\x42\x00\x23\x02\x00")
        script = result["assets"][0]
        refs = script["flag_references"]
        self.assertEqual(len(refs), 7)
        self.assertEqual([r["bank"] for r in refs], ["local", "local", "global", "context", "system", "system", "extra"])
        self.assertEqual([r["index"] for r in refs], [2, 18, 3, 5, 0x123, 0x8044, 3])
        self.assertEqual(refs[1]["extended_target"], 7)
        self.assertEqual(refs[1]["context_resolution"], "extended_target_unresolved")
        self.assertEqual(refs[1]["status"], "bank_width_unresolved")
        self.assertEqual(refs[3]["extended_target"], 8)
        self.assertEqual(refs[4]["index_semantics"], "encoded_selector_not_resolved_runtime_bit")
        self.assertEqual(refs[6]["scope"], "host_extra_flags")
        self.assertTrue(all(r["runtime_value"] is None for r in refs))
        self.assertEqual(script["status"], "decoded_supported_paths")

    def test_named_transition_preserves_encoded_entry_and_rejects_unclean_name(self):
        def transition(name):
            return catalog(b"\x3f\x34\x12" + bytes([len(name)]) + name + b"\x01\x82\x03")
        known = transition(b"town02")["assets"][0]["transitions"][0]
        self.assertEqual(known["target_scene_name"], "town02")
        self.assertTrue(known["target_in_scene_index"])
        self.assertEqual(known["status"], "encoded_named_reference")
        self.assertEqual((known["entry_x_encoded"], known["entry_z_encoded"], known["direction_encoded"]), (1, 130, 3))
        self.assertEqual(known["reachability"], "not_evaluated")
        absent = transition(b"unknown1")["assets"][0]["transitions"][0]
        self.assertFalse(absent["target_in_scene_index"])
        for name in (b"", b"town02\0", b"Town02", b"a" * 13, b"../town02"):
            ref = transition(name)["assets"][0]["transitions"][0]
            self.assertEqual(ref["status"], "unsupported_name_encoding")
            self.assertIsNone(ref["target_scene_name"])

    def test_dialogue_payload_and_unknown_regions_are_not_resource_scanned(self):
        # Apparent flag/opcode bytes inside MES are glyphs. Unsupported menu
        # width prevents further decoding, including the apparent named warp.
        result = catalog(b"\x1f+Q#\0\x4c\x80\x3f\0\0\x06town02\1\2\3")
        self.assertEqual((result["script_count"], result["dialogue_count"]), (2, 1))
        self.assertEqual((result["flag_reference_count"], result["transition_count"]), (0, 0))
        script, message, aliased = result["assets"]
        self.assertEqual(aliased["status"], "unavailable")
        self.assertIsNone(aliased["source_record"]["byte_offset"])
        self.assertIn("aliased", aliased["stops"][0]["reason"])
        self.assertEqual(script["status"], "partial")
        self.assertGreater(script["opaque_byte_count"], 0)
        self.assertEqual(script["stop_count"], 1)
        self.assertEqual(message["semantic_id"], "script://fixture/actors/man-p1/0001/dialogue/0005")
        self.assertEqual(message["script_id"], script["semantic_id"])
        self.assertEqual(message["text_length"], 3)
        self.assertEqual(message["token_count"], 3)
        self.assertEqual(message["script_status"], "partial")
        self.assertEqual(forbidden_fields(result), set())
        validate_metadata_only(result)
        json.dumps(result)
        with patch("importer.script_catalog.MAX_ASSETS", 1):
            with self.assertRaisesRegex(ImportError, "asset count"):
                catalog(b"\x1fHi\0")


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailScriptAssetCatalogTests(unittest.TestCase):
    def test_actual_town01_counts_ids_partial_coverage_and_payload_free_records(self):
        from importer.pipeline import _disc_context
        with _disc_context(os.environ["LEGAIA_DISC_BIN"]):
            result = load_script_asset_catalog(os.environ["LEGAIA_DISC_BIN"], "town01")
            # Verified field-state continuations expose ten more segments in
            # actors 25-30 and 36; their unknown tails still remain partial.
            # Acquire coverage reveals actor 40's conflicting target boundary;
            # its entire ambiguous graph must be withdrawn.
            # Flag-word branches expose five bounded P2[4] dialogue segments.
            self.assertEqual((result["actor_count"], result["script_count"], result["dialogue_count"]), (52, 91, 426))
            self.assertEqual((result["asset_count"], result["partial_script_count"]), (517, 60))
            self.assertEqual((result["flag_reference_count"], result["transition_count"]), (1145, 1))
            assets = {a["semantic_id"]: a for a in result["assets"]}
            self.assertEqual(result["partition_two_script_count"], 39)
            p2 = assets["script://town01/scripts/man-p2/0037"]
            self.assertEqual((p2["partition"], p2["dialogue_count"]), (2, 1))
            self.assertIsNone(p2["actor_semantic_id"])
            self.assertEqual(p2["owner_semantic_id"], "scene://town01/scripts/man-p2/0037")
            opening = assets["script://town01/scripts/man-p2/0003"]
            self.assertEqual((opening["status"], opening["dialogue_count"]), ("partial", 8))
            self.assertEqual(assets["script://town01/actors/man-p1/0040"]["instruction_count"], 0)
            self.assertEqual(len(assets), result["asset_count"])
            script_id = "script://town01/actors/man-p1/0049"
            script = assets[script_id]
            self.assertEqual((script["instruction_count"], script["dialogue_count"], script["opaque_byte_count"]), (23, 7, 4))
            self.assertEqual(script["status"], "partial")
            segment = assets[script_id + "/dialogue/0050"]
            self.assertEqual(segment["pc"], 0x50)
            self.assertEqual(segment["text_length"], 30)
            self.assertEqual(assets["script://town01/actors/man-p1/0001"]["status"], "partial")
            self.assertEqual(forbidden_fields(result), set())
            self.assertEqual(result, load_script_asset_catalog(os.environ["LEGAIA_DISC_BIN"], "town01"))


if __name__ == "__main__":
    unittest.main()
