"""Focused script-boundary and exact spawn-operand authoring regressions."""
from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.script_inspection import _instruction
from importer.script_reindex import reindex_spawn_operands


class ScriptReindexTests(unittest.TestCase):
    def test_rewrite_preserves_extended_target_and_opaque_spawn_like_bytes(self):
        source = bytes([0x44, 89, 0xc4, 7, 127, 0x2a, 0x44, 89])
        result, audit = reindex_spawn_operands(source, sha256(source).hexdigest(), 0,
                                               {89: 90, 127: 128})
        self.assertEqual(result, bytes([0x44, 90, 0xc4, 7, 128, 0x2a, 0x44, 89]))
        self.assertEqual([c['byte_offset'] for c in audit['changes']], [1, 4])
        self.assertEqual(audit['coverage'], 'partial')
        self.assertFalse(audit['complete_relocation_verified'])

    def test_reject_invalid_mapping_and_stale_source(self):
        source = b'\x44\x59'
        for mapping in ({89: 256}, {True: 90}, {89: False}, {}):
            with self.subTest(mapping=mapping), self.assertRaises(ImportError):
                reindex_spawn_operands(source, sha256(source).hexdigest(), 0, mapping)
        with self.assertRaises(ImportError):
            reindex_spawn_operands(source, '0'*64, 0, {89: 90})

    def test_bbox_branch_base_and_truncation(self):
        for prefix in (b'\x4d', b'\xcd\x07'):
            data = prefix+bytes([1, 2, 3, 4])+struct.pack('<h', -8)
            row = _instruction(data, 0)
            self.assertEqual(row['successors'][0]['pc'], len(data))
            self.assertEqual(row['successors'][1]['pc'], (len(prefix)+4-8)&65535)
            for end in range(len(prefix), len(data)):
                with self.assertRaises(ImportError):
                    _instruction(data[:end], 0)

    def test_fixed_payloads_do_not_decode_embedded_opcodes(self):
        for prefix in (b'\x4c', b'\xcc\x07'):
            for sub in range(0x10, 0x20):
                data = prefix+bytes([sub, 0x44, 89, 0x1f, 0x4d, 0])
                self.assertEqual(_instruction(data, 0)['length'], len(data))
            data = prefix+b'\x8a'+struct.pack('<hhh', -1, -32768, 32767)+b'\x12\x34\x56'
            row = _instruction(data, 0)
            self.assertEqual(row['operands']['signed_words'], [-1, -32768, 32767])
            self.assertEqual(row['operands']['packed_u24'], 0x563412)
            for end in range(len(prefix), len(data)):
                with self.assertRaises(ImportError):
                    _instruction(data[:end], 0)


if __name__ == '__main__':
    unittest.main()
