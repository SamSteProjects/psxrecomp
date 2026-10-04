from hashlib import sha256
import struct
import unittest
from importer.core import ImportError
from importer.relocated_disc import RelocatedLogicalDisc
from importer.disc_relocation_package import encode_relocation_package, decode_relocation_package, HEADER
import test_relocated_disc as fixtures


class RelocationPackageTests(unittest.TestCase):
    def fixture(self):
        source=fixtures.LogicalSource();original=source.read_file(source.find('PROT.DAT'))
        view=RelocatedLogicalDisc(source,b'R'*8192,sha256(original).hexdigest())
        data,audit=encode_relocation_package(view)
        return source,view,data,audit

    def test_complete_roundtrip_retains_prot_metadata_and_preimages(self):
        source,view,data,audit=self.fixture();result=decode_relocation_package(data,audit['sha256'])
        self.assertEqual(result['replacement'],view.replacement);self.assertEqual(result['metadata'],view.metadata)
        self.assertEqual(result['proposed_sector_count'],62);self.assertEqual(result['source_prot_sha256'],view.audit['source_prot_sha256'])
        for row in result['metadata_preimages']:
            self.assertEqual(row['source_sha256'],sha256(source.user_sector(row['source_lba'])).hexdigest())
        self.assertTrue(audit['readback_verified']);self.assertFalse(audit['runtime_connected'])

    def test_stale_hash_noncanonical_bounds_payload_and_records_reject(self):
        _,_,data,_=self.fixture()
        with self.assertRaises(ImportError):decode_relocation_package(data,'stale')
        for offset,value in ((8,2),(12,0),(16,60),(20,5),(24,1),(28,4097)):
            bad=bytearray(data);struct.pack_into('<I',bad,offset,value);bad=bytes(bad)
            with self.assertRaises(ImportError):decode_relocation_package(bad,sha256(bad).hexdigest())
        for offset in (HEADER.size,HEADER.size+8192+8+32+32):
            bad=bytearray(data);bad[offset]^=1;bad=bytes(bad)
            with self.assertRaises(ImportError):decode_relocation_package(bad,sha256(bad).hexdigest())
        for bad in (data[:-1],data+b'X'):
            with self.assertRaises(ImportError):decode_relocation_package(bad,sha256(bad).hexdigest())
        bad=bytearray(data);struct.pack_into('<I',bad,HEADER.size+8192+4,30);bad=bytes(bad)
        with self.assertRaises(ImportError):decode_relocation_package(bad,sha256(bad).hexdigest())


if __name__=='__main__':unittest.main()
