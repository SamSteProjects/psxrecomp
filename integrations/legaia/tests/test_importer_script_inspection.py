"""Meaningful bounded parser regressions and opt-in actual MAN inspection."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.script_inspection import decode_inline_message, inspect_record, inspect_actor_script


def covered_bytes(report, start, length):
    coverage = [0] * length
    for row in report["instructions"] + report["dialogues"] + report["opaque_regions"]:
        for offset in range(row["pc"], row["pc"] + row["length"]):
            coverage[offset] += 1
    return coverage[start:]


class ScriptInspectionTests(unittest.TestCase):
    def test_substitution_zero_operand_does_not_terminate_message(self):
        data = b"\x1f\xc1\x00, hello!\0"
        message = decode_inline_message(data, 0, 100)
        self.assertEqual(message["text"], "{character_name:0}, hello!")
        self.assertEqual(message["length"], len(data))
        self.assertEqual(message["tokens"][0], {"pc": 1, "byte_offset": 101, "length": 2,
                          "raw_hex": "c100", "kind": "substitution", "substitution": "character_name", "index": 0})

    def test_aliases_controls_and_unknown_font_tokens_preserve_raw_bytes(self):
        raw = b"\x1f\x5e\x2f\xce\x03\xffA\xcfB\xc0\x00\x80\xa0\0"
        row = decode_inline_message(raw, 0)
        self.assertEqual(row["text"], "{spacing:2}{spacing:3}AB{wide_glyph:c0:00}{control:80}{glyph:a0}")
        self.assertEqual(bytes.fromhex(row["raw_hex"]), raw)
        self.assertEqual([t["kind"] for t in row["tokens"]],
                         ["spacing", "spacing", "escaped_glyph", "escaped_glyph", "wide_glyph", "pager_control", "glyph"])

    def test_message_opcode_lookalikes_and_inline_data_are_not_disassembled(self):
        message = b"\x1f!#$%&?'?\0"
        # INLINE_DATA length 4 contains a fake text lead and two apparent ops.
        data = b"\x40\x04\x1fA\x31\x02" + message + b"\x21\x26\xfe\xff"
        report = inspect_record(data, 0)
        self.assertEqual([r["mnemonic"] for r in report["instructions"]], ["INLINE_DATA", "NOP", "JMP_REL"])
        self.assertEqual([r["text"] for r in report["dialogues"]], ["!#$%&?'?"])
        self.assertEqual(report["status"], "decoded_supported_paths")
        self.assertEqual(covered_bytes(report, 0, len(data)), [1] * len(data))

    def test_branch_graph_wraps_backwards_and_visits_both_flag_paths(self):
        # SYSFLAG_TEST at0: set target=0+2+5=7; clear falls through4.
        # The clear branch's JMP at4 targets11, the shared parking loop.
        data = b"\x71\x46\x05\0\x26\x06\0\x1fHi\0\x21\x26\xfe\xff"
        report = inspect_record(data, 0)
        self.assertEqual(report["instructions"][0]["successors"],
                         [{"pc": 7, "condition": "flag_set"}, {"pc": 4, "condition": "flag_clear"}])
        self.assertEqual(report["instructions"][-1]["successors"], [{"pc": 11, "condition": "unconditional"}])
        self.assertEqual([r["text"] for r in report["dialogues"]], ["Hi"])
        self.assertFalse(report["stops"])

    def test_unknown_width_stops_without_scanning_later_text(self):
        data = b"\x25\x4c\x80\x1fFake text\0"
        report = inspect_record(data, 0)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["instructions"]), 1)
        self.assertEqual(report["dialogues"], [])
        self.assertEqual(report["opaque_regions"][0]["pc"], 1)
        self.assertIn("unsupported MENU_CTRL", report["stops"][0]["reason"])
        self.assertEqual(covered_bytes(report, 0, len(data)), [1] * len(data))

    def test_conflicting_target_boundaries_fail_closed(self):
        # Branch into the second byte of a known instruction at4.
        data = b"\x71\x46\x03\0\x31\x02\x21\x26\xfe\xff"
        report = inspect_record(data, 0)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["instructions"], [])
        self.assertEqual(report["dialogues"], [])
        self.assertEqual(report["opaque_regions"][0]["length"], len(data))

    def test_truncation_bounds_and_cross_context_width(self):
        for data in (b"\x1f\xc1", b"\x1funterminated"):
            with self.assertRaises(ImportError):
                decode_inline_message(data, 0)
        for data in (b"\xa2", b"\x22", b"\x4b\xff\0"):
            self.assertEqual(inspect_record(data, 0)["status"], "partial")
        report = inspect_record(b"\xb1\x03\x02", 0)
        self.assertEqual(report["instructions"][0]["target_context"], 3)
        self.assertEqual(report["instructions"][0]["length"], 3)
        for data, start in ((bytes(65537), 0), (b"abc", 4), (b"abc", True)):
            with self.assertRaises(ImportError):
                inspect_record(data, start)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailScriptInspectionTests(unittest.TestCase):
    def test_real_dialogue_savepoint_unknowns_and_source_preservation(self):
        from importer.pipeline import _disc_context, import_scene
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc):
            scene = import_scene(disc, "town01")
            actor = next(a for a in scene["actors"] if a["semantic_id"].endswith("/0049"))
            original = deepcopy(actor)
            report = inspect_actor_script(disc, "town01", actor)
            self.assertTrue(report["read_only"])
            self.assertEqual(report["record"]["byte_offset"], 27081)
            self.assertEqual(report["record"]["byte_length"], 255)
            self.assertEqual(report["record"]["script_offset"], 21)
            self.assertEqual((len(report["instructions"]), len(report["dialogues"])), (23, 7))
            texts = [dialogue["text"] for dialogue in report["dialogues"]]
            self.assertEqual([len(text) for text in texts], [30, 18, 29, 23, 20, 14, 26])
            self.assertEqual(hashlib.sha256("\n".join(texts).encode()).hexdigest(),
                             "e007ea53f1a298efd808b648fa8e241dd1960a5341e5fde45c4ec66c79bf723f")
            first_token = report["dialogues"][0]["tokens"][0]
            self.assertEqual(first_token["kind"], "substitution")
            self.assertEqual(first_token["substitution"], "character_name")
            self.assertEqual(first_token["index"], 0)
            self.assertEqual(report["stops"], [])
            raw = bytes.fromhex(report["record"]["raw_hex"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), report["record"]["sha256"])
            self.assertEqual(covered_bytes(report, 21, 255), [1] * 234)
            self.assertEqual(actor, original)
            actor["source_record"]["byte_offset"] += 1
            with self.assertRaisesRegex(ImportError, "provenance"):
                inspect_actor_script(disc, "town01", actor)
            savepoint = next(a for a in scene["actors"] if a["semantic_id"].endswith("/0052"))
            result = inspect_actor_script(disc, "town01", savepoint)
            self.assertEqual(result["status"], "decoded_supported_paths")
            self.assertEqual((len(result["instructions"]), len(result["dialogues"])), (11, 0))
            debug = next(a for a in scene["actors"] if a["semantic_id"].endswith("/0001"))
            result = inspect_actor_script(disc, "town01", debug)
            self.assertEqual(result["status"], "partial")
            self.assertIn("0x29", result["stops"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
