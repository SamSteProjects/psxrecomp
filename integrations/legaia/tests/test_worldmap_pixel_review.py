from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import struct
from importer.texture_authoring import _validate
from importer.core import ImportError as RetailImportError
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_authoring import review_pixel,apply_pixel

class WorldPixelReviewTests(TestCase):
 def test_literal_packed_neighbors_history_and_receipt_gates_for_both_modes(self):
  for bpp,flag in [(4,8),(8,9)]:
   colors=struct.pack('<'+'H'*(1<<bpp),*range(1<<bpp));original=struct.pack('<II',16,flag)+struct.pack('<IHHHH',12+len(colors),0,1,1<<bpp,1)+colors+struct.pack('<IHHHHH',14,0,0,1,1,0x3210)
   identifier='texture://map01/kingdom/0000';ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,value:_validate(original,value),_source=lambda _:dict(disc=dict(sha256='a'*64)))
   with self.subTest(bpp=bpp),TemporaryDirectory() as root:
    p=ProjectService(Path(root));p.disc_path='fixture'
    with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
     source=p.texture_pixel_source(identifier,0,1,0);value=source['pixel']['palette_entry']^1;request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),palette_index=0,x=1,y=0,palette_entry=value,effective_sha256=sha256(original).hexdigest());held=deepcopy(p._document());receipt=review_pixel(p,request);self.assertEqual(p._document(),held)
     offset=8+struct.unpack_from('<I',original,8)[0]+12+(1//(8//bpp));shift=(1%(8//bpp))*bpp;expected=bytearray(original);mask=((1<<bpp)-1)<<shift;expected[offset]=(expected[offset]&(255^mask))|(value<<shift);expected=bytes(expected)
     self.assertEqual(receipt['candidate_tim_sha256'],sha256(expected).hexdigest());self.assertEqual(receipt['bpp'],bpp)
     with self.assertRaises(ProjectError):apply_pixel(p,request,'0'*64)
     apply_pixel(p,request,receipt['review_key']);binding=deepcopy(p.texture_overrides[identifier]);self.assertEqual(p.read_texture_replacement(binding),expected);self.assertEqual(sum(a!=b for a,b in zip(original,expected)),1);self.assertEqual(len(p.undo_stack),1)
     with self.assertRaises(ProjectError):apply_pixel(p,request,receipt['review_key'])
     p.undo();self.assertEqual(p.texture_overrides,{})
     p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides)
     p.undo();noop={**request,'palette_entry':source['pixel']['palette_entry']};receipt=review_pixel(p,noop);self.assertFalse(receipt['changed']);apply_pixel(p,noop,receipt['review_key']);self.assertEqual(p.texture_overrides,{})
     for key,value in [('x',True),('x',65536),('y',1),('palette_entry',1<<bpp),('palette_index',True),('effective_sha256','0'*64),('member_sha256','0'*64),('source_key','0'*64),('extra',0)]:
      with self.subTest(key=key),self.assertRaises((ProjectError,RetailImportError)):review_pixel(p,{**request,key:value})
     p.mode='live'
     with self.assertRaises(ProjectError):review_pixel(p,request)
