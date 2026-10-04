"""Vector allocations compose with stable faces and preserve replay budgets."""
from copy import deepcopy
from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_face_ledger import (create_face_ledger,replay_face_ledger,append_vector_ledger,
    append_face_ledger,append_content_ledger,append_removal_ledger,append_restoration_ledger,
    qualify_face_ledger,deleted_face_sources)
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic
import test_model_face_removal_ledger as fixtures


class VectorLedgerTests(unittest.TestCase):
    def test_new_lit_face_uses_allocated_rows_through_content_deletion_and_restoration(self):
        original=synthetic(((0x16,),));ledger=create_face_ledger(original)
        _,before=replay_face_ledger(original,ledger)
        requests=[dict(object_index=0,kind=kind,vectors=[[100,200,300],[400,500,600]]) for kind in ('vertices','normals')]
        current,ledger,audit=append_vector_ledger(original,ledger,requests)
        self.assertEqual(audit['faces'],before['faces'])
        self.assertEqual(audit['allocated_vector_count'],4)
        request=dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',
            donor_face_id=before['faces'][0]['face_id'],fields=dict(vertices=[5,6,0,1],normal_indices=[4,5,4,5]))
        current,ledger,_=append_face_ledger(original,ledger,[request])
        edited=bytearray(current);vertices=12+struct.unpack_from('<I',current,12)[0]
        struct.pack_into('<h',edited,vertices+6*8,901)
        current,ledger,_=append_content_ledger(original,ledger,bytes(edited))
        current,ledger,_=append_removal_ledger(original,ledger,[request['face_id']])
        captured=deleted_face_sources(original,ledger)[request['face_id']]
        current,ledger,audit=append_restoration_ledger(original,ledger,[request['face_id']])
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v5')
        self.assertEqual(audit['allocated_vector_count'],4);self.assertEqual(audit['vector_allocation_count'],1)
        self.assertEqual(audit['removed_face_ids'],[])
        face=next(row for row in audit['faces'] if row['face_id']==request['face_id'])
        row=inspect_model_primitives(current,include_normal_references=True)['objects'][0]['primitives'][face['current_primitive_index']]
        self.assertEqual(row['vertices'],[5,6,0,1]);self.assertEqual(row['normal_indices'],[4,5,4,5])
        self.assertEqual(current[row['byte_offset']:row['byte_offset']+len(captured['packet'])],captured['packet'])
        final_vertices=12+struct.unpack_from('<I',current,12)[0]
        self.assertEqual(struct.unpack_from('<h',current,final_vertices+6*8)[0],901)
        self.assertEqual(qualify_face_ledger(original,json.loads(json.dumps(ledger)),current),audit)

    def test_allocation_between_full_group_deletion_and_restoration_preserves_roots(self):
        original,current,ledger,audit,request=fixtures.RemovalLedgerTests().fixture()
        ids=[row['face_id'] for row in audit['faces'] if row['group_index']==0]+[request['face_id']]
        current,ledger,_=append_removal_ledger(original,ledger,ids)
        current,ledger,_=append_vector_ledger(original,ledger,[dict(object_index=0,kind='vertices',vectors=[[111,222,333]])])
        current,ledger,audit=append_restoration_ledger(original,ledger,ids)
        self.assertEqual(len(audit['faces']),5)
        self.assertEqual({row['group_index'] for row in audit['faces']},{0,1})
        self.assertEqual(audit['allocated_vector_count'],1)
        self.assertEqual(struct.unpack_from('<I',current,16)[0],6)
        self.assertEqual(qualify_face_ledger(original,ledger,current),audit)

    def test_schema_chain_and_operation_budget_rejection_does_not_mutate_requests(self):
        original=synthetic(((0x22,),));ledger=create_face_ledger(original)
        requests=[dict(object_index=0,kind='vertices',vectors=[[1,2,3]])];saved=deepcopy(requests)
        current,ledger,_=append_vector_ledger(original,ledger,requests)
        self.assertEqual(requests,saved);saved_ledger=deepcopy(ledger)
        for mutate in (lambda v:v.update(schema_version='legaia.model-face-addition-ledger.v4'),
                       lambda v:v['operations'][0].update(input_sha256='0'*64),
                       lambda v:v['operations'][0].update(proposed_sha256='0'*64),
                       lambda v:v['operations'][0].update(packet_hex='00'),
                       lambda v:v['operations'][0]['requests'][0].update(kind='unknown')):
            bad=deepcopy(ledger);mutate(bad)
            with self.assertRaises(ImportError):qualify_face_ledger(original,bad,current)
        with patch('importer.model_face_ledger.MAX_OPERATIONS',1):
            with self.assertRaises(ImportError):append_vector_ledger(original,ledger,requests)
        self.assertEqual(ledger,saved_ledger);self.assertEqual(requests,saved)

    def test_cumulative_vector_budget_applies_across_operations(self):
        original=synthetic(((0x22,),));ledger=create_face_ledger(original)
        current,ledger,audit=append_vector_ledger(original,ledger,[dict(object_index=0,kind='vertices',vectors=[[0,0,0]]*2000)])
        current,ledger,audit=append_vector_ledger(original,ledger,[dict(object_index=0,kind='normals',vectors=[[0,0,0]]*2096)])
        self.assertEqual(audit['allocated_vector_count'],4096)
        self.assertEqual(audit['vector_allocation_count'],2)
        saved=deepcopy(ledger)
        with self.assertRaises(ImportError):append_vector_ledger(original,ledger,[dict(object_index=0,kind='vertices',vectors=[[0,0,0]])])
        with patch('importer.model_face_ledger.MAX_LEDGER_VECTORS',4095):
            with self.assertRaises(ImportError):qualify_face_ledger(original,ledger,current)
        self.assertEqual(ledger,saved)


if __name__=='__main__':unittest.main()
