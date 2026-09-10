"""Pinned face-control widths and operands; no heading or execution inference."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.script_inspection import _instruction

class FaceRotationInspection(unittest.TestCase):
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
