"""Nested disc verification stays scoped and rejects changed input."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer import pipeline
from importer.core import ImportError, SUPPORTED_DISC_SHA256


class FakeImage:
    def __init__(self, path): self.path = path
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def find(self, name): return name
    def read_file(self, node): return b"synthetic metadata"


class VerifiedDiscScope(unittest.TestCase):
    def test_one_verification_per_outer_scope_and_change_rejection(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            path = Path(directory) / "fixture.bin"
            path.write_bytes(b"synthetic disc")
            stack.enter_context(patch.object(pipeline, "Mode2Image", FakeImage))
            hashed = stack.enter_context(patch.object(pipeline, "sha256_file", return_value=SUPPORTED_DISC_SHA256))
            stack.enter_context(patch.object(pipeline, "parse_cdname", return_value={2: "fixture"}))
            stack.enter_context(patch.object(pipeline, "ProtArchive", side_effect=lambda *_: object()))
            with pipeline._disc_context(path) as outer:
                with pipeline._disc_context(path) as nested:
                    self.assertIs(outer, nested)
                self.assertEqual(hashed.call_count, 1)
            self.assertIsNone(pipeline._active_disc_context.get())
            with pipeline._disc_context(path): pass
            self.assertEqual(hashed.call_count, 2)
            with self.assertRaisesRegex(ImportError, "changed"):
                with pipeline._disc_context(path):
                    path.write_bytes(b"a changed synthetic disc")
            with self.assertRaisesRegex(ImportError, "changed"):
                with pipeline._disc_context(path):
                    # Detect inner drift before the outer operation exits.
                    with self.assertRaisesRegex(ImportError, "changed"):
                        with pipeline._disc_context(path):
                            path.write_bytes(b"nested changed synthetic disc")
            self.assertIsNone(pipeline._active_disc_context.get())
            self.assertIsNone(pipeline._active_disc_context.get())
            with self.assertRaisesRegex(RuntimeError, "decoder failure"):
                with pipeline._disc_context(path):
                    raise RuntimeError("decoder failure")
            self.assertIsNone(pipeline._active_disc_context.get())


if __name__ == "__main__":
    unittest.main()
