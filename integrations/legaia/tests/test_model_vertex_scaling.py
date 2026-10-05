from hashlib import sha256
import json,unittest
from unittest.mock import patch
from importer.model_json import export_shape_json,import_shape_json,scale_shape_vertices
from importer.core import ImportError
from sdk.scene_preview import source_key
import test_model_primitive_workflow as fixtures
import test_model_vector_allocation_project as allocations
from sdk import model_vector_allocation
from test_model_primitive_workflow import ASSET,http_server

class VertexScalingTests(unittest.TestCase):
    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project

    def test_native_subset_rounding_history_noop_and_rejections(self):
        h,p=self.fixture();before=h.snapshot();doc=json.loads(export_shape_json(h.source))
        candidate,report=p._prepare_model_object(ASSET,0,'vertex_scaling',dict(indices=[0,1],percent=150,pivot='center'),sha256(h.source).hexdigest())
        after=json.loads(export_shape_json(candidate));original=doc['objects'][0]['vertices']
        for a in range(3):
            center2=min(original[i][a] for i in (0,1))+max(original[i][a] for i in (0,1))
            for i in (0,1):
                n=center2*100+(2*original[i][a]-center2)*150
                self.assertEqual(after['objects'][0]['vertices'][i][a],((abs(n)+100)//200)*(-1 if n<0 else 1))
        self.assertEqual(after['objects'][0]['vertices'][2:],original[2:]);self.assertEqual(after['objects'][0]['normals'],doc['objects'][0]['normals']);self.assertEqual(h.snapshot(),before)
        p.scale_model_vertices(ASSET,0,[0,1],150,'center',sha256(h.source).hexdigest());self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        unchanged=h.snapshot();p.scale_model_vertices(ASSET,0,[0,1],100,'center',sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),unchanged)
        for indices,percent,pivot,key in [([0,0],150,'center',sha256(candidate).hexdigest()),([True],150,'center',sha256(candidate).hexdigest()),([0],True,'origin',sha256(candidate).hexdigest()),([0],0,'origin',sha256(candidate).hexdigest()),([0],1001,'origin',sha256(candidate).hexdigest()),([0],150,'mean',sha256(candidate).hexdigest()),([0],150,'origin','0'*64)]:
            with self.assertRaises(ImportError):scale_shape_vertices(candidate,candidate,key,0,indices,percent,pivot)
        self.assertEqual(h.snapshot(),unchanged)
        probe=json.loads(export_shape_json(h.source));probe['objects'][0]['vertices'][0]=[-4,0,0];probe['objects'][0]['vertices'][1]=[3,0,0]
        negative=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(probe).encode())[0]
        rounded=scale_shape_vertices(negative,negative,sha256(negative).hexdigest(),0,[0,1],150,'center')
        self.assertEqual(json.loads(export_shape_json(rounded))['objects'][0]['vertices'][:2],[[-6,0,0],[5,0,0]])
        probe['objects'][0]['vertices'][0]=[32767,0,0];overflow=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(probe).encode())[0]
        with self.assertRaisesRegex(ImportError,'signed16'):scale_shape_vertices(overflow,overflow,sha256(overflow).hexdigest(),0,[0],200,'origin')

    def test_http_review_scene_and_exact_apply(self):
        h,p=self.fixture();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],percent=150,pivot='origin',expected_sha256=sha256(h.source).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            review=dict(asset_id=ASSET,object_index=0,operation='vertex_scaling',values={k:body[k] for k in ('indices','percent','pivot')},expected_sha256=body['expected_sha256'])
            status,report=post('/api/model-object-preview',review);self.assertEqual(status,200);self.assertEqual(report['values'],review['values']);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            for change in ({'extra':0},{'percent':True},{'percent':0},{'pivot':'mean'},{'indices':[0,0]},{'expected_sha256':'0'*64}):self.assertEqual(post('/api/model-vertices-scaling',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-scaling',body)[0],200)

    def test_allocated_rows_keep_ownership(self):
        h=allocations.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture();source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256']);current=model_vector_allocation.source(p,asset,'a'*64)
        p.scale_model_vertices(asset,0,[0,source['objects'][0]['vertex_count']],150,'center',current['effective_sha256']);after=model_vector_allocation.source(p,asset,'a'*64)
        self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview']);p.undo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],current['effective_sha256']);p.redo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],after['effective_sha256'])

if __name__=='__main__':unittest.main()
