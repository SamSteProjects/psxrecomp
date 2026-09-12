"""Synthetic ISO metadata relocation across the insertion boundary."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.iso_relocation import (path_table_locations, relocate_path_table,
                                     relocate_directory_record, relocate_primary_descriptor)


def record(name, extent, size, directory=False):
    out = bytearray(33+len(name)+(not len(name) % 2))
    out[0], out[25], out[32] = len(out), 2 if directory else 0, len(name)
    out[33:33+len(name)] = name
    struct.pack_into('<I', out, 2, extent)
    struct.pack_into('>I', out, 6, extent)
    struct.pack_into('<I', out, 10, size)
    struct.pack_into('>I', out, 14, size)
    return bytes(out)


class IsoRelocationTests(unittest.TestCase):
    def test_directory_extent_size_and_rejection(self):
        original = record(b'PROT.DAT;1', 100, 4096)
        updated = relocate_directory_record(original, 100, 4096, 2)
        self.assertEqual(struct.unpack_from('<I', updated, 10)[0], 8192)
        self.assertEqual(struct.unpack_from('>I', updated, 14)[0], 8192)
        following = record(b'MOV', 102, 2048, True)
        shifted = relocate_directory_record(following, 100, 4096, 2)
        self.assertEqual(struct.unpack_from('<I', shifted, 2)[0], 104)
        self.assertEqual(struct.unpack_from('>I', shifted, 6)[0], 104)
        self.assertEqual(shifted[10:], following[10:])
        bad = bytearray(following); bad[6] ^= 1
        for value in [bytes(bad), record(b'OVERLAP', 99, 4096), following[:-1]]:
            with self.assertRaises(ImportError):
                relocate_directory_record(value, 100, 4096, 2)

    def test_descriptor_uses_actual_table_locations(self):
        pvd = bytearray(2048); pvd[:7] = b'\x01CD001\x01'
        for fmt, offset, value in [('<I',80,300),('>I',84,300),('<H',128,2048),
                                    ('>H',130,2048),('<I',132,10),('>I',136,10),
                                    ('<I',140,150),('>I',148,151)]:
            struct.pack_into(fmt,pvd,offset,value)
        pvd[156:190] = record(b'\x00', 152, 2048, True)
        out = relocate_primary_descriptor(bytes(pvd),100,4096,2)
        self.assertEqual([t['lba'] for t in path_table_locations(out)], [152,153])
        self.assertEqual(struct.unpack_from('<I',out,158)[0],154)
        self.assertEqual(struct.unpack_from('>I',out,162)[0],154)
        self.assertEqual(struct.unpack_from('<I',out,80)[0],302)
        self.assertEqual(relocate_primary_descriptor(bytes(pvd),100,4096,0),bytes(pvd))

    def test_path_table_endianness_padding_and_truncation(self):
        for endian in ('<','>'):
            table = bytes([3,0])+struct.pack(endian+'IH',102,1)+b'MOV\x00'
            shifted = relocate_path_table(table,102,2,big_endian=endian=='>')
            self.assertEqual(struct.unpack_from(endian+'I',shifted,2)[0],104)
            self.assertEqual(shifted[6:],table[6:])
            with self.assertRaises(ImportError):
                relocate_path_table(table[:-1],102,2,big_endian=endian=='>')


if __name__ == '__main__':
    unittest.main()
