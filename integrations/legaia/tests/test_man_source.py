"""Source selection must preserve compression and reject ambiguous carriers."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from importer.core import ImportError
from importer.man_source import read_man_source


class ManSourceTests(TestCase):
    def test_raw_source_is_explicit_and_ambiguous_sources_are_rejected(self):
        candidate = dict(entry_index=70, payload_offset=4, payload=b'raw-man', chunk_header_offset=0)
        with patch('importer.man_source.find_scene_bundle', side_effect=ImportError('missing')), \
             patch('importer.man_source.find_streaming_man_candidates', return_value=[candidate]) as discover, \
             patch('importer.man_source.parse_man', return_value=SimpleNamespace(actors=[object()])):
            source = read_man_source(object(), 66, 75, 'dolk2')
            self.assertEqual(source.kind, 'raw_streaming_man')
            self.assertEqual(source.provenance()['compression'], 'none')
            self.assertEqual(source.provenance()['payload_offset'], 4)
            self.assertIsNone(source.bundle)
            discover.return_value = [candidate, candidate]
            with self.assertRaisesRegex(ImportError, 'no unique MAN source'):
                read_man_source(object(), 66, 75, 'dolk2')

    def test_bad_descriptor_does_not_fall_back_and_decode_is_bounded(self):
        descriptor = SimpleNamespace(type_byte=3, size=80, data_offset=16)
        following = SimpleNamespace(type_byte=1, size=80, data_offset=32)
        bundle = SimpleNamespace(entry_index=2, table_offset=4, descriptors=[descriptor, following])
        raw = bytes(range(64))
        with patch('importer.man_source.find_scene_bundle', return_value=(bundle, raw)), \
             patch('importer.man_source.find_streaming_man_candidates') as discover, \
             patch('importer.man_source.decompress_lzs', side_effect=ImportError('bad LZS')) as decode:
            with self.assertRaisesRegex(ImportError, 'bad LZS'):
                read_man_source(object(), 0, 4, 'town01')
            decode.assert_called_once_with(raw[20:36], 80)
            discover.assert_not_called()
