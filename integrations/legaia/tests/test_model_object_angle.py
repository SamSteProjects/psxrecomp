from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_json import export_shape_json,import_shape_json,rotate_shape_object
from importer.model_object_angle import rotate_object_angle
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_model_normal_rotation as normal_tests
import test_model_rotation as rotation_tests
from test_model_primitive_workflow import ASSET,http_server

class ObjectAngleTests(unittest.TestCase):
    def test_cardinal_parity_center_custom_and_owned_bytes(self):
        source=rotation_tests.ModelRotationTests().source();key=sha256(source).hexdigest()
        for axis in ('x','y','z'):
            for turn,angle in [(-1,3072),(1,1024),(2,2048)]:
                self.assertEqual(rotate_object_angle(source,source,key,0,axis,angle,'origin'),rotate_shape_object(source,source,key,0,axis,turn))
        doc=json.loads(export_shape_json(source));doc['objects'][0]['vertices']=[[0,0,0],[1,0,0],[0,1,0],[0,0,0]];doc['objects'][0]['normals'][0]=[1000,0,0];source=import_shape_json(source,key,json.dumps(doc).encode())[0];key=sha256(source).hexdigest()
        candidate=rotate_object_angle(source,source,key,0,'z',1024,'center');after=json.loads(export_shape_json(candidate))['objects'][0]
        self.assertEqual(after['vertices'],[[1,0,0],[1,1,0],[0,0,0],[1,0,0]]);self.assertEqual(after['normals'],[[0,1000,0]])
        angled=rotate_object_angle(source,source,key,0,'y',512,'origin');self.assertEqual(json.loads(export_shape_json(angled))['objects'][0]['normals'],[[707,0,-707]])
        vo,vc,no,nc=struct.unpack_from('<4I',source,12);allowed={12+off+i*8+a for off,count in [(vo,vc),(no,nc)] for i in range(count) for a in range(6)}
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(source,angled)) if a!=b));self.assertEqual(len(source),len(angled));self.assertEqual(rotate_object_angle(source,source,key,0,'z',0,'center'),source)

    def test_empty_normals_and_overflow_rejection(self):
        from test_importer_assets import model
        source=model(0x21);key=sha256(source).hexdigest();self.assertEqual(rotate_object_angle(source,source,key,0,'y',1024,'origin'),rotate_shape_object(source,source,key,0,'y',1))
        source=rotation_tests.ModelRotationTests().source();doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[-32768,0,0];source=import_shape_json(source,sha256(source).hexdigest(),json.dumps(doc).encode())[0];key=sha256(source).hexdigest()
        with self.assertRaisesRegex(ImportError,'signed16'):rotate_object_angle(source,source,key,0,'y',2048,'center')
        for obj,axis,angle,pivot,hash in [(True,'y',512,'origin',key),(0,'bad',512,'origin',key),(0,'y',True,'origin',key),(0,'y',4096,'origin',key),(0,'y',512,'bad',key),(0,'y',512,'origin','0'*64)]:
            with self.assertRaises(ImportError):rotate_object_angle(source,source,hash,obj,axis,angle,pivot)

    def test_review_receipt_atomic_history_noop(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);before=h.snapshot();key=sha256(h.source).hexdigest();values=dict(axis='y',angle_units=512,pivot='center');candidate,report=p._prepare_model_object(ASSET,0,'object_rotation_angle',values,key)
        self.assertEqual(report['values'],values);self.assertEqual(report['object_rotation_words']['proposed'],{k:json.loads(export_shape_json(candidate))['objects'][0][k] for k in ('vertices','normals')});self.assertEqual(h.snapshot(),before)
        with self.assertRaises(ProjectError):p.rotate_model_object_angle(ASSET,0,'y',512,'center',key,'0'*64)
        self.assertEqual(h.snapshot(),before);p.rotate_model_object_angle(ASSET,0,'y',512,'center',key,sha256(candidate).hexdigest());self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        before=h.snapshot();p.rotate_model_object_angle(ASSET,0,'y',0,'center',sha256(candidate).hexdigest(),sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),before)
        with self.assertRaises((ProjectError,ImportError)):p.rotate_model_object_angle(ASSET,0,'y',512,'center',key,sha256(candidate).hexdigest())
        self.assertEqual(h.snapshot(),before)

    def test_http_static_exact_fields_scene_readonly(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);key=sha256(h.source).hexdigest();values=dict(axis='y',angle_units=512,pivot='origin');candidate,report=p._prepare_model_object(ASSET,0,'object_rotation_angle',values,key);body=dict(asset_id=ASSET,object_index=0,**values,expected_sha256=key,proposed_sha256=sha256(candidate).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kw:prepared):
            from urllib.request import urlopen
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-object-angle.js') as module:self.assertEqual(module.status,200);self.assertIn(b'export function rotateObjectWords',module.read())
            review=dict(asset_id=ASSET,object_index=0,operation='object_rotation_angle',values=values,expected_sha256=key);self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for changes in ({'extra':0},{'pivot':'bad'},{'angle_units':True},{'expected_sha256':'0'*64},{'proposed_sha256':'0'*64}):self.assertEqual(post('/api/model-object-angle',dict(body,**changes))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-object-angle',body)[0],200)

if __name__=='__main__':unittest.main()
