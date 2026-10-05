from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from importer.core import ImportError, _pack_ranges, decompress_lzs, parse_scene_assets
from importer.model_face_ledger import create_face_ledger, append_face_ledger
from importer.model_pack_growth import grow_model_pack
from importer.model_pack_archive import _archive, rebuild_model_pack_entry
from sdk.model_growth import prepare_model_growth
from sdk.model_face_addition import source, review
from sdk.project import ProjectError
import test_model_face_addition_project as fixtures
from test_model_pack_growth import pack_source, container_for
from test_model_pack_archive import archive_source
from test_project_workflow import synthetic_scene


class ModelGrowthTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelFaceAdditionProjectTests();self.addCleanup(helper.doCleanups)
        p,asset,original,current=helper.project('tmd-shape')
        pack,models=pack_source();self.assertEqual(original,models[1])
        other='asset://fixture/model/other';p._model_source=lambda identifier,*args:{asset:models[1],other:models[0]}[identifier]
        doc=synthetic_scene();ranges=_pack_ranges(pack)
        doc['assets']['models']=[dict(semantic_id=identifier,asset_kind='tmd_model',source_record=dict(
            record_kind='decoded_lzs_section',prot_entry_index=1,container_section=1,
            compressed_stream_offset=44,containing_size=len(pack),byte_offset=ranges[slot][0],byte_length=len(models[slot])))
            for identifier,slot in ((asset,1),(other,0))]
        p.imports[p.active_scene]=doc
        self.enterContext(patch('sdk.scene_preview.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_face_addition.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_growth.import_scene',return_value=doc))
        donor=source(p,asset,'a'*64)['topology']['faces'][0]['face_id'];requests=[helper.request(donor)]
        report=review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        data=bytearray(models[0]);at=12+struct.unpack_from('<I',models[0],12)[0];struct.pack_into('<h',data,at,14)
        p.set_model_replacement(other,bytes(data))
        raw,_=archive_source(container_for(pack))
        return p,asset,other,pack,raw

    def test_all_shared_pack_edits_are_prepared_and_reopened_without_mutation(self):
        p,asset,other,pack,raw=self.fixture();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        requests,audit=prepare_model_growth(p,_archive(raw))
        self.assertEqual(len(requests),1);self.assertEqual(audit['deferred_model_ids'],sorted([asset,other]))
        self.assertNotIn(asset,audit['model_content_changes']) # topology ledger is not relabeled as coordinate-only
        words=audit['model_content_changes'][other];self.assertTrue(words)
        for word in words:
            self.assertEqual(struct.unpack_from('<h',p._model_source(other),word['byte_offset'])[0],word['before_value']);self.assertEqual(struct.unpack_from('<h',p.read_model_replacement(other,p.model_overrides[other]),word['byte_offset'])[0],word['after_value'])
        self.assertEqual({row['slot_index'] for row in requests[0]['replacements']},{0,1})
        result,rebuild=rebuild_model_pack_entry(raw,sha256(raw).hexdigest(),**requests[0])
        reopened=_archive(result);entry=reopened.entry(1);body=reopened.read_entry(entry)
        descriptor=parse_scene_assets(body,1).descriptors[1]
        candidate,_=decompress_lzs(body[descriptor.data_offset:],descriptor.size)
        for slot,identifier in ((1,asset),(0,other)):
            start,_=_pack_ranges(candidate)[slot];payload=p.read_model_replacement(identifier,p.model_overrides[identifier])
            self.assertEqual(candidate[start:start+len(payload)],payload)
        old,new=_pack_ranges(pack)[2],_pack_ranges(candidate)[2]
        self.assertEqual(pack[slice(*old)],candidate[slice(*new)])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertTrue(rebuild['reopened_pack_verified']);self.assertFalse(audit['build_ready'])

    def test_content_capacity_uses_shared_relocation_and_other_errors_propagate(self):
        from importer.serialization import LzsCapacityError
        p,asset,other,pack,raw=self.fixture()
        p.model_overrides[asset]=deepcopy(p.model_overrides[asset]['base_binding'])
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        # Native Retail workflow covers the real encoder overflow. This isolates
        # the typed fallback boundary and all shared-carrier content retention.
        with patch('importer.model_authoring.model_shape_overlays',side_effect=LzsCapacityError('capacity')):
            requests,audit=prepare_model_growth(p,_archive(raw))
        self.assertEqual(audit['content_growth_model_ids'],sorted([asset,other]))
        self.assertEqual(set(audit['model_content_changes']),{asset,other})
        self.assertEqual(audit['carriers'][0]['reason'],'compressed-content-capacity')
        result,_=rebuild_model_pack_entry(raw,sha256(raw).hexdigest(),**requests[0])
        archive=_archive(result);body=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(body,1).descriptors[1]
        decoded,_=decompress_lzs(body[descriptor.data_offset:],descriptor.size)
        for slot,identifier in ((1,asset),(0,other)):
            start,_=_pack_ranges(decoded)[slot];payload=p.read_model_replacement(identifier,p.model_overrides[identifier])
            self.assertEqual(decoded[start:start+len(payload)],payload)
        with patch('importer.model_authoring.model_shape_overlays',return_value=([],[])):
            self.assertEqual(prepare_model_growth(p,_archive(raw))[0],[])
        with patch('importer.model_authoring.model_shape_overlays',side_effect=ImportError('unaudited content')):
            with self.assertRaisesRegex(ImportError,'unaudited content'):prepare_model_growth(p,_archive(raw))
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)

    def test_stale_directory_carrier_and_imported_bounds_reject(self):
        p,asset,_,_,raw=self.fixture()
        record=next(a['source_record'] for a in p.imports[p.active_scene]['assets']['models'] if a['semantic_id']==asset)
        for key,value in (('byte_offset',record['byte_offset']+4),('byte_length',999999),
                          ('compressed_stream_offset',45),('record_kind','raw_prot_entry')):
            before=deepcopy(record);record[key]=value
            with self.assertRaises(ProjectError):prepare_model_growth(p,_archive(raw))
            record.clear();record.update(before)
        record['pack_slot']=0
        with self.assertRaises(ProjectError):prepare_model_growth(p,_archive(raw))
        with patch('sdk.model_growth.import_scene',return_value={}):
            with self.assertRaises(ProjectError):prepare_model_growth(p,_archive(raw))

    def test_padded_owned_model_and_retained_base_replay_are_byte_exact(self):
        pack,models=pack_source();ranges=_pack_ranges(pack);slot=1;start,end=ranges[slot]
        original=pack[start:end];base=bytearray(original);at=12+struct.unpack_from('<I',base,12)[0];struct.pack_into('<h',base,at,7);base=bytes(base)
        base_binding=dict(format='tmd-shape',source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(base).hexdigest(),byte_length=len(base),source_scene_id='scene://fixture')
        donor=f'face://source/{sha256(base).hexdigest()}/0/0'
        expected,ledger,_=append_face_ledger(base,create_face_ledger(base),[dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',donor_face_id=donor,fields={'vertices':[3,2,1,0]})])
        replacement=dict(slot_index=slot,ledger=ledger,source_model_byte_length=len(original),base_binding=base_binding,base_payload=base)
        candidate,_=grow_model_pack(pack,sha256(pack).hexdigest(),[replacement]);new_start,new_end=_pack_ranges(candidate)[slot]
        self.assertEqual(candidate[new_start:new_end],expected);self.assertEqual(candidate[new_end-4:new_end],b'PAD!')
        for change in (lambda r:r.update(source_model_byte_length=True),lambda r:r.update(source_model_byte_length=len(original)+4),
                       lambda r:r['base_binding'].update(asset_sha256='0'*64),lambda r:r['base_binding'].update(format='tmd-face-addition-v1'),
                       lambda r:r.update(base_payload=base[:-1])):
            bad=deepcopy(replacement);change(bad)
            with self.assertRaises(ImportError):grow_model_pack(pack,sha256(pack).hexdigest(),[bad])


if __name__=='__main__':unittest.main()
