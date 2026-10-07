from hashlib import sha256
import json,unittest
from importer.model_json import export_shape_json,import_shape_json,rotate_shape_vertices,rotate_shape_vertices_angle
from importer.core import ImportError
import test_model_vertex_rotation as fixtures
from test_model_primitive_workflow import ASSET
from test_model_primitive_workflow import http_server
from unittest.mock import patch
from sdk.scene_preview import source_key

class VertexAngles(unittest.TestCase):
    def fixture(self):return fixtures.VertexRotationTests.fixture(self)
    def test_cardinals_pivots_and_literal_intermediate_coordinates(self):
        h,p=self.fixture();key=sha256(h.source).hexdigest()
        for axis in ['x','y','z']:
            for pivot in ['origin','center']:
                for turn,angle in [(-1,3072),(1,1024),(2,2048)]:
                    self.assertEqual(rotate_shape_vertices_angle(h.source,h.source,key,0,[0,1],axis,angle,pivot),rotate_shape_vertices(h.source,h.source,key,0,[0,1],axis,turn,pivot))
        probe=json.loads(export_shape_json(h.source));probe['objects'][0]['vertices'][0]=[1000,0,0]
        native=import_shape_json(h.source,key,json.dumps(probe).encode())[0];digest=sha256(native).hexdigest()
        result=rotate_shape_vertices_angle(native,native,digest,0,[0],'y',512,'origin');out=json.loads(export_shape_json(result))
        self.assertEqual(out['objects'][0]['vertices'][0],[707,0,-707]);self.assertEqual(out['objects'][0]['vertices'][1:],probe['objects'][0]['vertices'][1:]);self.assertEqual(out['objects'][0]['normals'],probe['objects'][0]['normals'])
        self.assertEqual(rotate_shape_vertices_angle(native,native,digest,0,[0,1],'x',0,'center'),native)

    def test_source_qualified_review_history_and_atomic_rejection(self):
        h,p=self.fixture();key=sha256(h.source).hexdigest();values=dict(indices=[0,1],axis='y',angle_units=512,pivot='center')
        candidate,report=p._prepare_model_object(ASSET,0,'vertex_rotation_angle',values,key);self.assertEqual(report['values'],values)
        p.rotate_model_vertices_angle(ASSET,0,[0,1],'y',512,'center',key);self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        before=h.snapshot();p.rotate_model_vertices_angle(ASSET,0,[0,1],'y',0,'center',sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)
        for angle in [True,-1,4096,512.5,None]:
            with self.assertRaises(ImportError):rotate_shape_vertices_angle(h.source,h.source,key,0,[0],'y',angle,'origin')
        with self.assertRaises(ImportError):rotate_shape_vertices_angle(h.source,h.source,'f'*64,0,[0],'y',512,'origin')
        for indices,axis,pivot in [([0,0],'y','origin'),([True],'y','origin'),([0],'w','origin'),([0],'y','mean')]:
            with self.assertRaises(ImportError):rotate_shape_vertices_angle(h.source,h.source,key,0,indices,axis,512,pivot)
        probe=json.loads(export_shape_json(h.source));probe['objects'][0]['vertices'][0]=[32767,0,32767];native=import_shape_json(h.source,key,json.dumps(probe).encode())[0]
        with self.assertRaises(ImportError):rotate_shape_vertices_angle(native,native,sha256(native).hexdigest(),0,[0],'y',512,'origin')

    def test_http_exact_source_review_scene_and_apply(self):
        h,p=self.fixture();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],axis='y',angle_units=512,pivot='center',expected_sha256=sha256(h.source).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            review=dict(asset_id=ASSET,object_index=0,operation='vertex_rotation_angle',values={k:body[k] for k in ('indices','axis','angle_units','pivot')},expected_sha256=body['expected_sha256'])
            status,report=post('/api/model-object-preview',review);self.assertEqual(status,200);self.assertEqual(report['values'],review['values']);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):
                self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for change in ({'extra':0},{'angle_units':True},{'angle_units':-1},{'angle_units':4096},{'angle_units':1.5},{'pivot':'mean'},{'indices':[0,0]},{'expected_sha256':'0'*64}):
                self.assertEqual(post('/api/model-vertices-angle',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-angle',body)[0],200)
