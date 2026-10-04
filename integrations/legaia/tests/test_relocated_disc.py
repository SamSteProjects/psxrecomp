from hashlib import sha256
import struct
import unittest

from importer.core import ImportError, Mode2Image, MODE2_SECTOR
from importer.relocated_disc import RelocatedLogicalDisc
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from test_iso_relocation import record
import test_model_pack_composition as composition_fixtures


class LogicalSource(Mode2Image):
    def __init__(self):
        self.sectors=[bytes([index])*2048 for index in range(60)]
        self.size=60*MODE2_SECTOR;self.closed=False
        pvd=bytearray(2048);pvd[:7]=b'\x01CD001\x01'
        for fmt,offset,value in (('<I',80,60),('>I',84,60),('<H',128,2048),('>H',130,2048),
                                 ('<I',132,22),('>I',136,22),('<I',140,42),('>I',148,43)):
            struct.pack_into(fmt,pvd,offset,value)
        pvd[156:190]=record(b'\0',22,2048,True);self.sectors[16]=bytes(pvd)
        root=record(b'\0',22,2048,True)+record(b'\1',22,2048,True)+record(b'PROT.DAT;1',30,4096)+record(b'MOV',40,2048,True)
        self.sectors[22]=root.ljust(2048,b'\0')
        child=record(b'\0',40,2048,True)+record(b'\1',22,2048,True)+record(b'MOVIE.STR;1',48,2048)
        self.sectors[40]=child.ljust(2048,b'\0')
        for lba,endian in ((42,'<'),(43,'>')):
            table=bytes([1,0])+struct.pack(endian+'IH',22,1)+b'\0\0'+bytes([3,0])+struct.pack(endian+'IH',40,1)+b'MOV\0'
            self.sectors[lba]=table.ljust(2048,b'\0')
        self.root=self._directory_record(self.sectors[16],156)

    def user_sector(self,lba):return self.sectors[lba]
    def close(self):self.closed=True


class RelocatedDiscTests(unittest.TestCase):
    def test_reopens_iso_paths_tables_replacement_and_shifted_payload_without_export(self):
        source=LogicalSource();original=source.read_file(source.find('PROT.DAT'));replacement=b'R'*8192
        before=list(source.sectors)
        view=RelocatedLogicalDisc(source,replacement,sha256(original).hexdigest())
        self.assertEqual(view.read_file(view.find('PROT.DAT')),replacement)
        self.assertEqual(view.find('MOV').extent_lba,42);self.assertEqual(view.find('MOV/MOVIE.STR').extent_lba,50)
        self.assertEqual(view.read_file(view.find('MOV/MOVIE.STR')),source.sectors[48])
        self.assertEqual(struct.unpack_from('<I',view.user_sector(16),80)[0],62)
        self.assertEqual(struct.unpack_from('<I',view.user_sector(16),140)[0],44)
        self.assertEqual(struct.unpack_from('>I',view.user_sector(16),148)[0],45)
        self.assertEqual(struct.unpack_from('<I',view.user_sector(44),12)[0],42)
        self.assertEqual(struct.unpack_from('>I',view.user_sector(45),12)[0],42)
        for old in range(60):
            if old not in (16,22,30,31,40,42,43):
                self.assertEqual(view.user_sector(old+(2 if old>=32 else 0)),source.user_sector(old))
        self.assertEqual(source.sectors,before);view.close();self.assertFalse(source.closed)
        self.assertEqual(view.audit['growth_sectors'],2);self.assertTrue(view.audit['reopened_iso_prot_verified'])
        self.assertFalse(view.audit['runtime_connected']);self.assertFalse(view.audit['build_ready'])
        with self.assertRaises(ImportError):view._raw_sector(0)
        for lba in (-1,62,True):
            with self.assertRaises(ImportError):view.user_sector(lba)

    def test_same_size_replacement_and_exact_source_binding(self):
        source=LogicalSource();original=source.read_file(source.find('PROT.DAT'))
        view=RelocatedLogicalDisc(source,original,sha256(original).hexdigest())
        self.assertEqual(view.audit['growth_sectors'],0);self.assertEqual(view.audit['metadata_sectors'],[])
        for lba in range(60):self.assertEqual(view.user_sector(lba),source.user_sector(lba))
        for payload,digest in ((original,'stale'),(b'',sha256(original).hexdigest()),
                               (b'A'*2048,sha256(original).hexdigest()),(original+b'X',sha256(original).hexdigest())):
            with self.assertRaises(ImportError):RelocatedLogicalDisc(source,payload,digest)

    def test_composed_model_archive_reopens_through_relocated_iso_lookup(self):
        base=LogicalSource();raw,requests,patches=composition_fixtures.ModelPackCompositionTests().fixture()
        source=RelocatedLogicalDisc(base,raw,sha256(base.read_file(base.find('PROT.DAT'))).hexdigest())
        grown,audit=compose_model_pack_archive(raw,sha256(raw).hexdigest(),requests,patches)
        view=RelocatedLogicalDisc(source,grown,sha256(raw).hexdigest())
        reopened=view.read_file(view.find('PROT.DAT'));self.assertEqual(reopened,grown)
        archive=_archive(reopened);neighbor=archive.entry(3).start_lba*2048
        self.assertEqual(reopened[neighbor+10:neighbor+13],b'abc')
        self.assertEqual(view.read_file(view.find('MOV/MOVIE.STR')),base.sectors[48])
        self.assertEqual(view.audit['growth_sectors'],audit['growth_bytes']//2048)
        self.assertGreater(view.find('MOV/MOVIE.STR').extent_lba,source.find('MOV/MOVIE.STR').extent_lba)


if __name__=='__main__':unittest.main()
