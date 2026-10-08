from copy import deepcopy
from hashlib import sha256
import struct,unittest
from unittest.mock import patch
from importer.model_vertex_sequence import transform_shape_vertices_sequence
from importer.core import ImportError
from sdk.scene_preview import source_key
from test_model_primitive_workflow import ModelPrimitiveProjectWorkflow,ASSET,http_server

STEPS=[dict(operation='scaling',values=dict(percent=150,pivot='origin')),
       dict(operation='rotation',values=dict(axis='y',quarter_turns=1,pivot='origin')),
       dict(operation='translation',values=dict(offset=[5,0,7]))]

class VertexSequenceTests(unittest.TestCase):
 def fixture(self):
  h=ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
 def test_literal_composition_one_history_step_and_noop(self):
  h,p=self.fixture();key=sha256(h.source).hexdigest();before=h.snapshot();steps=deepcopy(STEPS)
  expected=bytearray(h.source);offset=12+struct.unpack_from('<I',h.source,12)[0];struct.pack_into('<hhh',expected,offset,5,0,7);struct.pack_into('<hhh',expected,offset+8,5,0,-8)
  candidate,report=p._prepare_model_object(ASSET,0,'vertex_sequence',dict(indices=[0,1],steps=steps),key)
  self.assertEqual(candidate,bytes(expected));self.assertEqual(report['values'],dict(indices=[0,1],steps=steps));self.assertEqual(steps,STEPS);self.assertEqual(h.snapshot(),before)
  depth=len(p.undo_stack);p.transform_model_vertices_sequence(ASSET,0,[0,1],steps,key);self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(h.effective(),bytes(expected));p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),bytes(expected))
  unchanged=h.snapshot();p.transform_model_vertices_sequence(ASSET,0,[0,1],[dict(operation='translation',values=dict(offset=[1,0,0])),dict(operation='translation',values=dict(offset=[-1,0,0]))],sha256(expected).hexdigest());self.assertEqual(h.snapshot(),unchanged)
 def test_atomic_invalid_late_step_bounds_shapes_and_stale_sources(self):
  h,p=self.fixture();key=sha256(h.source).hexdigest();before=h.snapshot()
  bad=[None,[],STEPS*6,[dict(operation='unknown',values={})],[dict(operation='scaling',values=dict(percent=150,pivot='origin',extra=0))],STEPS+[dict(operation='scaling',values=dict(percent=0,pivot='origin'))],STEPS+[dict(operation='translation',values=dict(offset=[32767,0,0]))]]
  for steps in bad:
   with self.assertRaises(ImportError):p.transform_model_vertices_sequence(ASSET,0,[0,1],steps,key)
   self.assertEqual(h.snapshot(),before)
  with self.assertRaises(ImportError):transform_shape_vertices_sequence(h.source,h.source,'0'*64,0,[0,1],STEPS)
  with self.assertRaises(ImportError):p.transform_model_vertices_sequence(ASSET,0,[True],STEPS,key)
  self.assertEqual(h.snapshot(),before)
 def test_http_review_and_apply_exact_fields(self):
  h,p=self.fixture();key=sha256(h.source).hexdigest();before=h.snapshot();body=dict(asset_id=ASSET,object_index=0,indices=[0,1],steps=deepcopy(STEPS),expected_sha256=key)
  with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
   request=dict(asset_id=ASSET,object_index=0,operation='vertex_sequence',values=dict(indices=[0,1],steps=deepcopy(STEPS)),expected_sha256=key)
   status,report=post('/api/model-object-preview',request);self.assertEqual(status,200);self.assertEqual(report['values'],request['values']);self.assertEqual(h.snapshot(),before)
   with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(request,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
   for change in [dict(extra=0),dict(steps=[]),dict(indices=[0,0]),dict(expected_sha256='0'*64)]:self.assertEqual(post('/api/model-vertices-sequence',{**body,**change})[0],400);self.assertEqual(h.snapshot(),before)
   with patch.object(server,'state',return_value=dict(applied=True)):self.assertEqual(post('/api/model-vertices-sequence',body)[0],200)
 def test_retained_allocations_keep_ownership(self):
  from test_model_vector_allocation_project import VectorAllocationProjectTests
  from sdk import model_vector_allocation
  h=VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture();source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
  p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256']);current=model_vector_allocation.source(p,asset,'a'*64)
  p.transform_model_vertices_sequence(asset,0,[0,source['objects'][0]['vertex_count']],STEPS,current['effective_sha256']);after=model_vector_allocation.source(p,asset,'a'*64)
  self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview'])
  p.undo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],current['effective_sha256']);p.redo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],after['effective_sha256'])

if __name__=='__main__':unittest.main()
