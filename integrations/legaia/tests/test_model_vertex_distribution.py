from copy import deepcopy
from hashlib import sha256
import json,unittest
from unittest.mock import patch
from importer.model_json import export_shape_json,import_shape_json,distribute_shape_vertices
from importer.core import ImportError
from sdk.scene_preview import source_key
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET,http_server

class VertexDistributionTests(unittest.TestCase):
 def fixture(self):
  h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
 def test_signed_extents_ties_selection_and_opaque_words(self):
  h,p=self.fixture()
  for coords in ([-5,-4,4],[-32768,-32767,32767],[-4,-4,4],[7,7,7]):
   doc=json.loads(export_shape_json(h.source))
   for i,x in enumerate(coords):doc['objects'][0]['vertices'][i][0]=x
   current=import_shape_json(h.source,sha256(h.source).hexdigest(),json.dumps(doc).encode())[0];key=sha256(current).hexdigest()
   result=distribute_shape_vertices(h.source,current,key,0,[2,0,1],'x');expected=deepcopy(doc);expected['source_sha256']=key;ordered=sorted(range(3),key=lambda i:(coords[i],i));low=coords[ordered[0]];span=coords[ordered[-1]]-low
   for rank,i in enumerate(ordered):expected['objects'][0]['vertices'][i][0]=low+(2*span*rank+2)//4
   self.assertEqual(result,import_shape_json(current,key,json.dumps(expected).encode())[0]);self.assertEqual(distribute_shape_vertices(h.source,current,key,0,[0,1,2],'x'),result)
   self.assertEqual(distribute_shape_vertices(h.source,current,key,0,[0,2],'x'),current)
   for indices,axis in [([0],'x'),([0,0],'x'),([True,1],'x'),([0,999],'x'),([0,1],'w')]:
    with self.assertRaises(ImportError):distribute_shape_vertices(h.source,current,key,0,indices,axis)
   with self.assertRaises(ImportError):distribute_shape_vertices(h.source,current,'0'*64,0,[0,1,2],'x')
 def test_history_and_exact_http_scene_review(self):
  h,p=self.fixture();before=h.snapshot();key=sha256(h.source).hexdigest();values=dict(indices=[0,1,2],axis='y');body=dict(asset_id=ASSET,object_index=0,**values,expected_sha256=key)
  with http_server(p) as (server,post),patch.object(server,'model_preview',side_effect=lambda asset,prepared=None,**kwargs:prepared):
   review=dict(asset_id=ASSET,object_index=0,operation='vertex_distribution',values=values,expected_sha256=key)
   code,r=post('/api/model-object-preview',review);self.assertEqual(code,200,r);self.assertEqual(r['values'],values);self.assertEqual(r['operation'],'vertex_distribution');self.assertEqual(h.snapshot(),before)
   with patch.object(server,'scene_shape_proposal',side_effect=lambda asset,entity,candidate,report,key,all_instances:report):self.assertEqual(post('/api/model-object-scene-preview',dict(review,entity_id='scene://fixture/actors/man-p1/0001',source_key=source_key(p)))[0],200)
   for change in ({'extra':0},{'indices':[0]},{'indices':[0,0]},{'axis':'w'},{'expected_sha256':'0'*64}):self.assertEqual(post('/api/model-vertices-distribution',dict(body,**change))[0],400);self.assertEqual(h.snapshot(),before)
   with patch.object(server,'state',return_value={'applied':True}):self.assertEqual(post('/api/model-vertices-distribution',body)[0],200)
  content=h.effective();history=deepcopy((p.undo_stack,p.redo_stack));p.distribute_model_vertices(ASSET,0,[0,1,2],'y',sha256(content).hexdigest());self.assertEqual((p.undo_stack,p.redo_stack),history)
  if content!=h.source:p.undo();self.assertEqual(h.effective(),h.source);p.redo();self.assertEqual(h.effective(),content)

 def test_allocated_rows_preserve_vector_ownership(self):
  import test_model_vector_allocation_project as allocations
  from sdk import model_vector_allocation
  h=allocations.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture();source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();review=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64);p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,review['proposed_sha256'])
  current=model_vector_allocation.source(p,asset,'a'*64);count=source['objects'][0]['vertex_count'];before=p.read_model_replacement(asset,p.model_overrides[asset]);doc=json.loads(export_shape_json(before));indices=[0,1,count];rows=doc['objects'][0]['vertices'];ordered=sorted(indices,key=lambda i:(rows[i][0],i));low=rows[ordered[0]][0];span=rows[ordered[-1]][0]-low
  for rank,i in enumerate(ordered):rows[i][0]=low+(2*span*rank+2)//4
  expected=import_shape_json(before,current['effective_sha256'],json.dumps(doc).encode())[0];p.distribute_model_vertices(asset,0,indices,'x',current['effective_sha256']);self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),expected)
  after=model_vector_allocation.source(p,asset,'a'*64);self.assertEqual(after['allocated_vector_count'],current['allocated_vector_count']);self.assertEqual(after['objects'],current['objects']);self.assertEqual(after['retail_preview'],current['retail_preview'])

if __name__=='__main__':unittest.main()
