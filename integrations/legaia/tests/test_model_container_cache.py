"""Operation-owned model LZS reuse preserves immutable bytes and locator guards."""
from contextlib import nullcontext
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import struct
import unittest
from importer import assets
from importer.core import ImportError, ProtEntry


def container(*sections):
    header = bytearray(8 + 8 * (len(sections) + 1))
    streams = bytearray()
    for index, body in enumerate(sections):
        struct.pack_into('<II', header, 8 + index * 8, len(body), len(header) + len(streams))
        for start in range(0, len(body), 8):
            chunk = body[start:start + 8]
            streams.append((1 << len(chunk)) - 1)
            streams.extend(chunk)
    return bytes(header + streams)


class ModelContainerCacheTests(unittest.TestCase):
    def fixture(self):
        entry = ProtEntry(3, 4, 1, 1)
        archive = SimpleNamespace(_model_lzs_sections={}, entry=lambda index: entry,
                                  read_entry=lambda entry: container(b'abcdefgh', b'ijklmnop'))
        source = dict(prot_entry_index=3, byte_offset=0, byte_length=4, containing_size=8,
                      iso_file='PROT.DAT', disc={'sha256': 'a' * 64},
                      record_kind='decoded_lzs_section', container_section=0,
                      compressed_stream_offset=32)
        asset = dict(asset_kind='tmd_model', semantic_id='model://fixture/1', source_record=source)
        self.enterContext(patch.object(assets, '_disc_context', side_effect=lambda _: nullcontext((None, 'a' * 64, None, archive))))
        decoded = self.enterContext(patch.object(assets, 'decompress_lzs', wraps=assets.decompress_lzs))
        return archive, asset, decoded

    def test_shared_container_distinct_spans_and_sections_are_exact(self):
        archive, asset, decoded = self.fixture()
        before = deepcopy(asset)
        self.assertEqual(assets.load_model_source('fixture', asset), b'abcd')
        other = deepcopy(asset); other['source_record']['byte_offset'] = 4
        self.assertEqual(assets.load_model_source('fixture', other), b'efgh')
        self.assertEqual(decoded.call_count, 1)
        other['source_record'].update(container_section=1, compressed_stream_offset=41)
        self.assertEqual(assets.load_model_source('fixture', other), b'mnop')
        self.assertEqual(decoded.call_count, 2)
        self.assertEqual(asset, before)
        self.assertTrue(all(isinstance(row[1], bytes) for row in archive._model_lzs_sections.values()))

    def test_warm_cache_cannot_hide_changed_locator_or_disc_identity(self):
        archive, asset, decoded = self.fixture()
        assets.load_model_source('fixture', asset)
        for field, value in [('compressed_stream_offset', 33), ('container_section', -1),
                             ('container_section', 2), ('containing_size', 9), ('byte_offset', 7),
                             ('disc', {'sha256': 'b' * 64})]:
            altered = deepcopy(asset); altered['source_record'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ImportError):
                assets.load_model_source('fixture', altered)
        self.assertEqual(decoded.call_count, 1)
        self.assertEqual(assets.load_model_source('fixture', asset), b'abcd')

    def test_entry_identity_and_recent_hits_control_reuse(self):
        archive, asset, decoded = self.fixture()
        archive.entry = lambda index: ProtEntry(index, index + 1, 1, 1)
        archive.read_entry = lambda entry: container(bytes([entry.index]) * 8)
        asset['source_record']['compressed_stream_offset'] = 24
        with patch.object(assets, 'MAX_MODEL_CONTAINER_CACHE_ENTRIES', 2):
            def read(index):
                selected = deepcopy(asset); selected['source_record']['prot_entry_index'] = index
                return assets.load_model_source('fixture', selected)
            self.assertEqual(read(3), b'\x03' * 4)
            self.assertEqual(read(4), b'\x04' * 4)
            read(3)  # Recent hit protects entry 3 when entry 5 arrives.
            self.assertEqual(read(5), b'\x05' * 4)
            read(3)
            self.assertEqual(decoded.call_count, 3)
            read(4)
            self.assertEqual(decoded.call_count, 4)

    def test_lru_count_and_byte_bounds_force_fresh_derivation(self):
        for limit in ('MAX_MODEL_CONTAINER_CACHE_ENTRIES', 'MAX_MODEL_CONTAINER_CACHE_BYTES'):
            archive, asset, decoded = self.fixture()
            with patch.object(assets, limit, 1 if limit.endswith('ENTRIES') else 8):
                assets.load_model_source('fixture', asset)
                other = deepcopy(asset); other['source_record'].update(container_section=1, compressed_stream_offset=41)
                assets.load_model_source('fixture', other)
                self.assertEqual(len(archive._model_lzs_sections), 1)
                assets.load_model_source('fixture', asset)
                self.assertEqual(decoded.call_count, 3)

    def test_oversized_cache_item_and_decoder_failure_are_not_retained(self):
        archive, asset, decoded = self.fixture()
        with patch.object(assets, 'MAX_MODEL_CONTAINER_CACHE_BYTES', 4):
            assets.load_model_source('fixture', asset)
            self.assertFalse(archive._model_lzs_sections)
        with patch.object(assets, 'decompress_lzs', side_effect=ImportError('truncated')):
            with self.assertRaisesRegex(ImportError, 'truncated'):
                assets.load_model_source('fixture', asset)
        self.assertFalse(archive._model_lzs_sections)


if __name__ == '__main__': unittest.main()
