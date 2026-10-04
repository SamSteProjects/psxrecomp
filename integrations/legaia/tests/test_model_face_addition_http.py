from copy import deepcopy
from hashlib import sha256
from http.client import HTTPConnection
import unittest
from unittest.mock import patch

from sdk.export_snapshot import capture_export_inputs
from sdk.project import ProjectError
import test_model_face_addition_project as fixtures
from test_model_primitive_workflow import http_server


class ModelFaceAdditionHttpTests(unittest.TestCase):
    def fixture(self, kind=None):
        helper = fixtures.ModelFaceAdditionProjectTests();self.addCleanup(helper.doCleanups)
        self.enterContext(patch('sdk.scene_preview.source_key', return_value='a'*64))
        self.enterContext(patch('sdk.model_face_addition.source_key', return_value='a'*64))
        return helper, helper.project(kind)

    def test_source_review_apply_and_stale_repeat_leave_qualified_history(self):
        helper,(p,asset,_,current) = self.fixture('tmd-shape')
        with http_server(p) as (server, post), patch.object(server, 'state', return_value={'applied':True}):
            status,info = post('/api/model-face-addition-source',dict(asset_id=asset,source_key='a'*64))
            self.assertEqual(status,200)
            self.assertEqual(info['objects'][0]['primitives'][0]['corner_count'],4)
            request = helper.request(info['topology']['faces'][0]['face_id'])
            body=dict(asset_id=asset,source_key='a'*64,expected_sha256=sha256(current).hexdigest(),requests=[request])
            before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            status,report=post('/api/model-face-addition-preview',body)
            self.assertEqual(status,200);self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            self.assertFalse(report['project_changed'])
            status,_=post('/api/model-face-addition',dict(body,proposed_sha256='0'*64))
            self.assertEqual(status,400);self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
            status,_=post('/api/model-face-addition',dict(body,proposed_sha256=report['proposed_sha256']))
            self.assertEqual(status,200);self.assertEqual(len(p.undo_stack),1)
            candidate=p.read_model_replacement(asset,p.model_overrides[asset])
            self.assertEqual(sha256(candidate).hexdigest(),report['proposed_sha256'])
            applied=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
            self.assertEqual(post('/api/model-face-addition',dict(body,proposed_sha256=report['proposed_sha256']))[0],400)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),applied)

    def test_exact_envelopes_types_limits_and_declared_body_reject_before_source(self):
        _,(p,asset,_,current) = self.fixture()
        source_body=dict(asset_id=asset,source_key='a'*64)
        review_body=dict(source_body,expected_sha256=sha256(current).hexdigest(),requests=[{}])
        with http_server(p) as (server,post), patch('sdk.model_face_addition.source') as source, patch('sdk.model_face_addition.review') as review:
            cases=[('/api/model-face-addition-source',dict(source_body,extra=True)),
                   ('/api/model-face-addition-source',dict(source_body,asset_id=[])),
                   ('/api/model-face-addition-source',dict(source_body,source_key=True)),
                   ('/api/model-face-addition-source',dict(source_body,source_key='A'*64)),
                   ('/api/model-face-addition-preview',dict(review_body,requests={})),
                   ('/api/model-face-addition-preview',dict(review_body,requests=[])),
                   ('/api/model-face-addition-preview',dict(review_body,requests=[{}]*129)),
                   ('/api/model-face-addition-preview',dict(review_body,expected_sha256=False)),
                   ('/api/model-face-addition',dict(review_body,proposed_sha256='stale'))]
            for route,body in cases:self.assertEqual(post(route,body)[0],400)
            for route,limit in (('/api/model-face-addition-source',32768),('/api/model-face-addition-preview',256*1024),('/api/model-face-addition',256*1024)):
                connection=HTTPConnection('127.0.0.1',server.server_port,timeout=10)
                try:
                    connection.request('POST',route,body=b'',headers={'Content-Type':'application/json','Content-Length':str(limit+1)})
                    response=connection.getresponse();self.assertEqual(response.status,400);response.read()
                finally:connection.close()
            source.assert_not_called();review.assert_not_called()
        self.assertEqual(p.model_overrides,{});self.assertEqual(p.undo_stack,[])

    def test_snapshot_includes_and_qualifies_retained_base_dependency(self):
        helper,(p,asset,_,current) = self.fixture('tmd-shape')
        from sdk.model_face_addition import source,review
        donor=source(p,asset,'a'*64)['topology']['faces'][0]['face_id'];requests=[helper.request(donor)]
        report=review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
        p.apply_model_face_additions(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        before=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));binding=p.model_overrides[asset]
        _,files=capture_export_inputs(p)
        base_path=f"Authored/Models/{binding['base_binding']['asset_sha256']}.tmd"
        self.assertEqual(files[base_path],current)
        self.assertEqual(files[f"Authored/Models/{binding['asset_sha256']}.tmd"],p.read_model_replacement(asset,binding))
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),before)
        with self.assertRaises(ProjectError):capture_export_inputs(p,max_files=2)
        (p.root/base_path).write_bytes(bytes(len(current)))
        with self.assertRaises(ProjectError):capture_export_inputs(p)


if __name__=='__main__':unittest.main()
