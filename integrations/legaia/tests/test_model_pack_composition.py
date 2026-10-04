from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from importer.core import ImportError, parse_scene_assets, decompress_lzs
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.serialization import compress_lzs
from test_model_pack_growth import pack_source, ledger_for, container_for
from test_model_pack_archive import archive_source


class ModelPackCompositionTests(unittest.TestCase):
    def fixture(self):
        pack,models=pack_source();carrier=container_for(pack).ljust(2048,b'\0')
        header=bytearray(2048);struct.pack_into('<ii',header,4,6,1)
        struct.pack_into('<6I',header,16,1,2,3,4,5,0)
        source=bytes(header)+b'A'*2048+carrier+carrier+b'B'*2048+b'Z'*(8*2048)
        _,ledger=ledger_for(models[2],32,varied=True)
        requests=[dict(entry_index=index,descriptor_index=1,expected_pack_sha256=sha256(pack).hexdigest(),
                       replacements=[dict(slot_index=2,ledger=ledger)]) for index in (1,2)]
        patches=[]
        for offset,payload in ((2*2048+40,b'EDIT'),(3*2048+40,b'NEXT'),(4*2048+10,b'abc')):
            patches.append(dict(offset=offset,payload=payload,source_sha256=sha256(source[offset:offset+len(payload)]).hexdigest()))
        return source,requests,patches

    def test_composition_preserves_patches_in_two_growing_carriers_and_shifted_neighbor(self):
        source,requests,patches=self.fixture();snapshot=deepcopy((requests,patches))
        result,audit=compose_model_pack_archive(source,sha256(source).hexdigest(),list(reversed(requests)),patches)
        self.assertGreater(audit['growth_bytes'],0);self.assertEqual((requests,patches),snapshot)
        archive=_archive(result)
        for index,lead in ((1,b'EDIT'),(2,b'NEXT')):
            start=archive.entry(index).start_lba*2048;self.assertEqual(result[start+40:start+44],lead)
            raw=archive.read_entry(archive.entry(index));table=parse_scene_assets(raw,index)
            descriptor=table.descriptors[1];pack,_=decompress_lzs(raw[descriptor.data_offset:],descriptor.size)
            self.assertEqual(sha256(pack).hexdigest(),audit['resources'][index-1]['carrier']['pack_audit']['proposed_sha256'])
            neighbor=table.descriptors[2];self.assertEqual(raw[neighbor.data_offset:neighbor.data_offset+8],b'NEIGHBOR')
        start=archive.entry(3).start_lba*2048;self.assertEqual(result[start:start+2048],b'B'*10+b'abc'+b'B'*(2048-13))
        self.assertEqual(result[-8*2048:],source[-8*2048:]);self.assertTrue(audit['final_packs_verified'])
        self.assertFalse(audit['build_ready']);self.assertFalse(audit['gameplay_verified'])

    def test_patch_conflicts_stale_preimages_header_and_owned_pack_mutation_reject(self):
        source,requests,patches=self.fixture()
        for changes in (patches+[patches[0]], [dict(patches[0],source_sha256='0'*64)],
                        [dict(patches[0],offset=16)], [dict(patches[0],offset=True)],
                        [dict(patches[0],payload=b'')], [dict(patches[0],offset=len(source))]):
            with self.assertRaises(ImportError):compose_model_pack_archive(source,sha256(source).hexdigest(),requests,changes)
        offset=2*2048+44
        damaged=dict(offset=offset,payload=bytes([source[offset]^1]),source_sha256=sha256(source[offset:offset+1]).hexdigest())
        with self.assertRaises(ImportError):compose_model_pack_archive(source,sha256(source).hexdigest(),requests,[damaged])

    def test_two_resources_in_one_carrier_reopen_after_both_relocations(self):
        pack,models=pack_source();stream=compress_lzs(pack);carrier=bytearray(40)
        struct.pack_into('<II',carrier,0,4,0xAABBCCDD)
        for index,payload in enumerate((b'LEAD',stream,stream,b'TAIL')):
            struct.pack_into('<II',carrier,8+index*8,((2 if index in (1,2) else 1)<<24)|
                             (len(pack) if index in (1,2) else len(payload)),len(carrier))
            carrier.extend(payload)
        _,ledger=ledger_for(models[2],32,varied=True)
        requests=[dict(entry_index=1,descriptor_index=index,expected_pack_sha256=sha256(pack).hexdigest(),
                       replacements=[dict(slot_index=2,ledger=ledger)]) for index in (1,2)]
        for header_offset in (0,2048):
            source,starts=archive_source(bytes(carrier),header_offset)
            offset=starts[1]*2048+40;patch=dict(offset=offset,payload=b'EDIT',source_sha256=sha256(b'LEAD').hexdigest())
            result,audit=compose_model_pack_archive(source,sha256(source).hexdigest(),requests,[patch],header_offset=header_offset)
            archive=_archive(result);raw=archive.read_entry(archive.entry(1));table=parse_scene_assets(raw,1)
            self.assertEqual(raw[40:44],b'EDIT');self.assertGreater(table.descriptors[2].data_offset,44+len(stream))
            self.assertEqual(raw[table.descriptors[3].data_offset:table.descriptors[3].data_offset+4],b'TAIL')
            self.assertEqual(len(audit['resources']),2);self.assertTrue(audit['final_packs_verified'])

    def test_duplicate_malformed_requests_and_source_reject(self):
        source,requests,patches=self.fixture()
        for changes in ([],requests+[requests[0]], [dict(requests[0],entry_index=True)],
                        [dict(requests[0],unexpected=1)],requests*17):
            with self.assertRaises(ImportError):compose_model_pack_archive(source,sha256(source).hexdigest(),changes,patches)
        with self.assertRaises(ImportError):compose_model_pack_archive(source,'stale',requests,patches)
        with self.assertRaises(ImportError):compose_model_pack_archive(source,sha256(source).hexdigest(),requests,patches,header_offset=True)


if __name__=='__main__':unittest.main()
