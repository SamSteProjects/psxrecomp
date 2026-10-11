"""Whole-MAP assignment oracle, donor-chain retention and command persistence."""
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,os,struct,tempfile
from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_binding import compose,read_base,replay,validate,owner
from sdk.worldmap_scripted_placement_allocation import review as create,source
from sdk.worldmap_scripted_placement_model import review
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server

class ScriptedModelTests(TestCase):
 def test_literal_model_words_donor_chain_history_and_refusals(self):
  cases=[]
  for dc in (0,1):
   with self.subTest(dc=dc),tempfile.TemporaryDirectory() as root,ExitStack() as stack:
    raw,fallback,man,floor,requests=fixture(dc);terrain=bytearray(raw)
    for cell in (202,203,204,205):struct.pack_into('<H',terrain,32768+cell*2,0x3000|10)
    raw=bytes(terrain)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
    def inputs(project,scene,key,include_scripted=True):
     current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
     return raw,provenance,floor,current,[],fallback,man,man,{},[]
    for module in ('allocation','model','edit','group','relocate','remove'):
     stack.enter_context(patch('sdk.worldmap_scripted_placement_'+module+'._inputs',side_effect=inputs))
    geometry=dict(scene_graph=dict(assets=[dict(asset_id='asset://map01/worldmap/models/0002',preview=dict(vertices=[0,0,0],triangles=[0,0,0]),source_record=dict(fixture=True))]))
    stack.enter_context(patch('sdk.worldmap_geometry.inspect',return_value=geometry))
    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
    parent=requests[0]['placement_id'];child='placement://authored/66666666-6666-4666-8666-666666666666';grand='placement://authored/77777777-7777-4777-8777-777777777777'
    for rows in (requests,[{**deepcopy(requests[0]),'placement_id':child,'donor_cell':200,'target_cell':202,'record_index':5}],
                          [{**deepcopy(requests[0]),'placement_id':grand,'donor_cell':202,'target_cell':204,'record_index':6}]):
     key=state_key(p);r=create(p,'map01',key,rows);p.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=rows,review_key=r['review_key']))
    s=source(p,'map01',state_key(p));before=b64decode(s['current_map_base64']);held=deepcopy((p._document(),p.undo_stack));key=state_key(p)
    r=review(p,'map01',key,[parent],2);expected=bytearray(before);struct.pack_into('<H',expected,4*32+16,2)
    self.assertEqual(b64decode(r['proposed_map_base64']),bytes(expected));self.assertEqual((p._document(),p.undo_stack),held)
    self.assertEqual(r['audit']['retained_child_models'],[dict(placement_id=child,model_pool_index=struct.unpack_from('<H',before,5*32+16)[0])])
    binding=r['binding'];base=read_base(p,binding);allocated,audits=replay(base,fallback,man,floor,binding)
    cases.append(dict(name='model-chain-anchor-'+str(dc),base=b64encode(base).decode(),fallback=b64encode(fallback).decode(),man=b64encode(man).decode(),normal=b64encode(raw).decode(),allocated=b64encode(allocated).decode(),merged=r['proposed_map_base64'],floor=floor,binding=binding,provenance={**provenance,'source_man_sha256':sha256(man).hexdigest(),'fallback_sha256':sha256(fallback).hexdigest()},audits=audits))
    bad=deepcopy(binding);bad['schema_version']='legaia.worldmap-scripted-placement-ledger.v1'
    with self.assertRaises(ProjectError):validate(p,owner('map01'),bad)
    command=dict(type='assign_worldmap_scripted_models',scene='map01',source_key=key,placement_ids=[parent],model_pool_index=2,review_key=r['review_key'])
    with http_server(p) as (server,post):
     self.assertEqual(post('/api/worldmap-scripted-model-review',{k:v for k,v in command.items() if k not in ('type','review_key')}),(200,r))
     for bad in ({**command,'extra':1},{**command,'review_key':'0'*64},{**command,'model_pool_index':True}):
      self.assertEqual(post('/api/command',bad)[0],400);self.assertEqual((p._document(),p.undo_stack),held)
     self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(post('/api/command',command)[0],400)
    self.assertEqual(b64decode(source(p,'map01',state_key(p))['current_map_base64']),bytes(expected))
    self.assertEqual(len(p.undo_stack),len(held[1])+1);p.save();saved=deepcopy(p._document());self.assertEqual(ProjectService.open(Path(root))._document(),saved)
    p.undo();self.assertEqual(p._document(),held[0]);p.redo();self.assertEqual(p._document(),saved)
    noop=review(p,'map01',state_key(p),[parent],2);history=deepcopy(p.undo_stack)
    p.command({**command,'source_key':state_key(p),'review_key':noop['review_key']});self.assertEqual(p.undo_stack,history)
    from sdk.worldmap_scripted_placement_edit import review as transform
    val=dict(offset=dict(x=17,y=-18,z=19),yaw_units=99);t=transform(p,'map01',state_key(p),parent,val)
    moved=bytearray(expected);struct.pack_into('<3h',moved,128,17,-18,19);struct.pack_into('<H',moved,138,(struct.unpack_from('<H',moved,138)[0]&0xf000)|99)
    self.assertEqual(b64decode(t['proposed_map_base64']),bytes(moved))
    group=review(p,'map01',state_key(p),sorted([parent,child]),2);group_expected=bytearray(expected);struct.pack_into('<H',group_expected,5*32+16,2)
    self.assertEqual(b64decode(group['proposed_map_base64']),bytes(group_expected));self.assertEqual(group_expected[192:224],before[192:224])
    for ids,index in (([],2),([parent,parent],2),(['missing'],2),([parent],0),([parent],512),([parent],True),([parent],3)):
     with self.assertRaises(ProjectError):review(p,'map01',state_key(p),ids,index)
    self.assertEqual((p._document(),p.undo_stack),(saved,history))
  if os.environ.get('LEGAIA_SCRIPTED_MODEL_CASES'):Path(os.environ['LEGAIA_SCRIPTED_MODEL_CASES']).write_text(json.dumps(cases),encoding='utf-8')
