from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import struct
from importer.texture_authoring import _validate
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_authoring import review_restore,apply_restore

class WorldTimRestoreTests(TestCase):
 def test_selected_binding_history_noop_and_same_retail_payload(self):
  original=struct.pack('<II',16,2)+struct.pack('<IHHHH',16,0,0,1,2)+b'\x10\x32\x54\x76';current=original[:-1]+b'\x77';identifier='texture://map01/kingdom/0000';neighbor='texture://map02/kingdom/0000'
  ctx=SimpleNamespace(original_tim=lambda _:original,validate_replacement=lambda _,v:_validate(original,v),_source=lambda _:dict(disc=dict(sha256='a'*64)))
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch.object(p,'_texture_context',return_value=ctx),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
    p.set_texture_replacement(identifier,current);p.set_texture_replacement(neighbor,current);bindings=deepcopy(p.texture_overrides);request=dict(texture_id=identifier,source_key='a'*64,member_sha256=sha256(original).hexdigest(),effective_sha256=sha256(current).hexdigest());held=deepcopy(p._document());review=review_restore(p,request);self.assertTrue(review['has_override']);self.assertTrue(review['content_changed']);self.assertEqual(review['changed_image_bytes'],1);self.assertEqual(p._document(),held)
    with self.assertRaises(ProjectError):apply_restore(p,request,'0'*64)
    apply_restore(p,request,review['review_key']);self.assertEqual(p.texture_overrides,{neighbor:bindings[neighbor]});self.assertEqual(len(p.undo_stack),3)
    with self.assertRaises(ProjectError):apply_restore(p,request,review['review_key'])
    p.undo();self.assertEqual(p.texture_overrides,bindings)
    p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides)
    noop={**request,'effective_sha256':sha256(original).hexdigest()};review=review_restore(p,noop);self.assertFalse(review['has_override']);before=len(p.undo_stack);apply_restore(p,noop,review['review_key']);self.assertEqual(len(p.undo_stack),before)
    p.set_texture_replacement(identifier,original);review=review_restore(p,noop);self.assertTrue(review['has_override']);self.assertFalse(review['content_changed']);apply_restore(p,noop,review['review_key']);self.assertNotIn(identifier,p.texture_overrides)
    for key,value in [('source_key','0'*64),('member_sha256','0'*64),('effective_sha256','0'*64),('texture_id','texture://map01/kingdom/00'),('extra',0)]:
     with self.subTest(key=key),self.assertRaises(ProjectError):review_restore(p,{**noop,key:value})
    p.mode='live'
    with self.assertRaises(ProjectError):review_restore(p,noop)
