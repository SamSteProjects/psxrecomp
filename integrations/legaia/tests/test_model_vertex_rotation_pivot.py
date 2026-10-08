from hashlib import sha256
import struct,unittest
from importer.model_json import rotate_shape_vertices,rotate_shape_vertices_angle
from importer.core import ImportError
from test_model_primitive_workflow import ModelPrimitiveProjectWorkflow,ASSET

class ExplicitRotationPivotTests(unittest.TestCase):
 def fixture(self):
  h=ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
 def test_literal_quarter_and_custom_words_history_and_unchanged_bytes(self):
  h,p=self.fixture();key=sha256(h.source).hexdigest();offset=12+struct.unpack_from('<I',h.source,12)[0];pivot=[10,-20,30]
  quarter=bytearray(h.source);struct.pack_into('<hhh',quarter,offset,-20,0,40);struct.pack_into('<hhh',quarter,offset+8,-20,0,30)
  custom=bytearray(h.source);struct.pack_into('<hhh',custom,offset,-18,0,16);struct.pack_into('<hhh',custom,offset+8,-11,0,9)
  before=h.snapshot();self.assertEqual(rotate_shape_vertices(h.source,h.source,key,0,[0,1],'y',1,pivot),bytes(quarter));self.assertEqual(rotate_shape_vertices_angle(h.source,h.source,key,0,[0,1],'y',512,pivot),bytes(custom));self.assertEqual(h.snapshot(),before)
  for axis in ['x','y','z']:
   for turn,angle in [(-1,3072),(1,1024),(2,2048)]:self.assertEqual(rotate_shape_vertices(h.source,h.source,key,0,[0,1],axis,turn,pivot),rotate_shape_vertices_angle(h.source,h.source,key,0,[0,1],axis,angle,pivot))
  values=dict(indices=[0,1],axis='y',angle_units=512,pivot=pivot)
  candidate,report=p._prepare_model_object(ASSET,0,'vertex_rotation_angle',values,key);self.assertEqual(candidate,bytes(custom));self.assertEqual(report['values'],values)
  p.rotate_model_vertices_angle(ASSET,0,[0,1],'y',512,pivot,key);self.assertEqual(h.effective(),bytes(custom));p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),bytes(custom))
  before=h.snapshot();p.rotate_model_vertices_angle(ASSET,0,[0,1],'y',0,[-32768,32767,0],sha256(custom).hexdigest());self.assertEqual(h.snapshot(),before)
 def test_malformed_pivots_and_overflow_refuse_without_mutation(self):
  h,p=self.fixture();key=sha256(h.source).hexdigest();before=h.snapshot()
  for pivot in [None,[],[0],[0,0],[0,0,0,0],[True,0,0],[0.5,0,0],['0',0,0],[32768,0,0],[-32769,0,0]]:
   for rotate in [lambda:rotate_shape_vertices(h.source,h.source,key,0,[0,1],'y',1,pivot),lambda:rotate_shape_vertices_angle(h.source,h.source,key,0,[0,1],'y',512,pivot)]:
    with self.assertRaises(ImportError):rotate()
    self.assertEqual(h.snapshot(),before)
  with self.assertRaises(ImportError):rotate_shape_vertices(h.source,h.source,key,0,[0,1],'y',2,[32767,0,0])
  with self.assertRaises(ImportError):rotate_shape_vertices_angle(h.source,h.source,key,0,[0,1],'y',2048,[32767,0,0])
  self.assertEqual(h.snapshot(),before)

 def test_explicit_pivot_retains_allocated_row_ownership(self):
  from test_model_vector_allocation_project import VectorAllocationProjectTests
  from sdk import model_vector_allocation
  h=VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture()
  source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();report=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
  p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,report['proposed_sha256']);current=model_vector_allocation.source(p,asset,'a'*64)
  p.rotate_model_vertices_angle(asset,0,[0,source['objects'][0]['vertex_count']],'y',512,[10,-20,30],current['effective_sha256']);after=model_vector_allocation.source(p,asset,'a'*64)
  self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview'])
  p.undo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],current['effective_sha256']);p.redo();self.assertEqual(model_vector_allocation.source(p,asset,'a'*64)['effective_sha256'],after['effective_sha256'])

if __name__=='__main__':unittest.main()
