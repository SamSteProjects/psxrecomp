from hashlib import sha256
import json,struct,unittest
from unittest.mock import patch
from importer.core import ImportError
from importer.model_json import export_shape_json
from importer.model_normal_rebuild import rebuild_object_normals,rebuild_words
from importer.model_primitives import inspect_model_primitives
from sdk.project import ProjectError
from sdk.scene_preview import source_key
from test_model_primitives import synthetic
from test_model_primitive_workflow import ASSET,http_server
import test_model_primitive_workflow as fixtures


def source(flags=0x16):
    data=bytearray(synthetic(((flags,),(0x14,)),count=1))
    start=12+struct.unpack_from('<I',data,12)[0]
    for i,row in enumerate([(0,0,0),(10,0,0),(0,10,0),(10,10,0),(7,8,9)]):struct.pack_into('<hhh',data,start+i*8,*row)
    return bytes(data)


class NormalRebuildTests(unittest.TestCase):
    def test_literal_flat_gouraud_triangle_quad_and_complete_bytes(self):
        for flags,count in [(0x10,1),(0x12,1),(0x14,3),(0x16,4)]:
            original=source(flags);key=sha256(original).hexdigest();base=12+struct.unpack_from('<I',original,20)[0]
            for direction,sign in [('winding',1),('reverse',-1)]:
                expected=bytearray(original)
                for i in range(count):struct.pack_into('<hhh',expected,base+i*8,0,0,4096*sign)
                result=rebuild_object_normals(original,original,key,0,direction)
                self.assertEqual(result,bytes(expected));self.assertEqual(rebuild_object_normals(original,result,sha256(result).hexdigest(),0,direction),result)

    def test_area_weighting_shared_corner_dedup_and_exact_rounding(self):
        vertices=[[0,0,0],[2,0,0],[0,2,0],[0,0,1]]
        faces=[dict(corner_count=3,gouraud=True,vertices=[0,1,2],normal_indices=[0,0,0]),dict(corner_count=3,gouraud=False,vertices=[0,3,1],normal_indices=[0])]
        self.assertEqual(rebuild_words(vertices,[[1,2,3],[9,8,7]],faces,'winding'),[[0,1832,3664],[9,8,7]])
        self.assertEqual(rebuild_words(vertices,[[1,2,3]],faces,'reverse'),[[0,-1832,-3664]])

    def test_current_retargeted_sharing_and_malformed_reference(self):
        from importer.model_normal_retarget import retarget_object_normals
        original=source(0x10);key=sha256(original).hexdigest()
        current=retarget_object_normals(original,original,key,0,0,3)
        base=12+struct.unpack_from('<I',current,20)[0];expected=bytearray(current);struct.pack_into('<hhh',expected,base+3*8,0,0,4096)
        self.assertEqual(rebuild_object_normals(original,current,sha256(current).hexdigest(),0,'winding'),bytes(expected))
        face=inspect_model_primitives(original)['objects'][0]['primitives'][0];bad=bytearray(original);struct.pack_into('<H',bad,face['byte_offset']+12,7);bad=bytes(bad)
        with self.assertRaisesRegex(ImportError,'misaligned'):rebuild_object_normals(bad,bad,sha256(bad).hexdigest(),0,'winding')

    def test_degenerate_cancel_unlit_stale_and_invalid_atomic(self):
        original=source();key=sha256(original).hexdigest()
        for obj,direction,hash in [(True,'winding',key),(99,'winding',key),(0,'bad',key),(0,'winding','0'*64)]:
            with self.assertRaises(ImportError):rebuild_object_normals(original,original,hash,obj,direction)
        for flags in (0x20,0x24):
            data=source(flags)
            with self.assertRaisesRegex(ImportError,'lit face'):rebuild_object_normals(data,data,sha256(data).hexdigest(),0,'winding')
        data=synthetic(((0x14,),),count=1)
        with self.assertRaisesRegex(ImportError,'degenerate'):rebuild_object_normals(data,data,sha256(data).hexdigest(),0,'winding')
        face=dict(corner_count=3,gouraud=False,vertices=[0,1,2],normal_indices=[0])
        with self.assertRaisesRegex(ImportError,'cancelling'):rebuild_words([[0,0,0],[10,0,0],[0,10,0]],[[0,0,0]],[face,dict(face,vertices=[0,2,1])],'winding')

    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow()
        with patch.object(fixtures,'model',return_value=source()):h.setUp()
        self.addCleanup(h.doCleanups);return h,h.project

    def test_review_hash_history_noop_save_open(self):
        h,p=self.fixture();before=h.snapshot();key=sha256(h.source).hexdigest()
        candidate,report=p._prepare_model_object(ASSET,0,'normal_rebuild',dict(direction='winding'),key)
        self.assertEqual(h.snapshot(),before);self.assertEqual(report['normal_rebuild_words']['current'],json.loads(export_shape_json(h.source))['objects'][0]['normals'])
        self.assertTrue(all(row['kind']=='normal' and row['object_index']==0 for row in report['changes_from_current']))
        with self.assertRaises(ProjectError):p.rebuild_model_normals(ASSET,0,'winding',key,'0'*64)
        self.assertEqual(h.snapshot(),before);p.rebuild_model_normals(ASSET,0,'winding',key,sha256(candidate).hexdigest());self.assertEqual(h.effective(),candidate)
        p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),candidate)
        snapshot=h.snapshot();p.rebuild_model_normals(ASSET,0,'winding',sha256(candidate).hexdigest(),sha256(candidate).hexdigest());self.assertEqual(h.snapshot(),snapshot)
        from sdk.project import ProjectService
        opened=ProjectService.open(p.save());self.assertEqual(opened.read_model_replacement(ASSET,opened.model_overrides[ASSET]),candidate)

    def test_http_exact_fields_and_readonly_scene_preview(self):
        h,p=self.fixture();key=sha256(h.source).hexdigest();review=dict(asset_id=ASSET,object_index=0,operation='normal_rebuild',values=dict(direction='winding'),expected_sha256=key)
        candidate=p._prepare_model_object(ASSET,0,'normal_rebuild',review['values'],key)[0];body=dict(asset_id=ASSET,object_index=0,direction='winding',expected_sha256=key,proposed_sha256=sha256(candidate).hexdigest());before=h.snapshot()
        with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
            from urllib.request import urlopen
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-normal-rebuild.js') as response:self.assertIn(b'qualifyNormalRebuild',response.read())
            self.assertEqual(post('/api/model-object-preview',review)[0],200)
            with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
            self.assertEqual(h.snapshot(),before)
            for changes in ({'extra':0},{'direction':True},{'object_index':True},{'expected_sha256':'0'*64},{'proposed_sha256':'0'*64}):self.assertEqual(post('/api/model-object-normal-rebuild',dict(body,**changes))[0],400);self.assertEqual(h.snapshot(),before)
            with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-object-normal-rebuild',body)[0],200)
