from copy import deepcopy
from fractions import Fraction
import struct,unittest
from sdk.animation_record_interpolation import stage,interpolate_axis
from sdk.animation_record_edit import prepare
from sdk.animation_record_ledger import compose,verified_source
from sdk.project import ProjectService,ProjectError
from importer.animation import animation_record_ranges
from importer.animation_authoring import patch_animation_channels
from importer.animation_allocation import allocate_animation_record
from test_animation_record_effective_interpolation import EffectiveInterpolation
from test_model_primitive_workflow import http_server

class CurveWords(unittest.TestCase):
 def test_literal_curves_and_refusal(self):
  for curve,expected in [('linear',[-12,-4,4,12,20]),('ease_in',[-12,-10,-4,6,20]),('ease_out',[-12,2,12,18,20]),('smoothstep',[-12,-7,4,15,20])]:
   self.assertEqual([interpolate_axis('translation',-12,20,i,4,curve) for i in range(5)],expected)
  self.assertEqual([interpolate_axis('rotation_psx',4080,48,i,4,'ease_in') for i in range(5)],[4080,4080,0,16,48])
  self.assertEqual(interpolate_axis('translation',-1,0,1,2,'smoothstep'),0)
  for curve in [None,False,0,'unknown',{},[]]:
   with self.assertRaises(ProjectError):interpolate_axis('translation',0,1,1,2,curve)

class NativeCurves(EffectiveInterpolation):
 def native_mapped(self,mapping,edits):
  source,_=verified_source(self.project,self.project.active_scene);a,b=animation_record_ranges(source)[int(self.entry['donor_animation_id'].split('/')[-1])]
  captured,_=patch_animation_channels(source[a:b],self.entry['donor_record_sha256'],self.entry['donor_edits'])
  return allocate_animation_record(captured,self.entry['effective_donor_record_sha256'],mapping,edits)[0]
 def test_curved_complete_native_bytes_and_history(self):
  mapping=[1,0,1,0,1];edits=[dict(frame_index=0,object_index=0,translation=dict(x=-12),rotation_psx=dict(y=4080)),dict(frame_index=4,object_index=0,translation=dict(x=20),rotation_psx=dict(y=48))]
  args={**self.args,'source_frame_indices':mapping,'edits':edits,'end':4};held=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack));original=self.native_mapped(mapping,edits);objects=struct.unpack_from('<H',original)[0]&255
  def words(frame,obj):
   at=8+(frame*objects+obj)*8;v=original[at:at+8];signed=lambda n:n-4096 if n&2048 else n
   return [signed(v[0]|(v[2]&15)<<8),signed(v[1]|(v[2]>>4)<<8),signed(v[3]|(v[4]&15)<<8),*v[5:]]
  for all_objects in [False,True]:
   for curve in ['ease_in','ease_out','smoothstep']:
    report=stage(self.project,**args,curve=curve,all_objects=all_objects);candidate=self.native_mapped(mapping,report['edits']);expected=bytearray(original)
    for obj in range(objects) if all_objects else [0]:
     first,last=words(0,obj),words(4,obj)
     for frame in range(5):
      t=Fraction(frame,4);t=t*t if curve=='ease_in' else 2*t-t*t if curve=='ease_out' else t*t*(3-2*t);out=[]
      for axis in range(6):
       delta=last[axis]-first[axis]
       if axis>=3:
        delta%=256
        if delta>128:delta-=256
       v=Fraction(first[axis])+t*delta+Fraction(1,2);out.append(v.numerator//v.denominator)
      at=8+(frame*objects+obj)*8;x,y,z=[v&4095 for v in out[:3]];expected[at:at+4]=bytes([x&255,y&255,(x>>8)|((y>>8)<<4),z&255]);expected[at+4]=(expected[at+4]&240)|(z>>8);expected[at+5:at+8]=bytes(v%256 for v in out[3:])
    self.assertEqual(candidate,bytes(expected));self.assertEqual(report['curve'],curve);self.assertEqual(report['schema_version'],'legaia.animation-record-interpolation.v4' if all_objects else 'legaia.animation-record-interpolation.v3');self.assertEqual((self.project._document(),self.project.undo_stack,self.project.redo_stack),held)
  with http_server(self.project) as (_,post):
   self.assertEqual(post('/api/animation-record-interpolation',{**args,'curve':'smoothstep'})[0],200)
   for curve in [None,False,'unknown',{}]:self.assertEqual(post('/api/animation-record-interpolation',{**args,'curve':curve})[0],400)
  request={k:report[k] for k in ['scene_id','record_id','source_frame_indices','edits']};request['expected_source_key']=args['expected_source_key'];_,review=prepare(self.project,**request);self.project.command(dict(type='edit_animation_record',**request,review_key=review['review_key']));bank,_=compose(self.project,self.project.active_scene);a,b=animation_record_ranges(bank)[-1];self.assertEqual(bank[a:b],candidate);self.assertEqual(len(self.project.undo_stack),len(held[1])+1);self.project.save();self.assertEqual(compose(ProjectService.open(self.project.root),self.project.active_scene)[0],bank);self.project.undo();self.assertEqual((self.project._document(),self.project.undo_stack),held[:2]);self.project.redo();self.assertEqual(compose(self.project,self.project.active_scene)[0],bank)
