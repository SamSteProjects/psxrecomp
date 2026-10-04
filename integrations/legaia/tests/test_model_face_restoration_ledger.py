"""Restoration replays captured packets without raw packet fields or recursion."""
from copy import deepcopy
from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_face_ledger import (append_restoration_ledger,append_removal_ledger,
    append_content_ledger,append_face_ledger,replay_face_ledger,deleted_face_sources,
    qualify_face_ledger)
import test_model_face_removal_ledger as fixtures
from test_model_face_reinsertion import packet


class RestorationLedgerTests(unittest.TestCase):
    def test_restoration_content_additions_and_redeletion_use_latest_preimage(self):
        original,current,ledger,before,request=fixtures.RemovalLedgerTests().fixture()
        ids=[before['faces'][0]['face_id'],request['face_id']]
        current,ledger,_=append_removal_ledger(original,ledger,ids)
        captured=deleted_face_sources(original,ledger)
        current,ledger,audit=append_restoration_ledger(original,ledger,ids)
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v4')
        self.assertEqual(audit['removed_face_ids'],[])
        self.assertEqual(deleted_face_sources(original,ledger),{})
        by_id={row['face_id']:row for row in audit['faces']}
        for identity in ids:self.assertEqual(packet(current,by_id[identity]),captured[identity]['packet'])
        changed=bytearray(current);vertex=12+struct.unpack_from('<I',current,12)[0]
        struct.pack_into('<h',changed,vertex,91)
        current,ledger,_=append_content_ledger(original,ledger,bytes(changed))
        new={**request,'face_id':'face://authored/00000000-0000-4000-8000-000000000002'}
        new['donor_face_id']=request['face_id']
        current,ledger,audit=append_face_ledger(original,ledger,[new])
        self.assertEqual(audit['authored_face_count'],2)
        latest_hash=sha256(current).hexdigest()
        current,ledger,_=append_removal_ledger(original,ledger,[request['face_id']])
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v4')
        self.assertEqual(deleted_face_sources(original,ledger)[request['face_id']]['deletion_input_sha256'],latest_hash)
        current,ledger,audit=append_restoration_ledger(original,ledger,[request['face_id']])
        self.assertEqual(audit['authored_face_count'],2)
        self.assertEqual(len(audit['faces']),6)
        final_vertex=12+struct.unpack_from('<I',current,12)[0]
        self.assertEqual(struct.unpack_from('<h',current,final_vertex)[0],91)
        self.assertEqual(qualify_face_ledger(original,json.loads(json.dumps(ledger)),current),audit)
        with self.assertRaises(ImportError):append_face_ledger(original,ledger,[request])
        # Ensure replay does not recurse through the public wrapper.
        with patch('importer.model_face_reinsertion.reinsert_ledger_faces',side_effect=AssertionError('recursive replay')):
            self.assertEqual(replay_face_ledger(original,ledger),(current,audit))

    def test_restore_missing_group_and_preserve_unselected_deleted_ids(self):
        original,current,ledger,before,request=fixtures.RemovalLedgerTests().fixture()
        ids=[face['face_id'] for face in before['faces'] if face['group_index']==0]
        current,ledger,_=append_removal_ledger(original,ledger,ids+[request['face_id']])
        current,ledger,audit=append_restoration_ledger(original,ledger,ids)
        self.assertEqual(audit['removed_face_ids'],[request['face_id']])
        self.assertEqual(set(deleted_face_sources(original,ledger)),{request['face_id']})
        self.assertEqual({face['group_index'] for face in audit['faces']},{0,1})
        self.assertEqual(qualify_face_ledger(original,ledger,current),audit)

    def test_schema_hash_selection_and_operation_budget_rejections_preserve_input(self):
        original,current,ledger,_,request=fixtures.RemovalLedgerTests().fixture()
        _,ledger,_=append_removal_ledger(original,ledger,[request['face_id']]);saved=deepcopy(ledger)
        for ids in ([],['missing'],[request['face_id']]*2):
            with self.assertRaises(ImportError):append_restoration_ledger(original,ledger,ids)
            self.assertEqual(ledger,saved)
        candidate,restored,_=append_restoration_ledger(original,ledger,[request['face_id']])
        for mutate in (lambda v:v.update(schema_version='legaia.model-face-addition-ledger.v3'),
                       lambda v:v['operations'][-1].update(input_sha256='0'*64),
                       lambda v:v['operations'][-1].update(proposed_sha256='0'*64),
                       lambda v:v['operations'][-1].update(packet_hex='00'),
                       lambda v:v['operations'][-1].update(face_ids=['missing'])):
            bad=deepcopy(restored);mutate(bad)
            with self.assertRaises(ImportError):qualify_face_ledger(original,bad,candidate)
        with self.assertRaises(ImportError):append_restoration_ledger(original,restored,[request['face_id']])
        with patch('importer.model_face_ledger.MAX_OPERATIONS',len(ledger['operations'])):
            with self.assertRaises(ImportError):append_restoration_ledger(original,ledger,[request['face_id']])
        self.assertEqual(ledger,saved)


if __name__=='__main__':unittest.main()
