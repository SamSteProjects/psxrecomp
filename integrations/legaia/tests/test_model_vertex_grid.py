from hashlib import sha256
import json,unittest
from importer.model_json import export_shape_json,import_shape_json
from importer.model_vertex_grid import snap_shape_vertices
from importer.core import ImportError
from test_model_primitive_workflow import ModelPrimitiveProjectWorkflow,ASSET,http_server

class VertexGridTests(unittest.TestCase):
 def fixture(self):
  h=ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
 def test_signed_halfway_subset_preservation_and_atomic_overflow(self):
  h,p=self.fixture();doc=json.loads(export_shape_json(h.source));doc['objects'][0]['vertices'][0]=[-8,8,7];source=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(doc).encode())[0]
  candidate=snap_shape_vertices(source,source,sha256(source).hexdigest(),0,[0],['x','y'],16);after=json.loads(export_shape_json(candidate));self.assertEqual(after['objects'][0]['vertices'][0],[-16,16,7]);after['source_sha256']=doc['source_sha256'];doc['objects'][0]['vertices'][0]=[-16,16,7];self.assertEqual(after,doc)
  doc['objects'][0]['vertices'][0]=[32767,0,0];overflow=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(doc).encode())[0]
  with self.assertRaisesRegex(ImportError,'signed16'):snap_shape_vertices(overflow,overflow,sha256(overflow).hexdigest(),0,[0],['x'],16)
 def test_review_http_history_noop_and_stale(self):
  h,p=self.fixture();before=h.snapshot();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],axes=['x','y','z'],spacing=16,expected_sha256=sha256(h.source).hexdigest())
  with http_server(p) as (_,post):
   for bad in (dict(body,extra=1),dict(body,spacing=True),dict(body,spacing=0),dict(body,spacing=32769),dict(body,axes=[]),dict(body,axes=['x','x']),dict(body,indices=[0,0]),dict(body,expected_sha256='0'*64)):
    status,error=post('/api/model-vertices-grid',bad);self.assertEqual(status,400,error);self.assertEqual(h.snapshot(),before)
  candidate,report=p._prepare_model_object(ASSET,0,'vertex_grid',{k:body[k] for k in ('indices','axes','spacing')},body['expected_sha256']);self.assertEqual(report['values']['spacing'],16);self.assertEqual(h.snapshot(),before)
  p.snap_model_vertices(ASSET,0,body['indices'],body['axes'],16,body['expected_sha256']);after=h.snapshot();self.assertEqual(len(p.undo_stack),1);current=p.read_model_replacement(ASSET,p.model_overrides[ASSET]);self.assertEqual(current,candidate)
  p.snap_model_vertices(ASSET,0,body['indices'],body['axes'],16,sha256(current).hexdigest());self.assertEqual(h.snapshot(),after);p.undo();self.assertEqual(p.model_overrides,{});self.assertEqual(len(p.redo_stack),1);p.redo();self.assertEqual(h.snapshot(),after)

if __name__=='__main__':unittest.main()
