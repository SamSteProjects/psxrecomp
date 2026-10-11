"""Atomic native group transforms across donor operations and separate anchors."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from urllib.request import urlopen
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_binding import compose
from sdk.worldmap_scripted_placement_allocation import review as create,source
from sdk.worldmap_scripted_placement_group import review,entries
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedGroupTests(TestCase):
 def test_literal_map_atomic_history_and_refusals(self):
  for dc in (0,1):
   with self.subTest(dc=dc),tempfile.TemporaryDirectory() as root:
    raw,fallback,man,floor,requests=fixture(dc);terrain=bytearray(raw)
    for cell in (202,203,204,205):struct.pack_into('<H',terrain,0x8000+cell*2,0x3000|10)
    raw=bytes(terrain)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
    def inputs(project,scene,key,include_scripted=True):
     current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
     return raw,provenance,floor,current,[],fallback,man,man,{},[]
    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
    child='placement://authored/66666666-6666-4666-8666-666666666666';grandchild='placement://authored/77777777-7777-4777-8777-777777777777'
    with patch('sdk.worldmap_scripted_placement_allocation._inputs',side_effect=inputs),patch('sdk.worldmap_scripted_placement_group._inputs',side_effect=inputs):
     for rows in (requests,[{**deepcopy(requests[0]),'placement_id':child,'donor_cell':200,'target_cell':202,'record_index':5}],
                          [{**deepcopy(requests[0]),'placement_id':grandchild,'donor_cell':202,'target_cell':204,'record_index':6}]):
      key=state_key(p);r=create(p,'map01',key,rows);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=rows,review_key=r['review_key']))
     s=source(p,'map01',state_key(p));before=b64decode(s['current_map_base64']);held=deepcopy((p._document(),p.undo_stack));key=state_key(p)
     edits=[dict(placement_id=requests[0]['placement_id'],values=dict(offset=dict(x=-32768,y=123,z=32767),yaw_units=4095)),
            dict(placement_id=child,values=dict(offset=dict(x=17,y=-18,z=19),yaw_units=0))]
     r=review(p,'map01',key,edits);self.assertEqual(review(p,'map01',key,list(reversed(edits))),r)
     expected=bytearray(before)
     for record,entry in zip((4,5),edits):
      at=record*32;value=entry['values'];struct.pack_into('<3h',expected,at,*(value['offset'][axis] for axis in ('x','y','z')))
      struct.pack_into('<H',expected,at+10,(struct.unpack_from('<H',before,at+10)[0]&0xf000)|value['yaw_units'])
     self.assertEqual(b64decode(r['proposed_map_base64']),bytes(expected));self.assertEqual(expected[6*32:7*32],before[6*32:7*32])
     self.assertEqual((p._document(),p.undo_stack),held)
     command=dict(type='transform_worldmap_scripted_placements',scene='map01',source_key=key,entries=edits,review_key=r['review_key'])
     with http_server(p) as (server,post):
      with urlopen(f'http://127.0.0.1:{server.server_port}/worldmap-scripted-group-state.js') as response:
       self.assertIn(b'export async function qualifyScriptedGroupReview',response.read())
      self.assertEqual(post('/api/worldmap-scripted-group-transform-review',dict(scene='map01',source_key=key,entries=edits)),(200,r))
      for bad in ({**command,'review_key':'0'*64},{**command,'extra':True},{**command,'entries':edits+[edits[0]]}):
       self.assertEqual(post('/api/command',bad)[0],400);self.assertEqual((p._document(),p.undo_stack),held)
      self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(post('/api/command',command)[0],400)
     self.assertEqual(len(p.undo_stack),len(held[1])+1);self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),bytes(expected))
     p.save();saved=deepcopy(p._document());self.assertEqual(ProjectService.open(Path(root))._document(),saved)
     p.undo();self.assertEqual(p._document(),held[0]);p.redo();self.assertEqual(p._document(),saved)
     noop=review(p,'map01',state_key(p),edits);self.assertEqual(noop['audit']['changed_bytes'],[]);history=deepcopy(p.undo_stack)
     p.command({**command,'source_key':state_key(p),'review_key':noop['review_key']});self.assertEqual(p.undo_stack,history)
     for bad in ([],edits[:1],edits+[edits[0]],edits*17,[{**edits[0],'extra':True},edits[1]],
                 [{**edits[0],'placement_id':'missing'},edits[1]],
                 [{**edits[0],'values':dict(offset=dict(x=True,y=0,z=0),yaw_units=0)},edits[1]]):
      with self.assertRaises(ProjectError):review(p,'map01',state_key(p),bad)
     self.assertEqual(p._document(),saved);self.assertEqual(p.undo_stack,history)
     from sdk.worldmap_scripted_placement_group import merge_current
     def corrupt(*args,**kwargs):
      data=bytearray(merge_current(*args,**kwargs));data[31]^=1;return bytes(data)
     with patch('sdk.worldmap_scripted_placement_group.merge_current',side_effect=corrupt),self.assertRaisesRegex(ProjectError,'unrelated bytes'):
      review(p,'map01',state_key(p),edits)
