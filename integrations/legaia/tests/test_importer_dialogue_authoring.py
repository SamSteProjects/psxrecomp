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
    def test_renderer_newlines_split_editable_runs_and_are_preserved(self):
        # MES yields Glyph(0x7C), but the font renderer uses it as newline.
        for script in (b"\x1fHello|World\0",
                       b"\x1fQ\0\x27\x12\0\x10\0\x1fYes|No\0\x1fEnd\0\x4c\xff"):
            context,original=fixture(script)
            runs=context.options(ACTOR)['runs']
            self.assertTrue(runs)
            self.assertTrue(all('|' not in run['text'] for run in runs))
            self.assertEqual([run['text'] for run in runs],['Hello','World'] if script[1:2]==b'H' else ['Yes','No','End'])
            changed,audit=context.patch({runs[0]['semantic_id']:'OK'})
            self.assertEqual(len(changed),len(original))
            self.assertEqual([i for i,b in enumerate(original) if b==0x7c],[i for i,b in enumerate(changed) if b==0x7c])
            offset=runs[0]['decoded_byte_offset'];size=runs[0]['byte_length']
            self.assertEqual(changed[:offset],original[:offset]);self.assertEqual(changed[offset+size:],original[offset+size:])
            with self.assertRaisesRegex(ImportError,'renderer newline'):
                context.patch({runs[0]['semantic_id']:'|'})
            self.assertEqual(context.patch({}), (original,[]))

    def test_menu_labels_preserve_targets_controls_and_append_offsets(self):
        for count in (2, 3, 4):
            for continuation in (b"", b"\x24", b"\x4c\xff"):
                for high in (0, 0x80):
                    script = bytearray(b"\x1fPrompt\0" + bytes([0x25 + count + high]) + bytes(count*2) + continuation)
                    menu = 8
                    for _ in range(count):
                        script.extend(b"\x1fYes\x5e\x2dNo\xc1\0End\0")
                    target = 5 + len(script)
                    script.extend(b"\x4c\xff")
                    for index in range(count):
                        entry = 5 + menu + 1 + index*2
                        struct.pack_into('<h', script, menu + 1 + index*2, target - entry)
                    context, original = fixture(bytes(script))
                    options = context.options(ACTOR)
                    self.assertTrue(options['supported'], options['reason'])
                    runs = options['runs']
                    self.assertEqual(len(runs), count*3)
                    self.assertTrue(all(r['kind']=='menu_label' for r in runs))
                    self.assertEqual([r['text'] for r in runs[:3]], ['Yes', 'No', 'End'])
                    self.assertEqual(runs[0]['encoded_target'], target)
                    self.assertEqual(runs[-1]['option_index'], count-1)
                    changed, audit = context.patch({runs[0]['semantic_id']:'OK', runs[-1]['semantic_id']:''})
                    allowed = {i for a in audit for i in range(a['decoded_byte_offset'], a['decoded_byte_offset']+a['byte_length'])}
                    self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,changed))))
                    self.assertEqual(parse_man(changed), parse_man(original))
                    self.assertEqual(context.patch({r['semantic_id']:r['text'] for r in runs}), (original, []))
                    from importer.man_actor_structure import append_actor_donor
                    from hashlib import sha256
                    appended,_ = append_actor_donor(original,sha256(original).hexdigest(),1)
                    composed,relocated = context.patch_appended(appended,{runs[0]['semantic_id']:'OK'})
                    offset=relocated[0]['decoded_byte_offset']
                    self.assertEqual(composed[offset:offset+3],b'OK ')
                    self.assertEqual(composed[:offset],appended[:offset])
                    self.assertEqual(composed[offset+3:],appended[offset+3:])
                    with self.assertRaises(ImportError):
                        context.patch({runs[0]['semantic_id']:'Overlong'})
                    with self.assertRaises(ImportError):
                        context.patch({runs[0]['semantic_id'].replace('/option/0','/option/4'):'No'})

    def test_menu_conflicts_and_malformed_labels_are_not_authorable(self):
        # Target into a label, truncated label and aliased actor remain blocked.
        for script in (b"\x1fQ\0\x27\x06\0\x04\0\x1fYes\0\x1fNo\0",
                       b"\x1fQ\0\x27\x10\0\x20\0\x1fYes\0\x1fNo"):
            context,_=fixture(script)
            self.assertFalse(context.options(ACTOR)['supported'])
            self.assertEqual(context.options(ACTOR)['runs'],[])
        context,_=fixture(b"\x1fQ\0\x27\x10\0\x20\0\x1fYes\0\x1fNo\0",alias=True)
        self.assertFalse(context.options(ACTOR)['supported'])

    def test_raw_source_keeps_equal_span_validation_without_fake_compression(self):
        compressed, man = fixture()
        raw = DialogueAuthoringContext('fixture', man, man, {'compression':'none'}, compression='none')
        run = raw.options(ACTOR)['runs'][0]['semantic_id']
        self.assertEqual(raw.patch({run:'World'}), compressed.patch({run:'World'}))
        with self.assertRaisesRegex(ImportError, 'sources disagree'):
            DialogueAuthoringContext('fixture', man, man + b'x', {}, compression='none')
        with self.assertRaisesRegex(ImportError, 'compression'):
            DialogueAuthoringContext('fixture', man, man, {}, compression='unknown')

    def test_grown_table_dialogue_rebases_exact_span(self):
        context,source=fixture()
        run=context.options(ACTOR)['runs'][0]['semantic_id']
        grown=bytearray(source[:0x2b]+source[0x2b:0x2e]+source[0x2b:])
        struct.pack_into('<h',grown,0x22,2)
        grown=bytes(grown)
        result,audit=context.patch_appended(grown,{run:'World'})
        change=audit[0]
        self.assertEqual(change['decoded_byte_offset'],change['source_decoded_byte_offset']+3)
        offset=change['decoded_byte_offset']
        self.assertEqual(result[offset:offset+5],b'World')
        self.assertEqual(result[:offset],grown[:offset])
        self.assertEqual(result[offset+5:],grown[offset+5:])
        with self.assertRaisesRegex(ImportError,'preimage'):
            context.patch_appended(result,{run:'World'})

    def test_loader_rejects_descriptor_alias_and_oversize_before_decode(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch
        from importer.dialogue_authoring import MAX_MAN_BYTES
        for size, alias in ((16, True), (MAX_MAN_BYTES + 1, False)):
            descriptors = [SimpleNamespace(type_byte=3, size=size, data_offset=8, index=0)]
            if alias:
                descriptors.append(SimpleNamespace(type_byte=2, size=16, data_offset=8, index=1))
            bundle = SimpleNamespace(descriptors=descriptors, table_offset=0, entry_index=0)
            with patch("importer.dialogue_authoring._disc_context", return_value=nullcontext((None,"hash",None,None))), \
                 patch("importer.dialogue_authoring._bounded_scene_range", return_value=(0,1)), \
                 patch("importer.dialogue_authoring.find_scene_bundle", return_value=(bundle,bytes(32))), \
                 patch("importer.dialogue_authoring.decompress_lzs") as decoder:
                with self.assertRaises(ImportError):
                    load_dialogue_authoring_context("unused", "fixture")
                decoder.assert_not_called()

    def test_partition_two_equal_span_edits_and_unresolved_tail_rejection(self):
        identifier = "scene://fixture/scripts/man-p2/0000"
        for script, supported in ((b"\x1fHello\0", True), (b"\x1fHello\0\x2a", False)):
            _, original = fixture()
            region = 0x2B + 12
            section = int.from_bytes(original[0x28:0x2B], "little")
            p2 = bytes(4) + script
            man = bytearray(original[:region + section] + p2 + original[region + section:])
            man[0x34:0x37] = section.to_bytes(3, "little")
            man[0x28:0x2B] = (section + len(p2)).to_bytes(3, "little")
            man = bytes(man)
            context = DialogueAuthoringContext("fixture", man, literals(man), {})
            options = context.options(identifier)
            self.assertEqual(options["supported"], supported)
            if supported:
                run = options["runs"][0]
                changed, audit = context.patch({run["semantic_id"]: "Hi"}, original=man)
                offset = run["decoded_byte_offset"]
                self.assertEqual(changed[offset:offset + 5], b"Hi   ")
                self.assertEqual(changed[:offset], man[:offset])
                self.assertEqual(changed[offset + 5:], man[offset + 5:])
                self.assertEqual(len(audit), 1)
                from hashlib import sha256
                from importer.man_actor_structure import append_actor_donor
                appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
                composed,relocated=context.patch_appended(appended,{run['semantic_id']:'Hi'})
                new_offset=relocated[0]['decoded_byte_offset']
                self.assertGreater(new_offset,offset)
                self.assertEqual(composed[new_offset:new_offset+5],b'Hi   ')
                self.assertEqual(composed[:new_offset],appended[:new_offset])
                self.assertEqual(composed[new_offset+5:],appended[new_offset+5:])
                self.assertEqual(parse_man(composed),parse_man(appended))
            else:
                self.assertEqual(options["runs"], [])
        context, _ = fixture()
        with self.assertRaisesRegex(ImportError, "aliased"):
            context.options(identifier)

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

    def test_extended_position_context_and_operands_survive_text_edits(self):
        for ticks in (0, 12):
            # The extended actor target is unresolved, but these source spans
            # and the position instruction's encoded continuation are bounded.
            position = bytes([0xC3, 9, 9]) + struct.pack("<4H", 0xFFFF, 0x8000, 64, ticks)
            context, original = fixture(position + b"\x1fHello\0")
            options = context.options(ACTOR)
            self.assertTrue(options["supported"], options["reason"])
            run = options["runs"][0]
            changed, audit = context.patch({run["semantic_id"]: "Ready"})
            offset = run["decoded_byte_offset"]
            self.assertEqual(changed[:offset], original[:offset])
            self.assertEqual(changed[offset + 5:], original[offset + 5:])
            self.assertEqual(changed[offset:offset + 5], b"Ready")
            before_report = context._inspect(ACTOR, original)
            after_report = context._inspect(ACTOR, changed)
            self.assertEqual(before_report["instructions"], after_report["instructions"])
            self.assertEqual(after_report["instructions"][0]["target_context"], 9)
            self.assertEqual(len(audit), 1)

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
        for text in (None, True, {}, "a\nb", "^", "|", "\x1f", "\x7f", "caf\u00e9", "a" * 4097):
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
            menu_runs = context.options("scene://town01/actors/man-p1/0001")["runs"]
            self.assertTrue(menu_runs)
            self.assertTrue(all(r.get("kind") == "menu_label" for r in menu_runs))


if __name__ == "__main__":
    unittest.main()
