"""Synthetic container checks for descriptor relocation and untouched payloads."""
from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, parse_scene_table, decompress_lzs
from importer.man_container import encode_man_candidate
from importer.serialization import compress_lzs


class ManContainerTests(unittest.TestCase):
    def test_growth_roundtrip_and_noop(self):
        source = b'original MAN candidate'
        stream = compress_lzs(source)
        header = bytearray(56)
        struct.pack_into('<I', header, 0, 6)
        offset = 56
        payload = stream
        for i in range(6):
            size = len(source) if i == 0 else 3
            struct.pack_into('<II', header, 8+i*8, ((3 if i == 0 else 1)<<24)|size, offset)
            offset += len(stream) if i == 0 else 3
            if i: payload += bytes([i])*3
        container = bytes(header)+payload
        args = (container, sha256(container).hexdigest(), 0, sha256(source).hexdigest())
        unchanged, audit = encode_man_candidate(*args, source)
        self.assertEqual(unchanged, container)
        self.assertEqual(audit['moved_descriptors'], [])
        candidate = bytes(range(256))
        with self.assertRaises(ImportError):
            encode_man_candidate(*args, candidate)
        result, audit = encode_man_candidate(*args, candidate, allow_growth=True)
        table = parse_scene_table(result, 0)
        decoded, _ = decompress_lzs(result[56:], len(candidate))
        self.assertEqual(decoded, candidate)
        self.assertEqual(audit['growth_bytes'] % 4, 0)
        for descriptor in table.descriptors[1:]:
            self.assertEqual(result[descriptor.data_offset:descriptor.data_offset+3],
                             bytes([descriptor.index])*3)


if __name__ == '__main__':
    unittest.main()
