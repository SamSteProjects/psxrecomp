"""Bounded synthetic serializer tests; optional retail package build validation."""
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from importer.core import ImportError, decompress_lzs, parse_man
from importer.serialization import compress_lzs, encode_placement_coordinate, patch_man_positions, serialize_man_stream
from integrations.legaia.tests.test_importer import synthetic_man


def literals(data):
    return b"".join(bytes([0xFF]) + data[start:start + 8] for start in range(0, len(data), 8))


class SerializationTests(unittest.TestCase):
    def test_every_retail_coordinate_has_exact_inverse(self):
        for encoded in range(256):
            decoded = (encoded & 127) * 128 + (128 if encoded & 128 else 64)
            self.assertEqual(encode_placement_coordinate(decoded), encoded)
        for value in [0, -64, 65, 9952, 16448, 64.5, True, float("nan"), 10 ** 1000]:
            with self.assertRaisesRegex(ImportError, "multiple of 64"):
                encode_placement_coordinate(value, "position.x")

    def test_man_unchanged_and_sparse_edit_preserve_opaque_bytes(self):
        original = synthetic_man()
        actor = parse_man(original).actors[0]
        unchanged, edits = patch_man_positions(original, "town01", {1: {"x": actor.world_x}})
        self.assertEqual(unchanged, original)
        self.assertEqual(edits, [])
        changed, edits = patch_man_positions(original, "town01", {1: {"x": actor.world_x + 64}})
        self.assertEqual(len(edits), 1)
        offset = edits[0]["decoded_byte_offset"]
        self.assertEqual(changed[:offset], original[:offset])
        self.assertEqual(changed[offset + 1:], original[offset + 1:])
        self.assertEqual(parse_man(changed).actors[0].world_x, actor.world_x + 64)
        with self.assertRaisesRegex(ImportError, "only X/Z"):
            patch_man_positions(original, "town01", {1: {"y": 64}})

    def test_lzs_encoder_decodes_exactly_for_ring_overlap_and_wrap(self):
        rng = random.Random(94254)
        cases = [b"", b"a", b"\0" * 6000, b"AB" * 4097, bytes(range(256)) * 40,
                 bytes(rng.randrange(256) for _ in range(7000)), synthetic_man()]
        cases += [bytes(rng.randrange(4) for _ in range(length)) for length in range(0, 128, 7)]
        for data in cases:
            encoded = compress_lzs(data)
            decoded, consumed = decompress_lzs(encoded, len(data))
            self.assertEqual(decoded, data)
            self.assertEqual(consumed, len(encoded))
            self.assertEqual(compress_lzs(data), encoded)

    def test_unchanged_stream_is_byte_exact_and_changed_span_keeps_its_length(self):
        original = synthetic_man()
        stream = literals(original)
        actor = parse_man(original).actors[0]
        no_change, edits, _ = serialize_man_stream(stream + b"OPAQUE", len(original), "town01", {1: {"x": actor.world_x}})
        self.assertEqual(no_change, stream)
        self.assertEqual(edits, [])
        changed, edits, sizes = serialize_man_stream(stream + b"OPAQUE", len(original), "town01", {1: {"x": actor.world_x + 64}})
        self.assertEqual(len(changed), len(stream))
        self.assertLessEqual(sizes["new_encoded_size"], len(stream))
        self.assertEqual(parse_man(decompress_lzs(changed, len(original))[0]).actors[0].world_x, actor.world_x + 64)

    def test_expanded_stream_and_escaping_output_fail_closed(self):
        original = synthetic_man()
        stream = compress_lzs(original)
        actor = parse_man(original).actors[0]
        with patch("importer.serialization.compress_lzs", side_effect=literals):
            with self.assertRaisesRegex(ImportError, "relocation is unsupported"):
                serialize_man_stream(stream, len(original), "town01", {1: {"x": actor.world_x + 64}})
        from sdk.build import _write_exact, BuildError
        with tempfile.TemporaryDirectory() as raw:
            boundary = Path(raw)
            with self.assertRaisesRegex(BuildError, "escapes"):
                _write_exact(boundary.parent / "outside.bin", b"x", boundary)
            output = boundary / "test.bin"
            _write_exact(output, b"original", boundary)
            with self.assertRaisesRegex(BuildError, "differs"):
                _write_exact(output, b"changed", boundary)
            self.assertEqual(output.read_bytes(), b"original")


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "LEGAIA_DISC_BIN is not set")
class RetailBuildTests(unittest.TestCase):
    def test_unrepresentable_rejected_and_representable_package_is_deterministic(self):
        from importer.pipeline import import_scene
        from sdk.project import ProjectService
        from sdk.build import build_project, BuildError
        disc = os.environ["LEGAIA_DISC_BIN"]
        metadata = import_scene(disc, "town01")
        actor = metadata["actors"][0]
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw), "Synthetic authoring validation")
            project.import_metadata(metadata, disc)
            project.command({"type": "set_transform", "entity_id": actor["semantic_id"],
                             "position": {"x": actor["imported_transform"]["position"]["x"] + 32}})
            with self.assertRaisesRegex(BuildError, "multiple of 64"):
                build_project(project)
            project.undo()
            project.command({"type": "set_transform", "entity_id": actor["semantic_id"],
                             "position": {"x": actor["imported_transform"]["position"]["x"] + 64}})
            first = build_project(project)
            second = build_project(project)
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["changed_fields"], 1)
            self.assertTrue(Path(first["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
