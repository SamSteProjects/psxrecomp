"""Synthetic boundary-preserving MES edits plus opt-in private retail evidence."""
from copy import deepcopy
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, decompress_lzs, parse_man
from importer.dialogue_authoring import (DialogueAuthoringContext, load_dialogue_authoring_context,
                                         validate_dialogue_text, validate_run_id)
from importer.serialization import patch_man_positions, serialize_man_decoded

ACTOR = "scene://fixture/actors/man-p1/0001"


def literals(data):
    return b"".join(b"\xff" + data[n:n + 8] for n in range(0, len(data), 8))


def fixture(script=b"\x1fHello\0", alias=False):
    counts = (1, 2, 1)
    region = 0x2B + 3 * sum(counts)
    record = b"\0\x01\x01\x02\x03" + script
    section = 8 + len(record)
    man = bytearray(region + section + 18)
    struct.pack_into("<hhh", man, 0x22, *counts)
    man[0x28:0x2B] = section.to_bytes(3, "little")
    # P2 normally aliases the P0 controller, and optionally the editable actor.
    for index, offset in enumerate((0, 4, 8, 8 if alias else 0)):
        man[0x2B + index*3:0x2E + index*3] = offset.to_bytes(3, "little")
    man[region + 8:region + section] = record
    man = bytes(man)
    return DialogueAuthoringContext("fixture", man, literals(man), {"synthetic": True}), man


class DialogueAuthoringTests(unittest.TestCase):
    def test_control_and_substitution_boundaries_split_runs_and_remain_exact(self):
        script = b"\x1f\xc1\0Hello\x5e\x2dWorld\xffA\xc2\0End\x80ok\0"
        context, original = fixture(script)
        options = context.options(ACTOR)
        self.assertTrue(options["supported"])
        self.assertEqual([r["text"] for r in options["runs"]], ["Hello", "World", "End", "ok"])
        first, second, _, last = options["runs"]
        changed, audit = context.patch({first["semantic_id"]: "Bye", last["semantic_id"]: ""}, original=original)
        self.assertEqual(len(changed), len(original))
        self.assertEqual([a["padding_bytes"] for a in audit], [2, 2])
        allowed = {n for a in audit for n in range(a["decoded_byte_offset"], a["decoded_byte_offset"] + a["byte_length"])}
        self.assertTrue(all(a == b or n in allowed for n, (a, b) in enumerate(zip(original, changed))))
        self.assertEqual(changed[first["decoded_byte_offset"]:first["decoded_byte_offset"] + 5], b"Bye  ")
        self.assertEqual(parse_man(changed), parse_man(original))
        # Mutating returned options must not change the verified source intervals.
        first["decoded_byte_offset"] = 0
        options["runs"].clear()
        self.assertEqual(context.options(ACTOR)["runs"][1], second)
        self.assertEqual(context.patch({})[0], original)

    def test_exact_noop_and_combined_header_edits_compress_once(self):
        context, original = fixture()
        run = context.options(ACTOR)["runs"][0]
        self.assertEqual(context.patch({run["semantic_id"]: run["text"]}), (original, []))
        changed, audit = context.patch({run["semantic_id"]: "Ready"})
        combined, positions = patch_man_positions(changed, "fixture", {1: {"x": 704}})
        stream, _ = serialize_man_decoded(literals(original), len(original), combined, "fixture")
        self.assertEqual(decompress_lzs(stream, len(original))[0], combined)
        self.assertEqual(len(stream), len(literals(original)))
        self.assertEqual(len(audit), 1)
        self.assertEqual(len(positions), 1)
        with self.assertRaisesRegex(ImportError, "baseline"):
            context.patch({}, original=combined)

    def test_invalid_text_ids_capacity_and_late_failure_are_transactional(self):
        context, original = fixture()
        run = context.options(ACTOR)["runs"][0]
        for text in (None, True, {}, "a\nb", "^", "\x1f", "\x7f", "caf\u00e9", "a" * 4097):
            with self.subTest(text_type=type(text).__name__), self.assertRaises(ImportError):
                validate_dialogue_text(text)
        self.assertEqual(validate_dialogue_text(""), "")
        with self.assertRaisesRegex(ImportError, "at most 5"):
            context.patch({run["semantic_id"]: "longer"})
        for identifier in (None, "../run", run["semantic_id"].replace("0001", "0002"),
                           run["semantic_id"][:-4] + "FFFF", run["semantic_id"][:-4] + "0000"):
            with self.subTest(identifier=identifier), self.assertRaises(ImportError):
                context.patch({run["semantic_id"]: "Ready", identifier: "No"})
            self.assertEqual(context.patch({})[0], original)
        with self.assertRaises(ImportError):
            validate_run_id("scene://other/actors/man-p1/0001", run["semantic_id"])

    def test_unknown_graphs_and_cross_partition_aliases_fail_closed(self):
        for script in (b"\x1fHello\0\x4c\x80", b"\x1funterminated",
                       b"\x71\x46\x03\0\x31\x02\x21\x26\xfe\xff"):
            context, original = fixture(script)
            options = context.options(ACTOR)
            self.assertFalse(options["supported"])
            self.assertEqual(options["runs"], [])
            self.assertEqual(context.patch({})[0], original)
        context, _ = fixture(alias=True)
        self.assertFalse(context.options(ACTOR)["supported"])
        self.assertIn("non-aliased", context.options(ACTOR)["reason"])

    def test_unvisited_tail_stays_opaque_and_uneditable(self):
        context, original = fixture(b"\x1fHello\0\x26\xff\xff\x1fOpaque\0")
        options = context.options(ACTOR)
        self.assertTrue(options["supported"])
        self.assertEqual(options["graph_status"], "partial")
        self.assertEqual(len(options["runs"]), 1)
        run = options["runs"][0]
        changed, _ = context.patch({run["semantic_id"]: "Ready"})
        self.assertEqual(changed[-26:], original[-26:])
        # Even a structurally plausible glyph PC is not accepted without a proved span.
        invented = run["semantic_id"].rsplit("/dialogue/", 1)[0] + "/dialogue/000f/run/0010"
        with self.assertRaisesRegex(ImportError, "supported span"):
            context.patch({invented: "No"})


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailDialogueAuthoringTests(unittest.TestCase):
    def test_first_real_town01_run_roundtrips_without_tracking_retail_text(self):
        from importer.pipeline import _disc_context
        with _disc_context(os.environ["LEGAIA_DISC_BIN"]):
            context = load_dialogue_authoring_context(os.environ["LEGAIA_DISC_BIN"], "town01")
            original = context.patch({})[0]
            options = context.options("scene://town01/actors/man-p1/0049")
            self.assertEqual(len(options["runs"]), 7)
            run = options["runs"][0]
            self.assertEqual(run["semantic_id"], "script://town01/actors/man-p1/0049/dialogue/0050/run/0053")
            self.assertEqual((run["decoded_byte_offset"], run["byte_length"]), (27164, 12))
            changed, audit = context.patch({run["semantic_id"]: "SDK"}, original=original)
            self.assertEqual(len(changed), 45338)
            self.assertEqual(changed[27164:27176], b"SDK" + b" " * 9)
            self.assertEqual(changed[:27164], original[:27164])
            self.assertEqual(changed[27176:], original[27176:])
            self.assertEqual(audit[0]["padding_bytes"], 9)
            self.assertEqual(context.patch({run["semantic_id"]: run["text"]}), (original, []))
            self.assertFalse(context.options("scene://town01/actors/man-p1/0001")["supported"])


if __name__ == "__main__":
    unittest.main()
