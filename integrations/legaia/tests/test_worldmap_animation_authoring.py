from hashlib import sha256
from copy import deepcopy
from pathlib import Path
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from importer.worldmap_animation_authoring import patch_world_animation_bank
from importer.worldmap_object_animation import resolve_object_animation
from importer.core import ImportError
from test_worldmap_object_animation import fixture


class WorldAnimationAuthoringTests(TestCase):
 def test_literal_bank_neighbors_opaque_and_noop(self):
  bind,single,geometry=fixture();record=bytearray(single[8:]);record[12]=0xa0
  bank=struct.pack('<3I',2,16,48)+b'GAP!'+bytes(record)+single[8:]
  edits=[dict(frame_index=0,object_index=0,translation=dict(x=2047,y=-2048),rotation_psx=dict(y=4080)),dict(frame_index=1,object_index=0,translation=dict(z=-2048))]
  held=deepcopy(edits);candidate,audit=patch_world_animation_bank(bank,sha256(bank).hexdigest(),0,sha256(record).hexdigest(),edits)
  expected=bytearray(bank);expected[24:27]=bytes([255,0,0x87]);expected[30]=255;expected[35]=0;expected[36]=8
  self.assertEqual(candidate,bytes(expected));self.assertEqual(edits,held);self.assertEqual(candidate[28],0xa0);self.assertEqual(candidate[48:],bank[48:]);self.assertEqual(candidate[:24],bank[:24])
  self.assertEqual([r['byte_offset'] for r in audit['changed_bytes']],[24,26,30,36]);self.assertFalse(audit['gameplay_verified'])
  pose=resolve_object_animation(bind,candidate,geometry,0);self.assertEqual(pose['object_transforms'][0]['translation'],[2047,-2048,0]);self.assertEqual(pose['object_transforms'][0]['opaque_nibble'],10)
  no,receipt=patch_world_animation_bank(bank,sha256(bank).hexdigest(),0,sha256(record).hexdigest(),[]);self.assertEqual(no,bank);self.assertEqual(receipt['changed_bytes'],[])

 def test_domains_and_source_ownership(self):
  _,bank,_=fixture();hash=sha256(bank).hexdigest();record_hash=sha256(bank[8:]).hexdigest()
  for index,source_hash,clip_hash,edits in [(True,hash,record_hash,[]),(1,hash,record_hash,[]),(0,'0'*64,record_hash,[]),(0,hash,'0'*64,[]),(0,hash,record_hash,[dict(frame_index=0,object_index=0,rotation_psx=dict(x=1))]),(0,hash,record_hash,[dict(frame_index=0,object_index=0,translation=dict(z=-2049))]),(0,hash,record_hash,[dict(frame_index=0,object_index=0,translation=dict(x=True))])]:
   with self.subTest(index=index,edits=edits),self.assertRaises(ImportError):patch_world_animation_bank(bank,source_hash,index,clip_hash,edits)

 def test_review_http_exact_shape_and_unchanged_project(self):
  from sdk.project import ProjectService
  from sdk.worldmap_authoring import state_key
  from sdk.worldmap_animation_review import review
  from test_project_workflow import synthetic_scene
  from test_model_primitive_workflow import http_server
  from base64 import b64decode
  bind,bank,geometry=fixture();preview=resolve_object_animation(bind,bank,geometry,0)
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.import_metadata(synthetic_scene());held=deepcopy((p._document(),p.undo_stack));key=state_key(p)
   before=dict(preview=preview,model_asset_id='model',model_source=dict(fixture=True),binding=dict(bind=bind))
   edits=[dict(frame_index=0,object_index=0,translation=dict(x=2))];body=dict(scene='map01',source_key=key,entity_id='entity',frame_index=0,edits=edits)
   with patch('sdk.worldmap_animation_review.inspect',return_value=before),patch('sdk.worldmap_animation_review.current_placements',return_value=dict(scene_graph=dict(assets=[dict(asset_id='model',source_record=dict(fixture=True),preview=geometry)]))):
    result=review(p,'map01',key,'entity',0,edits);expected=bytearray(bank);expected[16]=2;self.assertEqual(b64decode(result['proposed_preview']['bank_base64']),bytes(expected));self.assertFalse(result['build_ready'])
    with http_server(p) as (_,post):
     self.assertEqual(post('/api/worldmap-object-animation-review',body),(200,result))
     for invalid in ({},{**body,'extra':1},{**body,'edits':None},{**body,'source_key':'0'*64}):self.assertEqual(post('/api/worldmap-object-animation-review',invalid)[0],400)
   self.assertEqual((p._document(),p.undo_stack),held)
