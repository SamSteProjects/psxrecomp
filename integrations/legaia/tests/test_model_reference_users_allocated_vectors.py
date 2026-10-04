"""New vectors have qualified Current users and no invented Retail counterpart."""
from copy import deepcopy
from hashlib import sha256
import unittest
import struct
from unittest.mock import patch
from sdk import model_vertex_users,model_normal_users,model_vector_allocation,model_face_addition
from test_model_primitive_workflow import http_server
import test_model_reference_users_post_addition as fixtures


class AllocatedReferenceTests(unittest.TestCase):
    def fixture(self,removed=False):
        helper=fixtures.AddedReferenceUsersTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture(removed=removed,flags=0x16)
        self.enterContext(patch('sdk.model_vector_allocation.source_key',return_value='a'*64))
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        requests=[dict(object_index=0,kind=kind,vectors=[[100,200,300],[400,500,600],[700,800,900]]) for kind in ('vertices','normals')]
        report=model_vector_allocation.review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_vector_allocations(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        donor=model_face_addition.source(p,asset,'a'*64)['topology']['faces'][0]
        requests=[dict(face_id='face://authored/00000000-0000-4000-8000-000000000099',
            donor_face_id=donor['face_id'],fields=dict(vertices=[5,6,0,1],normal_indices=[4,5,4,5]))]
        report=model_face_addition.review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        return p,asset

    def test_both_layers_qualify_new_and_retained_rows_without_mutation(self):
        for removed in (False,True):
            p,asset=self.fixture(removed);current=p.read_model_replacement(asset,p.model_overrides[asset]);state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            for noun,module,index,unused,retail_count,current_count in (
                    ('vertex',model_vertex_users,5,7,5,8),('normal',model_normal_users,4,6,4,7)):
                with self.subTest(noun=noun,removed=removed):
                    report=module.inspect(p,asset,0,index,sha256(current).hexdigest(),'a'*64)
                    self.assertEqual(report['schema_version'],f'legaia.model-{noun}-users.v3')
                    self.assertEqual(report['vector_origin'],'allocated')
                    self.assertIsNone(report['retail_coordinates']);self.assertEqual(report['retail_users'],[])
                    self.assertEqual(report['current_coordinates'],[100,200,300])
                    self.assertEqual(report['retail_vector_count'],retail_count);self.assertEqual(report['current_vector_count'],current_count)
                    self.assertTrue(report['current_users']);self.assertEqual(len({row['primitive_index'] for row in report['current_users']}),1)
                    authored=next(face for face in report['authored_faces'] if face['face_id'].endswith('0099'))
                    self.assertEqual({row['primitive_index'] for row in report['current_users']},{authored['current_index']})
                    old=module.inspect(p,asset,0,0,sha256(current).hexdigest(),'a'*64)
                    self.assertEqual(old['vector_origin'],'retail');self.assertIsNotNone(old['retail_coordinates']);self.assertTrue(old['retail_users'])
                    empty=module.inspect(p,asset,0,unused,sha256(current).hexdigest(),'a'*64)
                    self.assertEqual(empty['current_users'],[]);self.assertEqual(empty['current_coordinates'],[700,800,900]);self.assertIsNone(empty['retail_coordinates'])
                    if removed:self.assertIsNone(report['face_mapping'][0]['current_index'])
                    self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)

    def test_HTTP_allocated_rows_and_stale_inspection_rejection(self):
        p,asset=self.fixture();current=p.read_model_replacement(asset,p.model_overrides[asset]);state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            for noun,index in (('vertex',5),('normal',4)):
                body=dict(asset_id=asset,object_index=0,source_key='a'*64,expected_sha256=sha256(current).hexdigest(),**{noun+'_index':index})
                status,report=post(f'/api/model-{noun}-users',body);self.assertEqual(status,200)
                self.assertEqual(report['vector_origin'],'allocated');self.assertIsNone(report['retail_coordinates']);self.assertEqual(report['retail_users'],[])
                for changes in (dict(expected_sha256='0'*64),dict(source_key='0'*64),{noun+'_index':True},{noun+'_index':99}):
                    self.assertEqual(post(f'/api/model-{noun}-users',dict(body,**changes))[0],400)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)

    def test_first_normal_in_empty_retail_table_has_no_retail_coordinates(self):
        from test_model_primitives import synthetic
        original=bytearray(synthetic(((0x22,),),count=2));struct.pack_into('<II',original,20,0,0)
        helper=fixtures.AddedReferenceUsersTests();self.addCleanup(helper.doCleanups)
        with patch('test_model_reference_users_post_addition.synthetic',return_value=bytes(original)):
            p,asset=helper.fixture(flags=0x22)
        self.enterContext(patch('sdk.model_vector_allocation.source_key',return_value='a'*64))
        current=p.read_model_replacement(asset,p.model_overrides[asset]);requests=[dict(object_index=0,kind='normals',vectors=[[4096,0,0]])]
        proposal=model_vector_allocation.review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_vector_allocations(asset,requests,sha256(current).hexdigest(),'a'*64,proposal['proposed_sha256'])
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        report=model_normal_users.inspect(p,asset,0,0,sha256(current).hexdigest(),'a'*64)
        self.assertEqual(report['retail_vector_count'],0);self.assertEqual(report['current_vector_count'],1)
        self.assertEqual(report['vector_origin'],'allocated');self.assertIsNone(report['retail_coordinates'])
        self.assertEqual(report['current_coordinates'],[4096,0,0]);self.assertEqual(report['current_users'],[])


if __name__=='__main__':unittest.main()
