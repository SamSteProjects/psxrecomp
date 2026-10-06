import os,tempfile,unittest,json
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from unittest.mock import patch
from importer.floor_authoring import patch_floor_tiers
from importer.core import ImportError
from sdk.floor_rectangle import review
from sdk.project import ProjectService,ProjectError
from test_project_workflow import synthetic_scene
def floor_fixture():
 document=synthetic_scene();document['source']['disc_identity']='sha256:'+'a'*64;return document

RECT=dict(row_start=0,row_end=1,column_start=0,column_end=1,tier=3)

def context(p,source):
 return dict(floor_height_lut=[i*16 for i in range(16)],source_record=dict(map_sha256=sha256(source).hexdigest(),disc_sha256=p.imports[p.active_scene]['source']['disc_identity'].removeprefix('sha256:'),man_sha256='1'*64))

class FloorAuthoring(unittest.TestCase):
 def test_exact_low_bits_all_tiers_corners_and_invalid_inputs(self):
  source=bytes([0xa5])*0x12000;h=sha256(source).hexdigest();edits=[dict(row=0,column=i,tier=i) for i in range(16)]+[dict(row=127,column=127,tier=0)]
  changed,audit=patch_floor_tiers(source,h,edits);self.assertEqual(len(audit),16)
  self.assertEqual(changed[0x4000:0x4010],bytes(0xa0+i for i in range(16)));self.assertEqual(changed[0x7fff],0xa0)
  self.assertTrue(all((a^b)&0xf0==0 for a,b in zip(source,changed)));self.assertEqual(source,bytes([0xa5])*0x12000)
  for bad in [[edits[0],edits[0]],[dict(row=True,column=0,tier=0)],[dict(row=0,column=0,tier=True)],[dict(row=128,column=0,tier=0)],[dict(row=0,column=0,tier=16)],[{**edits[0],'extra':1}],edits*4096]:
   with self.assertRaises(ImportError):patch_floor_tiers(source,h,bad)
  with self.assertRaises(ImportError):patch_floor_tiers(source,'0'*64,edits)
 def test_rectangle_history_restore_preserves_walls_and_outside_floor(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());source=bytes([0xa5])*0x12000
   with patch.object(ProjectService,'_environment_source',return_value=source),patch('sdk.floor_rectangle.load_environment_placements',return_value=context(p,source)):
    p.command(dict(type='set_collision_walls',entity_id=p.active_scene,value=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(row=1,column=0,quadrant=0,blocked=True)])))
    p.command(dict(type='set_floor_tiers',entity_id=p.active_scene,value=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(row=3,column=3,tier=7)])));before=deepcopy(p.overrides);depth=len(p.undo_stack)
    r=review(p,p.active_scene,RECT);self.assertEqual(r['effective_change_count'],4);self.assertEqual(p.overrides,before)
    p.command(dict(type='apply_floor_rectangle',entity_id=p.active_scene,rectangle=RECT,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[p.active_scene]['Collision'],before[p.active_scene]['Collision']);self.assertEqual(len(p.overrides[p.active_scene]['FloorTiers']['edits']),5)
    p.undo();self.assertEqual(p.overrides,before);p.redo();p=ProjectService.open(p.save());self.assertEqual(len(p.overrides[p.active_scene]['FloorTiers']['edits']),5)
    restore=review(p,p.active_scene,{**RECT,'tier':'retail'});p.command(dict(type='apply_floor_rectangle',entity_id=p.active_scene,rectangle=restore['rectangle'],review_key=restore['review_key']));self.assertEqual(p.overrides[p.active_scene]['FloorTiers'],before[p.active_scene]['FloorTiers'])
 def test_http_readonly_stale_input_and_source_guards(self):
  from test_model_primitive_workflow import http_server
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());source=bytes(0x12000)
   with patch.object(ProjectService,'_environment_source',return_value=source),patch('sdk.floor_rectangle.load_environment_placements',return_value=context(p,source)),http_server(p) as (_,post):
    for bad in [{**RECT,'tier':True},{**RECT,'row_start':-1},{**RECT,'column_end':128},{**RECT,'row_end':127,'column_end':127},{**RECT,'extra':1},{**RECT,'row_start':2}]:
     self.assertEqual(post('/api/floor-rectangle-review',dict(entity_id=p.active_scene,rectangle=bad))[0],400)
    body=dict(entity_id=p.active_scene,rectangle=RECT);before=deepcopy(p._document());status,r=post('/api/floor-rectangle-review',body);self.assertEqual(status,200,r);self.assertEqual(p._document(),before);self.assertEqual(p.undo_stack,[])
    self.assertEqual(post('/api/floor-rectangle-review',{**body,'extra':1})[0],400)
    command=dict(type='apply_floor_rectangle',**body,review_key=r['review_key']);self.assertEqual(post('/api/command',{**command,'rectangle':{**RECT,'tier':4}})[0],400)
    p.name='Changed';self.assertEqual(post('/api/command',command)[0],400);self.assertEqual(p.undo_stack,[])
    r=review(p,p.active_scene,RECT);self.assertEqual(post('/api/command',{**command,'review_key':r['review_key']})[0],200)
   wrong=context(p,source);wrong['source_record']['disc_sha256']='0'*64
   with patch.object(ProjectService,'_environment_source',return_value=source),patch('sdk.floor_rectangle.load_environment_placements',return_value=wrong):
    with self.assertRaisesRegex(ProjectError,'disc evidence'):review(p,p.active_scene,RECT)

