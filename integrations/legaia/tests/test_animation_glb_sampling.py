import struct,unittest
from copy import deepcopy
from importer.animation_glb import import_animation_glb,sampling_config
from importer.core import ImportError
from test_animation_glb import document,encode,record
class ExternalSampling(unittest.TestCase):
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
