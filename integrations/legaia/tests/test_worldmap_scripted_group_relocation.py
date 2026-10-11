"""Literal grouped cell motion, overlap, destination bytes and donor lineage."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct,tempfile
from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_binding import compose,owner,COMPONENT
from sdk.worldmap_scripted_placement_allocation import review as create,source
from sdk.worldmap_scripted_group_relocate import review
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server

class ScriptedGroupRelocationTests(TestCase):
 def test_overlap_literal_map_history_and_bounds(self):
  for dc in (0,1):
   with self.subTest(dc=dc),tempfile.TemporaryDirectory() as root,ExitStack() as stack:
    raw,fallback,man,floor,requests=fixture(dc);terrain=bytearray(raw)
    for cell in range(202,214):struct.pack_into('<H',terrain,32768+cell*2,0x3000|10)
    terrain[14*32+20:14*32+24]=bytes([11,12,13,14]);struct.pack_into('<H',terrain,32768+206*2,0x3000|14);raw=bytes(terrain)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
    def inputs(project,scene,key,include_scripted=True):
     current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
     return raw,provenance,floor,current,[],fallback,man,man,{},[]
    for module in ('sdk.worldmap_scripted_placement_allocation','sdk.worldmap_scripted_group_relocate','sdk.worldmap_scripted_placement_model'):stack.enter_context(patch(module+'._inputs',side_effect=inputs))
    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
    child='placement://authored/66666666-6666-4666-8666-666666666666';grand='placement://authored/77777777-7777-4777-8777-777777777777'
    for rows in (requests,[{**deepcopy(requests[0]),'placement_id':child,'donor_cell':200,'target_cell':202,'record_index':5}],[{**deepcopy(requests[0]),'placement_id':grand,'donor_cell':202,'target_cell':204,'record_index':6}]):
     key=state_key(p);r=create(p,'map01',key,rows);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=rows,review_key=r['review_key']))
    from sdk.worldmap_scripted_placement_model import review as assign
    geometry=dict(scene_graph=dict(assets=[dict(asset_id='asset://map01/worldmap/models/0002',preview=dict(vertices=[[0,0,0]],triangles=[[0,0,0]]),source_record=dict(fixture=True))]))
    with patch('sdk.worldmap_geometry.inspect',return_value=geometry):
     key=state_key(p);r=assign(p,'map01',key,[grand],2);p.command(dict(type='assign_worldmap_scripted_models',scene='map01',source_key=key,placement_ids=[grand],model_pool_index=2,review_key=r['review_key']))
    ids=sorted([child,grand]);key=state_key(p);src=source(p,'map01',key);before=b64decode(src['current_map_base64']);held=deepcopy((p._document(),p.undo_stack));delta=dict(col=2,row=0);r=review(p,'map01',key,ids,delta)
    upstream=review(p,'map01',key,sorted([requests[0]['placement_id'],child]),dict(col=8,row=0));self.assertEqual(b64decode(upstream['proposed_map_base64'])[192:224],before[192:224]);self.assertEqual(upstream['audit']['dependent_donor_placements'],[child,grand])
    expected=bytearray(before)
    for cell in {202,202+dc,204,204+dc}:expected[32768+2*cell:32770+2*cell]=raw[32768+2*cell:32770+2*cell]
    for cell,record,environment in ((204,5,10),(206,6,14)):
     struct.pack_into('<H',expected,32768+2*cell,(struct.unpack_from('<H',raw,32768+2*cell)[0]&~511)|record)
     expected[record*32+20:record*32+24]=raw[environment*32+20:environment*32+24]
    for cell in (204+dc,206+dc):struct.pack_into('<H',expected,32768+2*cell,struct.unpack_from('<H',expected,32768+2*cell)[0]|1024)
    for index,operation in enumerate(src['binding']['operations']):
     at=65536+operation['relocation_offset']
     if index>=1:expected[at+8:at+10]=bytes([(204+dc)%128,(204+dc)//128])
     if index>=2:expected[at+12:at+14]=bytes([(206+dc)%128,(206+dc)//128])
    self.assertEqual(b64decode(r['proposed_map_base64']),bytes(expected));self.assertEqual(expected[128:160],before[128:160]);self.assertEqual(struct.unpack_from('<H',expected,208)[0],2)
    self.assertEqual(r['audit']['dependent_donor_placements'],[grand]);self.assertEqual((p._document(),p.undo_stack),held)
    command=dict(type='relocate_worldmap_scripted_group',scene='map01',source_key=key,placement_ids=ids,delta=delta,review_key=r['review_key'])
    with http_server(p) as (_,post):
     self.assertEqual(post('/api/worldmap-scripted-group-relocation-review',{k:v for k,v in command.items() if k not in ('type','review_key')}),(200,r))
     proposal=dict(placement_ids=ids,delta=delta,review_key=r['review_key'])
     for malformed in ({**proposal,'placement_ids':ids[0]},{**proposal,'delta':dict(col=True,row=0)},{**proposal,'review_key':'0'*64},{**proposal,'target_cell':204}):
      self.assertEqual(post('/api/worldmap-scripted-placement-scene',dict(scene='map01',source_key=key,scripted_proposal=malformed))[0],400)
     self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400);self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(post('/api/command',command)[0],400)
    self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),bytes(expected));self.assertEqual(len(p.undo_stack),len(held[1])+1)
    p.save();saved=deepcopy(p._document());self.assertEqual(ProjectService.open(Path(root))._document(),saved);p.undo();self.assertEqual(p._document(),held[0]);p.redo();self.assertEqual(p._document(),saved)
    no=review(p,'map01',state_key(p),ids,dict(col=0,row=0));history=deepcopy(p.undo_stack);p.command({**command,'source_key':state_key(p),'delta':dict(col=0,row=0),'review_key':no['review_key']});self.assertEqual(p.undo_stack,history)
    for bad_ids,bad_delta in (([],delta),(ids[:1],delta),(ids[::-1],delta),(ids+[ids[0]],delta),(['missing',grand],delta),(ids,dict(col=True,row=0)),(ids,dict(col=128,row=0)),(ids,dict(col=0,row=-2)),(ids,dict(col=-4,row=0)),(ids,dict(col=0,row=0,extra=1))):
     with self.assertRaises(ProjectError):review(p,'map01',state_key(p),bad_ids,bad_delta)
    self.assertEqual((p._document(),p.undo_stack),(saved,history))
