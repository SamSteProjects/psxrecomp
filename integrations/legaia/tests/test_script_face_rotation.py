"""Pinned face-control widths and operands; no heading or execution inference."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.script_inspection import _instruction, inspect_record

class FaceRotationInspection(unittest.TestCase):
    def test_picker_table_labels_and_signed_entry_relative_targets(self):
        for count in (2, 3, 4):
            for continuation in (b"", b"\x24", b"\x25", b"\x48", b"\x4c\xff"):
                encoded = bytes([0x25 + count]) + b"".join(struct.pack("<h", -2 + i) for i in range(count))
                encoded += continuation + b"\x1fChoice\0" * count
                row = _instruction(encoded, 0)
                self.assertEqual(row["length"], len(encoded))
                self.assertEqual([edge["pc"] for edge in row["successors"]], [-1 + 3*i for i in range(count)])
                options = row["operands"]["options"]
                self.assertEqual([o["encoded_target"] for o in options], [-1 + 3*i for i in range(count)])
                self.assertEqual([o["label"] for o in options], ["Choice"] * count)
                self.assertIn("unresolved_control_flow", row["operands"])
                for end in range(1, len(encoded)):
                    with self.assertRaises(ImportError):
                        _instruction(encoded[:end], 0)

    def test_menu_choices_follow_only_encoded_targets_and_reject_overlap(self):
        script = b"\x27\x0b\0\x09\0\x1fA\0\x1fB\0\xfe\x1fC\0"
        report = inspect_record(script, 0)
        self.assertEqual([d["pc"] for d in report["dialogues"]], [12])
        self.assertEqual(report["opaque_regions"][0]["pc"], 11)
        self.assertEqual(len(report["stops"]), 1)
        self.assertIn("pager continuation", report["stops"][0]["reason"])
        # A choice landing inside the menu's label region is ambiguous.
        conflicting = script[:1] + b"\x04\0" + script[3:]
        rejected = inspect_record(conflicting, 0)
        self.assertEqual(rejected["dialogues"], [])
        self.assertEqual(rejected["instructions"], [])
        self.assertTrue(any("inside" in stop["reason"] for stop in rejected["stops"]))
        conflict = next(stop for stop in rejected["stops"] if "inside" in stop["reason"])
        self.assertEqual(conflict["owner_pc"], 0)
        self.assertEqual(conflict["pc"], 5)

    def test_picker_high_bit_is_control_not_extended_target(self):
        for count in (2, 3, 4):
            for continuation in (b"", b"\xa4", b"\xa5", b"\xc8", b"\x4c\xff"):
                encoded = bytes([0xA5 + count]) + struct.pack("<h", 20) * count
                encoded += continuation + b"\x1fChoice\0" * count
                node = _instruction(encoded, 0)
                self.assertIsNone(node["target_context"])
                self.assertEqual(node["length"], len(encoded))
                self.assertEqual(node["operands"]["options"][0]["entry_pc"], 1)
                self.assertEqual(node["operands"]["options"][0]["encoded_target"], 21)
                self.assertEqual(node["raw_hex"], encoded.hex())
                for end in range(1, len(encoded)):
                    with self.assertRaises(ImportError):
                        _instruction(encoded[:end], 0)

    def test_flag_word_branch_signed_target_and_context(self):
        for sub in (0xA0, 0xA1, 0xA2):
            for header in (bytes([0x4C]), bytes([0xCC, 5])):
                encoded = header + bytes([sub, 31, 0xFE, 0xFF])
                node = _instruction(encoded, 0)
                self.assertEqual(node["mnemonic"], "FLAG_WORD_BRANCH")
                self.assertEqual(node["successors"], [{"pc": -2, "condition": "flag_bit_set"},
                                                     {"pc": len(encoded), "condition": "flag_bit_clear"}])
                self.assertEqual(node["operands"]["bit_encoded"], 31)
                for end in range(1, len(encoded)):
                    with self.assertRaises(ImportError):
                        _instruction(encoded[:end], 0)

    def test_position_sentinel_and_timed_host_boundary(self):
        for header in (bytes([0x43]), bytes([0xC3, 9])):
            for ticks in (0, 12):
                encoded = header + bytes([9]) + struct.pack("<4H", 0xFFFF, 0x8000, 64, ticks)
                node = _instruction(encoded, 0)
                self.assertEqual(node["successors"][0]["pc"], len(encoded))
                args = node["operands"]
                self.assertEqual(args["encoded_xyz"], [65535, 32768, 64])
                self.assertEqual(args["mode"], "host_tween" if ticks else "immediate")
                self.assertEqual(args.get("unchanged_axes"), None if ticks else ["x"])
                self.assertEqual(args["runtime_effect"], "not_evaluated")
                for end in range(1, len(encoded)):
                    with self.assertRaises(ImportError):
                        _instruction(encoded[:end], 0)
        # Halt-acquire continuation remains unresolved; do not infer fallthrough.
        with self.assertRaises(ImportError):
            _instruction(bytes([0x43, 1, 0, 0, 0, 0]), 0)

    def test_setup_reset_and_extended_context(self):
        operands = bytes([7, 3]) + struct.pack("<I4Hh", 0x12345678, 1, 2, 3, 4, -20)
        for header in (bytes([0x43]), bytes([0xC3, 9])):
            encoded = header + operands
            decoded = _instruction(encoded, 0)
            self.assertEqual(decoded["mnemonic"], "FACE_ROTATION_SETUP")
            self.assertEqual(decoded["successors"][0]["pc"], len(encoded))
            self.assertEqual(decoded["operands"]["parameters_u16"], [1, 2, 3, 4])
            self.assertEqual(decoded["operands"]["payload_u32"], 0x12345678)
            self.assertEqual(decoded["operands"]["target_i16"], -20)
            self.assertEqual(decoded["target_context"], 9 if len(header) == 2 else None)
            for end in range(1, len(encoded)):
                with self.assertRaises(ImportError):
                    _instruction(encoded[:end], 0)
        self.assertEqual(_instruction(bytes([0x43, 8]), 0)["successors"][0]["pc"], 2)
        with self.assertRaises(ImportError):
            _instruction(bytes([0x43, 9, 0, 0]), 0)

if __name__ == "__main__":
    unittest.main()
