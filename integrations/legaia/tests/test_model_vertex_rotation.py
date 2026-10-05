from hashlib import sha256
import json,unittest
from unittest.mock import patch
from importer.model_json import export_shape_json,import_shape_json,rotate_shape_vertices
from importer.core import ImportError
from sdk.scene_preview import source_key
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET,http_server

class VertexRotationTests(unittest.TestCase):
    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project

    def test_axes_pivots_rounding_subset_and_history(self):
        h,p=self.fixture();doc=json.loads(export_shape_json(h.source));probe=json.loads(export_shape_json(h.source));probe['objects'][0]['vertices'][:2]=[[-4,0,1],[3,1,2]]
        native=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(probe).encode())[0]
        for axis,expected in [('x',[-4,-1,0]),('y',[1,0,4]),('z',[0,-4,1])]:
            result=rotate_shape_vertices(native,native,sha256(native).hexdigest(),0,[0],axis,1,'origin')
            self.assertEqual(json.loads(export_shape_json(result))['objects'][0]['vertices'][0],expected)
        result=rotate_shape_vertices(native,native,sha256(native).hexdigest(),0,[0,1],'y',1,'center')
        out=json.loads(export_shape_json(result));self.assertEqual(out['objects'][0]['vertices'][:2],[[-1,0,5],[0,1,-2]])
        self.assertEqual(out['objects'][0]['vertices'][2:],probe['objects'][0]['vertices'][2:]);self.assertEqual(out['objects'][0]['normals'],probe['objects'][0]['normals'])
        key=sha256(h.source).hexdigest();candidate,report=p._prepare_model_object(ASSET,0,'vertex_rotation',dict(indices=[0,1],axis='y',quarter_turns=1,pivot='center'),key)
        p.rotate_model_vertices(ASSET,0,[0,1],'y',1,'center',key);self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        before=h.snapshot();p.rotate_model_vertices(ASSET,0,[0],'z',2,'center',sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)
        # Signed permutations invert exactly about the origin when representable.
        inverse=rotate_shape_vertices(native,native,sha256(native).hexdigest(),0,[0,1],'z',-1,'origin')
        restored=rotate_shape_vertices(native,inverse,sha256(inverse).hexdigest(),0,[0,1],'z',1,'origin');self.assertEqual(restored,native)

    def test_rejections_and_overflow_are_atomic(self):
        h,p=self.fixture();key=sha256(h.source).hexdigest();before=h.snapshot()
        for indices,axis,turn,pivot,digest in [([0,0],'x',1,'origin',key),([True],'x',1,'origin',key),([0],'w',1,'origin',key),([0],'x',True,'origin',key),([0],'x',0,'origin',key),([0],'x',3,'origin',key),([0],'x',1,'mean',key),([0],'x',1,'origin','0'*64)]:
            with self.assertRaises(ImportError):rotate_shape_vertices(h.source,h.source,digest,0,indices,axis,turn,pivot)
        probe=json.loads(export_shape_json(h.source));probe['objects'][0]['vertices'][0]=[-32768,0,0];native=import_shape_json(h.source,key,json.dumps(probe).encode())[0]
        with self.assertRaisesRegex(ImportError,'signed16'):rotate_shape_vertices(native,native,sha256(native).hexdigest(),0,[0],'y',1,'origin')
        self.assertEqual(h.snapshot(),before)

    def test_allocated_rows_keep_ownership(self):
        import test_model_vector_allocation_project as allocations
        from sdk import model_vector_allocation
        h=allocations.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture();source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256']);current=model_vector_allocation.source(p,asset,'a'*64)
        p.rotate_model_vertices(asset,0,[0,source['objects'][0]['vertex_count']],'y',1,'center',current['effective_sha256']);after=model_vector_allocation.source(p,asset,'a'*64)
        self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview']);p.undo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],current['effective_sha256']);p.redo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],after['effective_sha256'])

    def test_http_exact_review_scene_and_apply(self):
        h,p=self.fixture();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],axis='y',quarter_turns=1,pivot='origin',expected_sha256=sha256(h.source).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            review=dict(asset_id=ASSET,object_index=0,operation='vertex_rotation',values={k:body[k] for k in ('indices','axis','quarter_turns','pivot')},expected_sha256=body['expected_sha256'])
            status,report=post('/api/model-object-preview',review);self.assertEqual(status,200);self.assertEqual(report['values'],review['values']);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            for change in ({'extra':0},{'quarter_turns':True},{'quarter_turns':0},{'pivot':'mean'},{'indices':[0,0]},{'expected_sha256':'0'*64}):self.assertEqual(post('/api/model-vertices-rotation',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-rotation',body)[0],200)

if __name__=='__main__':unittest.main()
