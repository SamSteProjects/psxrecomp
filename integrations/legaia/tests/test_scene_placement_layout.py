from copy import deepcopy
from hashlib import sha256
import struct,tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,digest
from sdk.scene_placement_group import layout_review
import test_scene_placement_group as fixtures
from test_scene_placement_group import SCENE,ACTOR,MIXED,IDS,source_map

class MixedLayoutTests(unittest.TestCase):
 def test_alignment_atomic_history_save_noop_and_preservation(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory)
   with patch.object(ProjectService,'_environment_source',return_value=source_map()):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(y=77)))
    before=deepcopy(p.overrides);depth=len(p.undo_stack);op=dict(kind='align',axis='x',anchor_entity_id=ACTOR)
    r=layout_review(p,SCENE,MIXED,op);self.assertEqual(p.overrides,before);self.assertEqual(r['affected_count'],1)
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']))
    self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR],before[ACTOR]);after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(ProjectService.open(p.save()).overrides,after)
    r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change']);p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
 def test_distribution_grid_endpoints_rejections_and_stale(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<h',source,4*32,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    r=layout_review(p,SCENE,MIXED+[IDS[1]],dict(kind='distribute',axis='x'));positions={t['entity_id']:t['proposed']['x'] for t in r['targets']};self.assertEqual(positions,{ACTOR:128,IDS[0]:256,IDS[1]:320})
    for op in (dict(kind='align',axis='y',anchor_entity_id=ACTOR),dict(kind='align',axis='x',anchor_entity_id='other'),dict(kind='distribute',axis='x',extra=1)):
     with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,op)
    p.name='Changed'
    with self.assertRaises(ProjectError):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=r['entity_ids'],operation=r['operation'],review_key=r['review_key']))
    self.assertEqual(p.overrides,{})
   with patch.object(p,'_environment_source',return_value=source_map()):
    with self.assertRaisesRegex(ProjectError,'grid'):layout_review(p,SCENE,MIXED,dict(kind='align',axis='x',anchor_entity_id=IDS[0]))
    with self.assertRaisesRegex(ProjectError,'grid'):layout_review(p,SCENE,MIXED,dict(kind='distribute',axis='x'))

class MixedResetTests(unittest.TestCase):
 def test_reset_exact_source_clears_axes_preserves_components_and_history(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=source_map()
   with patch.object(ProjectService,'_environment_source',return_value=source):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=192,z=320,y=77)))
    environment=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(x=40,y=50,z=60))],instances=[dict(cell_index=129,offset=dict(x=70,y=80),rotation_psx=dict(y=777)),dict(cell_index=258,offset=dict(z=90))])
    p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=environment));before=deepcopy(p.overrides);depth=len(p.undo_stack);op={'kind':'reset'}
    r=layout_review(p,SCENE,MIXED,op);self.assertEqual(p.overrides,before);self.assertEqual(r['reset_actor_axes'],{ACTOR:['x','z']});self.assertTrue(all(t['proposed']==t['retail'] for t in r['targets']))
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR]['Transform']['position'],{'y':77});self.assertEqual(p.overrides[SCENE]['Environment']['edits'],environment['edits']);entries={e['cell_index']:e for e in p.overrides[SCENE]['Environment']['instances']};self.assertEqual(entries[258],environment['instances'][1]);self.assertEqual(entries[129]['offset'],dict(x=10,y=80,z=30));self.assertEqual(entries[129]['rotation_psx'],dict(y=777))
    after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(ProjectService.open(p.save()).overrides,after);noop=layout_review(p,SCENE,MIXED,op);self.assertFalse(noop['project_change']);history=deepcopy((p.undo_stack,p.redo_stack));p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=noop['review_key']));self.assertEqual((p.undo_stack,p.redo_stack),history)
 def test_metadata_only_reset_and_off_grid_recovery(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory)
   with patch.object(p,'_environment_source',return_value=source_map()):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=128,z=256)))
    op={'kind':'reset'};r=layout_review(p,SCENE,MIXED,op);self.assertEqual(r['affected_count'],0);self.assertTrue(r['project_change']);p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertNotIn(ACTOR,p.overrides)
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=1)))
    r=layout_review(p,SCENE,MIXED,op);self.assertEqual(next(t for t in r['targets'] if t['kind']=='actor')['proposed']['x'],128)
    with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(kind='reset',axis='x'))

