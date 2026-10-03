from copy import deepcopy
from hashlib import sha256
import json
import unittest

from importer.core import ImportError
from importer.model_face_addition import add_model_faces
from importer.model_face_ledger import (create_face_ledger, append_face_ledger,
    replay_face_ledger, qualify_face_ledger, MAX_BATCHES, MAX_LEDGER_FACES)
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic


def request(index, donor, corners=3):
    return dict(face_id=f'face://authored/00000000-0000-4000-8000-{index:012x}',
                donor_face_id=donor, fields={'vertices':list(reversed(range(corners)))})


class ModelFaceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.original = synthetic(((0x20, 0x22), (0x24,)), count=2)
        self.ledger = create_face_ledger(self.original)
        self.source_hash = sha256(self.original).hexdigest()

    def source_id(self, owner, primitive):
        return f'face://source/{self.source_hash}/{owner}/{primitive}'

    def test_empty_record_is_exact_source_and_detached(self):
        candidate, audit = replay_face_ledger(self.original, self.ledger)
        self.assertEqual(candidate, self.original)
        self.assertEqual(audit['authored_face_count'], 0)
        self.assertEqual(len(audit['faces']), 6)
        audit['faces'][0]['current_primitive_index'] = 999
        self.assertEqual(replay_face_ledger(self.original, self.ledger)[1]['faces'][0]['current_primitive_index'], 0)

    def test_roundtrip_composes_stable_donors_across_shifted_groups_and_objects(self):
        first = [request(1, self.source_id(0, 0)), request(2, self.source_id(1, 1))]
        one, ledger, audit = append_face_ledger(self.original, self.ledger, first)
        self.assertEqual(self.ledger['batches'], [])
        first[0]['fields']['vertices'][0] = 99
        second = [request(3, request(1, '')['face_id']), request(4, self.source_id(0, 2), 4)]
        two, ledger2, final = append_face_ledger(self.original, json.loads(json.dumps(ledger)), second)
        self.assertEqual(len(ledger['batches']), 1)
        self.assertEqual(ledger2['batches'][1]['input_sha256'], sha256(one).hexdigest())
        replayed, replay_audit = replay_face_ledger(self.original, json.loads(json.dumps(ledger2)))
        self.assertEqual(replayed, two)
        self.assertEqual(final, replay_audit)
        faces = {row['face_id']: row for row in final['faces']}
        self.assertEqual(faces[self.source_id(0, 2)]['current_primitive_index'], 4)
        self.assertEqual(faces[second[0]['face_id']]['current_primitive_index'], 3)
        self.assertEqual(faces[second[1]['face_id']]['current_primitive_index'], 6)
        self.assertEqual(faces[second[0]['face_id']]['donor_face_id'], request(1, '')['face_id'])
        self.assertEqual(len(faces), 10)
        self.assertEqual(final['authored_face_count'], 4)
        self.assertEqual(qualify_face_ledger(self.original, ledger2, two), final)
        expected, _ = add_model_faces(one, sha256(one).hexdigest(), [
            dict(face_id=second[0]['face_id'], object_index=0, group_index=0, donor_primitive_index=2, fields=second[0]['fields']),
            dict(face_id=second[1]['face_id'], object_index=0, group_index=1, donor_primitive_index=3, fields=second[1]['fields'])])
        self.assertEqual(two, expected)
        decoded = inspect_model_primitives(two)
        self.assertEqual(decoded['objects'][0]['primitives'][6]['vertices'], [3, 2, 1, 0])

    def test_authored_donor_copies_its_current_typed_packet_not_retail_donor(self):
        first = request(1, self.source_id(1, 0))
        first['fields']['colors'] = [[7, 8, 9]] * 3
        _, ledger, _ = append_face_ledger(self.original, self.ledger, [first])
        candidate, _, _ = append_face_ledger(self.original, ledger, [request(2, first['face_id'])])
        decoded = inspect_model_primitives(candidate)
        self.assertEqual(decoded['objects'][1]['primitives'][3]['colors'], [[7, 8, 9]] * 3)

    def test_source_schema_chain_and_complete_candidate_are_bound(self):
        candidate, ledger, _ = append_face_ledger(self.original, self.ledger, [request(1, self.source_id(0, 0))])
        changes = [lambda x:x.update(source_sha256='0'*64), lambda x:x.update(source_byte_length=True),
            lambda x:x.update(extra=True), lambda x:x.update(schema_version='future'),
            lambda x:x['batches'][0].update(input_sha256='0'*64),
            lambda x:x['batches'][0].update(proposed_sha256='0'*64),
            lambda x:x['batches'][0].update(extra=True),
            lambda x:x['batches'][0]['additions'][0]['fields'].update(vertices=[0, 1, 2])]
        for change in changes:
            invalid = deepcopy(ledger);change(invalid)
            with self.assertRaises(ImportError): replay_face_ledger(self.original, invalid)
        mutated = bytearray(candidate);mutated[-1] ^= 1
        with self.assertRaises(ImportError): qualify_face_ledger(self.original, ledger, bytes(mutated))
        with self.assertRaises(ImportError): replay_face_ledger(self.original + bytes(4), ledger)

    def test_uuid_uniqueness_and_previous_model_donor_ownership(self):
        first = request(1, self.source_id(0, 0))
        _, ledger, _ = append_face_ledger(self.original, self.ledger, [first])
        invalid = [[first], [request(2, self.source_id(0, 99))], [request(2, 'face://source/'+'0'*64+'/0/0')],
            [request(2, request(3, '')['face_id']), request(3, self.source_id(0, 0))],
            [dict(request(2, self.source_id(0, 0)), donor_face_id=[])],
            [dict(request(2, self.source_id(0, 0)), face_id=self.source_id(0, 1))],
            [dict(request(2, self.source_id(0, 0)), face_id='face://authored/invalid')],
            [dict(request(2, self.source_id(0, 0)), object_index=0)], []]
        snapshot = deepcopy(ledger)
        for requests in invalid:
            with self.assertRaises(ImportError): append_face_ledger(self.original, ledger, requests)
            self.assertEqual(ledger, snapshot)

    def test_batch_and_total_face_budgets(self):
        ledger = self.ledger
        for index in range(MAX_BATCHES):
            _, ledger, _ = append_face_ledger(self.original, ledger, [request(index+1, self.source_id(0, 0))])
        with self.assertRaises(ImportError): append_face_ledger(self.original, ledger, [request(100, self.source_id(0, 0))])
        oversized = deepcopy(ledger);oversized['batches'].append(deepcopy(oversized['batches'][-1]))
        with self.assertRaises(ImportError): replay_face_ledger(self.original, oversized)
        _, full, _ = append_face_ledger(self.original, self.ledger, [request(i+1, self.source_id(0, 0)) for i in range(MAX_LEDGER_FACES)])
        with self.assertRaises(ImportError): append_face_ledger(self.original, full, [request(1000, self.source_id(0, 0))])


if __name__ == '__main__':
    unittest.main()
