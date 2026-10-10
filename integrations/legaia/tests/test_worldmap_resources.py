from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,digest
from sdk.worldmap_resources import inspect
from test_project_workflow import synthetic_scene
H='a'*64

def geometry(scene):
 source=dict(scene=scene,disc_sha256=H,map_sha256=H,bundle_sha256=H,floor_lut_sha256=H,bundle_entry_index=1,texture_slot=dict(slot_index=0,decoded_byte_length=100))
 texture=dict(semantic_id=f'texture://{scene}/kingdom/0000',pack_slot=0,byte_offset=4,byte_length=32,prot_entry_index=1,descriptor_index=0,decoded_member_sha256=H,bpp=4,width=4,height=4)
 ground=f'asset://{scene}/worldmap/walk-ground';model=f'asset://{scene}/worldmap/models/0001';preview=dict(bounds=dict(min=[0,0,0],max=[1,1,1]),vertices=[[0,0,0]],triangles=[[0,0,0]],objects=[{}],materials=[dict(textured=True)],textures=[dict(material_index=0,status='address_match',source_ids=[texture['semantic_id']])])
 model_source=dict(disc_sha256=H,prot_entry_index=1,pack_slot=1,decoded_member_offset=4,decoded_member_span_end=36,decoded_byte_length=100,decoded_member_sha256=H)
 assets=[dict(asset_id=ground,source_record=deepcopy(source),preview=deepcopy(preview)),dict(asset_id=model,source_record=model_source,preview=deepcopy(preview))]
 entities=[dict(entity_id=f'scene://{scene}/worldmap/ground',asset_id=ground),dict(entity_id=f'scene://{scene}/worldmap/placements/0001',asset_id=model)]
 p=deepcopy(preview);p['texture_catalog']=dict(textures=[texture],diagnostics=[])
 return dict(scene=scene,semantic_id=ground,source_record=source,preview=p,scene_graph=dict(assets=assets,entities=entities,coverage=dict(unresolved=[])))

class WorldResources(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=ProjectService(Path(self.temp.name));self.p.import_metadata(synthetic_scene());self.p.disc_path='private'
  self.key=patch('sdk.worldmap_resources.state_key',return_value=H);self.key.start();self.addCleanup(self.key.stop)
 def test_source_graph_metadata_and_project_immutability(self):
  held=deepcopy((self.p._document(),self.p.assets.records,self.p.undo_stack,self.p.redo_stack,self.p.selected))
  with patch('sdk.worldmap_resources.load_worldmap_geometry',side_effect=lambda d,s:geometry(s)):r=inspect(self.p,H)
  self.assertEqual(r['coverage'],dict(kingdom_count=3,asset_count=12,reference_count=15,geometry_asset_count=6,texture_asset_count=3));self.assertTrue(r['metadata_only']);self.assertTrue(all(a['scene_id'] is None for a in r['assets']))
  self.assertEqual((self.p._document(),self.p.assets.records,self.p.undo_stack,self.p.redo_stack,self.p.selected),held)
  def keys(v):
   if isinstance(v,dict):return set(v)|set().union(*(keys(x) for x in v.values()))
   if isinstance(v,list):return set().union(*(keys(x) for x in v)) if v else set()
   return set()
  self.assertFalse(keys(r)&{'vertices','triangles','rgba','stp','glb_base64'})
 def test_unplaced_native_inventory_has_no_source_instances(self):
  def loader(d,s):
   result=geometry(s);result['scene_graph']['entities']=result['scene_graph']['entities'][:1];return result
  with patch('sdk.worldmap_resources.load_worldmap_geometry',side_effect=loader):r=inspect(self.p,H)
  models=[a for a in r['assets'] if a['resource_role']=='native_unplaced_model']
  self.assertEqual(len(models),3)
  self.assertTrue(all(a['source_instance_ids']==[] and 'unplaced' in a['name'] for a in models))
  self.assertFalse(any(e['kind']=='source_instance' for e in r['references']))
 def test_invalid_source_spans_foreign_material_and_duplicates_refuse(self):
  changes=[lambda g:g['preview']['texture_catalog']['textures'][0].update(byte_length=101),lambda g:g['scene_graph']['assets'][1]['source_record'].update(prot_entry_index=2),lambda g:g['scene_graph']['assets'][1]['preview']['textures'][0].update(source_ids=['foreign']),lambda g:g['scene_graph']['assets'].append(deepcopy(g['scene_graph']['assets'][1])),lambda g:g['scene_graph']['assets'][1]['preview'].update(bounds=dict(min=[2,0,0],max=[1,1,1]))]
  held=digest(self.p._document())
  for change in changes:
   def loader(d,s):
    result=geometry(s);change(result);return result
   with patch('sdk.worldmap_resources.load_worldmap_geometry',side_effect=loader):
    with self.assertRaises(ProjectError):inspect(self.p,H)
   self.assertEqual(digest(self.p._document()),held)
 def test_stale_and_live_refuse_before_source_reads(self):
  with patch('sdk.worldmap_resources.load_worldmap_geometry',side_effect=AssertionError('source must not load')):
   with self.assertRaises(ProjectError):inspect(self.p,'0'*64)
   self.p.mode='live'
   with self.assertRaises(ProjectError):inspect(self.p,H)

if __name__=='__main__':unittest.main()
