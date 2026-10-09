from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch
from importer.controller_bgm import ControllerBgmAuthoringContext
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from sdk.controller_bgm_build import compose_bgm
from sdk.build import BuildError
from test_controller_branches import source, OWNER

ID='script://fixture/controllers/man-p1/0000/bgm/0007'

class ControllerBgmBuild(unittest.TestCase):
 def context(self,extended=False):
  header=bytes([0xb5,7]) if extended else bytes([0x35])
  length=len(header)+3
  src,man=source(bytes([0x61,0x23])+header+bytes([0x34,0x12,128,0x26])+((5-(7+length+1))&65535).to_bytes(2,'little'))
  return ControllerSystemFlagAuthoringContext(src),man,64+len(header)
 def components(self,value):return {'ControllerBgm':{'entries':{ID:{'encoded_id':value}}}}
 def test_literal_complete_man_and_mixed_preimages(self):
  for extended in (False,True):
   ctx,man,at=self.context(extended)
   for value in (0,1,255,256,32768,65535):
    for mixed in (False,True):
     working=bytearray(man);previous=[]
     if mixed:
      working[62:64]=bytes([0x60,3]);previous=[{'decoded_byte_offset':62,'byte_length':2}]
     working=bytes(working)
     result,audit=compose_bgm(ctx,OWNER,self.components(value),working,previous)
     expected=bytearray(working);expected[at:at+2]=value.to_bytes(2,'little')
     self.assertEqual(result,bytes(expected));self.assertEqual(len(audit),1)
     row=audit[0]
     from sdk.build import build_report,package_change_kinds
     report=build_report(dict(edits=[dict(row,scene='fixture')],validation={},overlays=[]))
     self.assertEqual(report['changes'][0]['asset_id'],ID);self.assertEqual(report['changes'][0]['after'],{'encoded_id':value})
     self.assertEqual(package_change_kinds(audit),['controller BGM argument'])
     self.assertEqual(row['decoded_byte_offset'],at);self.assertEqual(row['byte_length'],2)
     self.assertEqual(row['effective_record_sha256'],sha256(working[57:-18]).hexdigest())
     self.assertEqual(row['candidate_record_sha256'],sha256(result[57:-18]).hexdigest())
     self.assertEqual(row['changed_bytes'],[dict(decoded_byte_offset=at+i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(man[at:at+2],expected[at:at+2])) if a!=b])
   self.assertEqual(compose_bgm(ctx,OWNER,self.components(4660),man),(man,[]))
 def test_relocated_mixed_record_and_both_byte_overlap_refuse(self):
  ctx,man,at=self.context();candidate=bytearray(man[:49]+bytes(4)+man[49:])
  for location in (40,46):candidate[location:location+3]=(int.from_bytes(man[location:location+3],'little')+4).to_bytes(3,'little')
  candidate[66:68]=bytes([0x60,3]);candidate=bytes(candidate)
  result,audit=compose_bgm(ctx,OWNER,self.components(65535),candidate,[dict(decoded_byte_offset=66,byte_length=2)],appended=True)
  expected=bytearray(candidate);expected[at+4:at+6]=bytes([255,255]);self.assertEqual(result,bytes(expected))
  self.assertEqual(audit[0]['source_decoded_byte_offset'],at);self.assertEqual(audit[0]['decoded_byte_offset'],at+4)
  self.assertEqual(audit[0]['appended_man_sha256'],sha256(candidate).hexdigest())
  for byte in (at,at+1):
   with self.assertRaises(BuildError):compose_bgm(ctx,OWNER,self.components(4660),man,[dict(decoded_byte_offset=byte,byte_length=1)])
  for byte in (at,at+1,at+2,at-1):
   forged=bytearray(man);forged[byte]^=1
   with self.assertRaises(BuildError):compose_bgm(ctx,OWNER,self.components(65535),bytes(forged))
 def test_receipt_tampering_and_unaudited_bytes_refuse(self):
  ctx,man,at=self.context();components=self.components(65535)
  native,audit=ControllerBgmAuthoringContext(ctx._source).patch(components['ControllerBgm']['entries'])
  variants=[[],audit+audit]
  for field,value in [('source_record_sha256','f'*64),('sub_op',True),('target_context',0),('before_values',{'encoded_id':True}),('after_values',{'encoded_id':True}),('after_hex','00'),('byte_length',1),('decoded_byte_offset',float(at)),('bgm_id',ID[:-4]+'0008')]:
   forged=deepcopy(audit);forged[0][field]=value;variants.append(forged)
  for receipts in variants:
   with patch.object(ControllerBgmAuthoringContext,'patch',return_value=(native,receipts)):
    with self.assertRaises(BuildError):compose_bgm(ctx,OWNER,components,man)
  for byte in (50,at+2):
   forged=bytearray(native);forged[byte]^=1
   with patch.object(ControllerBgmAuthoringContext,'patch',return_value=(bytes(forged),audit)):
    with self.assertRaises(BuildError):compose_bgm(ctx,OWNER,components,man)
 def test_foreign_and_unreached_targets_refuse(self):
  ctx,man,_=self.context()
  for identity in (ID.replace('fixture','other'),ID[:-4]+'0008'):
   with self.assertRaises(BuildError):compose_bgm(ctx,OWNER,{'ControllerBgm':{'entries':{identity:{'encoded_id':1}}}},man)
