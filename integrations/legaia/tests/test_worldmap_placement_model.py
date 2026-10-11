from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import base64,struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from importer.worldmap_placement_allocation import allocate
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation_binding import COMPONENT,SCHEMA,MODEL_SCHEMA,owner,validate,replay
from sdk.worldmap_placement_allocation import build,review as create_review
from sdk.worldmap_placement_model import review,reassigned_binding
from test_worldmap_placement_allocation import fixture,request
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationModelTests(TestCase):
 def test_literal_model_word_child_retention_v2_guards_and_persistence(self):
  original,floor=fixture();data=bytearray(original)
  for cell in (202,203,204):struct.pack_into('<H',data,0x8000+cell*2,0x3400|10)
  raw=bytes(data);first=request();second=request(5,201,2);second['donor_cell']=200
  third=request(6,202,3);third['donor_cell']=201
  provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
  current=raw;ops=[]
  for requests in ([first],[second],[third]):
   current,audit=allocate(current,floor,'map01',requests);ops.append(dict(requests=requests,proposed_map_sha256=audit['proposed_sha256']))
  binding=dict(schema_version=SCHEMA,**provenance,operations=ops)
  geometry=dict(scene_graph=dict(assets=[dict(asset_id=f'asset://map01/worldmap/models/{i:04d}',source_record=dict(slot=i),preview=dict(vertices=[[0,0,0]],triangles=[[0,0,0]])) for i in (1,2)]))
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
   p.overrides[owner('map01')]={COMPONENT:binding};held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
   context=(raw,provenance,{},48,floor,None,raw,[])
   with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_model.context',return_value=context),patch('sdk.worldmap_geometry.inspect',return_value=geometry):
    key=state_key(p);value=review(p,'map01',key,first['placement_id'],2);expected=bytearray(current);struct.pack_into('<H',expected,4*32+16,2)
    self.assertEqual(base64.b64decode(value['proposed_map_base64']),bytes(expected));self.assertEqual(value['binding']['schema_version'],MODEL_SCHEMA)
    self.assertEqual(value['binding']['operations'][1]['requests'][0]['model_pool_index'],1)
    self.assertNotIn('model_pool_index',value['binding']['operations'][2]['requests'][0])
    self.assertEqual(value['audit']['retained_child_models'],[dict(placement_id=second['placement_id'],model_pool_index=1)])
    self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
    for invalid in (0,512,True,2.0,511,1):
     with self.subTest(invalid=invalid),self.assertRaises(ProjectError):review(p,'map01',key,first['placement_id'],invalid)
    command=dict(type='assign_worldmap_authored_model',scene='map01',source_key=key,placement_id=first['placement_id'],model_pool_index=2,review_key=value['review_key'])
    with http_server(p) as (_,post):
     body={k:command[k] for k in ('scene','source_key','placement_id','model_pool_index')}
     self.assertEqual(post('/api/worldmap-decoration-model-review',body)[0],200)
     self.assertEqual(post('/api/worldmap-decoration-model-review',{**body,'extra':True})[0],400)
     self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
     self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(post('/api/command',command)[0],400)
    applied=deepcopy(p._document());p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
    overlays=[];build(p,overlays);self.assertEqual(overlays[0]['payload'],bytes(expected))
    # Creation after model assignment retains v2 and remains donor-derived.
    created=create_review(p,'map01',state_key(p),[request(7,203,4)])
    self.assertEqual(created['binding']['schema_version'],MODEL_SCHEMA)
    with self.assertRaises(ProjectError):create_review(p,'map01',state_key(p),[{**request(7,203,4),'model_pool_index':2}])
    bad=deepcopy(value['binding']);bad['schema_version']=SCHEMA
    with self.assertRaises(ProjectError):validate(p,owner('map01'),bad)
    with self.assertRaises(ProjectError):replay(raw,floor,bad)
    for invalid in (True,0,512):
     bad=deepcopy(value['binding']);bad['operations'][0]['requests'][0]['model_pool_index']=invalid
     with self.assertRaises(ProjectError):validate(p,owner('map01'),bad)
    # A structurally valid but unsupported model must still fail Build.
    _,allocations=replay(raw,floor,value['binding'])
    forged,_=reassigned_binding(raw,floor,value['binding'],allocations,first['placement_id'],511)
    p.overrides[owner('map01')]={COMPONENT:forged}
    with self.assertRaisesRegex(ProjectError,'drawable'):build(p,[])
    p.overrides[owner('map01')]={COMPONENT:deepcopy(value['binding'])}
    p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied);p.undo();self.assertEqual(p._document(),held)
