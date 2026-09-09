"""Synthetic frame-major/transform tests and opt-in private retail coverage."""
from copy import deepcopy
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.animation import (animation_capabilities, animation_record_ranges,
                                decode_animation_record, decode_bone_transform,
                                load_animation_preview, pose_vertices)
from importer.core import ImportError


def record(bones=2, frames=3):
    head = struct.pack("<4H", bones | 0x100, frames, 0x080C, 4)
    # Translation X tags each (frame,bone) independently.
    body = b"".join(bytes([frame * 10 + bone, 0, 0, 0, 0, 0, 0, 0])
                    for frame in range(frames) for bone in range(bones))
    return head + body + bytes(8)


class AnimationTests(unittest.TestCase):
    def test_signed_translation_extremes_and_rotation_units(self):
        decoded = decode_bone_transform(bytes([0, 255, 0x78, 255, 0xAF, 0, 64, 255]))
        self.assertEqual(decoded["translation"], [-2048, 2047, -1])
        self.assertEqual(decoded["rotation_psx"], [0, 1024, 4080])
        self.assertEqual(decoded["opaque_nibble"], 10)
        with self.assertRaisesRegex(ImportError, "eight bytes"):
            decode_bone_transform(bytes(7))

    def test_frame_major_channel_order_and_counts(self):
        decoded = decode_animation_record(record())
        self.assertEqual((decoded["frame_count"], decoded["bone_count"]), (3, 2))
        self.assertEqual([[t["translation"][0] for t in f["object_transforms"]]
                          for f in decoded["frames"]], [[0, 1], [10, 11], [20, 21]])
        self.assertEqual([f["frame_index"] for f in decoded["frames"]], [0, 1, 2])

    def test_unknown_modes_truncation_padding_and_limits(self):
        raw = record()
        malformed = [raw[:-1], raw + bytes(1), raw[:-1] + b"\1"]
        for offset, value in ((0, 0x201), (2, 513), (4, 0x080D), (6, 0x0401), (0, 0)):
            modified = bytearray(raw)
            struct.pack_into("<H", modified, offset, value)
            malformed.append(bytes(modified))
        for candidate in malformed:
            with self.subTest(header=candidate[:8]), self.assertRaises(ImportError):
                decode_animation_record(candidate)

    def test_bundle_offsets_are_absolute_and_bounded(self):
        a, b = record(), record(1, 2)
        bundle = struct.pack("<III", 2, 12, 12 + len(a)) + a + b
        self.assertEqual(animation_record_ranges(bundle), ((12, 12 + len(a)), (12 + len(a), len(bundle))))
        for offsets in ((4, 12), (12, 12), (12, len(bundle) + 1)):
            broken = struct.pack("<III", 2, *offsets) + a + b
            with self.assertRaises(ImportError):
                animation_record_ranges(broken)

    def test_rigid_composition_is_rotate_then_translate_in_psx_axes(self):
        objects = [{"object_index": 0, "vertex_start": 0, "vertex_count": 3}]
        transforms = [{"object_index": 0, "translation": [10, -20, 30],
                       "rotation_psx": [1024, 1024, 1024]}]
        source = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        # Rx then Ry then Rz maps X->-Z, Y->Y, Z->X for this triple quarter-turn.
        expected = [[10, -20, 29], [10, -19, 30], [11, -20, 30]]
        posed = pose_vertices(source, objects, transforms)
        for row, want in zip(posed, expected):
            for actual, value in zip(row, want):
                self.assertAlmostEqual(actual, value)
        self.assertEqual(source, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    def test_pose_mapping_fails_on_missing_overlap_or_nonfinite_channels(self):
        vertices = [[1, 2, 3], [4, 5, 6]]
        objects = [{"object_index": 0, "vertex_start": 0, "vertex_count": 2}]
        transform = {"object_index": 0, "translation": [0, 0, 0], "rotation_psx": [0, 0, 0]}
        with self.assertRaisesRegex(ImportError, "mapping"):
            pose_vertices(vertices, objects, [])
        with self.assertRaisesRegex(ImportError, "without"):
            pose_vertices(vertices, [dict(objects[0], vertex_count=1)], [transform])
        with self.assertRaisesRegex(ImportError, "overlap"):
            pose_vertices(vertices, objects * 2, [transform] * 2)
        with self.assertRaisesRegex(ImportError, "finite"):
            pose_vertices(vertices, objects, [dict(transform, translation=[math.nan, 0, 0])])

    def test_unsupported_association_rejects_before_disc_access(self):
        for asset in ({}, None, {"semantic_id": "asset://town01/models/scene-tmd/0088"}):
            self.assertFalse(animation_capabilities(asset)["supported"])
            with self.assertRaisesRegex(ImportError, "Only the three"):
                load_animation_preview("missing.bin", asset)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from importer.pipeline import import_scene
        cls.disc = os.environ["LEGAIA_DISC_BIN"]
        scene = import_scene(cls.disc, "town01")
        cls.assets = [next(a for a in scene["assets"]["models"]
                          if a["semantic_id"] == f"asset://legaia/models/global-special/{i:04x}")
                      for i in (0xF0, 0xF1, 0xF2)]

    def test_all_three_party_banks_idle_and_walk(self):
        expected = {"idle": [15, 15, 15], "walk": [15, 10, 15]}
        for slot, asset in enumerate(self.assets):
            for clip in ("idle", "walk"):
                with self.subTest(slot=slot, clip=clip):
                    preview = load_animation_preview(self.disc, asset, clip)
                    self.assertEqual(preview["frame_count"], expected[clip][slot])
                    self.assertEqual(preview["source_record"]["record_index"], slot * 7 + (clip == "idle"))
                    self.assertEqual(preview["bone_count"], 10)
                    self.assertEqual(len(preview["geometry"]["objects"]), 10)
                    self.assertEqual(preview["timing"]["fps"], 30)
                    self.assertIsNone(preview["skeleton"]["hierarchy"])
                    self.assertTrue(any(f["vertices"] != preview["frames"][0]["vertices"]
                                        for f in preview["frames"][1:]), "clip must contain changing poses")
                    for frame in preview["frames"]:
                        self.assertEqual(len(frame["vertices"]), len(preview["geometry"]["vertices"]))
                        self.assertTrue(all(math.isfinite(c) for v in frame["vertices"] for c in v))
                        self.assertTrue(all(max(tri) < len(frame["vertices"]) for tri in preview["geometry"]["triangles"]))

    def test_model_locator_tampering_and_unknown_clip_fail(self):
        changed = deepcopy(self.assets[0])
        changed["source_record"]["byte_offset"] += 4
        with self.assertRaisesRegex(ImportError, "provenance"):
            load_animation_preview(self.disc, changed)
        with self.assertRaisesRegex(ImportError, "choose idle or walk"):
            load_animation_preview(self.disc, self.assets[0], "attack")


if __name__ == "__main__":
    unittest.main()
