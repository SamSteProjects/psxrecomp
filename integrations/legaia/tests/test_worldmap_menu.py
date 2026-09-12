import struct
import unittest
from importer.core import ImportError, validate_metadata_only
from importer.worldmap_menu import decode_worldmap_menu


def fixture():
    data=bytearray(0x64600);data[:8]=b'PS-X EXE';struct.pack_into('<I',data,0x18,0x80010000)
    for i in range(16):
        value=f'Landmark {i}'.encode();at=0x64318+i*32;data[at:at+len(value)]=value
    struct.pack_into('<BBHBB',data,0x64298,2,7,123,10,20)
    struct.pack_into('<BBHBB',data,0x6429e,19,9,456,30,40)
    data[0x642a4]=255
    return data

class WorldmapMenuTests(unittest.TestCase):
    def test_source_offsets_unknown_names_and_unobserved_flags(self):
        data=bytes(fixture());r=decode_worldmap_menu(data);validate_metadata_only(r)
        self.assertEqual(len(r['names']),16);self.assertEqual(len(r['placements']),2)
        row=r['placements'][0];self.assertEqual(row['name'],'Landmark 2');self.assertEqual(row['source_offset'],0x64298)
        self.assertEqual(row['discovery_flag_index'],39);self.assertEqual(row['destination_scene_id'],123)
        self.assertFalse(r['placements'][1]['resolved_name']);self.assertIsNone(r['placements'][1]['name'])
        self.assertEqual(r['runtime_state'],'not_observed');self.assertEqual(r,decode_worldmap_menu(data))
    def test_bad_header_bounds_and_missing_terminator_reject(self):
        for data in (b'bad',bytes(fixture()[:0x64000])):
            with self.assertRaises(ImportError):decode_worldmap_menu(data)
        data=fixture();data[0x64298:0x64298+384]=bytes(384)
        with self.assertRaisesRegex(ImportError,'terminator'):decode_worldmap_menu(bytes(data))

if __name__=='__main__':unittest.main()
