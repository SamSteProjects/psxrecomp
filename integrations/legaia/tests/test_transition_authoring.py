"""Source-span transition serializer checks without retail payloads."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.transition_authoring import patch_transition_entry

class TransitionEntryTests(unittest.TestCase):
    def test_three_fields_change_only_the_entry_span(self):
        for header in (bytes([0x3f]), bytes([0xbf, 7])):
            source = header + bytes([1, 2, 6]) + b"town01" + bytes([3, 4, 5]) + b"opaque"
            changed, audit = patch_transition_entry(source, 0, 0,
                {"entry_x_encoded": 0, "entry_z_encoded": 255, "direction_encoded": 8}, base_offset=100)
            entry = len(header) + 9
            self.assertEqual(changed[:entry], source[:entry])
            self.assertEqual(changed[entry:entry+3], bytes([0,255,8]))
            self.assertEqual(changed[entry+3:], source[entry+3:])
            self.assertEqual([a["decoded_byte_offset"] for a in audit], [100+entry+i for i in range(3)])
            self.assertEqual(patch_transition_entry(source, 0, 0, {"entry_x_encoded":3}), (source, []))

    def test_invalid_values_targets_and_source_are_rejected(self):
        source = b"\x3f\x01\x02\x06town01\x03\x04\x05"
        for edits in ({}, {"name":"town02"}, {"entry_x_encoded":True}, {"entry_x_encoded":256}, {"entry_x_encoded":-1}, {"entry_x_encoded":1.5}):
            with self.assertRaises(ImportError):patch_transition_entry(source,0,0,edits)
        for pc in (True, -1, 2, 999):
            with self.assertRaises(ImportError):patch_transition_entry(source,0,pc,{"entry_x_encoded":1})
        for malformed in (source[:-1], source.replace(b"town01",b"Town01"), b"\xff"+source):
            with self.assertRaises(ImportError):patch_transition_entry(malformed,0,0,{"entry_x_encoded":1})

if __name__ == "__main__":unittest.main()