class MixedRotationTests(unittest.TestCase):
 def test_quarter_turns_exact_anchor_preservation_history_and_save(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=source_map()
   with patch.object(ProjectService,'_environment_source',return_value=source):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=512,z=512,y=77)))
    env=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(y=50))],instances=[dict(cell_index=129,offset=dict(y=80),rotation_psx=dict(y=777)),dict(cell_index=258,offset=dict(z=90))])
    p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=env));before=deepcopy(p.overrides);depth=len(p.undo_stack)
    for turns in (-1,1,2):
     op=dict(kind='rotate',anchor_entity_id=ACTOR,quarter_turns=turns);r=layout_review(p,SCENE,MIXED,op);self.assertEqual(p.overrides,before)
     for target in r['targets']:
      x,z=target['current']['x']-512,target['current']['z']-512
      expected=(512-z,512+x) if turns==1 else (512+z,512-x) if turns==-1 else (512-x,512-z)
      self.assertEqual((target['proposed']['x'],target['proposed']['z']),expected)
     self.assertEqual(r['affected_count'],1)
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR],before[ACTOR]);self.assertEqual(p.overrides[SCENE]['Environment']['edits'],env['edits']);entries={e['cell_index']:e for e in p.overrides[SCENE]['Environment']['instances']};self.assertEqual(entries[129]['offset']['y'],80);self.assertEqual(entries[129]['rotation_psx'],dict(y=777));self.assertEqual(entries[258],env['instances'][1])
    after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(ProjectService.open(p.save()).overrides,after)
 def test_decoration_anchor_actor_grid_and_atomic_rejections(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,0,0,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    op=dict(kind='rotate',anchor_entity_id=IDS[0],quarter_turns=1);r=layout_review(p,SCENE,MIXED,op);actor=next(t for t in r['targets'] if t['kind']=='actor');self.assertEqual(actor['proposed'],dict(x=128,z=128))
    before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
    for invalid in (dict(op,quarter_turns=True),dict(op,quarter_turns=0),dict(op,quarter_turns=4),dict(op,quarter_turns=1.0),dict(op,axis='x'),dict(op,anchor_entity_id='other')):
     with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,invalid)
    p.name='Changed'
    with self.assertRaises(ProjectError):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']))
    p.name=before['name'];self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)
   with patch.object(p,'_environment_source',return_value=source_map()):
    native=layout_review(p,SCENE,MIXED,op);anchor=next(t for t in native['targets'] if t['entity_id']==IDS[0]);self.assertEqual(anchor['proposed'],anchor['current']);actor=next(t for t in native['targets'] if t['kind']=='actor');self.assertTrue(all(actor['proposed'][a]%64==0 for a in ('x','z')))
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=16384,z=16384)))
    with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(op,quarter_turns=2))
 def test_coincident_positions_noop_preserves_redo(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-64,0,-64)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=192)));p.undo();history=deepcopy((p.undo_stack,p.redo_stack));op=dict(kind='rotate',anchor_entity_id=ACTOR,quarter_turns=1);r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change']);p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual((p.undo_stack,p.redo_stack),history)

