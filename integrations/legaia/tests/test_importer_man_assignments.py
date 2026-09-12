"""Synthetic-only MAN donor assignment guards and lossless serialization."""
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from importer.core import ImportError, decompress_lzs, parse_man
from importer.man_assignments import ManAssignmentContext, load_man_assignment_context
from importer.serialization import compress_lzs, patch_man_positions
from integrations.legaia.tests.test_importer import synthetic_man


def literals(data):
    return b"".join(b"\xff" + data[i:i+8] for i in range(0, len(data), 8))


def fixture(*, bones=(2, 2), model_counts=None, alias=False, compressed=False, opaque_prefix=b""):
    man = bytearray(synthetic_man())
    man[:len(opaque_prefix)] = opaque_prefix
    actors = parse_man(man).actors
    for actor, model, animation in zip(actors, (4, 5), (1, 2)):
        offset = actor.byte_offset + 1 + actor.local_count * 2
        man[offset:offset+2] = bytes((model, animation))
    if alias:
        man[0x2B:0x2E] = man[0x31:0x34]  # P0 aliases actor1's record.
    records = [struct.pack("<4H", count, 2, 0x080C, 2) + bytes(count * 2 * 8 + 8)
               for count in bones]
    anm = struct.pack("<III", 2, 12, 12 + len(records[0])) + b"".join(records)
    man = bytes(man)
    context = ManAssignmentContext("synthetic", man, compress_lzs(man) if compressed else literals(man),
                                   model_counts or {4: 2, 5: 2, 6: 2}, anm, {"synthetic": True})
    return context, man


