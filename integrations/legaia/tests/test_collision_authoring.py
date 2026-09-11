"""Exact collision wall-bit writes preserve unrelated MAP content."""
from hashlib import sha256
import unittest

from importer.collision_authoring import patch_collision_walls
from importer.core import ImportError


class CollisionAuthoringTests(unittest.TestCase):
    def test_all_byte_values_and_quadrants_preserve_every_other_bit(self):
        source = bytearray(0x12000)
        edits = []
        for value in range(256):
            row, column = 1 + value // 128, value % 128
            source[0x4000 + row * 128 + column] = value
            for q in range(4):
                edits.append(dict(row=row, column=column, quadrant=q, blocked=not bool(value & (16 << q))))
        source = bytes(source)
        result, audit = patch_collision_walls(source, sha256(source).hexdigest(), edits)
        self.assertEqual(len(audit), 1024)
        for i, (before, after) in enumerate(zip(source, result)):
            self.assertEqual(after, before ^ 0xf0 if 0x4080 <= i < 0x4180 else before)
        restored, _ = patch_collision_walls(result, sha256(result).hexdigest(), [{**e, "blocked": not e["blocked"]} for e in edits])
        self.assertEqual(restored, source)
        self.assertEqual(patch_collision_walls(source, sha256(source).hexdigest(), list(reversed(edits))), (result, audit))

    def test_invalid_edits_fail_and_noop_preserves_source(self):
        source = bytes(0x12000)
        digest = sha256(source).hexdigest()
        edit = dict(row=1, column=0, quadrant=0, blocked=False)
        self.assertEqual(patch_collision_walls(source, digest, [edit]), (source, []))
        for invalid in ([{**edit, "row": 0}], [{**edit, "row": True}], [{**edit, "column": 128}],
                        [{**edit, "quadrant": 4}], [{**edit, "blocked": 1}], [{**edit, "extra": 0}],
                        [edit, edit], [edit] * 4097, None):
            with self.subTest(invalid=str(invalid)[:80]), self.assertRaises(ImportError):
                patch_collision_walls(source, digest, invalid)
        with self.assertRaises(ImportError):
            patch_collision_walls(source, "0" * 64, [])
        with self.assertRaises(ImportError):
            patch_collision_walls(source[:-1], digest, [])
