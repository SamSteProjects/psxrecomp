from hashlib import sha256
import random
import struct
import unittest
from uuid import uuid4

from importer.animation import animation_record_ranges
from importer.animation_allocation import append_animation_records
from importer.animation_bank_growth import grow_scene_animation_bank,qualify_animation_bank,rebuild_animation_bank_entry
from importer.animation_authoring import patch_animation_channels
from importer.core import ImportError,parse_scene_assets,decompress_lzs
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.serialization import compress_lzs
from test_animation_allocation import bank
from test_animation_glb import record
from test_model_pack_growth import pack_source,ledger_for
from test_model_pack_archive import archive_source


def fixture(offset=0):
    rng=random.Random(17)
    donor=record([[([rng.randrange(-2048,2048) for _ in range(3)],
                    [rng.randrange(256) for _ in range(3)]) for _ in range(64)] for _ in range(64)])
    original=bank([donor,b'opaque retained neighbor'],b'PAD!')
    expanded,_=append_animation_records(original,sha256(original).hexdigest(),[
        dict(record_id=str(uuid4()),donor_record_index=0,source_frame_indices=list(range(64)),edits=[])])
    pack,models=pack_source();streams=[b'HEAD',compress_lzs(original),compress_lzs(pack),b'TAIL opaque bytes']
    carrier=bytearray(b'P'*offset+bytes(40))
    struct.pack_into('<II',carrier,offset,4,0xAABBCCDD)
    for i,(kind,size,payload) in enumerate(zip((1,5,2,1),(4,len(original),len(pack),len(streams[-1])),streams)):
        struct.pack_into('<II',carrier,offset+8+i*8,(kind<<24)|size,len(carrier)-offset);carrier.extend(payload)
    return bytes(carrier),original,expanded,pack,models


class AnimationBankGrowth(unittest.TestCase):
    def test_compressed_descriptor_growth_at_nonzero_table_preserves_neighbors_and_prefix(self):
        for offset in (0,2048):
            carrier,original,expanded,_,_=fixture(offset)
            result,audit=grow_scene_animation_bank(carrier,sha256(carrier).hexdigest(),offset,1,sha256(original).hexdigest(),expanded)
            self.assertGreater(audit['growth_bytes'],2048)
            self.assertEqual(result[:offset],carrier[:offset])
            old=parse_scene_assets(carrier,0,offset);new=parse_scene_assets(result,0,offset)
            self.assertEqual(new.descriptors[1].size,len(expanded))
            self.assertEqual(decompress_lzs(result[offset+new.descriptors[1].data_offset:],len(expanded))[0],expanded)
            for i in (0,2,3):
                oldstart=offset+old.descriptors[i].data_offset;newstart=offset+new.descriptors[i].data_offset
                length=(old.descriptors[i+1].data_offset-old.descriptors[i].data_offset) if i<3 else len(carrier)-oldstart
                self.assertEqual(result[newstart:newstart+length],carrier[oldstart:oldstart+length])
            self.assertTrue(audit['following_payload_preserved'])

    def test_archive_combines_animation_and_model_growth_and_source_addressed_patches(self):
        carrier,original,expanded,pack,models=fixture()
        _,ledger=ledger_for(models[2],32,varied=True)
        requests=[dict(kind='animation-bank',entry_index=1,table_offset=0,descriptor_index=1,
            expected_bank_sha256=sha256(original).hexdigest(),bank=expanded),
            dict(entry_index=1,descriptor_index=2,expected_pack_sha256=sha256(pack).hexdigest(),replacements=[dict(slot_index=2,ledger=ledger)])]
        for header in (0,2048):
            source,starts=archive_source(carrier,header)
            patch=dict(offset=starts[1]*2048+40,payload=b'EDIT',source_sha256=sha256(b'HEAD').hexdigest())
            result,audit=compose_model_pack_archive(source,sha256(source).hexdigest(),list(reversed(requests)),[patch],header_offset=header)
            archive=_archive(result);raw=archive.read_entry(archive.entry(1));table=parse_scene_assets(raw,1)
            self.assertEqual(raw[40:44],b'EDIT')
            self.assertEqual(decompress_lzs(raw[table.descriptors[1].data_offset:],table.descriptors[1].size)[0],expanded)
            self.assertEqual(raw[table.descriptors[3].data_offset:table.descriptors[3].data_offset+17],b'TAIL opaque bytes')
            self.assertGreater(audit['growth_bytes'],0)
            self.assertTrue(audit['final_animation_banks_verified'])
            self.assertEqual(result[-8*2048:],source[-8*2048:])

    def test_noop_identity_and_existing_axes_are_qualified_but_opaque_mutation_rejects(self):
        carrier,original,expanded,_,_=fixture()
        result,_=grow_scene_animation_bank(carrier,sha256(carrier).hexdigest(),0,1,sha256(original).hexdigest(),original)
        self.assertEqual(result,carrier)
        ranges=animation_record_ranges(expanded);start,end=ranges[0]
        edited,_=patch_animation_channels(expanded[start:end],sha256(expanded[start:end]).hexdigest(),[
            dict(frame_index=0,object_index=0,translation={'x':33})])
        candidate=expanded[:start]+edited+expanded[end:]
        self.assertEqual(qualify_animation_bank(original,candidate)['allocated_record_count'],1)
        damaged=bytearray(candidate);damaged[ranges[1][0]]^=1
        with self.assertRaises(ImportError):qualify_animation_bank(original,bytes(damaged))
        damaged=bytearray(candidate);damaged[4+4*len(ranges)]^=1
        with self.assertRaises(ImportError):qualify_animation_bank(original,bytes(damaged))

    def test_stale_sources_wrong_descriptors_aliases_and_locators_reject(self):
        carrier,original,expanded,_,_=fixture()
        for args in [('0'*64,0,1,sha256(original).hexdigest()),(sha256(carrier).hexdigest(),True,1,sha256(original).hexdigest()),
                     (sha256(carrier).hexdigest(),0,2,sha256(original).hexdigest()),(sha256(carrier).hexdigest(),0,1,'0'*64)]:
            with self.assertRaises(ImportError):grow_scene_animation_bank(carrier,*args,expanded)
        damaged=bytearray(carrier);struct.pack_into('<I',damaged,12+2*8,struct.unpack_from('<I',carrier,12+8)[0])
        with self.assertRaises(ImportError):grow_scene_animation_bank(bytes(damaged),sha256(damaged).hexdigest(),0,1,sha256(original).hexdigest(),expanded)


if __name__=='__main__':unittest.main()
