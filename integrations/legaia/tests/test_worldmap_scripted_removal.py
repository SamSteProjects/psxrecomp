"""Literal leaf/cascade deletion, separate anchors and last-ledger history."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_binding import compose,COMPONENT,owner
from sdk.worldmap_scripted_placement_allocation import review as create,source
from sdk.worldmap_scripted_placement_remove import review,removal_ids
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedRemovalTests(TestCase):
 def test_transitive_branching_donors_keep_unrelated_siblings(self):
  def r(id,donor,target):return dict(placement_id=id,donor_cell=donor,target_cell=target)
  binding=dict(operations=[dict(requests=[r('a',100,200),r('b',100,201)]),dict(requests=[r('c',200,300),r('d',201,301)]),dict(requests=[r('e',300,400),r('f',300,401)])])
  held=deepcopy(binding)
  self.assertEqual(removal_ids(binding,'a'),['a','c','e','f']);self.assertEqual(removal_ids(binding,'b'),['b','d']);self.assertEqual(removal_ids(binding,'e'),['e'])
  self.assertEqual(binding,held)
  with self.assertRaises(ProjectError):removal_ids(binding,'missing')

 def test_removing_same_operation_sibling_compacts_only_its_bind_row(self):
  raw,fallback,man,floor,requests=fixture();sibling=deepcopy(requests[0]);sibling.update(placement_id='placement://authored/66666666-6666-4666-8666-666666666666',target_cell=201,record_index=5)
  requests.append(sibling)
  provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
  def inputs(project,scene,key,include_scripted=True):
   current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
   return raw,provenance,floor,current,[],fallback,man,man,{},[]
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
   with patch('sdk.worldmap_scripted_placement_allocation._inputs',side_effect=inputs),patch('sdk.worldmap_scripted_placement_remove._inputs',side_effect=inputs):
    key=state_key(p);r=create(p,'map01',key,requests);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=requests,review_key=r['review_key']))
    before=b64decode(source(p,'map01',state_key(p))['current_map_base64']);table=p.overrides[owner('map01')][COMPONENT]['operations'][0]['relocation_offset']
    removed=review(p,'map01',state_key(p),requests[0]['placement_id'],False);expected=bytearray(before)
    expected[4*32:5*32]=raw[4*32:5*32];expected[0x8000+400:0x8002+400]=raw[0x8000+400:0x8002+400]
    at=0x10000+table;expected[at+4:at+8]=before[at+8:at+12];expected[at+8:at+12]=raw[at+8:at+12];struct.pack_into('<h',expected,0x10008,2)
    self.assertEqual(b64decode(removed['proposed_map_base64']),bytes(expected));self.assertEqual(expected[5*32:6*32],before[5*32:6*32]);self.assertEqual(removed['audit']['authored_scripted_placements'][0]['placement_id'],sibling['placement_id'])

 def test_literal_leaf_cascade_and_last_ledger_history(self):
  for dc in (0,1):
   with self.subTest(dc=dc),tempfile.TemporaryDirectory() as root:
    raw,fallback,man,floor,requests=fixture(dc);terrain=bytearray(raw)
    for cell in (202,203):struct.pack_into('<H',terrain,0x8000+cell*2,0x3000|10)
    raw=bytes(terrain)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
    def inputs(project,scene,key,include_scripted=True):
     current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
     return raw,provenance,floor,current,[],fallback,man,man,{},[]
    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
    child='placement://authored/66666666-6666-4666-8666-666666666666'
    with patch('sdk.worldmap_scripted_placement_allocation._inputs',side_effect=inputs),patch('sdk.worldmap_scripted_placement_remove._inputs',side_effect=inputs):
     for rows in (requests,[{**deepcopy(requests[0]),'placement_id':child,'donor_cell':200,'target_cell':202,'record_index':5}]):
      key=state_key(p);r=create(p,'map01',key,rows);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=rows,review_key=r['review_key']))
     before=b64decode(source(p,'map01',state_key(p))['current_map_base64']);held=deepcopy((p._document(),p.undo_stack));identifier=requests[0]['placement_id'];key=state_key(p)
     with self.assertRaisesRegex(ProjectError,'dependent placements'):review(p,'map01',key,identifier,False)
     for cascade in (None,0,1,'yes'):
      with self.assertRaises(ProjectError):review(p,'map01',key,child,cascade)
     leaf=review(p,'map01',key,child,False);expected=bytearray(before)
     expected[5*32:6*32]=raw[5*32:6*32]
     for cell in (202,202+dc):expected[0x8000+cell*2:0x8002+cell*2]=raw[0x8000+cell*2:0x8002+cell*2]
     operations=p.overrides[owner('map01')][COMPONENT]['operations'];last=operations[1]['relocation_offset'];expected[0x10000+last:0x10000+last+12]=raw[0x10000+last:0x10000+last+12]
     struct.pack_into('<2h',expected,0x10006,operations[0]['relocation_offset'],2)
     self.assertEqual(b64decode(leaf['proposed_map_base64']),bytes(expected));self.assertEqual(leaf['audit']['removed_placement_ids'],[child]);self.assertEqual(len(leaf['binding']['operations']),1)
     cascade=review(p,'map01',key,identifier,True);self.assertIsNone(cascade['binding']);self.assertEqual(b64decode(cascade['proposed_map_base64']),raw);self.assertEqual(cascade['audit']['removed_placement_ids'],[identifier,child])
     self.assertEqual((p._document(),p.undo_stack),held)
     for r in (leaf,cascade):
      command=dict(type='remove_worldmap_scripted_placement',scene='map01',source_key=state_key(p),placement_id=r['placement_id'],cascade=r['cascade'],review_key=r['review_key'])
      with http_server(p) as (_,post):
       self.assertEqual(post('/api/worldmap-scripted-removal-review',dict(scene='map01',source_key=state_key(p),placement_id=r['placement_id'],cascade=r['cascade'])),(200,r))
       self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400);self.assertEqual(post('/api/command',command)[0],200)
       self.assertEqual(post('/api/command',command)[0],400)
      self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),b64decode(r['proposed_map_base64']))
      p.save();reopened=ProjectService.open(Path(root));self.assertEqual(reopened._document(),p._document())
      p.undo();self.assertEqual(p._document(),held[0]);p.redo();self.assertEqual(p._document(),reopened._document());p.undo();self.assertEqual(p._document(),held[0])
     self.assertEqual((p._document(),p.undo_stack),held)
