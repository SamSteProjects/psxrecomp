"""Current/Proposed exports preserve retail geometry and match serialized records."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import os,tempfile,unittest,math
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placements import source,review,owner,patch as patch_map
from sdk.worldmap_placement_export import export
from sdk.worldmap_export import export as export_retail
from importer.pipeline import import_scene
from test_importer_export import parse_glb

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class WorldPlacementExport(unittest.TestCase):
 def test_three_kingdom_current_proposed_and_unchanged_binary(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN']);p.save()
   imports=deepcopy(p.imports)
   for scene in ('map01','map02','map03'):
    raw,_,records,_,floor=source(p,scene);row=next(r for r in records.values() if r['writable'] and r['source_cell_count']>1)
    value=deepcopy(row['retail_values']);value['offset']['x']+=128;value['offset']['y']+=64;value['offset']['z']+=256;value['yaw_units']=(value['yaw_units']+1024)%4096
    r,_=review(p,scene,state_key(p),row['record_id'],value,True);p.command(dict(type='set_worldmap_placement',scene=scene,source_key=state_key(p),record_id=row['record_id'],values=value,shared_record=True,review_key=r['review']['review_key']))
    key=state_key(p);before=deepcopy((p.overrides,p.undo_stack,p.redo_stack));retail=export_retail(p,scene,key,'source-scene');current=export(p,scene,key)
    proposed_values=deepcopy(value);proposed_values['offset']['x']+=64;proposed_values['yaw_units']=(value['yaw_units']+512)%4096
    r,_=review(p,scene,key,row['record_id'],proposed_values,True);proposal=dict(record_id=row['record_id'],values=proposed_values,shared_record=True,review_key=r['review']['review_key']);proposed=export(p,scene,key,proposal)
    source_doc,source_bin=parse_glb(Path(retail['path']).read_bytes())
    for item,values,representation in ((current,value,'current-source'),(proposed,proposed_values,'proposed-source')):
     doc,binary=parse_glb(Path(item['path']).read_bytes());self.assertEqual(binary,source_bin);self.assertEqual(doc['meshes'],source_doc['meshes']);self.assertEqual(doc['images'],source_doc['images']);self.assertEqual(doc['extras']['representation'],representation)
     metadata=doc['extras']['worldmap_source']['placement_authoring'];self.assertEqual(metadata['source_map_sha256'],sha256(raw).hexdigest());self.assertEqual(metadata['representation'],representation)
     binding=deepcopy(p.overrides[owner(scene)]['WorldMapPlacements']);binding['entries'][row['record_id']]['values']=values
     candidate,_,placements=patch_map(raw,records,binding['entries'],scene=scene,floor=floor);self.assertEqual(metadata['exported_map_sha256'],sha256(candidate).hexdigest());indexed={s['entity_id']:s for s in placements}
     roots={doc['nodes'][i]['extras']['entity_id']:doc['nodes'][i] for i in doc['scenes'][0]['nodes']}
     for identity,node in roots.items():
      if identity.endswith('/ground'):continue
      seed=indexed[identity];position=seed['source_position'];matrix=node['matrix'];self.assertAlmostEqual(matrix[12],position['x']);self.assertAlmostEqual(matrix[13],-position['y']);self.assertAlmostEqual(matrix[14],position['z']);angle=(seed['source_rotation_psx']['y']&4095)*math.tau/4096;self.assertAlmostEqual(matrix[0],math.cos(angle));self.assertAlmostEqual(matrix[2],-math.sin(angle));self.assertAlmostEqual(matrix[8],math.sin(angle));self.assertEqual(node['extras']['authored_source_transform']['exported_record_sha256'],seed['source_record_sha256'])
    self.assertEqual(p.imports,imports);self.assertEqual(before,(p.overrides,p.undo_stack,p.redo_stack));self.assertEqual(state_key(p),key)
 def test_stale_reviews_and_prewrite_drift_create_no_artifacts(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN']);p.save();key=state_key(p)
   with self.assertRaises(ProjectError):export(p,'map01','f'*64)
   raw,_,records,_,floor=source(p,'map01');row=next(r for r in records.values() if r['writable']);value=deepcopy(row['retail_values']);value['offset']['x']+=64
   with self.assertRaisesRegex(ProjectError,'stale'):export(p,'map01',key,dict(record_id=row['record_id'],values=value,shared_record=True,review_key='f'*64))
   from sdk.worldmap_placement_export import encode_worldmap_glb
   def drift(*args,**kwargs):
    result=encode_worldmap_glb(*args,**kwargs);p.name='changed';return result
   with patch('sdk.worldmap_placement_export.encode_worldmap_glb',side_effect=drift),patch('sdk.worldmap_placement_export.write_encoded_glb',side_effect=AssertionError('must reject before write')):
    with self.assertRaisesRegex(ProjectError,'inputs changed'):export(p,'map01',key)
   self.assertFalse((p.root/'Exports').exists())

if __name__=='__main__':unittest.main()
