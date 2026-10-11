from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_views import review
from sdk.scene_views import review_key
from sdk.worldmap_authoring import state_key
from sdk.build import authored_state_key
from test_worldmap_resources import geometry
H='a'*64

def display():return dict(camera=dict(projection='perspective',yaw=-.65,pitch=.8,distance=20,target=dict(x=0,y=1,z=2)),layer='retail',models=True,scope='selected-asset',selected_id='scene://map01/worldmap/placements/0001',wireframe=False)
class WorldViewsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.disc_path='C:/private/source.bin';self.loader=patch('sdk.worldmap_views.load_worldmap_geometry',side_effect=lambda d,s:geometry(s));self.loader.start();self.addCleanup(self.loader.stop)
 def create(self):
  self.p.command(dict(type='create_worldmap_view',scene='map01',source_key=state_key(self.p),name='Shared models',display=display()));id=next(iter(self.p.scene_views));return id,self.p.scene_views[id]
 def test_shared_collection_metadata_undo_save_open_and_noop(self):
  game=authored_state_key(self.p);source=state_key(self.p);id,value=self.create();self.assertEqual(value['kind'],'worldmap');self.assertEqual(self.p.imports,{});self.assertIsNone(self.p.selected)
  body=dict(type='update_worldmap_view',view_id=id,review_key=review_key(self.p,value),source_key=source,display=display());count=len(self.p.undo_stack);self.p.command(body);self.assertEqual(len(self.p.undo_stack),count)
  r=review(self.p,id,review_key(self.p,value),source);self.assertEqual(r['view'],value)
  self.p.undo();self.assertEqual(self.p.scene_views,{});self.p.redo();self.assertEqual(self.p.scene_views[id],value)
  self.p.save();opened=ProjectService.open(self.p.root);self.assertEqual(opened.scene_views,self.p.scene_views);self.assertEqual(authored_state_key(self.p),game);self.assertEqual(state_key(self.p),source)
  for kind in ['rename_scene_view','delete_scene_view']:
   with self.assertRaises(ProjectError):self.p.command(dict(type=kind,view_id=id,review_key=review_key(self.p,value),**({'name':'field alias'} if kind=='rename_scene_view' else {})))
 def test_invalid_display_stale_keys_and_changed_source_refuse_atomically(self):
  id,value=self.create();held=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack))
  for change in [dict(scope='foreign'),dict(selected_id='scene://map02/worldmap/ground'),dict(models=1),dict(camera={**display()['camera'],'distance':float('inf')}),dict(camera={**display()['camera'],'distance':10**1000})]:
   with self.assertRaises(ProjectError):self.p.command(dict(type='update_worldmap_view',view_id=id,review_key=review_key(self.p,value),source_key=state_key(self.p),display={**display(),**change}))
  with self.assertRaises(ProjectError):review(self.p,id,'0'*64,state_key(self.p))
  with self.assertRaises(ProjectError):review(self.p,id,review_key(self.p,value),'0'*64)
  def changed(d,s):
   g=geometry(s);g['source_record']['map_sha256']='b'*64;return g
  with patch('sdk.worldmap_views.load_worldmap_geometry',side_effect=changed):
   with self.assertRaises(ProjectError):review(self.p,id,review_key(self.p,value),state_key(self.p))
  self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack),held)
 def test_current_layer_requires_import_and_instance_binding_is_fresh(self):
  shown=display();shown['layer']='current'
  with self.assertRaises(ProjectError):self.p.command(dict(type='create_worldmap_view',scene='map01',source_key=state_key(self.p),name='Current',display=shown))
  self.assertFalse(self.p.scene_views)
  id,value=self.create();held=deepcopy((self.p._document(),self.p.undo_stack))
  def changed(d,s):
   g=geometry(s);g['scene_graph']['entities'].append(dict(entity_id=f'scene://{s}/worldmap/placements/0002',asset_id=f'asset://{s}/worldmap/models/0001'));return g
  with patch('sdk.worldmap_views.load_worldmap_geometry',side_effect=changed):
   with self.assertRaises(ProjectError):review(self.p,id,review_key(self.p,value),state_key(self.p))
  self.assertEqual((self.p._document(),self.p.undo_stack),held)
 def test_authored_target_stable_owner_persistence_and_atomic_refusal(self):
  from sdk.worldmap_views import validate
  from sdk.project import digest
  target='scene://map01/worldmap/authored-placements/00000000-0000-4000-8000-000000000001'
  shown={**display(),'layer':'current','selected_id':target}
  placement=dict(placement_id='placement://authored/'+target.rsplit('/',1)[1],record_index=4,target_cell=200,model_pool_index=1,donor_cell=100,values=dict(x=1,y=2,z=3,yaw=4))
  active=True
  def composed(project,g):
   if active:g['scene_graph']['entities'].append(dict(entity_id=target,asset_id='asset://map01/worldmap/models/0001',native_entity_id='scene://map01/worldmap/placements/00c8',placement_scope='authored_spawn_seed',authored_placement=deepcopy(placement)))
  with patch('sdk.worldmap_placements.context'),patch('sdk.worldmap_current_placements.compose',side_effect=composed):
   key=state_key(self.p);self.p.command(dict(type='create_worldmap_view',scene='map01',source_key=key,name='Authored Target',display=shown))
   id=next(iter(self.p.scene_views));value=deepcopy(self.p.scene_views[id]);receipt=review_key(self.p,value)
   self.assertEqual(value['binding']['source_instance_ids'],[target]);self.assertEqual(value['binding']['entity_sha256'],digest(value['binding']['authored_owner']))
   placement['values']['x']=99;placement['donor_cell']=50
   self.assertEqual(review(self.p,id,receipt,key)['view'],value)
   self.p.save();self.assertEqual(ProjectService.open(self.p.root).scene_views,self.p.scene_views)
   held=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));active=False
   with self.assertRaisesRegex(ProjectError,'removed'):review(self.p,id,receipt,key)
   active=True;placement['record_index']=5
   with self.assertRaises(ProjectError):review(self.p,id,receipt,key)
   self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack),held)
   for change in [dict(layer='retail'),dict(layer='proposed')]:
    with self.assertRaises(ProjectError):self.p.command(dict(type='create_worldmap_view',scene='map01',source_key=key,name='Invalid Target',display={**shown,**change}))
   forged=deepcopy(value);forged['binding']['authored_owner']['target_cell']+=1
   with self.assertRaises(ProjectError):validate(self.p,id,forged)
   self.p.undo();self.assertFalse(self.p.scene_views);self.p.redo();self.assertEqual(self.p.scene_views[id],value)

 def test_authored_view_complete_native_grid_and_relocated_owner_refusal(self):
  from sdk.worldmap_views import validate
  from sdk.project import digest
  target='scene://map01/worldmap/authored-placements/00000000-0000-4000-8000-000000000001'
  shown={**display(),'layer':'current','selected_id':target}
  cell=4095
  def composed(project,g):
   g['scene_graph']['entities'].append(dict(entity_id=target,asset_id='asset://map01/worldmap/models/0001',
    native_entity_id=f'scene://map01/worldmap/placements/{cell:04x}',placement_scope='authored_spawn_seed',
    authored_placement=dict(placement_id='placement://authored/'+target.rsplit('/',1)[1],record_index=4,target_cell=cell,model_pool_index=1)))
  with patch('sdk.worldmap_placements.context'),patch('sdk.worldmap_current_placements.compose',side_effect=composed):
   for cell in (4095,4096,16000,16383):
    with self.subTest(cell=cell):
     self.p.command(dict(type='create_worldmap_view',scene='map01',source_key=state_key(self.p),name=f'Cell {cell}',display=shown))
     id=next(reversed(self.p.scene_views));value=deepcopy(self.p.scene_views[id]);key=review_key(self.p,value)
     self.assertEqual(review(self.p,id,key,state_key(self.p))['view'],value)
     self.p.save();self.assertEqual(ProjectService.open(self.p.root).scene_views,self.p.scene_views)
     held=deepcopy((self.p._document(),self.p.undo_stack,self.p.redo_stack));previous=cell;cell=(cell+1)%16384
     with self.assertRaisesRegex(ProjectError,'ownership changed'):review(self.p,id,key,state_key(self.p))
     self.assertEqual((self.p._document(),self.p.undo_stack,self.p.redo_stack),held);cell=previous
     for invalid in (-1,16384,True,4096.0):
      forged=deepcopy(value);a=forged['binding']['authored_owner'];a['target_cell']=invalid
      if type(invalid) is int:a['native_entity_id']=f'scene://map01/worldmap/placements/{invalid:04x}'
      forged['binding']['entity_sha256']=digest(a)
      with self.subTest(invalid=invalid),self.assertRaises(ProjectError):validate(self.p,id,forged)
     self.p.undo();self.assertNotIn(id,self.p.scene_views);self.p.redo();self.assertEqual(self.p.scene_views[id],value)

 def test_offline_rename_delete_and_duplicate_name_guards(self):
  id,value=self.create()
  with self.assertRaises(ProjectError):self.create()
  self.p.disc_path=None;self.p.command(dict(type='rename_worldmap_view',view_id=id,review_key=review_key(self.p,value),name='Renamed'));value=self.p.scene_views[id]
  self.p.command(dict(type='delete_worldmap_view',view_id=id,review_key=review_key(self.p,value)));self.assertFalse(self.p.scene_views);self.p.undo();self.assertEqual(self.p.scene_views[id]['name'],'Renamed')
if __name__=='__main__':unittest.main()
