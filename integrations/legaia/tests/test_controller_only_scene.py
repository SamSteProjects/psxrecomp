"""Actor-free descriptor scenes retain a unique bounded controller and source bytes."""
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from importer.core import ImportError, parse_man
from importer.man_source import read_man_source


def controller_man(counts=(2, 1, 0), offsets=(0, 8, 16), section=24):
    base = 43 + sum(counts) * 3
    payload = bytearray(base + section + 18)
    struct.pack_into('<hhh', payload, 34, *counts)
    payload[40:43] = section.to_bytes(3, 'little')
    for i, offset in enumerate(offsets):
        payload[43+i*3:46+i*3] = offset.to_bytes(3, 'little')
    return bytes(payload)


class ControllerOnlyScene(unittest.TestCase):
    def read(self, payload):
        descriptor = SimpleNamespace(type_byte=3, size=len(payload), data_offset=16)
        bundle = SimpleNamespace(entry_index=2, table_offset=0, descriptors=[descriptor])
        with patch('importer.man_source.find_scene_bundle', return_value=(bundle, bytes(48))), \
                patch('importer.man_source.decompress_lzs', return_value=(payload, 20)):
            return read_man_source(object(), 0, 4, 'fixture')

    def test_bounded_controller_is_a_scene_without_invented_actors(self):
        payload = controller_man()
        source = self.read(payload)
        self.assertEqual(source.kind, 'descriptor_man')
        self.assertEqual(source.payload, payload)
        self.assertEqual(source.parsed.partition_counts, (2, 1, 0))
        self.assertEqual(source.parsed.actors, ())

    def test_duplicate_or_outside_record_ownership_refuses(self):
        for offsets in [(0, 8, 8), (0, 8, 24), (0, 8, 100)]:
            with self.subTest(offsets=offsets), self.assertRaisesRegex(ImportError, 'ownership is invalid'):
                self.read(controller_man(offsets=offsets))

    def test_missing_partition_one_controller_refuses(self):
        with self.assertRaisesRegex(ImportError, 'unique scene controller'):
            self.read(controller_man(counts=(3, 0, 0)))

    def test_raw_streaming_empty_source_still_refuses(self):
        candidate = dict(entry_index=2, payload_offset=4, payload=controller_man(), chunk_header_offset=0)
        with patch('importer.man_source.find_scene_bundle', side_effect=ImportError('missing')), \
                patch('importer.man_source.find_streaming_man_candidates', return_value=[candidate]):
            with self.assertRaisesRegex(ImportError, 'streaming MAN has no actor'):
                read_man_source(object(), 0, 4, 'fixture')


if __name__ == '__main__':
    unittest.main()
