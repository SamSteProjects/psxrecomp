from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,struct,tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placements import owner,patch as encode
from sdk.worldmap_placement_files import export_file,review,parse
from test_project_workflow import synthetic_scene

class PlacementFiles(unittest.TestCase):
 def test_sparse_transfer_refusals_atomic_history_and_persistence(self):
  from importer.worldmap_placements import decode_worldmap_placements
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
   raw=bytearray(0x12000);floor=[0]*16
   for index in (5,6):
    struct.pack_into('<3h',raw,index*32,index,0,0);struct.pack_into('<H',raw,index*32+10,0xa040);struct.pack_into('<2H',raw,index*32+16,1,2);struct.pack_into('<H',raw,0x8000+(100+index)*2,0x1000|index)
   raw=bytes(raw);placements=decode_worldmap_placements(raw,floor,scene='map01')['placements'];records={}
   for index in (5,6):
    records[f'{index:04d}']=dict(record_id=f'{index:04d}',object_record_index=index,writable=True,source_cell_count=1,source_record_sha256=sha256(raw[index*32:index*32+32]).hexdigest(),retail_values=dict(offset=dict(x=index,y=0,z=0),yaw_units=64),placements=[r for r in placements if r['object_record_index']==index])
   source=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256='c'*64)
   original_entry=dict(values=dict(offset=dict(x=22,y=0,z=0),yaw_units=128),shared_record=False,source_record_sha256=records['0006']['source_record_sha256'])
   p.overrides[owner('map01')]={'WorldMapPlacements':dict(source,entries={'0006':original_entry})}
   def context(project,scene):
    binding=project.overrides.get(owner(scene),{}).get('WorldMapPlacements');entries=(binding or {}).get('entries',{});rows=deepcopy(records)
    for i,r in rows.items():r['current_values']=deepcopy(entries.get(i,{}).get('values',r['retail_values']));r['authored_values']=deepcopy(entries.get(i,{}).get('values'))
    current,_,seeds=encode(raw,rows,entries,scene=scene,floor=floor);return raw,source,rows,0,floor,binding,current,seeds
   imported=deepcopy(p.imports)
   with patch('sdk.worldmap_placement_files.context',side_effect=context):
    exported=export_file(p,'map01',state_key(p));supplied=deepcopy(exported);supplied['entries']={'0005':dict(values=dict(offset=dict(x=33,y=-8,z=16),yaw_units=256),shared_record=False,source_record_sha256=records['0005']['source_record_sha256'])};content=json.dumps(supplied);held=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
    r=review(p,'map01',state_key(p),content);self.assertFalse(r['no_op']);self.assertEqual(r['after']['WorldMapPlacements']['entries']['0006'],original_entry);self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)
    for bad in (content.replace('"map01"','"map02"'),content.replace(records['0005']['source_record_sha256'],'f'*64),content.replace('"0005"','"0512"')):
     with self.assertRaises(ProjectError):review(p,'map01',state_key(p),bad)
     self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),held)
    body=dict(type='import_worldmap_placement_file',scene='map01',source_key=state_key(p),content=content,review_key=r['review_key']);p.command(body);self.assertEqual(len(p.undo_stack),len(held[1])+1)
    with self.assertRaises(ProjectError):p.command(body)
    after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,held[0]);p.redo();self.assertEqual(p.overrides,after)
    r=review(p,'map01',state_key(p),content);self.assertTrue(r['no_op']);count=len(p.undo_stack);p.command({**body,'source_key':state_key(p),'review_key':r['review_key']});self.assertEqual(len(p.undo_stack),count)
    clear={**supplied,'entries':{'0005':None}};r=review(p,'map01',state_key(p),json.dumps(clear));p.command({**body,'content':json.dumps(clear),'source_key':state_key(p),'review_key':r['review_key']});self.assertEqual(p.overrides,held[0]);p.save();self.assertEqual(ProjectService.open(p.root).overrides,p.overrides);self.assertEqual(p.imports,imported)
    from sdk.worldmap_placement_batch import review as batch_review
    batch_before=deepcopy(p.overrides);count=len(p.undo_stack);delta=dict(x=32,y=-16,z=64,yaw_units=-256);r=batch_review(p,'map01',state_key(p),['0005','0006'],delta,False);self.assertEqual(len(r['records']),2);self.assertEqual(p.overrides,batch_before)
    for row in r['records']:
     for axis in 'xyz':self.assertEqual(row['proposed_values']['offset'][axis],row['current_values']['offset'][axis]+delta[axis])
     self.assertEqual(row['proposed_values']['yaw_units'],(row['current_values']['yaw_units']-256)%4096)
    batch=dict(type='transform_worldmap_records',scene='map01',source_key=state_key(p),record_ids=['0005','0006'],delta=delta,shared_record=False,review_key=r['review_key']);p.command(batch);self.assertEqual(len(p.undo_stack),count+1);applied=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,batch_before);p.redo();self.assertEqual(p.overrides,applied);p.undo()
    for selected,change in ((['0005','0005'],delta),(['0005'],{**delta,'x':65535}),(['0005'],{**delta,'yaw_units':4096}),(['0512'],delta)):
     with self.assertRaises(ProjectError):batch_review(p,'map01',state_key(p),selected,change,False)
     self.assertEqual(p.overrides,batch_before)
    with self.assertRaises(ProjectError):p.command({**batch,'review_key':'f'*64})
    zero=dict(x=0,y=0,z=0,yaw_units=0);r=batch_review(p,'map01',state_key(p),['0005','0006'],zero,False);self.assertTrue(r['no_op']);p.command({**batch,'delta':zero,'source_key':state_key(p),'review_key':r['review_key']});self.assertEqual(len(p.undo_stack),count)
    exported['entries']['0006']['values']['offset']['x']=999;self.assertEqual(p.overrides[owner('map01')]['WorldMapPlacements']['entries']['0006'],original_entry)
 def test_json_budget_duplicates_nonfinite_and_unknown_schema(self):
  for value in ('{"entries":{},"entries":{}}','{"x":NaN}','x'*262145,'{}'):
   with self.assertRaises(ProjectError):parse(value)

if __name__=='__main__':unittest.main()
