"""Meaningful bounded parser regressions and opt-in actual MAN inspection."""
from copy import deepcopy
import hashlib
import os
import struct
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
    def test_retail_dispatch_halt_does_not_scan_trailing_text(self):
        report = inspect_record(b"\x2a\x1fOpaque\0", 0)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["instructions"][0]["mnemonic"], "DISPATCH_HALT")
        self.assertEqual(report["instructions"][0]["length"], 1)
        self.assertEqual(report["instructions"][0]["successors"], [])
        self.assertEqual(report["dialogues"], [])
        self.assertEqual(report["opaque_regions"][0]["pc"], 1)
        self.assertIn("same PC", report["stops"][0]["reason"])
        self.assertEqual(inspect_record(b"\xaa\x17\x1fOpaque\0", 0)["instructions"], [])

    def test_context_acquire_payload_and_wait_edges(self):
        for sub in (0x85, 0x8E, 0x8F):
            ordinary = bytes([0x4c, sub, 0x1f, 0, 0xff])
            for data in (ordinary, b"\xcc\x17" + ordinary[1:]):
                report = inspect_record(data + b"\x1fHi\0", 0)
                self.assertFalse(report["stops"])
                row = report["instructions"][0]
                self.assertEqual(row["length"], len(data))
                self.assertEqual(row["successors"], [{"pc": len(data), "condition": "acquire_succeeded"},
                                                      {"pc": 0, "condition": "acquire_wait"}])
                self.assertEqual([(d["pc"], d["text"]) for d in report["dialogues"]], [(len(data), "Hi")])
                for length in range(1, len(data)):
                    truncated = inspect_record(data[:length], 0)
                    self.assertEqual(truncated["status"], "partial")
                    self.assertEqual(truncated["instructions"], [])
                    self.assertEqual(truncated["dialogues"], [])

    def test_emitters_and_collision_paint_preserve_payload_boundaries(self):
        words = [-32768, 32767, -1, 0, 31, 3276]
        forms = [b"\x4c\x60" + struct.pack("<6h", *words),
                 b"\x4c\x61" + b"\x1f\0" * 7]
        forms += [bytes([0x4c, sub, 31, 255, 0, 254]) + (b"\x1f" if sub >= 0x72 else b"")
                  for sub in range(0x70, 0x74)]
        for ordinary in forms:
            for data in (ordinary, b"\xcc\x17" + ordinary[1:]):
                report = inspect_record(data + b"\x1fHi\0", 0)
                self.assertFalse(report["stops"])
                self.assertEqual(report["instructions"][0]["length"], len(data))
                self.assertEqual([(d["pc"], d["text"]) for d in report["dialogues"]], [(len(data), "Hi")])
                for length in range(1, len(data)):
                    truncated = inspect_record(data[:length], 0)
                    self.assertEqual(truncated["status"], "partial")
                    self.assertEqual(truncated["instructions"], [])
                    self.assertEqual(truncated["dialogues"], [])
        self.assertEqual(inspect_record(forms[0], 0)["instructions"][0]["operands"]["words"], words)
        edges = inspect_record(forms[1], 0)["instructions"][0]["successors"]
        self.assertEqual(edges, [{"pc": 16, "condition": "acquire_succeeded"}, {"pc": 0, "condition": "acquire_wait"}])
        for sub in (0x62, 0x6F, 0x74, 0x7F):
            self.assertEqual(inspect_record(bytes([0x4c, sub]) + b"\x1fOpaque\0", 0)["dialogues"], [])

    def test_context_allocation_has_no_invented_fallthrough(self):
        for data in (b"\xcc\x17\xcd\x1fOpaque\0",):
            report = inspect_record(data, 0)
            self.assertEqual(report["status"], "partial")
            self.assertEqual(len(report["instructions"]), 1)
            row = report["instructions"][0]
            self.assertEqual(row["mnemonic"], "SCRIPT_CONTEXT_ALLOC")
            self.assertEqual(row["successors"], [])
            self.assertEqual(row["length"], 3 if data[0] == 0xCC else 2)
            self.assertEqual(report["opaque_regions"][0]["pc"], row["length"])
            self.assertEqual(report["stops"][0]["kind"], "known_instruction_unresolved_control_flow")
            self.assertEqual(report["dialogues"], [])
            self.assertIn("allocated-context entry", report["stops"][0]["reason"])

    def test_retail_allocation_can_advance_or_wait_at_original_pc(self):
        report = inspect_record(b"\x4c\xcd\x1fHi\0", 0)
        self.assertFalse(report["stops"])
        self.assertEqual(report["instructions"][0]["successors"],
                         [{"pc": 2, "condition": "allocation_absent_or_flag_3_set"},
                          {"pc": 0, "condition": "allocated_context_wait"}])
        self.assertEqual([d["text"] for d in report["dialogues"]], ["Hi"])
        self.assertEqual(covered_bytes(report, 0, 6), [1] * 6)

    def test_actor_scene_menu_widths_and_slot_sentinel(self):
        widths = {0xC0: 1, 0xC1: 1, 0xC2: 2, 0xC3: 1, 0xC4: 3,
                  0xC5: 3, 0xC6: 3, 0xC7: 3, 0xC8: 1,
                  0xCA: 4, 0xCB: 4, 0xCC: 4, 0xCE: 2, 0xCF: 3}
        for sub, width in widths.items():
            ordinary = bytes([0x4c, sub]) + bytes([0x1f]) * (width - 1)
            for data in (ordinary, b"\xcc\x17" + ordinary[1:]):
                report = inspect_record(data + b"\x1fHi\0", 0)
                self.assertFalse(report["stops"])
                self.assertEqual(report["dialogues"][0]["pc"], len(data))
                for length in range(1, len(data)):
                    truncated = inspect_record(data[:length], 0)
                    self.assertEqual(truncated["status"], "partial")
                    self.assertEqual(truncated["instructions"], [])
        for sub in (0xCA, 0xCB, 0xCC):
            args = inspect_record(bytes([0x4c, sub, 255, 255, 255]), 0)["instructions"][0]["operands"]
            self.assertEqual(args["value"], -1)
            self.assertEqual(args["uses_frame_delta"], sub != 0xCA)
        self.assertEqual(inspect_record(b"\x4c\xc9\x1fOpaque\0", 0)["dialogues"], [])

    def test_camera_and_render_payload_boundaries(self):
        forms = [b"\x46\x24\x1f\0\xff\x45", b"\x46\x25\x1f",
                 b"\x45\x7f" + b"\x1f\0" * 9, b"\x45\xbf",
                 b"\x45\x3c\0\xff\xff",
                 b"\x45\x3f\xff\xff\xff" + struct.pack("<10H", *range(65526, 65536))]
        for ordinary in forms:
            for data in (ordinary, bytes([ordinary[0] | 0x80, 23]) + ordinary[1:]):
                with self.subTest(data=data):
                    report = inspect_record(data + b"\x1fHi\0", 0)
                    self.assertFalse(report["stops"])
                    self.assertEqual(report["instructions"][0]["length"], len(data))
                    self.assertEqual([(d["pc"], d["text"]) for d in report["dialogues"]], [(len(data), "Hi")])
                    for length in range(1, len(data)):
                        truncated = inspect_record(data[:length], 0)
                        self.assertEqual(truncated["status"], "partial")
                        self.assertEqual(truncated["instructions"], [])
                        self.assertEqual(truncated["dialogues"], [])
        sparse = inspect_record(b"\x45\x22\x01\x34\x12\xff\xff\x00\x80", 0)["instructions"][0]
        self.assertEqual(sparse["operands"]["parameters"], [{"slot": 0, "value": 65535}, {"slot": 9, "value": 32768}])
        self.assertEqual(sparse["operands"]["mode"], 8)
        self.assertEqual(sparse["operands"]["apply_trigger"], 0x1234)

    def test_camera_absolute_jump_skips_payload_and_checks_targets(self):
        report = inspect_record(b"\x45\xff\x08\0\x1fNo\0\x1fYes\0", 0)
        self.assertEqual([d["text"] for d in report["dialogues"]], ["Yes"])
        self.assertEqual(report["instructions"][0]["successors"], [{"pc": 8, "condition": "unconditional"}])
        for data in (b"\x45\xc0", b"\x45\xc0\x00", b"\x45\xc0\xff\xff"):
            self.assertEqual(inspect_record(data, 0)["status"], "partial")

    def test_model_animation_unsigned_fields_and_all_new_menu_boundaries(self):
        model = b"\x4c\x81\x1f\xff\x80" + struct.pack("<HH", 65535, 32768)
        row = inspect_record(model, 0)["instructions"][0]
        self.assertEqual(row["operands"]["model_id"], 0x80FF1F)
        self.assertEqual(row["operands"]["animation_frame"], 65535)
        self.assertEqual(row["operands"]["tween_frames"], 32768)
        forms = [model] + [bytes([0x4c, s]) for s in range(0x30, 0x40)]
        forms += [bytes([0x4c, s]) + struct.pack("<hH", -32768, 65535)
                  for s in (0x40, 0x41, 0x42, 0x46, 0x47, 0x48, 0x4a, 0x4b, 0x4c, 0x4d)]
        forms += [b"\x4c\x45\x1f" + struct.pack("<hhhH", -32768, 32767, -1, 65535)]
        for ordinary in forms:
            for data in (ordinary, b"\xcc\x17" + ordinary[1:]):
                report = inspect_record(data + b"\x1fHi\0", 0)
                self.assertFalse(report["stops"])
                self.assertEqual(report["instructions"][0]["length"], len(data))
                self.assertEqual(report["dialogues"][0]["pc"], len(data))
                for length in range(1, len(data)):
                    truncated = inspect_record(data[:length], 0)
                    self.assertEqual(truncated["status"], "partial")
                    self.assertEqual(truncated["instructions"], [])
                    self.assertEqual(truncated["dialogues"], [])

    def test_field_ramp_jumps_select_encoded_path_and_reject_invalid_targets(self):
        for sub, jump_ticks, fall_ticks in ((0x43, 0, 1), (0x44, 1, 0)):
            for ticks, target in ((jump_ticks, 10), (fall_ticks, 10)):
                data = bytes([0x4c, sub]) + struct.pack("<hH", target, ticks) + b"\x1fNo\0\x1fYes\0"
                report = inspect_record(data, 0)
                self.assertFalse(report["stops"])
                self.assertEqual(report["instructions"][0]["successors"][0]["pc"],
                                 10 if ticks == jump_ticks else 6)
                self.assertEqual([d["text"] for d in report["dialogues"]],
                                 ["Yes"] if ticks == jump_ticks else ["No", "Yes"])
            report = inspect_record(bytes([0x4c, sub]) + struct.pack("<hH", -1, jump_ticks), 0)
            self.assertEqual(report["status"], "partial")
        for sub in (0x49, 0x4e, 0x4f):
            report = inspect_record(bytes([0x4c, sub]) + b"\0\0\0\0\x1fOpaque\0", 0)
            self.assertEqual(report["dialogues"], [])
            self.assertEqual(report["status"], "partial")

    def test_effect_fixed_forms_preserve_operands_and_context_boundaries(self):
        forms = ((b"\x34\x0f\x1f\xff\x00" + struct.pack("<h", -32768),
                  "EFFECT_COLOR_INTENSITY", {"rgb": [31, 255, 0], "intensity": -32768}),
                 (b"\x34\x3f\x1f", "EFFECT_ANIMATION_TRIGGER", {"animation_operand": 31}))
        for ordinary, mnemonic, fields in forms:
            for data in (ordinary, b"\xb4\x17" + ordinary[1:]):
                with self.subTest(data=data):
                    report = inspect_record(data + b"\x1fHi\0", 0)
                    row = report["instructions"][0]
                    self.assertEqual(row["mnemonic"], mnemonic)
                    self.assertEqual(row["length"], len(data))
                    self.assertEqual(row["target_context"], 23 if data[0] == 0xB4 else None)
                    for key, value in fields.items():
                        self.assertEqual(row["operands"][key], value)
                    self.assertEqual([(d["pc"], d["text"]) for d in report["dialogues"]], [(len(data), "Hi")])
                    self.assertEqual(covered_bytes(report, 0, len(data) + 4), [1] * (len(data) + 4))
                    for length in range(1, len(data)):
                        truncated = inspect_record(data[:length], 0)
                        self.assertEqual(truncated["status"], "partial")
                        self.assertEqual(truncated["instructions"], [])
                        self.assertEqual(truncated["dialogues"], [])

    def test_effect_host_dependent_forms_remain_opaque(self):
        for sub in (1, 2, *range(4, 16)):
            report = inspect_record(bytes([0x34, sub << 4]) + b"\x1fOpaque\0", 0)
            self.assertEqual(report["status"], "partial")
            self.assertEqual(report["instructions"], [])
            self.assertEqual(report["dialogues"], [])
            self.assertIn("unsupported EFFECT", report["stops"][0]["reason"])

    def test_evidenced_menu_ed_e8_fields_and_continuation_ignore_operand_lookalikes(self):
        # The state byte and camera operands include apparent message/opcode
        # bytes. They must never become graph entry points or dialogue tokens.
        data = b"\x4c\xed\x1f\x4c\xe8" + struct.pack("<hhhh", -32768, 32767, -225, -1) + b"\x1fHi\0"
        report = inspect_record(data, 0, base_offset=100)
        state, camera = report["instructions"]
        self.assertEqual((state["pc"], state["length"], state["mnemonic"]), (0, 3, "SET_FIELD_STATE_BA66"))
        self.assertEqual(state["operands"], {"sub_op": 0xED, "address": "0x8007BA66", "value": 31,
                                            "encoded_hex": "ed1f"})
        self.assertEqual((camera["pc"], camera["length"], camera["mnemonic"]), (3, 10, "CAMERA_ZOOM"))
        self.assertEqual({key: camera["operands"][key] for key in ("zoom_x", "zoom_y", "zoom_z", "mode")},
                         {"zoom_x": -32768, "zoom_y": 32767, "zoom_z": -225, "mode": -1})
        self.assertEqual(camera["successors"], [{"pc": 13, "condition": "encoded_continuation"}])
        self.assertEqual([(d["pc"], d["text"]) for d in report["dialogues"]], [(13, "Hi")])
        self.assertEqual(report["status"], "decoded_supported_paths")
        self.assertEqual(covered_bytes(report, 0, len(data)), [1] * len(data))

    def test_menu_ed_e8_extended_context_lengths_and_every_truncated_prefix(self):
        for ordinary in (b"\x4c\xed\xff", b"\x4c\xe8" + struct.pack("<hhhh", 1, -2, 3, -4)):
            extended = b"\xcc\x17" + ordinary[1:]
            for data in (ordinary, extended):
                with self.subTest(data=data):
                    report = inspect_record(data, 0)
                    self.assertEqual(report["status"], "decoded_supported_paths")
                    row = report["instructions"][0]
                    self.assertEqual(row["length"], len(data))
                    self.assertEqual(row["target_context"], 23 if data is extended else None)
                    self.assertEqual(row["successors"][0]["pc"], len(data))
                    for length in range(1, len(data)):
                        truncated = inspect_record(data[:length], 0)
                        self.assertEqual(truncated["status"], "partial")
                        self.assertEqual(truncated["instructions"], [])
                        self.assertEqual(truncated["dialogues"], [])
                        self.assertEqual(truncated["opaque_regions"][0]["length"], length)

    def test_other_menu_e_subops_still_stop_without_scanning(self):
        for sub in (0xE0, 0xE1, 0xE7, 0xE9, 0xEB, 0xEE, 0xEF):
            data = bytes([0x4C, sub]) + b"\x1fOpaque\0\x4c\xed\1"
            report = inspect_record(data, 0)
            self.assertEqual(report["status"], "partial")
            self.assertEqual(report["instructions"], [])
            self.assertEqual(report["dialogues"], [])
            self.assertIn(f"0x{sub:02x}", report["stops"][0]["reason"])
            self.assertEqual(report["opaque_regions"][0]["length"], len(data))

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
