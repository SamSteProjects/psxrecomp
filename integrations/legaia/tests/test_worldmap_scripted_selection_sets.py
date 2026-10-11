from copy import deepcopy
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.build import authored_state_key
from sdk.worldmap_selection_sets import review,review_key,validate,SCRIPTED_SCHEMA
from test_project_workflow import synthetic_scene

class ScriptedSelectionTests(TestCase):
 def test_saved_owner_continuity_and_metadata_history(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.import_metadata(synthetic_scene());p.save()
   ids=[f'placement://authored/77777777-7777-4777-8777-{i:012x}' for i in (1,2)]
   allocations=[dict(placement_id=id,record_index=4+i,script_id='script://map01/worldmap/man-p0/0009') for i,id in enumerate(ids)]
   src=dict(source_record=dict(scene='map01',source_disc_sha256='a'*64,source_map_sha256='b'*64,source_floor_lut_sha256='c'*64),authored_scripted_placements=allocations)
   key=state_key(p);native=authored_state_key(p);before=deepcopy(p._document())
   with patch('sdk.worldmap_scripted_placement_allocation.source',return_value=src):
    p.command(dict(type='create_worldmap_scripted_selection_set',scene='map01',source_key=key,placement_ids=ids[::-1],name='Scripted Pair'))
    row=deepcopy(next(iter(p.worldmap_selection_sets.values())));self.assertEqual(row['schema_version'],SCRIPTED_SCHEMA)
    applied=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p._document(),applied);p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
    self.assertEqual(review(p,row['id'],review_key(p,row),key)['selection'],row)
    for mutate in (lambda v:v['authored_scripted_placements'].pop(),lambda v:v['authored_scripted_placements'][0].update(record_index=20),lambda v:v['authored_scripted_placements'][0].update(script_id='script://map01/worldmap/man-p0/0010')):
     bad=deepcopy(src);mutate(bad)
     with patch('sdk.worldmap_scripted_placement_allocation.source',return_value=bad),self.assertRaises(ProjectError):review(p,row['id'],review_key(p,row),key)
    for domain,field,values in [('authored','placement_ids',ids),('', 'record_ids',['0004'])]:
     kind='update_worldmap_'+(domain+'_' if domain else '')+'selection_set'
     with self.assertRaises(ProjectError):p.command(dict(type=kind,selection_set_id=row['id'],review_key=review_key(p,row),source_key=key,**{field:values}))
    self.assertEqual(state_key(p),key);self.assertEqual(authored_state_key(p),native)
    for mutate in (lambda v:v['bindings'][ids[0]].update(script_id='foreign'),lambda v:v['bindings'][ids[0]].pop('script_id'),lambda v:v.update(schema_version='unknown'),lambda v:v['placement_ids'].reverse()):
     bad=deepcopy(row);mutate(bad)
     with self.assertRaises(ProjectError):validate(p,row['id'],bad)
