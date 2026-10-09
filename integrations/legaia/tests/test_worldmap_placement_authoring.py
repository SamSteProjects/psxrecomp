"""Bounded source-record ownership, persistence and actual MAP package readback."""
from copy import deepcopy
from hashlib import sha256
import os,json,struct,tempfile,unittest,zipfile,tomllib
from pathlib import Path
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placements import source,values,patch as patch_map,review,owner,validate,build
from sdk.build import build_project,authored_state_key
from importer.pipeline import import_scene

class WorldPlacementGuards(unittest.TestCase):
 def test_value_domains_and_opaque_yaw_bits(self):
  from importer.worldmap_placements import decode_worldmap_placements
  raw=bytearray(0x12000);at=5*32
  struct.pack_into('<3h',raw,at,4,-8,12);struct.pack_into('<H',raw,at+10,0xa040);struct.pack_into('<2H',raw,at+16,1,2)
  for cell in (100,101):struct.pack_into('<H',raw,0x8000+cell*2,0x1000|5)
  original=bytes(raw);floor=[0]*16;placements=decode_worldmap_placements(original,floor,scene='map01')['placements']
  row=dict(object_record_index=5,writable=True,source_cell_count=2,source_record_sha256=sha256(raw[at:at+32]).hexdigest(),retail_values=dict(offset=dict(x=4,y=-8,z=12),yaw_units=64),placements=placements)
  value=dict(offset=dict(x=128,y=-16,z=48),yaw_units=1024)
  entry=dict(values=value,source_record_sha256=row['source_record_sha256'],shared_record=False)
  with self.assertRaisesRegex(ProjectError,'explicit shared'):patch_map(original,{'0005':row},{'0005':entry},scene='map01',floor=floor)
  entry['shared_record']=True;candidate,edits,reopened=patch_map(original,{'0005':row},{'0005':entry},scene='map01',floor=floor)
  expected=bytearray(original);struct.pack_into('<3h',expected,at,128,-16,48);struct.pack_into('<H',expected,at+10,0xa400)
  self.assertEqual(candidate,bytes(expected));self.assertEqual(len(reopened),2);self.assertEqual(len(edits),4)
  from sdk.build import build_report
  reported=build_report(dict(edits=edits,validation={},overlays=[]))['changes']
  for item in reported:
   self.assertEqual(item['record_index'],5);self.assertEqual(item['source_record_sha256'],sha256(original[at:at+32]).hexdigest())
   self.assertEqual(item['affected_source_entities'],[p['entity_id'] for p in placements])
  reported[0]['affected_source_entities'].clear();self.assertEqual(len(edits[0]['affected_source_entities']),2)

  for bad in [dict(offset=dict(x=True,y=0,z=0),yaw_units=0),dict(offset=dict(x=32768,y=0,z=0),yaw_units=0),dict(offset=dict(x=0,y=0,z=0),yaw_units=4096)]:
   with self.assertRaises(ProjectError):values(bad)
  with patch('sdk.worldmap_placements.context',return_value=(original,{}, {'0005':row},200,floor,dict(entries={'0005':entry}),candidate,reopened)):
   project=type('Project',(),{'overrides':{owner('map01'):{'WorldMapPlacements':{}}}})()
   disjoint=bytearray(original);disjoint[500]=9;overlays=[dict(offset=200,size=len(original),payload=bytes(disjoint),expected_sha256=sha256(original).hexdigest())]
   build(project,overlays);self.assertEqual(overlays[0]['payload'][500],9);self.assertEqual(overlays[0]['payload'][at:at+12],candidate[at:at+12])
   conflict=bytearray(original);conflict[at]=77;overlays=[dict(offset=200,size=len(original),payload=bytes(conflict),expected_sha256=sha256(original).hexdigest())]
   with self.assertRaisesRegex(ProjectError,'conflicts'):build(project,overlays)

