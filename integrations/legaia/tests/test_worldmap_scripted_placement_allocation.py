from copy import deepcopy
import struct
from unittest import TestCase

from importer.core import ImportError
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from test_worldmap_placement_allocation import fixture as placement_fixture, request
from test_worldmap_object_binds import fixture as man_fixture


def fixture(dc=0):
    raw,floor=placement_fixture();data=bytearray(raw)
    struct.pack_into('<H',data,9*32+18,0x17)
    struct.pack_into('<2b',data,9*32+6,dc,0)
    # Keep one donor footprint; its adjacent anchor is model-free terrain.
    struct.pack_into('<H',data,0x8000+101*2,0x1000|10)
    anchor=100+dc
    word=struct.unpack_from('<H',data,0x8000+anchor*2)[0]
    struct.pack_into('<H',data,0x8000+anchor*2,word|0x400)
    for cell in (200,201):struct.pack_into('<H',data,0x8000+cell*2,0x3000|10)
    struct.pack_into('<hh',data,0x10006,0x20,1)
    data[0x10020:0x10024]=bytes([anchor,0,0,0x83])
    man,_=man_fixture();row=request();row['shared_script']=True
    return bytes(data),bytes(0x2000),man,floor,[row]


class ScriptedWorldPlacementTests(TestCase):
    def test_literal_composed_map_and_separate_anchor(self):
        for dc in (0,1):
            with self.subTest(dc=dc):
                raw,fallback,man,floor,requests=fixture(dc);held=deepcopy(requests)
                candidate,audit=allocate_scripted_placements(raw,fallback,man,floor,'map01',requests,relocation_offset=0x40)
                expected=bytearray(raw);at=4*32
                expected[at:at+32]=raw[9*32:10*32]
                expected[at+20:at+24]=raw[10*32+20:10*32+24]
                struct.pack_into('<3h',expected,at,128,-16,48)
                struct.pack_into('<H',expected,at+10,0xa400)
                struct.pack_into('<H',expected,0x8000+200*2,0x3004)
                anchor_at=0x8000+(200+dc)*2
                struct.pack_into('<H',expected,anchor_at,struct.unpack_from('<H',expected,anchor_at)[0]|0x400)
                expected[0x10006:0x1000a]=bytes([0x40,0,2,0])
                expected[0x10040:0x10048]=bytes([100+dc,0,0,0x83,(200%128)+dc,200//128,0,0x83])
                self.assertEqual(candidate,bytes(expected));self.assertEqual(requests,held)
                self.assertEqual(audit['allocations'][0]['native_seed']['source_bind_owner'],'init_bind')
                self.assertEqual((audit['original_placement_count'],audit['proposed_placement_count']),(1,2))
                self.assertFalse(audit['gameplay_verified'])

    def test_scope_domains_and_existing_owners_refuse(self):
        for change in ({'shared_script':False},{'shared_script':1},{'donor_cell':101},{'target_cell':True},
                       {'record_index':9},{'record_index':True},{'extra':0}):
            raw,fallback,man,floor,requests=fixture();requests[0].update(change)
            with self.subTest(change=change),self.assertRaises(ImportError):
                allocate_scripted_placements(raw,fallback,man,floor,'map01',requests)
        for case in ('anchor_owned','target_bind','duplicate','outside','anchor_model'):
            raw,fallback,man,floor,requests=fixture(1);data=bytearray(raw)
            if case=='anchor_owned':struct.pack_into('<H',data,0x8000+201*2,0x340a)
            if case=='target_bind':
                struct.pack_into('<h',data,0x10008,2);data[0x10024:0x10028]=bytes([73,1,1,0])
            if case=='duplicate':requests.append(deepcopy(requests[0]))
            if case=='outside':
                struct.pack_into('<H',data,0x8000+255*2,0x300a);requests[0]['target_cell']=255
            if case=='anchor_model':struct.pack_into('<H',data,0x8000+201*2,0x1009)
            with self.subTest(case=case),self.assertRaises(ImportError):
                allocate_scripted_placements(bytes(data),fallback,man,floor,'map01',requests,relocation_offset=0x40)
