"""Typed removals compose with additions/content without reusing stable identities."""
from copy import deepcopy
from hashlib import sha256
import json,struct,unittest
from importer.core import ImportError
from importer.model_face_ledger import (create_face_ledger,replay_face_ledger,append_face_ledger,
    append_content_ledger,append_removal_ledger,qualify_face_ledger)
from importer.model_face_removal import remove_faces
from test_model_primitives import synthetic


class RemovalLedgerTests(unittest.TestCase):
    def fixture(self):
        original=synthetic(((0x12,0x22),),count=2);ledger=create_face_ledger(original)
        _,audit=replay_face_ledger(original,ledger)
        request=dict(face_id='face://authored/00000000-0000-4000-8000-000000000001',
                     donor_face_id=audit['faces'][2]['face_id'],fields={'vertices':[0,1,2,3]})
        current,ledger,audit=append_face_ledger(original,ledger,[request])
        return original,current,ledger,audit,request

    def test_group_remapping_content_removal_and_later_additions(self):
        original,current,ledger,audit,request=self.fixture()
        omitted=[row['face_id'] for row in audit['faces'] if row['origin']=='source' and row['group_index']==0]
        expected,_=remove_faces(current,current,[],[dict(object_index=0,primitive_index=i) for i in (0,1)])
        removed,ledger,audit=append_removal_ledger(original,ledger,omitted)
        self.assertEqual(removed,expected)
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v3')
        self.assertEqual(audit['removed_face_ids'],omitted)
        self.assertEqual({row['group_index'] for row in audit['faces']},{0})
        self.assertEqual({row['current_primitive_index'] for row in audit['faces']},{0,1,2})
        content=bytearray(removed);offset=12+struct.unpack_from('<I',content,12)[0];struct.pack_into('<h',content,offset,37)
        edited,ledger,audit=append_content_ledger(original,ledger,bytes(content))
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v3')
        final,ledger,audit=append_removal_ledger(original,ledger,[request['face_id']])
        self.assertEqual(audit['authored_face_count'],1) # Historical budget never resets after deletion.
        self.assertNotIn(request['face_id'],{row['face_id'] for row in audit['faces']})
        with self.assertRaises(ImportError):append_face_ledger(original,ledger,[request])
        fresh={**request,'face_id':'face://authored/00000000-0000-4000-8000-000000000002',
               'donor_face_id':audit['faces'][0]['face_id']}
        final,ledger,audit=append_face_ledger(original,ledger,[fresh])
        self.assertEqual(audit['authored_face_count'],2)
        self.assertEqual(len(audit['faces']),3)
        self.assertEqual(qualify_face_ledger(original,ledger,final),audit)
        self.assertEqual(qualify_face_ledger(original,json.loads(json.dumps(ledger)),final),audit)
        final_offset=12+struct.unpack_from('<I',final,12)[0]
        self.assertEqual(struct.unpack_from('<h',final,final_offset)[0],37)

    def test_invalid_selection_chains_and_preimages_do_not_mutate_inputs(self):
        original,current,ledger,audit,request=self.fixture();before=deepcopy(ledger)
        for identities in ([],[request['face_id']]*2,['missing'],[True],{}):
            with self.assertRaises(ImportError):append_removal_ledger(original,ledger,identities)
            self.assertEqual(ledger,before)
        candidate,ledger,audit=append_removal_ledger(original,ledger,[request['face_id']])
        for mutate in (lambda v:v.update(schema_version='legaia.model-face-addition-ledger.v2'),
                       lambda v:v['operations'][-1].update(input_sha256='0'*64),
                       lambda v:v['operations'][-1].update(proposed_sha256='0'*64),
                       lambda v:v['operations'][-1].update(face_ids=['missing']),
                       lambda v:v['operations'][-1].update(extra=True)):
            bad=deepcopy(ledger);mutate(bad)
            with self.assertRaises(ImportError):qualify_face_ledger(original,bad,candidate)
        with self.assertRaises(ImportError):append_removal_ledger(original,ledger,[request['face_id']])
        with self.assertRaises(ImportError):append_face_ledger(original,ledger,[{**request,'face_id':'face://authored/00000000-0000-4000-8000-000000000003','donor_face_id':request['face_id']}])

    def test_removal_shares_the_bounded_operation_budget(self):
        original,current,ledger,_,request=self.fixture()
        for value in range(1,64):
            candidate=bytearray(current);offset=12+struct.unpack_from('<I',candidate,12)[0]
            struct.pack_into('<h',candidate,offset,value)
            current,ledger,_=append_content_ledger(original,ledger,bytes(candidate))
        self.assertEqual(len(ledger['operations']),64)
        saved=deepcopy(ledger)
        with self.assertRaises(ImportError):append_removal_ledger(original,ledger,[request['face_id']])
        self.assertEqual(ledger,saved)


if __name__=='__main__':unittest.main()
