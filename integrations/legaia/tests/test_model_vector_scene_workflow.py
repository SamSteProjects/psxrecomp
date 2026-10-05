"""Vector preview shares Apply bytes while keeping project/history/files read-only."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.model_json import export_shape_json,import_shape_json
from sdk.project import ProjectError
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET,face_edit,http_server

class ModelVectorPreviewTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.ModelPrimitiveProjectWorkflow();helper.setUp();self.addCleanup(helper.doCleanups)
        return helper,helper.project

    def test_exact_current_candidate_compose_and_apply_history(self):
        h,p=self.fixture();h.apply([face_edit(h.source)]);effective=h.effective();before=h.snapshot()
        candidate,report=p.preview_model_vector(ASSET,0,'vertices',1,[14,5,6],sha256(effective).hexdigest())
        expected=json.loads(export_shape_json(effective));expected['objects'][0]['vertices'][1]=[14,5,6]
        self.assertEqual(candidate,import_shape_json(effective,sha256(effective).hexdigest(),json.dumps(expected).encode())[0])
        self.assertEqual(report['preview'],decode_tmd(candidate));self.assertEqual(report['current_preview'],decode_tmd(effective))
        self.assertEqual(h.snapshot(),before);self.assertFalse(report['project_changed'])
        p.set_model_vector(ASSET,0,'vertices',1,[14,5,6],sha256(effective).hexdigest());self.assertEqual(h.effective(),candidate)
        self.assertEqual(len(p.undo_stack),2);p.undo();self.assertEqual(h.effective(),effective);p.redo();self.assertEqual(h.effective(),candidate)
        for changes in [(0,'vertices',1,[1,2,3],'0'*64),(0,'vertices',99,[1,2,3],sha256(candidate).hexdigest()),(True,'vertices',0,[1,2,3],sha256(candidate).hexdigest()),(0,'vertices',0,[32768,0,0],sha256(candidate).hexdigest())]:
            with self.assertRaises((ProjectError,ValueError)):p.preview_model_vector(ASSET,*changes)

    def test_http_exact_envelopes_scene_source_and_read_only(self):
        h,p=self.fixture();before=h.snapshot();body=dict(asset_id=ASSET,object_index=0,kind='vertices',vector_index=1,values=[14,5,6],expected_sha256=sha256(h.source).hexdigest())
        with patch('sdk.scene_preview.source_key',return_value='a'*64),http_server(p) as (server,post):
            with patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
                status,report=post('/api/model-vector-preview',body);self.assertEqual(status,200);self.assertEqual(report['vector_index'],1)
                for changes in ({'extra':0},{'values':[True,0,0]},{'vector_index':999},{'expected_sha256':'0'*64}):self.assertEqual(post('/api/model-vector-preview',dict(body,**changes))[0],400)
                scene=dict(body,entity_id='scene://fixture/actors/man-p1/0001',source_key='a'*64,all_instances=True)
                with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:dict(report,entity_id=entity,project_source_key=key,all_instances=all_instances)) as compose:
                    status,report=post('/api/model-vector-scene-preview',scene);self.assertEqual(status,200);self.assertTrue(report['all_instances']);self.assertEqual(compose.call_count,1)
                    for changes in ({'source_key':'b'*64},{'all_instances':1},{'operation':'vector'}):self.assertEqual(post('/api/model-vector-scene-preview',dict(scene,**changes))[0],400)
                    self.assertEqual(compose.call_count,1)
        self.assertEqual(h.snapshot(),before)