class MixedScaleTests(unittest.TestCase):
 def test_grid_rounding_anchor_history_save_and_preservation(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,0,0,0)
   with patch.object(ProjectService,'_environment_source',return_value=bytes(source)):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=256,z=256,y=77)))
    before=deepcopy(p.overrides);depth=len(p.undo_stack);op=dict(kind='scale',anchor_entity_id=ACTOR,percent=50)
    r=layout_review(p,SCENE,MIXED,op);self.assertEqual(p.overrides,before)
    decor=next(t for t in r['targets'] if t['kind']=='decoration');self.assertEqual(decor['current'],dict(x=192,z=192));self.assertEqual(decor['proposed'],dict(x=224,z=224)) # scenery keeps native unit precision
    op['percent']=200;r=layout_review(p,SCENE,MIXED,op);self.assertEqual(next(t for t in r['targets'] if t['kind']=='decoration')['proposed'],dict(x=128,z=128))
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR],before[ACTOR]);after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(ProjectService.open(p.save()).overrides,after)
    noop=layout_review(p,SCENE,MIXED,dict(op,percent=100));self.assertFalse(noop['project_change']);history=deepcopy((p.undo_stack,p.redo_stack));p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=noop['operation'],review_key=noop['review_key']));self.assertEqual((p.undo_stack,p.redo_stack),history)
 def test_positive_half_grid_bounds_and_atomic_rejections(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,0,0,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    op=dict(kind='scale',anchor_entity_id=ACTOR,percent=50);r=layout_review(p,SCENE,MIXED,op);self.assertEqual(next(t for t in r['targets'] if t['kind']=='decoration')['proposed'],dict(x=160,z=224))
    before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
    for invalid in [dict(op,percent=v) for v in (True,0,1001,50.0,'50')]+[dict(op,axis='x'),dict(op,anchor_entity_id='other')]:
     with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,invalid)
    with self.assertRaises(ProjectError):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=dict(op,percent=200),review_key=r['review_key']))
    self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=16384,z=16384)))
    with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(op,anchor_entity_id=IDS[0],percent=1000))

class MixedNativeScaleTests(unittest.TestCase):
 def test_native_decoration_anchor_noop_and_actor_quantization(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory)
   with patch.object(p,'_environment_source',return_value=source_map()):
    before=deepcopy(p._document());op=dict(kind='scale',anchor_entity_id=IDS[0],percent=100);r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change']);self.assertTrue(all(t['proposed']==t['current'] for t in r['targets']))
    op['percent']=50;r=layout_review(p,SCENE,MIXED,op);anchor=next(t for t in r['targets'] if t['kind']=='decoration');self.assertEqual(anchor['proposed'],anchor['current'])
    actor=next(t for t in r['targets'] if t['kind']=='actor');expected={}
    for a in ('x','z'):
     n=anchor['current'][a]*100+(actor['current'][a]-anchor['current'][a])*50;expected[a]=((abs(n)+3200)//6400)*64*(1 if n>=0 else -1)
    self.assertEqual(actor['proposed'],expected);self.assertEqual(p._document(),before)
 def test_signed_native_unit_half_rounding(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-321,0,-65) # decoration (-129,257)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    op=dict(kind='scale',anchor_entity_id=ACTOR,percent=50);r=layout_review(p,SCENE,MIXED,op);self.assertEqual(next(t for t in r['targets'] if t['kind']=='decoration')['proposed'],dict(x=-1,z=257)) # -0.5 -> -1; 256.5 ->257
    op['percent']=100;r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change'])
 def test_native_offset_overflow_is_atomic(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,32767,0,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
    with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(kind='scale',anchor_entity_id=ACTOR,percent=200))
    self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)

class MixedNativeRotationTests(unittest.TestCase):
 def test_native_anchor_all_turns_and_atomic_history(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory)
   with patch.object(p,'_environment_source',return_value=source_map()):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(y=77)));before=deepcopy(p._document());depth=len(p.undo_stack)
    for turns in (-1,1,2):
     op=dict(kind='rotate',anchor_entity_id=IDS[0],quarter_turns=turns);r=layout_review(p,SCENE,MIXED,op);anchor=next(t for t in r['targets'] if t['entity_id']==IDS[0]);self.assertEqual(anchor['proposed'],anchor['current']);self.assertTrue(any(anchor['current'][a]%64 for a in ('x','z')))
     actor=next(t for t in r['targets'] if t['kind']=='actor');px,pz=(anchor['current'][a] for a in ('x','z'));dx,dz=actor['current']['x']-px,actor['current']['z']-pz;x,z=(-dz,dx) if turns==1 else (dz,-dx) if turns==-1 else (-dx,-dz)
     self.assertEqual(actor['proposed'],{a:((abs(n)+32)//64)*64*(1 if n>=0 else -1) for a,n in [('x',px+x),('z',pz+z)]});self.assertEqual(p._document(),before)
    old_key=digest(dict(project_source_key=r['project_source_key'],scene=SCENE,source_sha256=r['source_sha256'],entity_ids=r['entity_ids'],delta=r['delta'],operation=op,algorithm='source-grid-layout.v1',targets=sorted(r['targets'],key=lambda t:(t['kind']!='actor',t['entity_id']))))
    self.assertNotEqual(old_key,r['review_key'])
    with self.assertRaisesRegex(ProjectError,'changed since review'):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=old_key))
    self.assertEqual(p._document(),before)
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR]['Transform']['position']['y'],77);after=deepcopy(p.overrides);p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(ProjectService.open(p.save()).overrides,after)
 def test_actor_positive_half_and_decoration_native_units(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-112,0,48) # anchor (80,144), actor(128,256), 180 => (32,32) -> (64,64)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    r=layout_review(p,SCENE,MIXED,dict(kind='rotate',anchor_entity_id=IDS[0],quarter_turns=2));self.assertEqual(next(t for t in r['targets'] if t['kind']=='actor')['proposed'],dict(x=64,z=64));self.assertEqual(next(t for t in r['targets'] if t['kind']=='decoration')['proposed'],dict(x=80,z=144))
   source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-321,0,-65)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    r=layout_review(p,SCENE,MIXED,dict(kind='rotate',anchor_entity_id=ACTOR,quarter_turns=1));self.assertEqual(next(t for t in r['targets'] if t['kind']=='decoration')['proposed'],dict(x=127,z=-1))
 def test_native_rotation_offset_overflow_is_atomic(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,32767,0,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
    with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(kind='rotate',anchor_entity_id=ACTOR,quarter_turns=2))
    self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)

