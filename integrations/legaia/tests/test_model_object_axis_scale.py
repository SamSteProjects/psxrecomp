from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_json import export_shape_json,import_shape_json,scale_shape_object
from importer.model_object_axis_scale import scale_object_axes,scale_normal_axes
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_model_normal_rotation as normal_tests
from test_model_rotation import ModelRotationTests
from test_model_primitive_workflow import ASSET,http_server

class ObjectAxisScaleTests(unittest.TestCase):
    def test_literal_words_uniform_parity_owned_bytes(self):
        self.assertEqual(scale_normal_axes([1000,1000,0],[200,100,100]),[632,1265,0])
        self.assertEqual(scale_normal_axes([0,0,0],[1,1000,100]),[0,0,0])
        self.assertEqual(scale_normal_axes([-123,45,67],[175]*3),[-123,45,67])
        source=ModelRotationTests().source();key=sha256(source).hexdigest()
        for percent in [50,100,150]:self.assertEqual(scale_object_axes(source,source,key,0,[percent]*3,'origin'),scale_shape_object(source,source,key,0,percent))
        doc=json.loads(export_shape_json(source));obj=doc['objects'][0];obj['vertices']=[[0,0,0],[1,0,0],[0,1,0],[0,0,0]];obj['normals']=[[1000,1000,0]];source=import_shape_json(source,key,json.dumps(doc).encode())[0];key=sha256(source).hexdigest()
        scaled=scale_object_axes(source,source,key,0,[200,100,100],'center');obj=json.loads(export_shape_json(scaled))['objects'][0]
        self.assertEqual(obj['vertices'],[[-1,0,0],[2,0,0],[-1,1,0],[-1,0,0]]);self.assertEqual(obj['normals'],[[632,1265,0]])
        vo,vc,no,nc=struct.unpack_from('<4I',source,12);allowed={12+off+i*8+a for off,count in [(vo,vc),(no,nc)] for i in range(count) for a in range(6)}
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(source,scaled)) if a!=b));self.assertEqual(len(source),len(scaled))

    def test_empty_normals_invalid_and_normal_vertex_overflow(self):
        from test_importer_assets import model
        source=model(0x21);key=sha256(source).hexdigest();scale_object_axes(source,source,key,0,[110,100,100],'origin')
        for percents,pivot,obj,hash in [([True,100,100],'origin',0,key),([0,100,100],'origin',0,key),([1001,100,100],'origin',0,key),([100,100],'origin',0,key),([100,100,100],'bad',0,key),([100]*3,'origin',True,key),([100]*3,'origin',0,'0'*64)]:
            with self.assertRaises(ImportError):scale_object_axes(source,source,hash,obj,percents,pivot)
        source=ModelRotationTests().source();key=sha256(source).hexdigest();doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[32767]*3;source=import_shape_json(source,key,json.dumps(doc).encode())[0];key=sha256(source).hexdigest()
        with self.assertRaisesRegex(ImportError,'signed16'):scale_object_axes(source,source,key,0,[1,1000,1000],'origin')
        doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[0]*3;doc['objects'][0]['vertices'][0]=[32767,0,0];source=import_shape_json(source,key,json.dumps(doc).encode())[0]
        with self.assertRaisesRegex(ImportError,'signed16'):scale_object_axes(source,source,sha256(source).hexdigest(),0,[200,100,100],'origin')

    def test_review_receipt_atomic_history_noop(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);before=h.snapshot();key=sha256(h.source).hexdigest();values=dict(percents=[150,75,125],pivot='center');candidate,report=p._prepare_model_object(ASSET,0,'object_axis_scaling',values,key)
        self.assertEqual(report['values'],values);self.assertEqual(report['object_axis_scale_words']['proposed'],{k:json.loads(export_shape_json(candidate))['objects'][0][k] for k in ('vertices','normals')});self.assertEqual(h.snapshot(),before)
        with self.assertRaises(ProjectError):p.scale_model_object_axes(ASSET,0,values['percents'],'center',key,'0'*64)
        self.assertEqual(h.snapshot(),before);p.scale_model_object_axes(ASSET,0,values['percents'],'center',key,sha256(candidate).hexdigest());self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        before=h.snapshot();p.scale_model_object_axes(ASSET,0,[100]*3,'center',sha256(candidate).hexdigest(),sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)

    def test_http_static_exact_fields_scene_readonly(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);key=sha256(h.source).hexdigest();values=dict(percents=[150,75,125],pivot='center');candidate,report=p._prepare_model_object(ASSET,0,'object_axis_scaling',values,key);body=dict(asset_id=ASSET,object_index=0,**values,expected_sha256=key,proposed_sha256=sha256(candidate).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kw:prepared):
            from urllib.request import urlopen
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-object-axis-scale.js') as module:self.assertEqual(module.status,200)
            review=dict(asset_id=ASSET,object_index=0,operation='object_axis_scaling',values=values,expected_sha256=key);self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for changes in ({'extra':0},{'pivot':'bad'},{'percents':[True,100,100]},{'expected_sha256':'0'*64},{'proposed_sha256':'0'*64}):self.assertEqual(post('/api/model-object-axis-scale',dict(body,**changes))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-object-axis-scale',body)[0],200)

if __name__=='__main__':unittest.main()
