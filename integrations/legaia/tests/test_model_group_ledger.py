"""Stable authored groups survive compaction, restoration and vector operations."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from importer.core import ImportError
from importer.model_face_ledger import (create_face_ledger, replay_face_ledger, append_group_ledger,
    append_face_ledger, append_removal_ledger, append_restoration_ledger, append_vector_ledger,
    append_content_ledger, deleted_face_sources)
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from test_model_primitives import synthetic


def identity(prefix,index):
    return f'{prefix}://authored/00000000-0000-4000-8000-{index:012x}'


def group(index,donor,face_index=None,vertices=None):
    return dict(group_id=identity('group',index),donor_face_id=donor,
        faces=[dict(face_id=identity('face',index if face_index is None else face_index),
                    donor_face_id=donor,fields={'vertices':vertices or [2,1,0]})])


class GroupLedgerTests(unittest.TestCase):
    def fixture(self,groups=((0x20,0x20),)):
        original=synthetic(groups,count=2);ledger=create_face_ledger(original)
        _,audit=replay_face_ledger(original,ledger)
        return original,ledger,[row['face_id'] for row in audit['faces']]

    def test_full_group_deletion_new_allocation_restoration_and_stable_roots(self):
        original,ledger,source=self.fixture()
        request=group(1,source[2]);request['faces'].append(group(2,source[3])['faces'][0])
        added,ledger,audit=append_group_ledger(original,ledger,[request])
        self.assertEqual(audit['allocated_groups'][0]['origin_group_index'],2)
        removed,ledger,_=append_removal_ledger(original,ledger,[source[0],source[1],identity('face',1),identity('face',2)])
        _,ledger,audit=append_group_ledger(original,ledger,[group(3,source[2])])
        self.assertIsNone(audit['allocated_groups'][0]['current_group_index'])
        self.assertEqual(audit['allocated_groups'][1]['origin_group_index'],3)
        restored,ledger,audit=append_restoration_ledger(original,ledger,[identity('face',1)])
        self.assertEqual([r['current_group_index'] for r in audit['allocated_groups']],[1,2])
        restored,ledger,audit=append_restoration_ledger(original,ledger,[source[0],identity('face',2)])
        self.assertEqual([r['current_group_index'] for r in audit['allocated_groups']],[2,3])
        deleted=deleted_face_sources(original,ledger)
        self.assertEqual(set(deleted),{source[1]})
        row=next(r for r in audit['faces'] if r['face_id']==identity('face',2))
        primitive=inspect_model_primitives(restored)['objects'][0]['primitives'][row['current_primitive_index']]
        self.assertEqual(primitive['vertices'],[2,1,0])
        ordinary=group(4,identity('face',1))['faces'][0]
        _,ledger,audit=append_face_ledger(original,ledger,[ordinary])
        self.assertEqual(audit['allocated_groups'][0]['face_ids'],[identity('face',1),identity('face',2),identity('face',4)])
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v6')
        self.assertEqual(replay_face_ledger(original,json.loads(json.dumps(ledger)))[1],audit)

    def test_vector_allocation_content_and_lit_references_preserve_v6(self):
        original,ledger,source=self.fixture(((0x14,),))
        _,ledger,_=append_vector_ledger(original,ledger,[dict(object_index=0,kind='vertices',vectors=[[1,2,3]])])
        request=group(1,source[0],vertices=[5,1,0]);request['faces'][0]['fields']['normal_indices']=[3,2,1]
        snapshot=deepcopy((ledger,request))
        current,ledger,audit=append_group_ledger(original,ledger,[request])
        self.assertEqual(snapshot[1],request)
        current,ledger,audit=append_vector_ledger(original,ledger,[dict(object_index=0,kind='normals',vectors=[[0,4096,0]])])
        self.assertEqual(audit['allocated_vector_count'],2)
        row=next(r for r in audit['faces'] if r['face_id']==identity('face',1))
        changed,_=patch_model_primitives(current,sha256(current).hexdigest(),[
            dict(object_index=0,primitive_index=row['current_primitive_index'],normal_indices=[4,2,1])])
        final,ledger,audit=append_content_ledger(original,ledger,changed)
        self.assertEqual(ledger['schema_version'],'legaia.model-face-addition-ledger.v6')
        self.assertEqual(replay_face_ledger(original,ledger)[0],final)
        _,ledger,_=append_removal_ledger(original,ledger,[identity('face',1)])
        restored,ledger,audit=append_restoration_ledger(original,ledger,[identity('face',1)])
        self.assertEqual(inspect_model_primitives(restored,include_normal_references=True)['objects'][0]['primitives'][2]['normal_indices'],[4,2,1])
        self.assertEqual(audit['allocated_groups'][0]['current_group_index'],1)

    def test_group_and_face_tombstones_cannot_be_reused(self):
        original,ledger,source=self.fixture()
        _,ledger,_=append_group_ledger(original,ledger,[group(1,source[0])])
        _,ledger,audit=append_removal_ledger(original,ledger,[identity('face',1)])
        for request in (group(1,source[0],2),group(2,source[0],1)):
            with self.assertRaises(ImportError):append_group_ledger(original,ledger,[request])
        with self.assertRaises(ImportError):append_face_ledger(original,ledger,[group(1,source[0])['faces'][0]])
        self.assertIsNone(audit['allocated_groups'][0]['current_group_index'])

    def test_stable_donor_schema_chain_and_versions(self):
        original,ledger,source=self.fixture(((0x20,0x20),(0x20,)))
        request=group(1,source[0])
        for donor in (source[2],source[4]):
            invalid=deepcopy(request);invalid['faces'][0]['donor_face_id']=donor
            with self.assertRaises(ImportError):append_group_ledger(original,ledger,[invalid])
        _,ledger,_=append_group_ledger(original,ledger,[request])
        for mutate in (lambda l:l.update(schema_version='legaia.model-face-addition-ledger.v5'),
                       lambda l:l['operations'][0].update(input_sha256='0'*64),
                       lambda l:l['operations'][0].update(proposed_sha256='0'*64),
                       lambda l:l['operations'][0]['requests'][0].update(extra=True)):
            invalid=deepcopy(ledger);mutate(invalid)
            with self.assertRaises(ImportError):replay_face_ledger(original,invalid)

    def test_cumulative_group_face_and_batch_limits(self):
        original,initial,source=self.fixture()
        _,ledger,_=append_group_ledger(original,initial,[group(i,source[0]) for i in range(64)])
        with self.assertRaises(ImportError):append_group_ledger(original,ledger,[group(65,source[0])])
        _,ledger,_=append_face_ledger(original,initial,[group(i,source[0])['faces'][0] for i in range(504)])
        with self.assertRaises(ImportError):append_group_ledger(original,ledger,[group(i,source[0]) for i in range(504,513)])
        ledger=initial
        for i in range(8):_,ledger,_=append_group_ledger(original,ledger,[group(i,source[0])])
        with self.assertRaises(ImportError):append_group_ledger(original,ledger,[group(8,source[0])])

    def test_preview_current_v5_to_v6_retains_pose_and_appended_rows(self):
        from importer.assets import decode_tmd
        from importer.animation import pose_vertices
        from importer.model_authoring import preview_model_shape
        import test_model_vector_preview as preview_fixtures
        helper=preview_fixtures.VectorPreviewTests()
        original,current,binding=helper.fixture()
        _,audit=replay_face_ledger(original,binding['ledger'])
        donor=next(r['face_id'] for r in audit['faces'] if r['object_index']==1)
        request=group(9,donor,vertices=[5,0,1,2])
        proposed,ledger,_=append_group_ledger(original,binding['ledger'],[request])
        new_binding=dict(binding,ledger=ledger,asset_sha256=sha256(proposed).hexdigest(),byte_length=len(proposed))
        preview=preview_model_shape(decode_tmd(original),current,binding)
        transforms=[dict(object_index=i,translation=[10*i,20*i,30*i],rotation_psx=[0,0,1024]) for i in range(3)]
        preview.update(posed=True,pose=dict(object_transforms=transforms))
        preview['vertices']=pose_vertices(preview['vertices'],preview['objects'],transforms)
        snapshot=deepcopy(preview)
        result=preview_model_shape(preview,proposed,new_binding);shape=decode_tmd(proposed)
        self.assertEqual(preview,snapshot)
        self.assertEqual(result['vertices'],pose_vertices(shape['vertices'],result['objects'],transforms))
        self.assertEqual(result['triangles'],shape['triangles'])
        self.assertEqual(result['pose'],preview['pose'])


if __name__=='__main__':unittest.main()