class MixedMirrorTests(unittest.TestCase):
 def test_native_axes_anchor_preservation_history_and_save(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=source_map()
   with patch.object(p,'_environment_source',return_value=source):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(y=77)));env=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(y=50))],instances=[dict(cell_index=129,offset=dict(y=80),rotation_psx=dict(y=777)),dict(cell_index=258,offset=dict(z=90))]);p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=env));before=deepcopy(p._document());depth=len(p.undo_stack)
    for axis in ('x','z'):
     op=dict(kind='mirror',axis=axis,anchor_entity_id=IDS[0]);r=layout_review(p,SCENE,MIXED,op);anchor=next(t for t in r['targets'] if t['entity_id']==IDS[0]);self.assertEqual(anchor['proposed'],anchor['current']);self.assertNotEqual(anchor['current'][axis]%64,0)
     actor=next(t for t in r['targets'] if t['kind']=='actor');n=2*anchor['current'][axis]-actor['current'][axis];expected=deepcopy(actor['current']);expected[axis]=((abs(n)+32)//64)*64*(1 if n>=0 else -1);self.assertEqual(actor['proposed'],expected);self.assertEqual(p._document(),before)
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR]['Transform']['position']['y'],77);self.assertEqual(p.overrides[SCENE]['Environment'],env);self.assertNotIn('x',p.overrides[ACTOR]['Transform']['position']);after=deepcopy(p.overrides);p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(ProjectService.open(p.save()).overrides,after)
 def test_half_rounding_and_atomic_invalid_bounds(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-112,0,48)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    op=dict(kind='mirror',axis='x',anchor_entity_id=IDS[0]);r=layout_review(p,SCENE,MIXED,op);self.assertEqual(next(t for t in r['targets'] if t['kind']=='actor')['proposed'],dict(x=64,z=256));before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
    for invalid in [dict(op,axis='y'),dict(op,anchor_entity_id='unknown'),dict(op,percent=100),dict(op,axis=True),{'kind':'mirror','axis':'x'}]:
     with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,invalid)
    with self.assertRaises(ProjectError):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=dict(op,axis='z'),review_key=r['review_key']))
    self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)
   source=bytearray(source_map());struct.pack_into('<3h',source,4*32,32767,0,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)),self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,dict(kind='mirror',axis='x',anchor_entity_id=ACTOR))
   self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)
 def test_coincident_mirror_noop_keeps_redo(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<3h',source,4*32,-64,0,-64)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(x=192)));p.undo();history=deepcopy((p.undo_stack,p.redo_stack))
    for axis in ('x','z'):
     op=dict(kind='mirror',axis=axis,anchor_entity_id=ACTOR);r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change']);p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual((p.undo_stack,p.redo_stack),history)

if __name__=='__main__':unittest.main()
