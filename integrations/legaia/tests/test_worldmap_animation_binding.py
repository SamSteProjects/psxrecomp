from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_animation_binding import COMPONENT,owner,compose
from sdk.worldmap_animation_edit import review,current
from importer.worldmap_animation_authoring import patch_world_animation_bank
from importer.worldmap_object_animation import resolve_object_animation
from test_worldmap_object_animation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldAnimationBindingTests(TestCase):
 def test_shared_atomic_composition_history_persistence_and_reset(self):
  _,single,geometry=fixture();bank=struct.pack('<3I',2,16,48)+b'GAP!'+single[8:]+single[8:];disc='b'*64;source=dict(descriptor_type=5,decoded_sha256=sha256(bank).hexdigest())
  def native(p,scene,key,entity,frame,edits):
   index=0 if entity=='first' else 1;start=16+32*index;bind=dict(status='resolved_source_header',encoded_animation_selector=index+1)
   candidate,audit=patch_world_animation_bank(bank,sha256(bank).hexdigest(),index,sha256(bank[start:start+32]).hexdigest(),edits)
   return dict(before=dict(animation_source=source,preview=resolve_object_animation(bind,bank,geometry,frame),binding=dict(bind=bind)),current_model_geometry=geometry,audit=audit,animation_id=f'animation://{scene}/worldmap/anm/{index:04d}')
  with tempfile.TemporaryDirectory() as root,patch('sdk.worldmap_animation_binding.load_bank',return_value=(bank,source,disc)),patch('sdk.worldmap_animation_edit.native_review',side_effect=native):
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+disc;p.import_metadata(doc);held=deepcopy(p._document());ids=owner('map01')
   edits=[dict(frame_index=0,object_index=0,translation=dict(x=2))]
   def request(entity,rows,shared=True):
    key=state_key(p);r=review(p,'map01',key,entity,0,rows,shared);return r,dict(type='set_world_animation_channels',scene='map01',source_key=key,entity_id=entity,frame_index=0,edits=rows,shared_record=shared,review_key=r['review_key'])
   with self.assertRaises(ProjectError):request('first',edits,False)
   r,c=request('first',edits);self.assertEqual(p._document(),held)
   with http_server(p) as (_,post):
    self.assertEqual(post('/api/worldmap-animation-edit-review',{k:v for k,v in c.items() if k not in ('type','review_key')}),(200,r));self.assertEqual(post('/api/command',{**c,'review_key':'0'*64})[0],400);self.assertEqual(post('/api/command',c)[0],200);self.assertEqual(post('/api/command',c)[0],400)
   first=deepcopy(p._document());expected=bytearray(bank);expected[24]=2;self.assertEqual(compose(p,'map01',bank,disc)[0],bytes(expected));self.assertEqual(len(p.undo_stack),1)
   current_value=current(p,'map01',state_key(p),'first',0);self.assertEqual(current_value['preview']['object_transforms'][0]['translation'][0],2)
   with http_server(p) as (_,post):
    body=dict(scene='map01',source_key=state_key(p),entity_id='first',frame_index=0)
    self.assertEqual(post('/api/worldmap-object-animation-current',body),(200,current_value))
    self.assertEqual(post('/api/worldmap-object-animation-current',{**body,'extra':True})[0],400)
   r,c=request('first',edits);self.assertFalse(r['project_change']);p.command(c);self.assertEqual(len(p.undo_stack),1)
   r,c=request('second',[dict(frame_index=1,object_index=0,rotation_psx=dict(z=4080))]);p.command(c);expected[71]=255;self.assertEqual(compose(p,'map01',bank,disc)[0],bytes(expected))
   p.save();saved=deepcopy(p._document());self.assertEqual(ProjectService.open(Path(root))._document(),saved);p.undo();self.assertEqual(p._document(),first);p.redo();self.assertEqual(p._document(),saved)
   self.assertEqual(len([a for a in p.authored_assets() if a['kind']=='animation']),2)
   r,c=request('first',[]);p.command(c);expected[24]=1;self.assertEqual(compose(p,'map01',bank,disc)[0],bytes(expected));self.assertEqual(set(p.overrides[ids][COMPONENT]['entries']),{'0001'})
   r,c=request('second',[]);p.command(c);self.assertNotIn(ids,p.overrides);self.assertEqual(compose(p,'map01',bank,disc)[0],bank)
   p.undo();bad=deepcopy(p.overrides[ids]);bad[COMPONENT]['source_bank_sha256']='0'*64;p.overrides[ids]=bad
   with self.assertRaises(ProjectError):compose(p,'map01',bank,disc)
