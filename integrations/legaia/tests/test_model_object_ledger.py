"""Stable native object clones compose with existing face/vector/group operations."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from importer.core import ImportError
from importer.model_face_ledger import (create_face_ledger,replay_face_ledger,append_object_ledger,
    append_group_ledger,append_face_ledger,append_removal_ledger,append_restoration_ledger,
    append_vector_ledger,append_content_ledger)
from importer.model_object_ledger import source_objects
from importer.model_primitives import patch_model_primitives
from test_model_primitives import synthetic
from test_model_group_ledger import group,identity


def clone_request(audit,donor,index):
    faces=sorted([row for row in audit['faces'] if row['object_index']==donor['object_index']],key=lambda row:row['current_primitive_index'])
    groups=[]
    for row in faces:
        if row['group_index']==len(groups):groups.append(dict(group_id=identity('group',index+len(groups)),faces=[]))
        groups[-1]['faces'].append(dict(face_id=identity('face',index+row['current_primitive_index']),donor_face_id=row['face_id']))
    return dict(object_id=identity('object',index),donor_object_id=donor['object_id'],groups=groups)


class ObjectLedgerTests(unittest.TestCase):
    def fixture(self):
        original=synthetic(((0x14,0x22),(0x20,)),count=2);ledger=create_face_ledger(original)
        _,audit=replay_face_ledger(original,ledger);donor=next(iter(source_objects(original).values()))
        return original,ledger,audit,clone_request(audit,donor,100)

    def test_clone_stable_provenance_and_json_replay(self):
        original,ledger,audit,request=self.fixture();saved=deepcopy((ledger,request))
        added,ledger,final=append_object_ledger(original,ledger,[request])
        self.assertEqual((saved[0],saved[1]),(create_face_ledger(original),request))
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual((final['allocated_object_count'],final['allocated_group_count'],final['authored_face_count'],final['allocated_vector_count']),(1,2,4,9))
        self.assertEqual(final['objects'][-1],dict(object_id=request['object_id'],origin='authored',object_index=2,donor_object_id=request['donor_object_id']))
        new=[f for f in final['faces'] if f['object_index']==2]
        self.assertEqual([f['donor_face_id'] for f in new],[f['face_id'] for f in audit['faces'] if f['object_index']==0])
        self.assertEqual(replay_face_ledger(original,json.loads(json.dumps(ledger))),(added,final))
        # A newly authored object is an independent valid donor with stable ancestry.
        second=clone_request(final,final['objects'][-1],200)
        twice,ledger,final=append_object_ledger(original,ledger,[second])
        self.assertEqual(final['objects'][-1]['object_index'],3)
        self.assertEqual(final['objects'][-1]['donor_object_id'],request['object_id'])
        self.assertEqual(replay_face_ledger(original,ledger)[0],twice)

    def test_full_group_removal_new_group_restore_content_and_vectors(self):
        original,ledger,_,request=self.fixture();current,ledger,audit=append_object_ledger(original,ledger,[request])
        gone=[face['face_id'] for face in audit['faces'] if face['object_index']==2 and face['group_index']==0]
        current,ledger,audit=append_removal_ledger(original,ledger,gone)
        donor=next(face for face in audit['faces'] if face['object_index']==2)
        current,ledger,audit=append_group_ledger(original,ledger,[group(300,donor['face_id'],vertices=[2,1,0,3])])
        self.assertEqual(audit['allocated_groups'][-1]['origin_group_index'],2)
        current,ledger,audit=append_restoration_ledger(original,ledger,gone)
        self.assertEqual([g['current_group_index'] for g in audit['allocated_groups']],[0,1,2])
        donor=next(face for face in audit['faces'] if face['object_index']==2 and face['group_index']==0)
        current,ledger,audit=append_face_ledger(original,ledger,[dict(face_id=identity('face',400),donor_face_id=donor['face_id'],fields={'vertices':[2,1,0]})])
        current,ledger,audit=append_vector_ledger(original,ledger,[dict(object_index=2,kind='vertices',vectors=[[10,20,30]])])
        changed,_=patch_model_primitives(current,sha256(current).hexdigest(),[dict(object_index=2,primitive_index=0,vertices=[5,1,0])])
        current,ledger,audit=append_content_ledger(original,ledger,changed)
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(audit['allocated_vector_count'],10)
        self.assertEqual(replay_face_ledger(original,ledger)[0],current)

    def test_complete_donor_identity_reservation_schema_and_budgets(self):
        original,ledger,_,request=self.fixture()
        for mutate in (lambda r:r.update(donor_object_id='missing'),lambda r:r['groups'].pop(),lambda r:r['groups'][0]['faces'].reverse(),lambda r:r['groups'][0]['faces'][0].update(donor_face_id='missing'),lambda r:r.update(extra=True)):
            bad=deepcopy(request);mutate(bad)
            with self.assertRaises(ImportError):append_object_ledger(original,ledger,[bad])
        _,ledger,audit=append_object_ledger(original,ledger,[request])
        for mutation in ('v6','hash'):
            bad=deepcopy(ledger)
            if mutation=='v6':bad['schema_version']='legaia.model-face-addition-ledger.v6'
            else:bad['operations'][-1]['proposed_sha256']='0'*64
            with self.assertRaises(ImportError):replay_face_ledger(original,bad)
        _,ledger,audit=append_removal_ledger(original,ledger,[face['face_id'] for face in audit['faces'] if face['object_index']==2])
        with self.assertRaises(ImportError):append_object_ledger(original,ledger,[request])
        from unittest.mock import patch
        fresh=clone_request(audit,audit['objects'][0],500)
        with patch('importer.model_face_ledger.MAX_LEDGER_VECTORS',10):
            with self.assertRaises(ImportError):append_object_ledger(original,ledger,[fresh])


if __name__=='__main__':unittest.main()

