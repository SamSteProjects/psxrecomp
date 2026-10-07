from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_json import export_shape_json,import_shape_json,scale_shape_object
from importer.model_object_mirror import mirror_object
from sdk.project import ProjectError
from sdk.scene_preview import source_key
import test_model_normal_rotation as normal_tests
from test_model_rotation import ModelRotationTests
from test_model_primitive_workflow import ASSET,http_server

class ObjectMirrorTests(unittest.TestCase):
    def test_24_packet_families_literal_native_corners_and_involution(self):
        from test_model_primitives import synthetic
        from test_model_glb_reflection import mirrored_native
        for flags in range(0x10,0x28):
            source=synthetic(((flags,),));key=sha256(source).hexdigest()
            for axis in ('x','y','z'):
                a='xyz'.index(axis);scales=[1,1,1];scales[a]=-1;expected=bytearray(mirrored_native(source,scales))
                vo,vc,no,nc=struct.unpack_from('<4I',source,12)
                for start,count in [(12+vo,vc),(12+no,nc)]:
                    for i in range(count):struct.pack_into('<h',expected,start+i*8+a*2,-struct.unpack_from('<h',source,start+i*8+a*2)[0])
                candidate=mirror_object(source,source,key,0,axis,'origin');self.assertEqual(candidate,bytes(expected));self.assertEqual(mirror_object(source,candidate,sha256(candidate).hexdigest(),0,axis,'origin'),source)
            obj=json.loads(export_shape_json(source))['objects'][0];center=min(v[0] for v in obj['vertices'])+max(v[0] for v in obj['vertices']);candidate=mirror_object(source,source,key,0,'x','center');after=json.loads(export_shape_json(candidate))['objects'][0];self.assertEqual(after['vertices'],[[center-v[0],v[1],v[2]] for v in obj['vertices']]);self.assertEqual(mirror_object(source,candidate,sha256(candidate).hexdigest(),0,'x','center'),source)

    def test_invalid_and_signed16_atomic_overflow(self):
        source=ModelRotationTests().source();key=sha256(source).hexdigest()
        for axis,pivot,obj,hash in [('bad','origin',0,key),('x','bad',0,key),('x','origin',True,key),('x','origin',0,'0'*64)]:
            with self.assertRaises(ImportError):mirror_object(source,source,hash,obj,axis,pivot)
        doc=json.loads(export_shape_json(source));doc['objects'][0]['normals'][0]=[-32768,0,0];source=import_shape_json(source,key,json.dumps(doc).encode())[0]
        with self.assertRaisesRegex(ImportError,'signed16'):mirror_object(source,source,sha256(source).hexdigest(),0,'x','center')
    def test_review_receipt_atomic_history_noop(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);before=h.snapshot();key=sha256(h.source).hexdigest();values=dict(axis='x',pivot='center');candidate,report=p._prepare_model_object(ASSET,0,'object_mirror',values,key)
        self.assertEqual(report['values'],values);self.assertEqual(report['object_mirror_words']['proposed'],{k:json.loads(export_shape_json(candidate))['objects'][0][k] for k in ('vertices','normals')});self.assertEqual(h.snapshot(),before)
        with self.assertRaises(ProjectError):p.mirror_model_object(ASSET,0,values['axis'],'center',key,'0'*64)
        self.assertEqual(h.snapshot(),before);p.mirror_model_object(ASSET,0,values['axis'],'center',key,sha256(candidate).hexdigest());self.assertEqual(h.effective(),candidate);p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        p.mirror_model_object(ASSET,0,'x','center',sha256(candidate).hexdigest(),sha256(h.source).hexdigest());self.assertEqual(h.effective(),h.source)

    def test_http_static_exact_fields_scene_readonly(self):
        h,p=normal_tests.ObjectNormalAngles.fixture(self);key=sha256(h.source).hexdigest();values=dict(axis='x',pivot='center');candidate,report=p._prepare_model_object(ASSET,0,'object_mirror',values,key);body=dict(asset_id=ASSET,object_index=0,**values,expected_sha256=key,proposed_sha256=sha256(candidate).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kw:prepared):
            from urllib.request import urlopen
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-object-mirror.js') as module:self.assertEqual(module.status,200)
            review=dict(asset_id=ASSET,object_index=0,operation='object_mirror',values=values,expected_sha256=key);self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for changes in ({'extra':0},{'pivot':'bad'},{'axis':'bad'},{'expected_sha256':'0'*64},{'proposed_sha256':'0'*64}):self.assertEqual(post('/api/model-object-mirror',dict(body,**changes))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-object-mirror',body)[0],200)

if __name__=='__main__':unittest.main()
