"""Literal grid/bind moves, dependent donor retention and atomic command history."""
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
from sdk.worldmap_scripted_placement_relocate import review
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedRelocationTests(TestCase):
 def test_literal_move_with_distinct_anchor_and_later_donor_descendant(self):
  for dc in (0,1):
   with self.subTest(dc=dc),tempfile.TemporaryDirectory() as root:
    raw,fallback,man,floor,requests=fixture(dc);terrain=bytearray(raw)
    for cell in (202,203,300,301):struct.pack_into('<H',terrain,0x8000+cell*2,0x3000|10)
    raw=bytes(terrain)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
    def inputs(project,scene,key,include_scripted=True):
     current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
     return raw,provenance,floor,current,[],fallback,man,man,{},[]
    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
    with patch('sdk.worldmap_scripted_placement_allocation._inputs',side_effect=inputs),patch('sdk.worldmap_scripted_placement_relocate._inputs',side_effect=inputs):
     for rows in (requests,[{**deepcopy(requests[0]),'placement_id':'placement://authored/66666666-6666-4666-8666-666666666666','donor_cell':200,'target_cell':202,'record_index':5}]):
      key=state_key(p);r=create(p,'map01',key,rows);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=rows,review_key=r['review_key']))
     before=b64decode(source(p,'map01',state_key(p))['current_map_base64']);held=deepcopy((p._document(),p.undo_stack));identifier=requests[0]['placement_id'];key=state_key(p)
     r=review(p,'map01',key,identifier,300)
     expected=bytearray(before)
     for cell in (200,200+dc):expected[0x8000+cell*2:0x8002+cell*2]=raw[0x8000+cell*2:0x8002+cell*2]
     word=struct.unpack_from('<H',raw,0x8000+300*2)[0];struct.pack_into('<H',expected,0x8000+300*2,(word&~511)|4)
     at=0x8000+(300+dc)*2;struct.pack_into('<H',expected,at,struct.unpack_from('<H',expected,at)[0]|0x400)
     destination=struct.unpack_from('<H',raw,0x8000+300*2)[0]&511;expected[4*32+20:4*32+24]=raw[destination*32+20:destination*32+24]
     # Original one-row primary table; our first UUID is row 1 in both copies.
     for operation in p.overrides[owner('map01')][COMPONENT]['operations']:
      table=operation['relocation_offset'];expected[0x10000+table+4:0x10000+table+6]=bytes(((300+dc)%128,(300+dc)//128))
     self.assertEqual(b64decode(r['proposed_map_base64']),bytes(expected));self.assertEqual(before[5*32:6*32],expected[5*32:6*32])
     self.assertEqual(r['audit']['dependent_donor_placements'],['placement://authored/66666666-6666-4666-8666-666666666666'])
     self.assertEqual((p._document(),p.undo_stack),held)
     command=dict(type='relocate_worldmap_scripted_placement',scene='map01',source_key=key,placement_id=identifier,target_cell=300,review_key=r['review_key'])
     with http_server(p) as (_,post):
      self.assertEqual(post('/api/worldmap-scripted-relocation-review',dict(scene='map01',source_key=key,placement_id=identifier,target_cell=300)),(200,r))
      self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
      self.assertEqual(post('/api/command',command)[0],200)
     self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),bytes(expected))
     p.undo();self.assertEqual(p._document(),held[0]);p.redo();p.save();p=ProjectService.open(Path(root))
     self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),bytes(expected))
     count=len(p.undo_stack);noop=review(p,'map01',state_key(p),identifier,300);p.command({**command,'source_key':state_key(p),'review_key':noop['review_key']});self.assertEqual(len(p.undo_stack),count)
     saved=deepcopy((p._document(),p.undo_stack))
     for cell in (True,-1,16384,100,202):
      with self.assertRaises(ProjectError):review(p,'map01',state_key(p),identifier,cell)
     self.assertEqual((p._document(),p.undo_stack),saved)
     def corrupt(*args,**kwargs):
      native,audit=allocate_scripted_placements(*args,**kwargs);altered=bytearray(native)
      if args[5][0]['record_index']==5:altered[0x4000+900]^=0x10
      return bytes(altered),audit
     with patch('sdk.worldmap_scripted_placement_relocate.allocate_scripted_placements',side_effect=corrupt),self.assertRaisesRegex(ProjectError,'unrelated bytes'):
      review(p,'map01',state_key(p),identifier,200)
     self.assertEqual((p._document(),p.undo_stack),saved)
