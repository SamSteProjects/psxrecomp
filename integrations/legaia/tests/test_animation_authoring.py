"""Exact channel writes and immutable imported preview evidence."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.animation import decode_animation_record
from importer.animation_authoring import patch_animation_channels
from importer.core import ImportError
from importer.scene_animation import load_scene_actor_animation_catalog
from test_importer_scene_animation import fixture


def sha(data):
    return hashlib.sha256(data).hexdigest()


class AnimationAuthoringTests(unittest.TestCase):
    def test_shared_bank_merges_axes_and_preview_rejects_conflicts(self):
        catalog, actor, asset, model = fixture()
        other = deepcopy(actor)
        other["semantic_id"] += "-shared"
        catalog._actors[other["semantic_id"]] = other
        source = sha(catalog._body[8:])
        index = actor["placement_fields"]["animation_id"] - 1
        binding = {"animation_id": f"animation://{catalog.scene}/scene-anm/{index:04d}", "source_record_sha256": source}
        overrides = {
            actor["semantic_id"]: {**binding, "edits": [{"frame_index": 1, "object_index": 0, "translation": {"x": 100}}]},
            other["semantic_id"]: {**binding, "edits": [{"frame_index": 1, "object_index": 0, "translation": {"y": 200}}]}}
        with patch("importer.scene_animation.load_model_preview", return_value=deepcopy(model)):
            preview = catalog.authored_bank_preview(actor, asset, overrides)
        bank, audit = catalog.authored_bank(overrides)
        self.assertEqual(decode_animation_record(bank[8:])["frames"][1]["object_transforms"][0]["translation"], [100, 200, 0])
        self.assertEqual(preview["frames"][1]["vertices"], [[101, 202, 3]])
        self.assertEqual(len(audit), 2)
        self.assertEqual({row['field']:row['axis_owners'] for row in audit},
                         {'translation.x':[actor['semantic_id']], 'translation.y':[other['semantic_id']]})
        agreed=deepcopy(overrides);agreed[other['semantic_id']]['edits'][0]['translation']['x']=100
        agreed_bank,agreed_audit=catalog.authored_bank(agreed)
        self.assertEqual(agreed_bank,bank)
        self.assertEqual(next(row for row in agreed_audit if row['field']=='translation.x')['axis_owners'],sorted(overrides))

        with patch("importer.scene_animation.load_model_preview", side_effect=AssertionError("channel inspection must not load geometry")):
            values = catalog.channel_values(other, asset, 1, 0, overrides)
        self.assertEqual(values["retail"]["translation"], {"x": 10, "y": 0, "z": 0})
        self.assertEqual(values["effective"]["translation"], {"x": 100, "y": 200, "z": 0})
        self.assertEqual(values["contributors"], sorted(overrides))
        self.assertEqual(values['axis_contributors']['translation'],{'x':[actor['semantic_id']],'y':[other['semantic_id']],'z':[]})
        self.assertEqual(values['axis_contributors']['rotation_psx'],{'x':[],'y':[],'z':[]})
        values['axis_contributors']['translation']['x'].clear()
        self.assertEqual(catalog.channel_values(other,asset,1,0,overrides)['axis_contributors']['translation']['x'],[actor['semantic_id']])

        self.assertEqual(values["effective_record_sha256"], sha(bank[8:]))
        for frame, obj in ((True, 0), (-1, 0), (2, 0), (0, True), (0, 1)):
            with self.subTest(frame=frame, obj=obj), self.assertRaises(ImportError):
                catalog.channel_values(actor, asset, frame, obj)
        overrides[other["semantic_id"]]["edits"][0]["translation"]["x"] = 99
        with self.assertRaisesRegex(ImportError, "Conflicting"):
            catalog.authored_bank_preview(actor, asset, overrides)

    def test_exhaustive_translation_wire_roundtrip_preserves_opaque_nibbles(self):
        # Cover every signed12 value in all axes, all rotation bytes and every
        # opaque nibble using independently constructed source bytes.
        channels = []
        for i in range(4096):
            x, y, z = i, 4095 - i, (i + 2048) % 4096
            channels.append(bytes((x & 255, y & 255, x >> 8 | (y >> 8) << 4,
                                   z & 255, (i % 16) << 4 | z >> 8,
                                   i % 256, (i + 1) % 256, (i + 2) % 256)))
        original = struct.pack("<4H", 0x108, 512, 0x080C, 4) + b"".join(channels) + bytes(8)
        decoded = decode_animation_record(original)
        edits = [{"frame_index": frame["frame_index"], "object_index": channel["object_index"],
                  **{field: dict(zip("xyz", channel[field])) for field in ("translation", "rotation_psx")}}
                 for frame in decoded["frames"] for channel in frame["object_transforms"]]
        changed, audit = patch_animation_channels(original, sha(original), edits)
        self.assertEqual(changed, original)
        self.assertEqual(audit, [])

    def test_sparse_edit_exact_bytes_boundaries_and_deterministic_audit(self):
        catalog, _, _, _ = fixture()
        original = catalog._body[8:]
        original = original[:12] + bytes([0xA0]) + original[13:]
        edits = [{"frame_index": 1, "object_index": 0, "rotation_psx": {"z": 4080}},
                 {"frame_index": 0, "object_index": 0, "translation": {"x": -2048, "y": 2047, "z": -1}}]
        changed, audit = patch_animation_channels(original, sha(original), edits)
        self.assertEqual(changed[:8], original[:8])
        self.assertEqual(changed[8:16], bytes([0, 255, 0x78, 255, 0xAF, 0, 0, 0]))
        self.assertEqual(changed[16:23], original[16:23])
        self.assertEqual(changed[23], 255)
        self.assertEqual(changed[24:], original[24:])
        self.assertEqual(patch_animation_channels(original, sha(original), list(reversed(edits))), (changed, audit))
        self.assertEqual([row["field"] for row in audit], ["translation.x", "translation.y", "translation.z", "rotation_psx.z"])

    def test_invalid_source_indices_axes_ranges_duplicates_and_quantization(self):
        catalog, _, _, _ = fixture()
        original = catalog._body[8:]
        base = {"frame_index": 0, "object_index": 0, "translation": {"x": 0}}
        for edit in ({**base, "frame_index": True}, {**base, "frame_index": 2},
                     {**base, "object_index": -1}, {**base, "translation": {}},
                     {**base, "translation": {"w": 1}}, {**base, "translation": {"x": 2048}},
                     {**base, "translation": {"x": -2049}}, {**base, "translation": {"x": 1.0}},
                     {**base, "translation": {"x": True}}, {**base, "opaque_nibble": 1},
                     {**base, "rotation_psx": {"z": 1}}, {**base, "rotation_psx": {"z": 4096}},
                     {**base, "rotation_psx": {"z": -16}}):
            with self.subTest(edit=edit), self.assertRaises(ImportError):
                patch_animation_channels(original, sha(original), [edit])
        for edits in ([base, base], [base] * 4097, {}, None):
            with self.assertRaises(ImportError):
                patch_animation_channels(original, sha(original), edits)
        with self.assertRaisesRegex(ImportError, "hash"):
            patch_animation_channels(original, "0" * 64, [])
        with self.assertRaises(ImportError):
            patch_animation_channels(original[:-1], sha(original[:-1]), [])

    def test_authored_preview_uses_effective_frames_without_poisoning_imported_cache(self):
        catalog, actor, asset, model = fixture()
        raw = catalog._body[8:]
        edits = [{"frame_index": 1, "object_index": 0, "translation": {"x": 100}}]
        with patch("importer.scene_animation.load_model_preview", return_value=deepcopy(model)):
            before = catalog.animation_preview(actor, asset)
            authored = catalog.authored_animation_preview(actor, asset, edits, sha(raw))
            after = catalog.animation_preview(actor, asset)
        with patch("importer.scene_animation.load_model_preview", side_effect=AssertionError("record API must not expand meshes")):
            changed, metadata = catalog.authored_animation_record(actor, asset, edits, sha(raw))
        self.assertEqual(metadata, authored["authored"])
        self.assertEqual(sha(changed), metadata["effective_record_sha256"])
        self.assertEqual(decode_animation_record(changed)["frames"][1]["object_transforms"][0]["translation"][0], 100)
        self.assertEqual(before, after)
        self.assertEqual(authored["frames"][1]["vertices"], [[101, 2, 3]])
        self.assertEqual(authored["frames"][0], before["frames"][0])
        self.assertEqual(authored["source_record"], before["source_record"])
        self.assertEqual(authored["representation"], "authored")
        self.assertEqual(before["representation"], "imported")
        self.assertEqual(authored["authored"]["changes"][0]["before_value"], 10)
        with self.assertRaisesRegex(ImportError, "hash"):
            catalog.authored_animation_preview(actor, asset, edits, "0" * 64)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailAnimationAuthoringTests(unittest.TestCase):
    def test_all_referenced_town01_records_preserve_source_on_noop(self):
        catalog = load_scene_actor_animation_catalog(os.environ["LEGAIA_DISC_BIN"], "town01")
        seen = set()
        for item in catalog.referenced_animation_metadata()["bindings"]:
            source = item["source_record"]
            if source["record_index"] in seen:
                continue
            seen.add(source["record_index"])
            raw = catalog._body[source["byte_offset"]:source["byte_offset"] + source["byte_length"]]
            first = decode_animation_record(raw)["frames"][0]["object_transforms"][0]
            edit = {"frame_index": 0, "object_index": 0,
                    **{field: dict(zip("xyz", first[field])) for field in ("translation", "rotation_psx")}}
            self.assertEqual(patch_animation_channels(raw, source["record_sha256"], [edit]), (raw, []))
        self.assertGreater(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
