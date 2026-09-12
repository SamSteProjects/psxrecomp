"""Logical archive relocation with a raw end sentinel and terminal zero."""
from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.prot_rebuild import replace_physical_entry


class ProtRebuildTests(unittest.TestCase):
    def source(self):
        raw = bytearray(2048)+bytearray(b'A'*2048+b'B'*2048+b'C'*2048)
        struct.pack_into('<ii', raw, 4, 5, 1)
        struct.pack_into('<5I', raw, 16, 1, 2, 3, 4, 0)
        return bytes(raw)

    def test_growth_updates_end_sentinel_and_preserves_neighbors(self):
        raw = self.source()
        out, audit = replace_physical_entry(raw, sha256(raw).hexdigest(), 1, b'X'*4096)
        self.assertEqual(struct.unpack_from('<5I', out, 16), (1, 2, 4, 5, 0))
        self.assertEqual(out[2048:4096], b'A'*2048)
        self.assertEqual(out[4096:8192], b'X'*4096)
        self.assertEqual(out[8192:], b'C'*2048)
        self.assertEqual(audit['growth_sectors'], 1)
        same, _ = replace_physical_entry(raw, sha256(raw).hexdigest(), 1, b'B'*2048)
        self.assertEqual(same, raw)

    def test_invalid_sources_and_replacements_rejected(self):
        raw = self.source()
        for index, payload, digest in [(True, b'X'*2048, sha256(raw).hexdigest()),
                                       (3, b'X'*2048, sha256(raw).hexdigest()),
                                       (1, b'X', sha256(raw).hexdigest()),
                                       (1, b'', sha256(raw).hexdigest()),
                                       (1, b'X'*2048, 'stale')]:
            with self.assertRaises(ImportError):
                replace_physical_entry(raw, digest, index, payload)
        for starts in [(1, 3, 2, 4, 0), (1, 2, 0, 4, 0), (1, 2, 3, 5, 0)]:
            bad = bytearray(raw)
            struct.pack_into('<5I', bad, 16, *starts)
            bad = bytes(bad)
            with self.assertRaises(ImportError):
                replace_physical_entry(bad, sha256(bad).hexdigest(), 1, b'X'*4096)


if __name__ == '__main__':
    unittest.main()
