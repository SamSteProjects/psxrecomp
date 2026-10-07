from copy import deepcopy
from hashlib import sha256
import json,unittest
from unittest.mock import patch
from importer.model_json import export_shape_json,import_shape_json,align_shape_vertices
from importer.core import ImportError as RetailImportError
from sdk.scene_preview import source_key
from sdk.project import ProjectError
import test_model_primitive_workflow as fixtures
import test_model_vector_allocation_project as allocation_fixtures
from sdk import model_vector_allocation
from test_model_primitive_workflow import ASSET,http_server,face_edit

class VertexAlignmentTests(unittest.TestCase):
    def test_explicit_coordinate_preserves_other_words_and_is_atomic(self):
        h,p=self.fixture();h.apply([face_edit(h.source)]);current=h.effective();before=h.snapshot()
        for axis in ('x','y','z'):
            for target in (-32768,0,32767):
                values=dict(indices=[0,1],axis=axis,anchor=target);candidate,report=p._prepare_model_object(ASSET,0,'vertex_alignment',values,sha256(current).hexdigest())
                doc=json.loads(export_shape_json(current));a=('x','y','z').index(axis)
                for i in (0,1):doc['objects'][0]['vertices'][i][a]=target
                self.assertEqual(candidate,import_shape_json(current,sha256(current).hexdigest(),json.dumps(doc).encode())[0]);self.assertEqual(report['values'],values);self.assertEqual(h.snapshot(),before)
        for target in (-32769,32768,True,0.0,'0',None):
            with self.assertRaises((ProjectError,RetailImportError)):p.align_model_vertices(ASSET,0,[0,1],'y',target,sha256(current).hexdigest())
            self.assertEqual(h.snapshot(),before)
        p.align_model_vertices(ASSET,0,[0,1],'y',-123,sha256(current).hexdigest());aligned=h.effective();after=h.snapshot();p.align_model_vertices(ASSET,0,[0,1],'y',-123,sha256(aligned).hexdigest());self.assertEqual(h.snapshot(),after);p.undo();self.assertEqual(h.effective(),current);p.redo();self.assertEqual(h.effective(),aligned)

    def test_explicit_coordinate_http_review_and_apply(self):
        h,p=self.fixture();before=h.snapshot();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],axis='z',anchor=-123,expected_sha256=sha256(h.source).hexdigest())
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            request=dict(asset_id=ASSET,object_index=0,operation='vertex_alignment',values={k:body[k] for k in ('indices','axis','anchor')},expected_sha256=body['expected_sha256'])
            status,report=post('/api/model-object-preview',request);self.assertEqual(status,200);self.assertEqual(report['values']['anchor'],-123);self.assertEqual(h.snapshot(),before)
            for anchor in (True,1.0,-32769,32768,None):
                self.assertEqual(post('/api/model-vertices-alignment',dict(body,anchor=anchor))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-alignment',body)[0],200)
            self.assertEqual(post('/api/model-vertices-alignment',body)[0],400)

    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
    def test_candidate_axes_planes_rounding_content_history_and_noop(self):
        h,p=self.fixture();h.apply([face_edit(h.source)]);current=h.effective();before=h.snapshot()
        for axis in ('x','y','z'):
            for anchor in ('min','center','max'):
                values=dict(indices=[0,1],axis=axis,anchor=anchor);candidate,report=p._prepare_model_object(ASSET,0,'vertex_alignment',values,sha256(current).hexdigest())
                doc=json.loads(export_shape_json(current));a=('x','y','z').index(axis);coords=[doc['objects'][0]['vertices'][i][a] for i in (0,1)];target=min(coords) if anchor=='min' else max(coords) if anchor=='max' else (sum(coords)+1)//2
                for i in (0,1):doc['objects'][0]['vertices'][i][a]=target
                self.assertEqual(candidate,import_shape_json(current,sha256(current).hexdigest(),json.dumps(doc).encode())[0]);self.assertEqual(report['values'],values);self.assertEqual(h.snapshot(),before)
        p.align_model_vertices(ASSET,0,[0,1],'x','center',sha256(current).hexdigest());aligned=h.effective();self.assertEqual(len(p.undo_stack),2);unchanged=h.snapshot();p.align_model_vertices(ASSET,0,[0,1],'x','center',sha256(aligned).hexdigest());self.assertEqual(h.snapshot(),unchanged);p.undo();self.assertEqual(h.effective(),current);p.redo();self.assertEqual(h.effective(),aligned)
        doc=json.loads(export_shape_json(h.source));doc['objects'][0]['vertices'][0][0]=-4;doc['objects'][0]['vertices'][1][0]=3;negative=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(doc).encode())[0];result=align_shape_vertices(negative,negative,sha256(negative).hexdigest(),0,[0,1],'x','center');self.assertEqual(json.loads(export_shape_json(result))['objects'][0]['vertices'][0][0],-1)

    def test_http_exact_scene_review_and_stale_rejections(self):
        h,p=self.fixture();before=h.snapshot();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],axis='x',anchor='center',expected_sha256=sha256(h.source).hexdigest())
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            review=dict(asset_id=ASSET,object_index=0,operation='vertex_alignment',values={k:body[k] for k in ('indices','axis','anchor')},expected_sha256=body['expected_sha256'])
            self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            for change in ({'extra':0},{'indices':[0,0]},{'indices':[True]},{'axis':'w'},{'anchor':'mean'},{'expected_sha256':'0'*64}):self.assertEqual(post('/api/model-vertices-alignment',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-alignment',body)[0],200)

    def test_allocated_row_alignment_replays_without_changing_ownership(self):
        h=allocation_fixtures.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture()
        source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64);p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256'])
        current=model_vector_allocation.source(p,asset,'a'*64);count=source['objects'][0]['vertex_count'];before=p.read_model_replacement(asset,p.model_overrides[asset]);doc=json.loads(export_shape_json(before));target=min(doc['objects'][0]['vertices'][i][1] for i in (0,count))
        for i in (0,count):doc['objects'][0]['vertices'][i][1]=target
        expected=import_shape_json(before,current['effective_sha256'],json.dumps(doc).encode())[0]
        p.align_model_vertices(asset,0,[0,count],'y','min',current['effective_sha256']);self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),expected)
        after=model_vector_allocation.source(p,asset,'a'*64);self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview']);p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before);p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),expected)

if __name__=='__main__':unittest.main()
