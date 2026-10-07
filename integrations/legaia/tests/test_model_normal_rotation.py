from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_json import export_shape_json,import_shape_json
from importer.model_normal_rotation import rotate_object_normals
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET,http_server
from test_model_rotation import ModelRotationTests

class ObjectNormalAngles(unittest.TestCase):
    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow()
        with patch.object(fixtures,'model',return_value=ModelRotationTests().source()):h.setUp()
        self.addCleanup(h.doCleanups);return h,h.project

    def test_literal_cardinals_custom_words_and_only_normal_bytes(self):
        source=ModelRotationTests().source();doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[1000,0,0];source=import_shape_json(source,sha256(source).hexdigest(),json.dumps(doc).encode())[0];key=sha256(source).hexdigest()
        for axis,angle,expected in [('x',1024,[1000,0,0]),('y',1024,[0,0,-1000]),('z',1024,[0,1000,0]),('y',512,[707,0,-707]),('z',3072,[0,-1000,0])]:
            result=rotate_object_normals(source,source,key,0,axis,angle);normal=12+struct.unpack_from('<I',source,20)[0]
            self.assertEqual(list(struct.unpack_from('<hhh',result,normal)),expected)
            self.assertTrue(all(i in range(normal,normal+6) for i,(a,b) in enumerate(zip(source,result)) if a!=b))
            self.assertEqual(len(result),len(source))
        self.assertEqual(rotate_object_normals(source,source,key,0,'y',0),source)
        from test_importer_assets import model
        empty=model(0x21)
        with self.assertRaisesRegex(ImportError,'stored normals'):rotate_object_normals(empty,empty,sha256(empty).hexdigest(),0,'y',512)
        doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[-32768,0,0];overflow=import_shape_json(source,key,json.dumps(doc).encode())[0]
        with self.assertRaisesRegex(ImportError,'signed16'):rotate_object_normals(overflow,overflow,sha256(overflow).hexdigest(),0,'y',2048)

    def test_review_required_hash_history_and_noop(self):
        h,p=self.fixture();before=h.snapshot();values=dict(axis='y',angle_units=512);key=sha256(h.source).hexdigest();candidate,report=p._prepare_model_object(ASSET,0,'normal_rotation_angle',values,key)
        self.assertEqual(report['values'],values);self.assertEqual(report['normal_rotation_words']['current'],json.loads(export_shape_json(h.source))['objects'][0]['normals']);self.assertEqual(report['normal_rotation_words']['proposed'],json.loads(export_shape_json(candidate))['objects'][0]['normals']);self.assertEqual(h.snapshot(),before)
        with self.assertRaises(ProjectError):p.rotate_model_normals_angle(ASSET,0,'y',512,key,'0'*64)
        self.assertEqual(h.snapshot(),before);p.rotate_model_normals_angle(ASSET,0,'y',512,key,sha256(candidate).hexdigest());self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        before=h.snapshot();p.rotate_model_normals_angle(ASSET,0,'y',0,sha256(candidate).hexdigest(),sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)
        for obj,axis,angle,key in [(True,'y',512,sha256(candidate).hexdigest()),(99,'y',512,sha256(candidate).hexdigest()),(0,'w',512,sha256(candidate).hexdigest()),(0,'y',True,sha256(candidate).hexdigest()),(0,'y',4096,sha256(candidate).hexdigest()),(0,'y',-1,sha256(candidate).hexdigest()),(0,'y',512,'0'*64)]:
            with self.assertRaises((ImportError,ProjectError)):p.rotate_model_normals_angle(ASSET,obj,axis,angle,key,sha256(candidate).hexdigest())
        self.assertEqual(h.snapshot(),before)

    def test_http_exact_fields_and_scene_readonly(self):
        h,p=self.fixture();key=sha256(h.source).hexdigest();body=dict(asset_id=ASSET,object_index=0,axis='y',angle_units=512,expected_sha256=key);candidate,report=p._prepare_model_object(ASSET,0,'normal_rotation_angle',dict(axis='y',angle_units=512),key);body['proposed_sha256']=sha256(candidate).hexdigest();before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            from urllib.request import urlopen
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-normal-rotation.js') as module:
                self.assertEqual(module.status,200);self.assertIn('javascript',module.headers['Content-Type']);self.assertIn(b'export function rotateStoredNormals',module.read())
            review=dict(asset_id=ASSET,object_index=0,operation='normal_rotation_angle',values=dict(axis='y',angle_units=512),expected_sha256=key)
            self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for changes in ({'extra':0},{'axis':'w'},{'angle_units':True},{'expected_sha256':'0'*64},{'proposed_sha256':'0'*64}):self.assertEqual(post('/api/model-object-normal-angle',dict(body,**changes))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-object-normal-angle',body)[0],200)

    def test_allocated_normal_rows_preserve_ownership(self):
        import test_model_vector_allocation_project as allocations
        from sdk import model_vector_allocation
        h=allocations.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture();source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();review=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,review['proposed_sha256']);current=model_vector_allocation.source(p,asset,'a'*64)
        candidate,report=p._prepare_model_object(asset,0,'normal_rotation_angle',dict(axis='y',angle_units=512),current['effective_sha256']);p.rotate_model_normals_angle(asset,0,'y',512,current['effective_sha256'],sha256(candidate).hexdigest());after=model_vector_allocation.source(p,asset,'a'*64)
        self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['retail_preview'],current['retail_preview']);p.undo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],current['effective_sha256']);p.redo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],after['effective_sha256'])

if __name__=='__main__':unittest.main()
