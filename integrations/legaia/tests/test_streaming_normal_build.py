"""Normal packages preserve raw MAN carriers and compose audited source edits."""
import os,tempfile,unittest,json,zipfile,hashlib
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
from importer.pipeline import import_scene,_disc_context,_bounded_scene_range
from importer.man_source import read_man_source
from importer.serialization import patch_man_positions
from importer.core import parse_man
from sdk.project import ProjectService
from sdk.build import build_project,BuildError
from sdk.build_review import review
from sdk.build_history import verify_build

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class StreamingNormalBuild(unittest.TestCase):
 def project(self,d):
  p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'dolk2'));return p
 def source(self,p):
  with _disc_context(p.disc_path) as (_,_,mapping,archive):
   a,b=_bounded_scene_range(archive,mapping,'dolk2');carrier=read_man_source(archive,a,b,'dolk2');entry=archive.entry(carrier.entry_index);return carrier,archive.read_entry(entry),(archive.node.extent_lba+entry.start_lba)*2048
 def test_raw_placement_grid_noop_clear_and_exact_source_span(self):
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=self.project(d);carrier,body,base=self.source(p);baseline=build_project(p);actor=p.imports[p.active_scene]['actors'][10];owner=actor['semantic_id'];original=actor['imported_transform']['position']['x'];p.command(dict(type='set_transform',entity_id=owner,position={'x':original+64}));p.save();metadata=(p.root/'project.legaia.json').read_bytes();r=build_project(p);audit=json.loads(Path(r['audit']).read_text());overlay=audit['overlays'][0];self.assertEqual(overlay['offset'],base+carrier.payload_offset);self.assertEqual(overlay['source_kind'],'raw_streaming_man');self.assertEqual(overlay['compression'],'none');self.assertEqual(overlay['size'],len(carrier.payload));self.assertEqual(audit['validation']['raw_MAN_structural_round_trip'],True);self.assertEqual(audit['validation']['lz_decode_round_trip'],'not_required_no_compressed_scene_overlay');self.assertEqual(metadata,(p.root/'project.legaia.json').read_bytes())
   with zipfile.ZipFile(r['path']) as z:payload=z.read('assets/dolk2-man.bin')
   expected,changes=patch_man_positions(carrier.payload,'dolk2',{11:{'x':original+64}});self.assertEqual(payload,expected);self.assertEqual(len(changes),1);patched=body[:carrier.payload_offset]+payload+body[carrier.payload_offset+len(payload):];self.assertEqual(body[:carrier.payload_offset],patched[:carrier.payload_offset]);self.assertEqual(body[carrier.payload_offset+len(payload):],patched[carrier.payload_offset+len(payload):]);self.assertEqual(parse_man(payload,'dolk2').actors[10].world_x,original+64);self.assertEqual(verify_build(p,Path(r['audit']).parent.name)['report'],r['report'])
   p.overrides={owner:{'Transform':{'position':{'x':original}}}};self.assertEqual(build_project(p)['sha256'],baseline['sha256']);p.overrides={};self.assertEqual(build_project(p)['sha256'],baseline['sha256'])
 def test_raw_MAN_header_scripts_and_ANM_compose_with_exact_audit_bytes(self):
  from importer.flag_authoring import load_flag_authoring_context
  from importer.scene_animation import load_scene_actor_animation_catalog
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=self.project(d);carrier,body,base=self.source(p);owner='scene://dolk2/actors/man-p1/0001';p.overrides={
    'scene://dolk2/actors/man-p1/0041':{'ActorAppearance':{'donor_entity_id':owner}},
    'scene://dolk2/actors/man-p1/0011':{'Transform':{'position':{'x':9472}}},
    'scene://dolk2/actors/man-p1/0003':{'Dialogue':{'runs':{'script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018':'SDK'}}},
    'scene://dolk2/scripts/man-p2/0000':{'Transitions':{'entries':{'script://dolk2/scripts/man-p2/0000/transition/001a':{'entry_x_encoded':55}}}}}
   context=load_flag_authoring_context(p.disc_path,'dolk2');target=next(t for a in p.imports[p.active_scene]['actors'] for t in context.options(a['semantic_id'])['targets'] if t['mnemonic']=='CFLAG_SET' and t['values']['bit']==24);p.command(dict(type='set_flag_bit',entity_id=target['owner_id'],flag_id=target['semantic_id'],values={'bit':25}));options=p.animation_authoring_options(owner);binding=options['binding'];value=p.animation_channel_values(owner,0,0)['retail']['translation']['x']^1;p.command(dict(type='set_animation_channels',entity_id=owner,value=dict(animation_id=binding['semantic_id'],source_record_sha256=binding['source_record']['record_sha256'],edits=[dict(frame_index=0,object_index=0,translation={'x':value})])));p.save();reviewed=review(p);self.assertTrue(reviewed['normal_build_ready'],reviewed['blockers']);r=build_project(p);self.assertEqual(reviewed['assessment']['report'],r['report']);audit=json.loads(Path(r['audit']).read_text());self.assertEqual(len(audit['overlays']),2);self.assertEqual(audit['validation']['lz_decode_round_trip'],'not_required_no_compressed_scene_overlay');self.assertTrue(audit['validation']['raw_MAN_structural_round_trip'])
   with zipfile.ZipFile(r['path']) as z:payload=z.read('assets/dolk2-man.bin');anm=z.read('assets/dolk2-animation.bin')
   offsets={i for change in audit['edits'] if change.get('scope')!='shared-scene-animation-record' for i in range(change['decoded_byte_offset'],change['decoded_byte_offset']+change.get('byte_length',1))};self.assertEqual(len(payload),len(carrier.payload));self.assertTrue(all(a==b or i in offsets for i,(a,b) in enumerate(zip(carrier.payload,payload))));actors=parse_man(payload,'dolk2').actors;self.assertEqual(actors[10].world_x,9472);self.assertEqual((actors[40].model_index,actors[40].animation_id),(actors[0].model_index,actors[0].animation_id));catalog=load_scene_actor_animation_catalog(p.disc_path,'dolk2');expected,_=catalog.authored_bank({owner:p.overrides[owner]['AnimationChannels']});self.assertEqual(anm,expected);self.assertEqual({row['field'] for row in r['report']['changes']}&{'position.x','dialogue.text','flag.bit'},{'position.x','dialogue.text','flag.bit'});self.assertEqual(verify_build(p,Path(r['audit']).parent.name)['integrity'],'verified')
 def test_unaudited_byte_and_wrong_chunk_locator_fail_before_outputs(self):
  for fault in ['opaque','chunk']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
    p=self.project(d);carrier,_,_=self.source(p);p.overrides={'scene://dolk2/actors/man-p1/0011':{'Transform':{'position':{'x':9472}}}}
    def opaque(*args):
     candidate,audit=patch_man_positions(*args);candidate=bytes([candidate[0]^1])+candidate[1:];return candidate,audit
    target=patch('sdk.build.patch_man_positions',side_effect=opaque) if fault=='opaque' else patch('sdk.build.read_man_source',return_value=replace(carrier,chunk_header_offset=carrier.chunk_header_offset+4))
    with target,self.assertRaises(BuildError):build_project(p)
    self.assertFalse((p.root/'Builds').exists())
