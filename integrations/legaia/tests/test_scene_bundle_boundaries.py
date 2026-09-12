"""Overlapping PROT read windows must not lend the next scene's MAN table."""
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.core import find_scene_bundle, ImportError, parse_scene_assets, parse_scene_table


class SceneBundleBoundaries(unittest.TestCase):
    def test_streaming_model_slots_reject_invalid_members_and_multiple_pools(self):
        from importer.core import streaming_scene_tmd_pool
        descriptor = SimpleNamespace(type_byte=2, size=32, data_offset=40, index=1)
        bundle = SimpleNamespace(descriptors=[descriptor])
        archive = SimpleNamespace(entry=lambda i:i, read_entry=lambda *a, **kw:bytes(100))
        body = struct.pack('<III', 2, 3, 5) + bytes(20)
        with patch('importer.core.parse_scene_assets', return_value=bundle), \
             patch('importer.core.decompress_lzs', return_value=(body, 32)), \
             patch('importer.core._tmd_extent', side_effect=[(8, 1), None]):
            with self.assertRaisesRegex(ImportError, 'slot 1 is invalid'):
                streaming_scene_tmd_pool(archive, 0, 1)
        with patch('importer.core.parse_scene_assets', return_value=bundle), \
             patch('importer.core.decompress_lzs', return_value=(body, 32)), \
             patch('importer.core._tmd_extent', return_value=(8, 1)):
            with self.assertRaisesRegex(ImportError, 'multiple TMD packs'):
                streaming_scene_tmd_pool(archive, 0, 2)

    def test_four_asset_directory_does_not_imply_man_source(self):
        data = bytearray(72)
        struct.pack_into('<I', data, 0, 4)
        for index, kind in enumerate((1, 2, 6, 7)):
            struct.pack_into('<II', data, 8 + index * 8, (kind << 24) | 8, 40 + index * 8)
        self.assertEqual(len(parse_scene_assets(data, 69).descriptors), 4)
        self.assertIsNone(parse_scene_table(data, 69))
        struct.pack_into('<I', data, 12, 32)
        self.assertIsNone(parse_scene_assets(data, 69))

    def test_five_asset_directory_keeps_man_selection_separate(self):
        data = bytearray(88)
        struct.pack_into('<I', data, 0, 5)
        for index, kind in enumerate((1, 2, 6, 7, 20)):
            struct.pack_into('<II', data, 8 + index * 8, (kind << 24) | 8, 48 + index * 8)
        self.assertEqual(len(parse_scene_assets(data, 319).descriptors), 5)
        self.assertIsNone(parse_scene_table(data, 319))

    def test_borrowed_tail_rejected_but_owned_table_kept(self):
        table=bytearray(128)
        struct.pack_into('<I',table,0,6)
        for index in range(6):
            struct.pack_into('<II',table,8+index*8,((3 if index==0 else 1)<<24)|1,56+index*4)
        entries=[SimpleNamespace(index=i,start_lba=i) for i in range(3)]
        raw=bytes(2048)+bytes(table)+bytes(2048-len(table))
        archive=SimpleNamespace(SECTOR=2048,entries=entries,node=SimpleNamespace(size=6144),
                                entry=lambda i:entries[i],read_entry=lambda e,extended:raw)
        with self.assertRaisesRegex(ImportError,'no supported'):
            find_scene_bundle(archive,0,1)
        # The same table really belongs to the wider range.
        bundle,_=find_scene_bundle(archive,0,2)
        self.assertEqual(bundle.table_offset,2048)
        raw=bytes(table)+bytes(4096-len(table))
        bundle,_=find_scene_bundle(archive,0,1)
        self.assertEqual(bundle.table_offset,0)


if __name__=='__main__':unittest.main()
