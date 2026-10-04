from copy import deepcopy
from hashlib import sha256
import json,struct,unittest
from importer.core import ImportError
from importer.model_face_ledger import create_face_ledger,append_face_ledger,append_content_ledger,replay_face_ledger
from importer.model_primitives import inspect_model_primitives,patch_model_primitives
from test_model_primitives import synthetic
from test_model_face_ledger import request


class FaceContentLedgerTests(unittest.TestCase):
    def fixture(self):
        original=synthetic(((0x22,0x24),),count=2)
        first,ledger,audit=append_face_ledger(original,create_face_ledger(original),
            [request(1,f'face://source/{sha256(original).hexdigest()}/0/0',4)])
        return original,first,ledger,audit

    def test_content_between_additions_preserves_stable_faces_and_edited_donor(self):
        original,first,ledger,audit=self.fixture();before=deepcopy(ledger)
        changed=bytearray(first);vector=12+struct.unpack_from('<I',first,12)[0]
        struct.pack_into('<h',changed,vector,-123);changed=bytes(changed)
        candidate,updated,edited=append_content_ledger(original,ledger,changed)
        self.assertEqual(ledger,before);self.assertEqual(edited['faces'],audit['faces'])
        final,next_ledger,final_audit=append_face_ledger(original,updated,[request(2,request(1,'')['face_id'],4)])
        replayed,replay_audit=replay_face_ledger(original,json.loads(json.dumps(next_ledger)))
        self.assertEqual(replayed,final);self.assertEqual(replay_audit,final_audit)
        self.assertEqual(final_audit['authored_face_count'],2);self.assertEqual(final_audit['batch_count'],2)
        self.assertEqual(final_audit['operation_count'],3)
        newvector=12+struct.unpack_from('<I',final,12)[0];self.assertEqual(struct.unpack_from('<h',final,newvector)[0],-123)
        self.assertEqual(append_content_ledger(original,next_ledger,final)[1],next_ledger)

    def test_opaque_changes_count_changes_tampered_preimages_and_chain_reject(self):
        original,first,ledger,_=self.fixture();candidate=bytearray(first)
        vector=12+struct.unpack_from('<I',first,12)[0];candidate[vector]^=1
        _,updated,_=append_content_ledger(original,ledger,bytes(candidate))
        for change in (lambda value:value['operations'][-1].update(input_sha256='0'*64),
                       lambda value:value['operations'][-1]['runs'][0].update(before_hex='ff'),
                       lambda value:value['operations'][-1]['runs'][0].update(offset=True),
                       lambda value:value['operations'][-1].update(proposed_sha256='0'*64),
                       lambda value:value['operations'][-1].update(extra=True)):
            bad=deepcopy(updated);change(bad)
            with self.assertRaises(ImportError):replay_face_ledger(original,bad)
        oversized=deepcopy(updated);oversized['operations']=oversized['operations']*33
        with self.assertRaisesRegex(ImportError,'operation budget'):replay_face_ledger(original,oversized)
        opaque=bytearray(first);opaque[0]^=1
        for content in (bytes(opaque),first+b'XXXX'):
            with self.assertRaises(ImportError):append_content_ledger(original,ledger,content)


if __name__=='__main__':unittest.main()
