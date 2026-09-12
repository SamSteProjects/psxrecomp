"""Overlapping PROT read windows must not lend the next scene's MAN table."""
import struct
from types import SimpleNamespace
import unittest
from importer.core import find_scene_bundle, ImportError, parse_scene_assets, parse_scene_table


class SceneBundleBoundaries(unittest.TestCase):
    def test_four_asset_directory_does_not_imply_man_source(self):
        data = bytearray(72)
        struct.pack_into('<I', data, 0, 4)
        for index, kind in enumerate((1, 2, 6, 7)):
            struct.pack_into('<II', data, 8 + index * 8, (kind << 24) | 8, 40 + index * 8)
        self.assertEqual(len(parse_scene_assets(data, 69).descriptors), 4)
        self.assertIsNone(parse_scene_table(data, 69))
        struct.pack_into('<I', data, 12, 32)
        self.assertIsNone(parse_scene_assets(data, 69))

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
