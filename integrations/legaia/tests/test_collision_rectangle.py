import os,tempfile,unittest,json
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.collision_rectangle import review
from importer.collision_authoring import patch_collision_walls
from test_project_workflow import synthetic_scene

RECT=dict(row_start=1,row_end=2,column_start=0,column_end=1,quadrant='all',blocked=True)

class WallRectangle(unittest.TestCase):
 def test_atomic_history_preserved_outside_bits_and_retail_restore(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(synthetic_scene());source=bytes([0x0a])*0x12000
   with patch.object(ProjectService,'_environment_source',return_value=source):
    p.command(dict(type='set_collision_walls',entity_id=p.active_scene,value=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(row=3,column=0,quadrant=0,blocked=True)])));p.save();before=deepcopy(p.overrides);depth=len(p.undo_stack)
    r=review(p,p.active_scene,RECT);self.assertEqual(r['effective_change_count'],16);self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
    command=dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle=RECT,review_key=r['review_key']);p.command(command);self.assertEqual(len(p.undo_stack),depth+1)
    value=p.overrides[p.active_scene]['Collision'];changed,audit=patch_collision_walls(source,value['source_sha256'],value['edits']);self.assertEqual(len(audit),17)
    self.assertTrue(all((a&15)==(b&15) for a,b in zip(source,changed)));self.assertEqual(changed[0x4180],0x1a)
    p.undo();self.assertEqual(p.overrides,before);p.redo();clone=ProjectService.open(p.save());self.assertEqual(clone.overrides,p.overrides)
    restored={**RECT,'blocked':False};r=review(p,p.active_scene,restored);p.command(dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle=restored,review_key=r['review_key']));self.assertEqual(p.overrides,before)
    depth=len(p.undo_stack);r=review(p,p.active_scene,restored);self.assertFalse(r['project_change']);p.command(dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle=restored,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth)
 def test_bounds_mode_stale_context_and_changed_rectangle_reject(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(synthetic_scene());source=bytes(0x12000)
   with patch.object(p,'_environment_source',return_value=source):
    for rectangle in [{**RECT,'row_start':0},{**RECT,'row_end':0},{**RECT,'quadrant':True},{**RECT,'blocked':1},{**RECT,'row_end':127,'column_end':127},{**RECT,'column_start':3}, {**RECT,'extra':1}]:
     with self.assertRaises(ProjectError):review(p,p.active_scene,rectangle)
    r=review(p,p.active_scene,RECT);p.name='Changed'
    with self.assertRaises(ProjectError):p.command(dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle=RECT,review_key=r['review_key']))
    r=review(p,p.active_scene,RECT)
    with self.assertRaises(ProjectError):p.command(dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle={**RECT,'blocked':False},review_key=r['review_key']))
    p.mode='live'
    with self.assertRaises(ProjectError):review(p,p.active_scene,RECT)
    self.assertEqual(p.undo_stack,[])
 def test_combined_budget_and_capture_drift_reject_without_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(synthetic_scene());source=bytes(0x12000)
   with patch.object(p,'_environment_source',return_value=source):
    edits=[dict(row=1+n//128,column=n%128,quadrant=0,blocked=True) for n in range(4096)];p.command(dict(type='set_collision_walls',entity_id=p.active_scene,value=dict(source_sha256=sha256(source).hexdigest(),edits=edits)));before=deepcopy(p.overrides)
    with self.assertRaises(ProjectError):review(p,p.active_scene,{**RECT,'row_start':40,'row_end':40})
    self.assertEqual(p.overrides,before)
   p.overrides={}
   def drift(*args):p.name='Changed';return source
   with patch.object(p,'_environment_source',side_effect=drift):
    with self.assertRaisesRegex(ProjectError,'changed while'):review(p,p.active_scene,RECT)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailWallRectangle(unittest.TestCase):
 def test_retail_review_history_reopen_and_exact_map_package(self):
  from importer.pipeline import import_scene,_disc_context
  from sdk.build import build_project
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();source=p._environment_source(p.active_scene);rectangle={**RECT,'row_start':15,'row_end':16,'column_start':20,'column_end':21};r=review(p,p.active_scene,rectangle);self.assertGreater(r['effective_change_count'],0);p.command(dict(type='apply_collision_rectangle',entity_id=p.active_scene,rectangle=rectangle,review_key=r['review_key']));p.undo();self.assertFalse(p.dirty);p.redo();p=ProjectService.open(p.save());build=build_project(p);report=json.loads(Path(build['audit']).read_bytes());self.assertEqual(len(report['overlays']),1);overlay=report['overlays'][0];changed=(Path(build['package_directory'])/overlay['file']).read_bytes();expected,audit=patch_collision_walls(source,r['source_sha256'],r['value']['edits']);self.assertEqual(changed,expected);self.assertEqual(len(audit),r['audited_bit_count']);self.assertTrue(all((a&15)==(b&15) for a,b in zip(source,changed)))
