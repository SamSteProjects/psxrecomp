"""Source-span transition serializer checks without retail payloads."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.transition_authoring import patch_transition_entry, TransitionAuthoringContext
from test_importer_dialogue_authoring import fixture, ACTOR

class TransitionEntryTests(unittest.TestCase):
    def test_reference_interpretation_preserves_half_tile_and_sector_semantics(self):
        from importer.transition_authoring import reference_entry_interpretation
        for byte, coordinate in ((0,64),(127,16320),(128,128),(255,16384)):
            result = reference_entry_interpretation(dict(entry_x_encoded=byte, entry_z_encoded=byte, direction_encoded=255))
            self.assertEqual((result["x"],result["z"]), (coordinate,coordinate))
            self.assertEqual(result["facing_angle_12bit"],3584)
            self.assertFalse(result["runtime_verified"])

    def test_verified_man_owner_baseline_and_exact_audit(self):
        source, man = fixture(b"\x3f\x01\x02\x06town01\x03\x04\x05opaque")
        context = TransitionAuthoringContext(source)
        option = context.options(ACTOR)["transitions"][0]
        identifier = option["semantic_id"]
        self.assertTrue(identifier.endswith("/transition/0005"))
        self.assertEqual(option["destination"], "town01")
        changed, audit = context.patch({identifier: {"entry_x_encoded": 99}}, original=man)
        self.assertEqual([i for i, (a, b) in enumerate(zip(man, changed)) if a != b],
                         [option["decoded_byte_offset"]])
        self.assertEqual(audit[0]["transition_id"], identifier)
        option["values"]["entry_x_encoded"] = 77
        self.assertEqual(context.options(ACTOR)["transitions"][0]["values"]["entry_x_encoded"], 3)
        self.assertEqual(context.patch({}), (man, []))
        with self.assertRaisesRegex(ImportError, "baseline"):
            context.patch({identifier: {"entry_x_encoded": 99}}, original=changed)
        for bad in (identifier.replace("fixture", "foreign"), identifier[:-4] + "0006", 3):
            with self.assertRaises(ImportError):
                context.patch({bad: {"entry_x_encoded": 99}})
        # A later invalid edit does not mutate the immutable source snapshot.
        with self.assertRaises(ImportError):
            context.patch({identifier: {"entry_x_encoded": 99}, "invalid": {}})
        self.assertEqual(context.patch({}), (man, []))

    def test_aliased_owner_and_unknown_paths_are_not_editable(self):
        source, _ = fixture(b"\x3f\x01\x02\x06town01\x03\x04\x05", alias=True)
        with self.assertRaisesRegex(ImportError, "aliased"):
            TransitionAuthoringContext(source).options(ACTOR)
        source, _ = fixture(b"\xff\x3f\x01\x02\x06town01\x03\x04\x05")
        self.assertFalse(TransitionAuthoringContext(source).options(ACTOR)["supported"])

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
