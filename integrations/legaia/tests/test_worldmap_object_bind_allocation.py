"""Complete-byte checks for donor-derived World init binds."""
from copy import deepcopy
import struct
from unittest import TestCase

from importer.core import ImportError
from importer.worldmap_object_bind_allocation import allocate_object_bind_rows
from test_worldmap_object_binds import fixture


def inputs():
    data=bytearray(0x12000)
    struct.pack_into('<hh',data,0x10006,0x20,1)
    data[0x10020:0x10024]=bytes([8,9,0,0x83])
    man,_=fixture()
    request=dict(bind_id='bind://authored/11111111-1111-4111-8111-111111111111',
                 donor_index=0,tile_x=10,tile_z=11)
    return bytes(data),bytes(0x2000),man,[request]


class WorldObjectBindAllocationTests(TestCase):
    def test_literal_relocation_keeps_old_rows_and_other_tables(self):
        source,fallback,man,requests=inputs();data=bytearray(source)
        struct.pack_into('<hh',data,0x1000a,0x26,1)
        data[0x10026:0x1002a]=bytes([40,41,42,43]);source=bytes(data)
        actual,audit=allocate_object_bind_rows(source,fallback,man,'map01',requests,relocation_offset=0x40)
        expected=bytearray(source)
        expected[0x10006:0x1000a]=bytes([0x40,0,2,0])
        expected[0x10040:0x10048]=bytes([8,9,0,0x83,10,11,0,0x83])
        self.assertEqual(actual,bytes(expected))
        self.assertEqual(audit['relocation']['after_hex'],'08090083')
        self.assertEqual(audit['proposed_table_offset'],0x40)

    def test_relocation_destination_refusals(self):
        for at in (True,-2,0x10,0x21,0x20,0x1ffc,0x2000):
            source,fallback,man,requests=inputs()
            with self.subTest(at=at),self.assertRaises(ImportError):
                allocate_object_bind_rows(source,fallback,man,'map01',requests,relocation_offset=at)
        source,fallback,man,requests=inputs();data=bytearray(source);data[0x10043]=1
        with self.assertRaises(ImportError):
            allocate_object_bind_rows(bytes(data),fallback,man,'map01',requests,relocation_offset=0x40)

    def test_literal_complete_map_and_immutable_donor(self):
        source,fallback,man,requests=inputs();held=deepcopy(requests)
        actual,audit=allocate_object_bind_rows(source,fallback,man,'map01',requests)
        expected=bytearray(source)
        expected[0x10008:0x1000a]=b'\x02\x00'
        expected[0x10024:0x10028]=bytes([10,11,0,0x83])
        self.assertEqual(actual,bytes(expected));self.assertEqual(requests,held)
        row=audit['allocations'][0]
        self.assertEqual((row['gate_byte'],row['flat_man_record_index'],row['encoded_animation_selector']),(0x83,0,5))
        self.assertEqual(row['script_id'],'script://map01/worldmap/man-p0/0000')
        self.assertFalse(audit['gameplay_verified']);self.assertFalse(audit['placement_allocated'])

    def test_unclaimed_space_and_table_ownership(self):
        for case in ('nonzero','other_table','overlap','missing_donor','end'):
            with self.subTest(case=case):
                source,fallback,man,requests=inputs();data=bytearray(source)
                if case=='nonzero':data[0x10024]=1
                if case=='other_table':struct.pack_into('<hh',data,0x1000a,0x24,1)
                if case=='overlap':struct.pack_into('<hh',data,0x1000a,0x20,1)
                if case=='missing_donor':struct.pack_into('<h',data,0x10008,0)
                if case=='end':
                    struct.pack_into('<hh',data,0x10006,0x1ffc,1)
                    data[0x11ffc:]=bytes([8,9,0,0x83])
                with self.assertRaises(ImportError):allocate_object_bind_rows(bytes(data),fallback,man,'map01',requests)

    def test_no_primary_or_fallback_shadowing(self):
        for case in ('primary','fallback','donor'):
            with self.subTest(case=case):
                source,fallback,man,requests=inputs();data=bytearray(source);fb=bytearray(fallback)
                if case=='primary':requests[0].update(tile_x=8,tile_z=9)
                if case=='fallback':
                    struct.pack_into('<hh',fb,6,0x20,1);fb[0x20:0x24]=bytes([10,11,1,0])
                if case=='donor':
                    struct.pack_into('<h',data,0x10008,2)
                    data[0x10024:0x10028]=bytes([8,9,1,0]);requests[0]['donor_index']=1
                with self.assertRaises(ImportError):allocate_object_bind_rows(bytes(data),bytes(fb),man,'map01',requests)

    def test_invalid_domains_and_man_ownership(self):
        for change in ({'tile_x':True},{'tile_z':128},{'donor_index':True},
                       {'donor_index':1},{'bind_id':'foreign'},{'extra':0}):
            source,fallback,man,requests=inputs();requests[0].update(change)
            with self.assertRaises(ImportError):allocate_object_bind_rows(source,fallback,man,'map01',requests)
        for case in ('partition','alias','header','budget','duplicate_id','duplicate_tile'):
            source,fallback,man,requests=inputs()
            if case=='partition':
                man,_=fixture((1,1,0));data=bytearray(source);data[0x10022]=1;source=bytes(data)
            if case=='alias':
                data=bytearray(man);data[0x2e:0x31]=bytes(3);man=bytes(data)
            if case=='header':
                data=bytearray(man);data[0x31]=1;man=bytes(data)
            if case=='budget':requests*=33
            if case.startswith('duplicate'):
                other=deepcopy(requests[0])
                if case=='duplicate_id':other.update(tile_x=12,tile_z=13)
                else:other['bind_id']='bind://authored/22222222-2222-4222-8222-222222222222'
                requests.append(other)
            with self.subTest(case=case),self.assertRaises(ImportError):
                allocate_object_bind_rows(source,fallback,man,'map01',requests)
