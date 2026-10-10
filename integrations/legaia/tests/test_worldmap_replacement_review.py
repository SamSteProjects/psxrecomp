from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import struct,base64
from importer.texture_authoring import _validate
from importer.core import ImportError as RetailImportError
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_authoring import review_replacement,apply_replacement

class WorldReplacementReviewTests(TestCase):
 def test_exact_file_preview_history_and_refusal(self):
  for bpp,flag in [(4,8),(8,9),(16,2)]:
   colors=struct.pack('<'+'H'*(1<<bpp),*range(1<<bpp)) if bpp<16 else b''
   original=struct.pack('<II',16,flag)+(struct.pack('<IHHHH',12+len(colors),0,1,1<<bpp,1)+colors if colors else b'')+struct.pack('<IHHHH',20,0,0,2,2)+bytes(range(8))
   candidate=bytearray(original);candidate[-1]^=1
   if colors:candidate[20]^=1
   candidate=bytes(candidate);identifier='texture://map01/kingdom/0000'
   ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,v:_validate(original,v),_source=lambda _:dict(disc=dict(sha256='a'*64)))
   with self.subTest(bpp=bpp),TemporaryDirectory() as root:
    p=ProjectService(Path(root));p.disc_path='fixture'
    with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
     request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest(),palette_index=0,content_base64=base64.b64encode(candidate).decode())
     held=deepcopy(p._document());receipt=review_replacement(p,request);self.assertEqual(p._document(),held);self.assertNotIn('content_base64',receipt['request']);self.assertEqual(receipt['candidate_tim_sha256'],sha256(candidate).hexdigest());self.assertEqual(receipt['changed_palette_words'],int(bool(colors)));self.assertEqual(receipt['changed_image_bytes'],1);self.assertEqual(receipt['changed_pixel_count'],1 if bpp<16 else None)
     rgba=base64.b64decode(receipt['rgba_base64']);self.assertEqual(len(rgba),receipt['width']*receipt['height']*4);self.assertEqual(sha256(rgba).hexdigest(),receipt['rgba_sha256'])
     with self.assertRaises(ProjectError):apply_replacement(p,request,'0'*64)
     apply_replacement(p,request,receipt['review_key']);self.assertEqual(p.read_texture_replacement(p.texture_overrides[identifier]),candidate);self.assertEqual(len(p.undo_stack),1)
     with self.assertRaises(ProjectError):apply_replacement(p,request,receipt['review_key'])
     noop={**request,'effective_sha256':sha256(candidate).hexdigest()};review=review_replacement(p,noop);self.assertFalse(review['changed']);apply_replacement(p,noop,review['review_key']);self.assertEqual(len(p.undo_stack),1)
     p.undo();self.assertEqual(p.texture_overrides,{})
     p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides);p.undo()
     invalid=bytearray(candidate);invalid[4]^=1
     for key,value in [('content_base64','bad!'),('content_base64',base64.b64encode(candidate+b'x').decode()),('content_base64',base64.b64encode(invalid).decode()),('palette_index',True),('effective_sha256','0'*64),('member_sha256','0'*64),('source_key','0'*64),('extra',0)]:
      with self.subTest(key=key),self.assertRaises((ProjectError,RetailImportError)):review_replacement(p,{**request,key:value})
     original_request={**request,'content_base64':base64.b64encode(original).decode()};receipt=review_replacement(p,original_request);apply_replacement(p,original_request,receipt['review_key']);self.assertEqual(p.texture_overrides,{})
     p.mode='live'
     with self.assertRaises(ProjectError):review_replacement(p,request)

 def test_missing_local_palette_is_explicit_and_24_bit_pixels_are_supported(self):
  for flag,width_words,data in [(0,1,b'\x10\x32'),(3,3,b'\x01\x02\x03\x04\x05\x06')]:
   original=struct.pack('<II',16,flag)+struct.pack('<IHHHH',12+len(data),0,0,width_words,1)+data
   candidate=original[:-1]+bytes([original[-1]^1]);identifier='texture://map01/kingdom/0000'
   ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,v:_validate(original,v))
   with TemporaryDirectory() as root:
    p=ProjectService(Path(root))
    with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
     request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest(),palette_index=0,content_base64=base64.b64encode(candidate).decode())
     receipt=review_replacement(p,request)
     self.assertEqual(receipt['palette_count'],int(flag==3));self.assertEqual(len(base64.b64decode(receipt['rgba_base64'])),8 if flag==3 else 0)
     self.assertEqual(receipt['changed_pixel_count'],None if flag==3 else 1)
