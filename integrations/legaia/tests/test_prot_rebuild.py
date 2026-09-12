"""Logical archive relocation with a raw end sentinel and terminal zero."""
from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.prot_rebuild import replace_physical_entry, rebuild_man_entries, patch_archive_spans, patch_streaming_man_entry


class ProtRebuildTests(unittest.TestCase):
    def test_streaming_man_roundtrip_retains_toc_and_neighbor_sectors(self):
        from test_importer import synthetic_man
        from importer.serialization import patch_man_positions
        original = synthetic_man()
        original += bytes((-len(original)) % 4)
        candidate, _ = patch_man_positions(original, 'town01', {1: {'x': 64}})
        chunk = struct.pack('<I', (3 << 24) | len(original)) + original
        container = (chunk + struct.pack('<I', (5 << 24) | 4) + b'pose' + bytes(4)).ljust(2048, b'\0')
        source = self.source()
        source = source[:2048] + container + source[4096:] + b'Z' * (8 * 2048)
        digest = sha256(source).hexdigest()
        man_hash = sha256(original).hexdigest()
        result, audit = patch_streaming_man_entry(source, digest, 0, 0, man_hash, candidate)
        self.assertEqual(result[:2048], source[:2048])
        self.assertEqual(result[2048 + len(chunk):], source[2048 + len(chunk):])
        self.assertEqual(result[2052:2052 + len(candidate)], candidate)
        self.assertTrue(audit['reopened_man_verified'])
        self.assertTrue(audit['toc_unchanged'])
        for index, offset, before, payload in [(True, 0, man_hash, candidate),
                                              (0, 4, man_hash, candidate),
                                              (0, 0, 'stale', candidate),
                                              (0, 0, man_hash, candidate + bytes(4))]:
            with self.assertRaises(ImportError):
                patch_streaming_man_entry(source, digest, index, offset, before, payload)

    def test_equal_span_assets_are_source_bound_and_disjoint(self):
        source=b'0123456789'
        digest=sha256(source).hexdigest()
        patches=[dict(offset=2,payload=b'AB',expected_sha256=sha256(b'23').hexdigest()),
                 dict(offset=7,payload=b'CD',expected_sha256=sha256(b'78').hexdigest())]
        result,audit=patch_archive_spans(source,digest,patches)
        self.assertEqual(result,b'01AB456CD9')
        self.assertEqual(patch_archive_spans(source,digest,patches[::-1]),(result,audit))
        for invalid in ([patches[0],patches[0]], [dict(patches[0],offset=9)],
                        [dict(patches[0],expected_sha256='stale')]):
            with self.assertRaises(ImportError):
                patch_archive_spans(source,digest,invalid)

    def test_multiple_man_owners_survive_prior_growth(self):
        import random
        from importer.serialization import compress_lzs
        baseline=b'original MAN'
        stream=compress_lzs(baseline)
        header=bytearray(56)
        struct.pack_into('<I',header,0,6)
        offset=56
        payload=stream
        for index in range(6):
            struct.pack_into('<II',header,8+index*8,((3 if index==0 else 1)<<24)|(len(baseline) if index==0 else 3),offset)
            offset+=len(stream) if index==0 else 3
            if index:payload+=bytes([index])*3
        container=(bytes(header)+payload).ljust(2048,b'\0')
        raw=bytearray(2048)+container+container+b'Z'*(2048*8)
        struct.pack_into('<ii',raw,4,5,1)
        struct.pack_into('<5I',raw,16,1,2,3,4,0)
        source=bytes(raw)
        entries=[dict(entry_index=i,table_offset=0,source_man_sha256=sha256(baseline).hexdigest(),
                      candidate=random.Random(i).randbytes(3000)) for i in (0,1)]
        result,audit=rebuild_man_entries(source,sha256(source).hexdigest(),entries)
        reverse,other=rebuild_man_entries(source,sha256(source).hexdigest(),list(reversed(entries)))
        self.assertEqual(result,reverse)
        self.assertEqual(audit,other)
        self.assertTrue(all(item['reopened_man_verified'] for item in audit['entries']))
        self.assertEqual(result[-2048:],b'Z'*2048)
        self.assertEqual(struct.unpack_from('<5I',result,16),(1,4,7,8,0))
        with self.assertRaisesRegex(ImportError,'distinct'):
            rebuild_man_entries(source,sha256(source).hexdigest(),[entries[0],entries[0]])

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