class AssignmentTests(unittest.TestCase):
    def test_header_patch_rebases_after_table_growth(self):
        context, original = fixture()
        # An extra P0 table entry shifts every actor record by three bytes.
        candidate = bytearray(original[:0x2b] + original[0x2b:0x2e] + original[0x2b:])
        struct.pack_into('<h', candidate, 0x22, struct.unpack_from('<h', original, 0x22)[0] + 1)
        candidate = bytes(candidate)
        changed, audit = context.patch_appended(candidate, {1: {'model_index': 5, 'animation_id': 2}})
        self.assertEqual({i for i, (a, b) in enumerate(zip(candidate, changed)) if a != b},
                         {a['decoded_byte_offset'] for a in audit})
        self.assertTrue(all(a['decoded_byte_offset'] == a['source_decoded_byte_offset'] + 3 for a in audit))
        self.assertEqual((parse_man(changed).actors[0].model_index, parse_man(changed).actors[0].animation_id), (5, 2))
        with self.assertRaisesRegex(ImportError, 'baseline'):
            context.patch_appended(changed, {1: {'model_index': 5, 'animation_id': 2}})

    def test_donor_pair_patches_only_two_bytes_and_composes_positions(self):
        context, original = fixture()
        changed, audit = context.patch({1: {"model_index": 5, "animation_id": 2}}, original=original)
        self.assertEqual([a["field"] for a in audit], ["model_index", "animation_id"])
        expected_offsets = {a["decoded_byte_offset"] for a in audit}
        self.assertEqual({i for i, (a, b) in enumerate(zip(original, changed)) if a != b}, expected_offsets)
        self.assertEqual(len(original), len(changed))
        self.assertTrue(all(a["donor_records"] == [2] and a["script_compatibility"] == "unverified" for a in audit))
        self.assertEqual(parse_man(changed).actors[0].world_x, parse_man(original).actors[0].world_x)
        positioned, _ = patch_man_positions(changed, "synthetic", {1: {"x": 704}})
        self.assertEqual((parse_man(positioned).actors[0].model_index, parse_man(positioned).actors[0].animation_id), (5, 2))
        self.assertEqual(context.patch({})[0], original)

    def test_equal_span_encoded_roundtrip_and_exact_noop(self):
        context, original = fixture()
        unchanged, audit, _ = context.serialize({1: {"model_index": 4, "animation_id": 1}})
        self.assertEqual(unchanged, literals(original)); self.assertEqual(audit, [])
        encoded, audit, stats = context.serialize({1: {"model_index": 5, "animation_id": 2}})
        self.assertEqual(len(encoded), len(unchanged))
        changed, _ = context.patch({1: {"model_index": 5, "animation_id": 2}})
        self.assertEqual(decompress_lzs(encoded, len(original))[0], changed)
        self.assertLess(stats["new_encoded_size"], stats["original_encoded_size"])

    def test_bad_edits_do_not_modify_original_or_publish_partial_result(self):
        context, original = fixture()
        cases = [{1: {"model_index": True}}, {True: {"animation_id": 2}},
                 {0: {"model_index": 5}}, {3: {"model_index": 5}},
                 {1: {}}, {1: {"x": 704}}, {1: {"animation_id": 0}},
                 {1: {"animation_id": 3}}, {1: {"model_index": 0xF0}},
                 {1: {"model_index": 6, "animation_id": 2}},
                 {1: {"model_index": 5}},  # invented model5/animation1 combination
                 {1: {"model_index": 5, "animation_id": 2}, 2: {"animation_id": 255}}]
        for edits in cases:
            with self.subTest(edits=edits), self.assertRaises(ImportError):
                context.patch(edits)
            self.assertEqual(context.patch({})[0], original)
        with self.assertRaisesRegex(ImportError, "baseline"):
            context.patch({}, original=original[:-1] + b"\x01")

    def test_object_channel_mismatch_alias_and_unresolved_original(self):
        context, _ = fixture(bones=(2, 3))
        with self.assertRaisesRegex(ImportError, "channel count"):
            context.patch({1: {"model_index": 5, "animation_id": 2}})
        context, _ = fixture(bones=(2, 3), model_counts={4: 2, 5: 3})
        with self.assertRaisesRegex(ImportError, "same object"):
            context.patch({1: {"model_index": 5, "animation_id": 2}})
        context, _ = fixture(alias=True)
        with self.assertRaisesRegex(ImportError, "non-aliased"):
            context.patch({1: {"model_index": 5, "animation_id": 2}})
        context, _ = fixture(model_counts={5: 2})
        self.assertFalse(context.options(1)["supported"])

    def test_options_are_observed_pairs_and_caller_metadata_cannot_poison(self):
        context, original = fixture()
        options = context.options(1)
        self.assertEqual([(p["model_index"], p["animation_id"]) for p in options["pairs"]], [(4, 1), (5, 2)])
        options["pairs"][0]["donor_records"].append(999)
        provenance = context.provenance(); provenance["model_object_counts"][4] = 100
        self.assertEqual(context.provenance()["model_object_counts"][4], 2)
        self.assertEqual(context.options(1)["pairs"][0]["donor_records"], [1])
        self.assertEqual(context.patch({})[0], original)

    def test_actual_compressed_growth_rejects_and_keeps_source(self):
        # Opaque header bytes make the original encode to63bytes and the valid
        # two-byte donor patch to64. Exercise the real compressor, not a stub.
        context, original = fixture(compressed=True, opaque_prefix=bytes.fromhex(
            "010500020004040404010004000404050004020105000200000005000401"))
        changed, _ = context.patch({1: {"model_index": 5, "animation_id": 2}})
        self.assertGreater(len(compress_lzs(changed)), len(compress_lzs(original)))
        with self.assertRaisesRegex(ImportError, "compressed capacity"):
            context.serialize({1: {"model_index": 5, "animation_id": 2}})
        self.assertEqual(context.serialize({})[0], compress_lzs(original))


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailAssignmentTests(unittest.TestCase):
    def test_town01_has_verified_alternative_donor_pair_and_roundtrip(self):
        context = load_man_assignment_context(os.environ["LEGAIA_DISC_BIN"], "town01")
        self.assertFalse(context.options(1)["supported"])  # zero-animation initial header
        choices = context.options(5)
        alternatives = [p for p in choices["pairs"] if not p["unchanged"]]
        self.assertTrue(alternatives)
        pair = alternatives[0]
        edits = {5: {k: pair[k] for k in ("model_index", "animation_id")}}
        changed, audit = context.patch(edits)
        self.assertTrue(audit)
        actor = next(a for a in parse_man(changed).actors if a.record_index == 5)
        self.assertEqual((actor.model_index, actor.animation_id), (pair["model_index"], pair["animation_id"]))
        encoded, _, stats = context.serialize(edits)
        self.assertEqual(decompress_lzs(encoded, len(changed))[0], changed)
        self.assertLessEqual(stats["new_encoded_size"], stats["original_encoded_size"])


if __name__ == "__main__":
    unittest.main()
