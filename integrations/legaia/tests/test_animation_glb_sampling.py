import struct,unittest
from copy import deepcopy
from importer.animation_glb import import_animation_glb,sampling_config
from importer.core import ImportError
from test_animation_glb import document,encode,record
class ExternalSampling(unittest.TestCase):
 def test_repeat_ping_pong_reverse_and_boundary_frames_have_exact_native_bytes(self):
  source,glb=self.fixture()
  cases=[('repeat',3,15,[10,0,10]),('repeat',4,-15,[0,10,0]),('ping_pong',3,15,[10,20,10]),('ping_pong',2,-15,[0,10,20]),('repeat',3,0,[10,10,10])]
  for mode,start,rate,expected in cases:
   with self.subTest(mode=mode,start=start,rate=rate):
    actual,report=import_animation_glb(source,glb,fps=15,external_sampling=dict(start_seconds=start,rate=rate,mode=mode))
    self.assertEqual(actual,record([[([x,0,0],[0,0,0])] for x in expected]));self.assertEqual(len(actual),len(source))
    self.assertEqual(report['external_time_range'],dict(start_seconds=2.,end_seconds=4.));self.assertIn(mode,report['quantization']['timeline'])
 def test_clamp_canonicalization_and_static_loop_are_compatible(self):
  self.assertEqual(sampling_config(dict(start_seconds=0,rate=1,mode='clamp')),dict(start_seconds=0.,rate=1.))
  for mode in [None,True,0,'loop',[],{}]:
   with self.subTest(mode=mode),self.assertRaises(ImportError):sampling_config(dict(start_seconds=0,rate=1,mode=mode))
  frames=[[([4,0,0],[0,0,0])]]*3;doc,payload=document(frames);doc['animations']=[];doc['nodes'][0]['translation']=[4,0,0]
  for mode in ['repeat','ping_pong']:
   actual,report=import_animation_glb(record(frames),encode(doc,payload),fps=15,external_sampling=dict(start_seconds=0,rate=-1,mode=mode));self.assertEqual(actual,record(frames));self.assertIsNone(report['external_time_range'])
 def test_step_repeat_and_ping_pong_use_the_shared_clip_extent(self):
  source,glb=self.fixture(step=True)
  for mode,expected in [('repeat',[10,0,10]),('ping_pong',[10,20,10])]:
   actual,_=import_animation_glb(source,glb,fps=15,external_sampling=dict(start_seconds=3,rate=15,mode=mode));self.assertEqual(actual,record([[([x,0,0],[0,0,0])] for x in expected]))
 def fixture(self,step=False):
  frames=[[([x,0,0],[0,0,0])] for x in [0,10,20]];doc,payload=document(frames,mode='STEP' if step else 'LINEAR',terminal=False);payload=bytearray(payload)
  sampler=doc['animations'][0]['samplers'][0];accessor=doc['accessors'][sampler['input']];view=doc['bufferViews'][accessor['bufferView']];offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
  struct.pack_into('<3f',payload,offset,2,3,4)
  if step:
   for s in doc['animations'][0]['samplers']:s['interpolation']='STEP'
  return record(frames),encode(doc,bytes(payload))
 def test_longer_clip_requires_explicit_sampling_and_forward_matches_native(self):
  source,glb=self.fixture()
  with self.assertRaisesRegex(ImportError,'duration'):import_animation_glb(source,glb,fps=15)
  actual,report=import_animation_glb(source,glb,fps=15,external_sampling=dict(start_seconds=2,rate=15))
  self.assertEqual(actual,source);self.assertEqual(report['external_sampling'],dict(start_seconds=2.,rate=15.));self.assertIn('start_seconds',report['quantization']['timeline'])
 def test_reverse_hold_fractional_and_endpoint_samples_preserve_layout(self):
  source,glb=self.fixture()
  for start,rate,positions in [(4,-15,[20,10,0]),(3,0,[10,10,10]),(2.5,7.5,[5,10,15]),(3600,16,[20,20,20]),(0,-16,[0,0,0])]:
   with self.subTest(start=start,rate=rate):
    actual,_=import_animation_glb(source,glb,fps=15,external_sampling=dict(start_seconds=start,rate=rate))
    self.assertEqual(actual,record([[([x,0,0],[0,0,0])] for x in positions]));self.assertEqual(len(actual),len(source))
 def test_step_sampling_uses_external_seconds(self):
  source,glb=self.fixture(step=True);actual,_=import_animation_glb(source,glb,fps=15,external_sampling=dict(start_seconds=2.5,rate=7.5))
  self.assertEqual(actual,record([[([x,0,0],[0,0,0])] for x in [0,10,10]]))
 def test_sampling_structure_and_numeric_bounds(self):
  for value in [None,[],{},dict(start_seconds=0,rate=1,extra=0),dict(start_seconds=True,rate=1),dict(start_seconds=-1,rate=1),dict(start_seconds=3601,rate=1),dict(start_seconds=10**400,rate=1),dict(start_seconds=0,rate=False),dict(start_seconds=0,rate=float('nan')),dict(start_seconds=0,rate=17),dict(start_seconds=0,rate=-17)]:
   with self.subTest(value=value):
    with self.assertRaises(ImportError):sampling_config(value)

 def test_scaled_float32_step_export_times_preserve_every_native_frame(self):
  frames=[[([i*3,0,0],[0,0,0])] for i in range(15)];source=record(frames);doc,payload=document(frames);data=bytearray(payload)
  a=doc['accessors'][doc['animations'][0]['samplers'][0]['input']];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
  for i in range(a['count']):
   t=struct.unpack_from('<f',data,offset+4*i)[0];struct.pack_into('<f',data,offset+4*i,2+4*t)
  actual,_=import_animation_glb(source,encode(doc,bytes(data)),fps=15,external_sampling=dict(start_seconds=2,rate=4))
  self.assertEqual(actual,source)
