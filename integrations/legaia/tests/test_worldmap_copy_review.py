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
from sdk.worldmap_texture_authoring import review_copy,apply_copy

class WorldCopyReviewTests(TestCase):
 def test_literal_rectangle_history_and_gates(self):
  for bpp,flag in [(4,8),(8,9)]:
   colors=struct.pack('<'+'H'*(1<<bpp),*range(1<<bpp))
   original=struct.pack('<II',16,flag)+struct.pack('<IHHHH',12+len(colors),0,1,1<<bpp,1)+colors+struct.pack('<IHHHH',20,0,0,2,2)+bytes(range(8))
   identifier='texture://map01/kingdom/0000'
   ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,v:_validate(original,v),_source=lambda _:dict(disc=dict(sha256='a'*64)))
   with self.subTest(bpp=bpp),TemporaryDirectory() as root:
    p=ProjectService(Path(root));p.disc_path='fixture'
    with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
     request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),palette_index=0,x=1,y=0,width=2,height=2,source_x=0,source_y=0,effective_sha256=sha256(original).hexdigest())
     held=deepcopy(p._document());receipt=review_copy(p,request);self.assertEqual(p._document(),held)
     expected=bytearray(original);start=8+struct.unpack_from('<I',original,8)[0]+12
     changed=0
     for y in range(2):
      for x in (1,2):
       offset=start+y*4+x//(8//bpp);shift=(x%(8//bpp))*bpp;mask=((1<<bpp)-1)<<shift
       source_offset=start+y*4+(x-1)//(8//bpp);source_shift=((x-1)%(8//bpp))*bpp;value=(original[source_offset]>>source_shift)&((1<<bpp)-1)
       changed+=((original[offset]>>shift)&((1<<bpp)-1))!=value
       expected[offset]=(expected[offset]&(255^mask))|(value<<shift)
     expected=bytes(expected);self.assertEqual(receipt['candidate_tim_sha256'],sha256(expected).hexdigest());self.assertEqual(receipt['changed_pixel_count'],changed)
     with self.assertRaises(ProjectError):apply_copy(p,request,'0'*64)
     apply_copy(p,request,receipt['review_key']);self.assertEqual(p.read_texture_replacement(p.texture_overrides[identifier]),expected);self.assertEqual(len(p.undo_stack),1)
     with self.assertRaises(ProjectError):apply_copy(p,request,receipt['review_key'])
     noop={**request,'source_x':1,'effective_sha256':sha256(expected).hexdigest()};review=review_copy(p,noop);self.assertFalse(review['changed']);apply_copy(p,noop,review['review_key']);self.assertEqual(len(p.undo_stack),1)
     p.undo();self.assertEqual(p.texture_overrides,{})
     p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides)
     p.undo()
     for key,value in [('x',True),('width',0),('height',3),('width',65536),('source_x',65535),('source_y',True),('palette_index',True),('effective_sha256','0'*64),('member_sha256','0'*64),('source_key','0'*64),('extra',0)]:
      with self.subTest(key=key),self.assertRaises((ProjectError,RetailImportError)):review_copy(p,{**request,key:value})
     p.mode='live'
     with self.assertRaises(ProjectError):review_copy(p,request)
