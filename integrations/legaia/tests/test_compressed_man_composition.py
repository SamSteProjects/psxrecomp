"""Normal resource composition grows a native compressed MAN beside an ANM bank."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest
from importer.core import ImportError,parse_scene_assets,decompress_lzs,parse_man
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.man_actor_structure import append_actor_candidates
from importer.serialization import compress_lzs
from test_animation_bank_growth import fixture as bank_fixture
from test_man_actor_structure import fixture as man_fixture
from test_model_pack_archive import archive_source


class CompressedManComposition(unittest.TestCase):
    def test_shared_table_orders_patches_and_exact_final_payloads(self):
        _,bank,expanded,_,_=bank_fixture();man=man_fixture()
        candidate,_=append_actor_candidates(man,sha256(man).hexdigest(),[
            dict(id=f'npc-{i:02}',donor_record_index=1,position=dict(x=832,z=896)) for i in range(32)])
        for man_first in (False,True):
            resources=[(3,man),(5,bank)] if man_first else [(5,bank),(3,man)]
            carrier=bytearray(56);struct.pack_into('<II',carrier,0,6,0xAABBCCDD)
            for index,(kind,payload) in enumerate(resources+[(1,b'KEEP'),(1,b'opaque3'),(1,b'opaque4'),(1,b'opaque5')]):
                struct.pack_into('<II',carrier,8+8*index,(kind<<24)|len(payload),len(carrier))
                carrier.extend(compress_lzs(payload) if kind in (3,5) else payload)
            for header_offset in (0,2048):
                source,starts=archive_source(bytes(carrier),header_offset)
                table=parse_scene_assets(bytes(carrier),1);man_index=0 if man_first else 1;anm_index=1-man_index
                requests=[dict(kind='compressed-man',entry_index=1,table_offset=0,descriptor_index=man_index,
                    source_man_sha256=sha256(man).hexdigest(),candidate=candidate),
                    dict(kind='animation-bank',entry_index=1,table_offset=0,descriptor_index=anm_index,
                    expected_bank_sha256=sha256(bank).hexdigest(),bank=expanded)]
                patches=[dict(offset=starts[1]*2048+table.descriptors[2].data_offset,
                    source_sha256=sha256(b'KEEP').hexdigest(),payload=b'EDIT')]
                snapshot=deepcopy((requests,patches))
                result,audit=compose_model_pack_archive(source,sha256(source).hexdigest(),requests,patches,header_offset=header_offset)
                reverse,_=compose_model_pack_archive(source,sha256(source).hexdigest(),list(reversed(requests)),patches,header_offset=header_offset)
                self.assertEqual(result,reverse);self.assertEqual((requests,patches),snapshot)
                archive=_archive(result);raw=archive.read_entry(archive.entry(1));final=parse_scene_assets(raw,1)
                for index,expected in ((man_index,candidate),(anm_index,expanded)):
                    descriptor=final.descriptors[index]
                    self.assertEqual(decompress_lzs(raw[descriptor.data_offset:],descriptor.size)[0],expected)
                self.assertEqual(len(parse_man(candidate).actors),33)
                self.assertEqual(raw[final.descriptors[2].data_offset:final.descriptors[2].data_offset+4],b'EDIT')
                self.assertEqual(result[-8*2048:],source[-8*2048:])
                self.assertTrue(audit['final_compressed_man_verified']);self.assertGreater(len(result),len(source))
                for invalid in (requests+[requests[0]],[dict(requests[0],descriptor_index=anm_index)],
                    [dict(requests[0],source_man_sha256='0'*64)],[dict(requests[0],candidate=b'bad!')]):
                    with self.assertRaises(ImportError):
                        compose_model_pack_archive(source,sha256(source).hexdigest(),invalid,header_offset=header_offset)


if __name__=='__main__':unittest.main()
