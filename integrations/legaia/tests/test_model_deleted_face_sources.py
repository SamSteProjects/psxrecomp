"""Restoration inputs are recovered from exact qualified deletion preimages."""
from copy import deepcopy
from hashlib import sha256
import struct,unittest
from importer.core import ImportError
from importer.model_face_ledger import deleted_face_sources,append_removal_ledger,append_content_ledger,replay_face_ledger
from importer.model_materials import patch_model_materials
from importer.model_primitives import inspect_model_primitives
import test_model_face_removal_ledger as fixtures


class DeletedFaceSourceTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.RemovalLedgerTests()
        return helper.fixture()

    def test_exact_packet_descriptor_footer_and_original_group_after_compaction(self):
        original,current,ledger,audit,request=self.fixture()
        self.assertEqual(deleted_face_sources(original,ledger),{})
        source_ids=[row['face_id'] for row in audit['faces'] if row['origin']=='source' and row['group_index']==0]
        current,ledger,_=append_removal_ledger(original,ledger,source_ids)
        current,_=patch_model_materials(current,sha256(current).hexdigest(),[
            dict(kind='primitive',object_index=0,primitive_index=2,values={'clut_column':7,'page_row':1})])
        # Record the material edit as a typed content operation, preserving the ledger chain.
        prior,_=replay_face_ledger(original,ledger)
        current,ledger,_=append_content_ledger(original,ledger,current)
        row=inspect_model_primitives(current)['objects'][0]['primitives'][2]
        start=12+struct.unpack_from('<I',current,28)[0]
        count=struct.unpack_from('<H',current,start)[0];stride=current[start+5]*4
        expected_packet=current[row['byte_offset']:row['byte_offset']+stride]
        expected_descriptor=current[start:start+8]
        expected_footer=current[start+8+count*stride:start+8+(count+1)*stride]
        _,ledger,_=append_removal_ledger(original,ledger,[request['face_id']])
        records=deleted_face_sources(original,ledger);captured=records[request['face_id']]
        self.assertEqual(set(records),set(source_ids+[request['face_id']]))
        self.assertEqual(captured['packet'],expected_packet)
        self.assertEqual(captured['descriptor'],expected_descriptor)
        self.assertEqual(captured['footer'],expected_footer)
        self.assertEqual(captured['deletion_input_sha256'],sha256(current).hexdigest())
        self.assertEqual(captured['source_byte_length'],len(current))
        self.assertEqual(captured['packet_byte_offset'],row['byte_offset'])
        self.assertEqual(captured['face']['group_index'],0)
        self.assertEqual(captured['origin_group_index'],1)
        self.assertEqual(captured['stable_order'],4)
        self.assertNotEqual(current,prior)
        original_start=12+struct.unpack_from('<I',original,28)[0]
        self.assertEqual(records[source_ids[0]]['descriptor'],original[original_start:original_start+8])
        self.assertEqual(records[source_ids[0]]['stable_order'],0)
        self.assertEqual(records[source_ids[1]]['stable_order'],1)

    def test_detached_capture_and_full_replay_rejection_preserve_inputs(self):
        original,current,ledger,_,request=self.fixture()
        _,ledger,_=append_removal_ledger(original,ledger,[request['face_id']])
        saved=deepcopy(ledger);expected=deleted_face_sources(original,ledger)
        captured=deleted_face_sources(original,ledger)
        captured[request['face_id']]['packet']=b'wrong'
        captured[request['face_id']]['face']['group_index']=99
        self.assertEqual(deleted_face_sources(original,ledger),expected)
        self.assertEqual(ledger,saved)
        for mutate in (lambda value:value['operations'][-1].update(input_sha256='0'*64),
                       lambda value:value['operations'][-1].update(proposed_sha256='0'*64),
                       lambda value:value['operations'][-1].update(packet_hex='00'),
                       lambda value:value['operations'][-1].update(face_ids=['missing'])):
            bad=deepcopy(ledger);mutate(bad)
            with self.assertRaises(ImportError):deleted_face_sources(original,bad)
            self.assertEqual(ledger,saved)


if __name__=='__main__':unittest.main()