class FloorPaint(unittest.TestCase):
 def test_mixed_current_history_source_bits_and_strict_http(self):
  from test_model_primitive_workflow import http_server
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());source=bytes([0xa5])*0x12000;h=sha256(source).hexdigest()
   with patch.object(ProjectService,'_environment_source',return_value=source),patch('sdk.floor_rectangle.load_environment_placements',return_value=context(p,source)),http_server(p) as (_,post):
    p.command(dict(type='set_floor_tiers',entity_id=p.active_scene,value=dict(source_sha256=h,edits=[dict(row=127,column=127,tier=9),dict(row=0,column=1,tier=8)])));before=deepcopy(p.overrides);depth=len(p.undo_stack)
    rect={**RECT,'tier':'current'}
    noop=review(p,p.active_scene,rect,[]);self.assertFalse(noop['project_change']);p.command(dict(type='apply_floor_rectangle',entity_id=p.active_scene,rectangle=rect,cell_edits=[],review_key=noop['review_key']));self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
    cells=[dict(row=0,column=1,tier='retail'),dict(row=0,column=0,tier=3)];body=dict(entity_id=p.active_scene,rectangle=rect,cell_edits=cells)
    status,r=post('/api/floor-rectangle-review',body);self.assertEqual(status,200,r);self.assertEqual(r['schema_version'],'legaia.floor-rectangle-review.v2');self.assertEqual(p.overrides,before);self.assertEqual(r['effective_change_count'],2)
    command=dict(type='apply_floor_rectangle',**body,review_key=r['review_key']);self.assertEqual(post('/api/command',{**command,'cell_edits':[dict(row=0,column=0,tier=4)]})[0],400)
    for bad in [None,cells*2,[dict(row=2,column=0,tier=1)],[dict(row=0,column=0,tier=True)],[dict(row=0,column=0,tier='current')]]:self.assertEqual(post('/api/floor-rectangle-review',{**body,'cell_edits':bad})[0],400)
    self.assertEqual(post('/api/command',{**command,'cell_edits':None})[0],400)
    self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(len(p.undo_stack),depth+1);edits=p.overrides[p.active_scene]['FloorTiers']['edits'];self.assertEqual(edits,[dict(row=0,column=0,tier=3),dict(row=127,column=127,tier=9)])
    actual,_=patch_floor_tiers(source,h,edits);expected=bytearray(source);expected[0x4000]=0xa3;expected[0x7fff]=0xa9;self.assertEqual(actual,bytes(expected));p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail input')
class RetailFloorAuthoring(unittest.TestCase):
 def test_private_floor_wall_save_build_and_map_composer(self):
  from importer.pipeline import import_scene,_disc_context
  from sdk.build import build_project
  from sdk.map_build import prepare_map_patch
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();source=p._environment_source(p.active_scene);h=sha256(source).hexdigest();tier=((source[0x4000]&15)+1)%16
   wall=dict(row=1,column=0,quadrant=0,blocked=not bool(source[0x4080]&16));p.command(dict(type='set_collision_walls',entity_id=p.active_scene,value=dict(source_sha256=h,edits=[wall])));before=deepcopy(p.overrides)
   rect=dict(row_start=0,row_end=1,column_start=0,column_end=0,tier=tier);r=review(p,p.active_scene,rect);p.command(dict(type='apply_floor_rectangle',entity_id=p.active_scene,rectangle=rect,review_key=r['review_key']));p.undo();self.assertEqual(p.overrides,before);p.redo();p=ProjectService.open(p.save())
   expected=bytearray(source);expected[0x4000]=(source[0x4000]&0xf0)|tier;expected[0x4080]=((source[0x4080]^16)&0xf0)|tier
   with _disc_context(p.disc_path) as (_,_,_,archive):
    candidate,audit=prepare_map_patch(p,p.active_scene,p.overrides[p.active_scene],archive);self.assertEqual(candidate['payload'],bytes(expected));self.assertTrue(audit['floor_changes'])
   build=build_project(p);report=json.loads(Path(build['audit']).read_text(encoding='utf-8'));self.assertEqual(len(report['overlays']),1);actual=(Path(build['package_directory'])/report['overlays'][0]['file']).read_bytes();self.assertEqual(actual,bytes(expected))
