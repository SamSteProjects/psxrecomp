import json,os,struct,tempfile,unittest
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from unittest.mock import patch
from importer.floor_height_authoring import patch_floor_heights
from importer.core import ImportError,parse_man,decompress_lzs
from importer.man_actor_structure import append_actor_candidates
from sdk.project import ProjectService,ProjectError
from sdk.floor_heights import review,compose
from test_man_actor_structure import fixture
from test_floor_authoring import floor_fixture

class FloorHeights(unittest.TestCase):
 def test_exact_header_bounds_and_append_composition(self):
  source=fixture();h=sha256(source).hexdigest();edits=[dict(tier=0,height=-32768),dict(tier=15,height=32767)];actual,audit=patch_floor_heights(source,h,'fixture',edits);expected=bytearray(source);struct.pack_into('<h',expected,2,-32768);struct.pack_into('<h',expected,32,32767);self.assertEqual(actual,bytes(expected));self.assertEqual(len(audit),2);self.assertEqual(parse_man(actual).actors,parse_man(source).actors)
  for bad in [edits*2,[dict(tier=True,height=0)],[dict(tier=0,height=True)],[dict(tier=16,height=0)],[dict(tier=0,height=32768)],[{**edits[0],'extra':1}]]:
   with self.assertRaises(ImportError):patch_floor_heights(source,h,'fixture',bad)
  with self.assertRaises(ImportError):patch_floor_heights(source,'0'*64,'fixture',edits)
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());p.overrides[p.active_scene]={'FloorHeights':dict(source_sha256=h,edits=edits)};candidate,_=append_actor_candidates(source,h,[dict(id='clone',donor_record_index=1,position=dict(x=704,z=768))]);result,changes=compose(p,p.active_scene,source,candidate);self.assertEqual(result[:2],candidate[:2]);self.assertEqual(result[34:],candidate[34:]);self.assertEqual(result[2:34],actual[2:34]);self.assertEqual(len(changes),2)
   with self.assertRaisesRegex(ProjectError,'overlaps'):compose(p,p.active_scene,source,result)
 def test_review_http_history_save_open_stale_and_restore(self):
  from test_model_primitive_workflow import http_server
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(floor_fixture());source=fixture();h=sha256(source).hexdigest();record=dict(disc_sha256='a'*64,payload_sha256=h);heights=[0]*16;heights[3]=-96
   with patch('sdk.floor_heights.context',return_value=(source,record)),http_server(p) as (_,post):
    before=deepcopy(p._document());status,initial=post('/api/floor-height-context',dict(entity_id=p.active_scene));self.assertEqual(status,200,initial);self.assertEqual(initial['current'],[0]*16);self.assertEqual(initial['proposed'],initial['current']);self.assertFalse(initial['project_change']);self.assertEqual(post('/api/floor-height-context',dict(entity_id=p.active_scene,extra=1))[0],400);body=dict(entity_id=p.active_scene,heights=heights);status,r=post('/api/floor-height-review',body);self.assertEqual(status,200,r);self.assertEqual(p._document(),before);self.assertEqual(r['retail'],[0]*16);self.assertEqual(r['effective_change_count'],1)
    for bad in [heights[:-1],[True]+heights[1:],[32768]+heights[1:]]:self.assertEqual(post('/api/floor-height-review',{**body,'heights':bad})[0],400)
    command=dict(type='apply_floor_heights',**body,review_key=r['review_key']);self.assertEqual(post('/api/command',{**command,'heights':[0]*16})[0],400);self.assertEqual(p.undo_stack,[]);self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(len(p.undo_stack),1);authored=deepcopy(p.overrides)
    from sdk.floor_heights import proposal_view
    proposal=proposal_view(p,review(p,p.active_scene,[0]*16));self.assertNotIn('FloorHeights',proposal.overrides.get(p.active_scene,{}));self.assertEqual(p.overrides,authored)
    p.undo();self.assertEqual(p.overrides,{});p.redo();self.assertEqual(p.overrides,authored);self.assertEqual(ProjectService.open(p.save()).overrides,authored)
    stale=review(p,p.active_scene,heights);p.name='changed'
    with self.assertRaises(ProjectError):p.command(dict(command,review_key=stale['review_key']))
    noop=review(p,p.active_scene,heights);depth=len(p.undo_stack);p.command(dict(command,review_key=noop['review_key']));self.assertEqual(len(p.undo_stack),depth)
    restore=review(p,p.active_scene,[0]*16);p.command(dict(command,heights=[0]*16,review_key=restore['review_key']));self.assertEqual(p.overrides,{})

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail input')
class RetailFloorHeights(unittest.TestCase):
 def test_private_normal_build_exact_man_header_and_map_composition(self):
  from importer.pipeline import import_scene
  from sdk.floor_heights import context
  from sdk.build import build_project
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));source,record=context(p,p.active_scene);map_source=p._environment_source(p.active_scene);map_hash=sha256(map_source).hexdigest();heights=list(struct.unpack_from('<16h',source,2));heights[1]+=16;p.command(dict(type='set_collision_walls',entity_id=p.active_scene,value=dict(source_sha256=map_hash,edits=[dict(row=1,column=0,quadrant=0,blocked=not bool(map_source[0x4080]&16))])));p.command(dict(type='set_floor_tiers',entity_id=p.active_scene,value=dict(source_sha256=map_hash,edits=[dict(row=1,column=0,tier=1)])));before=deepcopy(p.overrides);r=review(p,p.active_scene,heights);p.command(dict(type='apply_floor_heights',entity_id=p.active_scene,heights=heights,review_key=r['review_key']));p.undo();self.assertEqual(p.overrides,before);p.redo();p=ProjectService.open(p.save());build=build_project(p);audit=json.loads(Path(build['audit']).read_text(encoding='utf-8'));self.assertEqual(len(audit['overlays']),2);man=next(row for row in audit['overlays'] if row['file'].endswith('-man.lzs'));payload=(Path(build['package_directory'])/man['file']).read_bytes();actual,_=decompress_lzs(payload,len(source));expected=bytearray(source);struct.pack_into('<h',expected,4,heights[1]);self.assertEqual(actual,bytes(expected));map_row=next(row for row in audit['overlays'] if row['file'].endswith('-environment.map'));expected_map=bytearray(map_source);expected_map[0x4080]=((map_source[0x4080]^16)&0xf0)|1;self.assertEqual((Path(build['package_directory'])/map_row['file']).read_bytes(),bytes(expected_map))
