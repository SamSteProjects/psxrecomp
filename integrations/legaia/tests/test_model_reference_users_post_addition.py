"""Stored reference navigation qualifies retained and authored face identities."""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch
from sdk import model_normal_users, model_vertex_users
from sdk.project import ProjectError
import test_model_face_addition_project as fixtures
from test_model_primitives import synthetic
from sdk.model_face_addition import source, review
from test_model_primitive_workflow import http_server


class AddedReferenceUsersTests(unittest.TestCase):
    def fixture(self, removed=False, flags=0x12):
        helper=fixtures.ModelFaceAdditionProjectTests();self.addCleanup(helper.doCleanups)
        helper.context();original=synthetic(((flags,),),count=2)
        with patch('test_model_face_addition_project.synthetic',return_value=original):
            p,asset,_,current=helper.project('tmd-face-removal-v1' if removed else None)
        p.disc_path='synthetic-disc.bin';p.imports[p.active_scene]={'assets':{'models':[{'semantic_id':asset}]}}
        donor=source(p,asset,'a'*64)['topology']['faces'][0]['face_id'];requests=[helper.request(donor)]
        proposal=review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,proposal['proposed_sha256'])
        for noun in ('normal','vertex'):
            self.enterContext(patch(f'sdk.model_{noun}_users._disc_context',side_effect=lambda _:nullcontext()))
            self.enterContext(patch(f'sdk.model_{noun}_users.source_key',return_value='a'*64))
        return p,asset

    def test_both_reference_layers_include_authored_faces_and_updated_content(self):
        p,asset=self.fixture()
        for noun,module,kind in [('normal',model_normal_users,'normals'),('vertex',model_vertex_users,'vertices')]:
            with self.subTest(noun=noun):
                current=p.read_model_replacement(asset,p.model_overrides[asset])
                p.set_model_vector(asset,0,kind,0,[17,23,-5],sha256(current).hexdigest())
                current=p.read_model_replacement(asset,p.model_overrides[asset])
                before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
                report=module.inspect(p,asset,0,0,sha256(current).hexdigest(),'a'*64)
                self.assertEqual(report['schema_version'],f'legaia.model-{noun}-users.v2')
                self.assertEqual(report['current_coordinates'],[17,23,-5])
                self.assertEqual(report['current_face_count'],3)
                self.assertEqual(len(report['authored_faces']),1)
                owned={row['current_index'] for row in report['face_mapping'] if row['current_index'] is not None}
                owned.update(row['current_index'] for row in report['authored_faces'])
                self.assertEqual(owned,{0,1,2})
                self.assertIn(report['authored_faces'][0]['current_index'],{row['primitive_index'] for row in report['current_users']})
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
                for obj,index,expected,key in [(False,0,sha256(current).hexdigest(),'a'*64),(0,0,'0'*64,'a'*64),(0,0,sha256(current).hexdigest(),'0'*64)]:
                    with self.assertRaises(ProjectError):module.inspect(p,asset,obj,index,expected,key)
                self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)

    def test_HTTP_reference_layers_keep_stable_authored_identity(self):
        p,asset=self.fixture();current=p.read_model_replacement(asset,p.model_overrides[asset])
        with http_server(p) as (_,post):
            for noun in ('normal','vertex'):
                body=dict(asset_id=asset,object_index=0,expected_sha256=sha256(current).hexdigest(),source_key='a'*64,**{noun+'_index':0})
                status,report=post(f'/api/model-{noun}-users',body)
                self.assertEqual(status,200)
                self.assertEqual(report['schema_version'],f'legaia.model-{noun}-users.v2')
                self.assertTrue(report['read_only'])
                self.assertFalse(report['gameplay_verified'])
                self.assertEqual(report['current_face_count'],3)
                self.assertEqual(post(f'/api/model-{noun}-users',dict(body,expected_sha256='0'*64))[0],400)

    def test_retained_removal_base_maps_both_reference_layers(self):
        p,asset=self.fixture(removed=True);current=p.read_model_replacement(asset,p.model_overrides[asset])
        for module in (model_normal_users,model_vertex_users):
            report=module.inspect(p,asset,0,0,sha256(current).hexdigest(),'a'*64)
            self.assertEqual(report['face_mapping'],[dict(retail_index=0,current_index=None),dict(retail_index=1,current_index=0)])
            self.assertEqual(report['current_face_count'],2)
            self.assertEqual(report['authored_faces'][0]['current_index'],1)
            self.assertEqual({row['primitive_index'] for row in report['current_users']},{0,1})
            self.assertEqual({row['primitive_index'] for row in report['retail_users']},{0,1})

    def test_baked_added_faces_do_not_invent_normal_operands(self):
        p,asset=self.fixture(flags=0x22);current=p.read_model_replacement(asset,p.model_overrides[asset])
        report=model_normal_users.inspect(p,asset,0,0,sha256(current).hexdigest(),'a'*64)
        self.assertEqual(report['current_face_count'],3)
        self.assertEqual(len(report['authored_faces']),1)
        self.assertEqual(report['current_users'],[])
        self.assertEqual(report['retail_users'],[])


if __name__=='__main__': unittest.main()
