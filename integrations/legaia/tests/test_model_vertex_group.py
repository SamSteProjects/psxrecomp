"""Atomic group movement shares scene review/Apply and preserves all other words."""
from hashlib import sha256
import json, unittest
from copy import deepcopy
from unittest.mock import patch
from importer.model_json import export_shape_json,import_shape_json
from importer.core import ImportError as RetailImportError
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET,http_server,face_edit

class VertexGroupTests(unittest.TestCase):
    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups)
        h.apply([face_edit(h.source)]);return h,h.project

    def test_exact_group_compose_read_only_apply_history_and_rejections(self):
        h,p=self.fixture();current=h.effective();before=h.snapshot()
        values=dict(indices=[0,2],offset=[16,-8,32]);candidate,report=p._prepare_model_object(ASSET,0,'vertex_translation',values,sha256(current).hexdigest())
        doc=json.loads(export_shape_json(current))
        for i in values['indices']:doc['objects'][0]['vertices'][i]=[v+values['offset'][a] for a,v in enumerate(doc['objects'][0]['vertices'][i])]
        self.assertEqual(candidate,import_shape_json(current,sha256(current).hexdigest(),json.dumps(doc).encode())[0]);self.assertEqual(h.snapshot(),before);self.assertEqual(report['values'],values)
        report['values']['indices'][0]=99;self.assertEqual(values['indices'],[0,2])
        p.translate_model_vertices(ASSET,0,values['indices'],values['offset'],sha256(current).hexdigest());self.assertEqual(h.effective(),candidate);self.assertEqual(len(p.undo_stack),2)
        p.undo();self.assertEqual(h.effective(),current);p.redo();self.assertEqual(h.effective(),candidate)
        for indices,offset in [([],[0,0,0]),([0,0],[1,0,0]),([True],[1,0,0]),([-1],[1,0,0]),([99],[1,0,0]),([0],[32768,0,0]),([0],[1.5,0,0]),([0],[True,0,0]),([0],[32767,0,0]),([0],[])]:
            before=h.snapshot()
            with self.assertRaises((ProjectError,ValueError,RetailImportError)):p.translate_model_vertices(ASSET,0,indices,offset,sha256(candidate).hexdigest())
            self.assertEqual(h.snapshot(),before)
        before=h.snapshot();p.translate_model_vertices(ASSET,0,[0,2],[0,0,0],sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)

    def test_http_exact_fields_stale_and_scene_review(self):
        h,p=self.fixture();key=source_key(p);values=dict(indices=[0,2],offset=[16,-8,32]);body=dict(asset_id=ASSET,object_index=0,indices=values['indices'],offset=values['offset'],expected_sha256=sha256(h.effective()).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            review=dict(asset_id=ASSET,object_index=0,operation='vertex_translation',values=values,expected_sha256=body['expected_sha256'])
            self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:dict(report,project_source_key=key)):
                scene=dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=key)
                status,report=post('/api/model-object-scene-preview',scene);self.assertEqual(status,200);self.assertEqual(report['values'],values)
                self.assertEqual(post('/api/model-object-scene-preview',dict(scene,source_key='0'*64))[0],400)
            self.assertEqual(h.snapshot(),before)
            for change in ({'extra':0},{'expected_sha256':'0'*64},{'indices':[0,0]},{'offset':[0,True,0]}):
                self.assertEqual(post('/api/model-vertices-translation',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-translation',body)[0],200)

if __name__=='__main__':unittest.main()
