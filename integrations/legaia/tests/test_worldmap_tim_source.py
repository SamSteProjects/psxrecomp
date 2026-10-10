from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import struct,base64
from importer.texture_authoring import _validate
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_authoring import tim_source

class WorldTimSourceTests(TestCase):
 def test_fresh_retail_current_bytes_without_mutation_and_stale_refusal(self):
  original=struct.pack('<II',16,2)+struct.pack('<IHHHH',16,0,0,1,2)+b'\x10\x32\x54\x76';current=original[:-1]+b'\x77';identifier='texture://map01/kingdom/0000'
  ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,v:_validate(original,v),_source=lambda _:dict(disc=dict(sha256='a'*64)))
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
    request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(original).hexdigest(),layer='current');held=deepcopy(p._document());self.assertEqual(base64.b64decode(tim_source(p,request)['tim_base64']),original);self.assertEqual(p._document(),held)
    p.set_texture_replacement(identifier,current);held=deepcopy(p._document());history=deepcopy(p.undo_stack);request['effective_sha256']=sha256(current).hexdigest()
    for layer,expected in [('retail',original),('current',current)]:
     response=tim_source(p,{**request,'layer':layer});self.assertEqual(base64.b64decode(response['tim_base64']),expected);self.assertEqual(response['tim_sha256'],sha256(expected).hexdigest());self.assertEqual(response['byte_length'],len(expected));self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
    for key,value in [('layer','live'),('member_sha256','0'*64),('effective_sha256','0'*64),('source_key','0'*64),('texture_id','texture://map01/kingdom/00'),('extra',0)]:
     with self.subTest(key=key),self.assertRaises(ProjectError):tim_source(p,{**request,key:value})
    p.mode='live'
    with self.assertRaises(ProjectError):tim_source(p,request)
