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
 def test_offline_rename_delete_and_duplicate_name_guards(self):
  id,value=self.create()
  with self.assertRaises(ProjectError):self.create()
  self.p.disc_path=None;self.p.command(dict(type='rename_worldmap_view',view_id=id,review_key=review_key(self.p,value),name='Renamed'));value=self.p.scene_views[id]
  self.p.command(dict(type='delete_worldmap_view',view_id=id,review_key=review_key(self.p,value)));self.assertFalse(self.p.scene_views);self.p.undo();self.assertEqual(self.p.scene_views[id]['name'],'Renamed')
if __name__=='__main__':unittest.main()
