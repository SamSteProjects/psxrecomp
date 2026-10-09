import unittest
from copy import deepcopy
from hashlib import sha256
from importer.core import ImportError,decompress_lzs
from importer.controller_bgm import ControllerBgmAuthoringContext,validate_bgm_values
from importer.controller_system_flags import ControllerRecordSource
from importer.man_layout import read_man_layout
from importer.serialization import compress_lzs
from importer.script_inspection import inspect_record
from test_controller_branches import source,OWNER
ID='script://fixture/controllers/man-p1/0000/bgm/0005'

class ControllerBgm(unittest.TestCase):
 def test_literal_full_man_word_boundaries_and_preserved_dispatch(self):
  for header in [bytes([0x35]),bytes([0xb5,7])]:
   for dispatch in [0,1,15,128,255]:
    length=len(header)+3;script=header+bytes([0x34,0x12,dispatch])+bytes([0x26])+((5-(5+length+1))&65535).to_bytes(2,'little')
    src,man=source(script);ctx=ControllerBgmAuthoringContext(src);target=ctx.options(OWNER)['targets'][0];at=57+5+len(header)
    self.assertEqual(target['decoded_byte_offset'],at);self.assertEqual(target['values'],{'encoded_id':4660});self.assertEqual(target['sub_op'],dispatch)
    self.assertEqual(ctx.patch({ID:{'encoded_id':4660}}),(man,[]))
    for value in [0,1,255,256,32767,32768,65535]:
     result,audit=ctx.patch({ID:{'encoded_id':value}});expected=bytearray(man);expected[at:at+2]=value.to_bytes(2,'little')
     self.assertEqual(result,bytes(expected));self.assertEqual(result[at+2],dispatch);self.assertEqual(read_man_layout(result),read_man_layout(man));self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest());self.assertEqual(audit[0]['source_decoded_man_sha256'],sha256(man).hexdigest());self.assertEqual(ctx._man,man)
     self.assertEqual(decompress_lzs(compress_lzs(result),len(result))[0],result)
 def test_relocated_exact_record_and_foreign_preimage_refusal(self):
  src,man=source(bytes([0x35,0x34,0x12,7,0x26,0xfb,0xff]));ctx=ControllerBgmAuthoringContext(src)
  candidate=bytearray(man[:49]+bytes(4)+man[49:]);candidate[40:43]=(int.from_bytes(man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(int.from_bytes(man[46:49],'little')+4).to_bytes(3,'little');candidate=bytes(candidate)
  changed,audit=ctx.patch_appended(candidate,{ID:{'encoded_id':65535}});expected=bytearray(candidate);expected[67:69]=bytes([255,255]);self.assertEqual(changed,bytes(expected));self.assertEqual(audit[0]['decoded_byte_offset'],67);self.assertEqual(audit[0]['source_decoded_byte_offset'],63)
  with self.assertRaises(ImportError):ctx.patch_appended(changed,{ID:{'encoded_id':65535}})
  with self.assertRaises(ImportError):ctx.patch_appended(bytearray(candidate),{})
 def test_owners_unknown_paths_boundaries_and_invalid_fields(self):
  src,man=source(bytes([0x35,0x34,0x12,7,0x26,0xfb,0xff]));ctx=ControllerBgmAuthoringContext(src)
  for owner in [OWNER.replace('fixture','other'),OWNER.replace('/0000','/0001'),OWNER.replace('/controllers/','/actors/')]:
   with self.assertRaises(ImportError):ctx.options(owner)
   with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/bgm/0005':{'encoded_id':1}})
  for fields in [{'encoded_id':True},{'encoded_id':-1},{'encoded_id':65536},{'encoded_id':1,'sub_op':2},{'encoded_id':1.5},{}]:
   with self.assertRaises(ImportError):validate_bgm_values(fields)
  for pc in ['0004','0006','0009']:
   with self.assertRaises(ImportError):ctx.patch({ID[:-4]+pc:{'encoded_id':1}})
  with self.assertRaises(ImportError):ctx.patch({ID:{'encoded_id':1}},original=man+bytes(1))
  with self.assertRaises(ImportError):ControllerBgmAuthoringContext(object())
  src,_=source(bytes([0x35,0x34,0x12,7,0xff]));ctx=ControllerBgmAuthoringContext(src);self.assertFalse(ctx.options(OWNER)['supported'])
  with self.assertRaises(ImportError):ctx.patch({ID:{'encoded_id':1}})
 def test_two_distinct_operands_compose_in_canonical_audit_order(self):
  src,man=source(bytes([0x35,0x34,0x12,7,0x35,0xff,0xff,128,0x26,0xf7,0xff]));ctx=ControllerBgmAuthoringContext(src)
  changed,audit=ctx.patch({ID[:-4]+'0009':{'encoded_id':256},ID:{'encoded_id':0}});expected=bytearray(man);expected[63:65]=bytes(2);expected[67:69]=bytes([0,1]);self.assertEqual(changed,bytes(expected));self.assertEqual([r['decoded_byte_offset'] for r in audit],[63,67])