class WorldPlacementResetGuards(unittest.TestCase):
 def test_reset_review_scope_stale_replay_and_one_step_history(self):
  from sdk.worldmap_placements import review_reset,apply_reset
  from test_project_workflow import synthetic_scene
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
   identifier=owner('map01');p.overrides[identifier]={'WorldMapPlacements':{'entries':{'0005':{'values':{}}}}}
   retail=dict(offset=dict(x=4,y=-8,z=12),yaw_units=64);current=dict(offset=dict(x=36,y=-8,z=12),yaw_units=64)
   row=dict(writable=True,source_record_sha256='a'*64,current_values=current,retail_values=retail,placements=[dict(entity_id='scene://map01/worldmap/placements/0064')])
   p.overrides[identifier]={'WorldMapPlacements':dict(scene='map01',source_disc_sha256=next(iter(p.imports.values()))['source']['disc_identity'].removeprefix('sha256:'),source_map_sha256='c'*64,source_floor_lut_sha256='d'*64,entries={'0005':dict(values=current,source_record_sha256='a'*64,shared_record=False)})}
   raw=bytes(32);changed=bytes([1])+raw[1:];binding=p.overrides[identifier]['WorldMapPlacements']
   context=(raw,{}, {'0005':row},0,[],binding,changed,[])
   held=deepcopy((p.overrides,p.imports,p.undo_stack,p.redo_stack));key=state_key(p)
   with patch('sdk.worldmap_placements.context',return_value=context):
    r=review_reset(p,'map01',key);self.assertEqual((p.overrides,p.imports,p.undo_stack,p.redo_stack),held)
    self.assertEqual(r['changed_bytes'],[dict(byte_offset=0,before_byte=1,after_byte=0)])
    body=dict(type='reset_worldmap_placements',scene='map01',source_key=key,review_key=r['review_key'])
    for bad in ({**body,'review_key':'f'*64},{**body,'extra':True},{**body,'source_key':'f'*64}):
     with self.assertRaises(ProjectError):apply_reset(p,bad)
     self.assertEqual((p.overrides,p.imports,p.undo_stack,p.redo_stack),held)
    p.command(body);self.assertNotIn(identifier,p.overrides);self.assertEqual(len(p.undo_stack),len(held[2])+1)
    with self.assertRaises(ProjectError):p.command(body)
    p.undo();self.assertEqual(p.overrides,held[0]);p.redo();self.assertNotIn(identifier,p.overrides)
    p.undo();p.save();self.assertEqual(ProjectService.open(p.root).overrides,p.overrides)
    row['writable']=False
    with self.assertRaises(ProjectError):review_reset(p,'map01',state_key(p))

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailWorldPlacements(unittest.TestCase):
 def test_three_kingdom_source_roundtrip_and_normal_package(self):
  with tempfile.TemporaryDirectory() as directory:
   project=ProjectService(Path(directory));project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN']);project.save()
   imported=deepcopy(project.imports);baseline=authored_state_key(project)
   for scene in ('map01','map02','map03'):
    raw,provenance,records,offset,floor=source(project,scene)
    unchanged,edits,_=patch_map(raw,records,{},scene=scene,floor=floor);self.assertEqual(unchanged,raw);self.assertEqual(edits,[])
    row=next(r for r in records.values() if r['writable'] and r['source_cell_count']>1)
    value=deepcopy(row['retail_values']);value['offset']['x']+=32;value['offset']['y']+=16;value['offset']['z']-=64;value['yaw_units']=(value['yaw_units']+512)%4096
    key=state_key(project);before_review=authored_state_key(project)
    with self.assertRaisesRegex(ProjectError,'explicit shared'):review(project,scene,key,row['record_id'],value,False)
    result,binding=review(project,scene,key,row['record_id'],value,True)
    self.assertEqual(authored_state_key(project),before_review);self.assertFalse(result['project_changed'])
    command=dict(type='set_worldmap_placement',scene=scene,source_key=key,record_id=row['record_id'],values=value,shared_record=True,review_key=result['review']['review_key'])
    with self.assertRaises(ProjectError):project.command(dict(command,review_key='f'*64))
    project.command(command);after=deepcopy(project.overrides);project.undo();self.assertNotIn(owner(scene),project.overrides);project.redo();self.assertEqual(project.overrides,after);project.save();project=ProjectService.open(project.root)
    self.assertEqual(project.overrides,after);self.assertEqual(project.imports,imported)
    bad=deepcopy(binding);bad['source_disc_sha256']='f'*64
    with self.assertRaises(ProjectError):validate(project,owner(scene),bad)
   built=build_project(project)
   with zipfile.ZipFile(built['path']) as package:
    manifest=tomllib.loads(package.read('manifest.toml').decode());self.assertEqual(len(manifest['overlay']),3)
    for scene in ('map01','map02','map03'):
     raw,_,records,offset,floor=source(project,scene);binding=project.overrides[owner(scene)]['WorldMapPlacements'];expected=bytearray(raw)
     for k,entry in binding['entries'].items():
      at=int(k)*32;v=entry['values'];struct.pack_into('<3h',expected,at,*(v['offset'][a] for a in ('x','y','z')));old=struct.unpack_from('<H',raw,at+10)[0];struct.pack_into('<H',expected,at+10,(old&0xf000)|v['yaw_units'])
     overlay=next(o for o in manifest['overlay'] if o['offset']==offset);payload=package.read(overlay['file']);self.assertEqual(payload,bytes(expected));self.assertEqual(sha256(raw).hexdigest(),overlay['expected_sha256']);self.assertEqual(sha256(payload).hexdigest(),overlay['sha256'])
    self.assertIn('default_enabled = false',package.read('manifest.toml').decode())
   self.assertEqual(built['report']['scene_count'],3);self.assertEqual(built['report']['change_count'],12);self.assertEqual(project.imports,imported)
   project.mode='live'
   with self.assertRaises(ProjectError):review(project,'map01',state_key(project),'0001',None,True)

if __name__=='__main__':unittest.main()
