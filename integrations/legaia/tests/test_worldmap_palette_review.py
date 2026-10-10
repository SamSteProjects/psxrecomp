from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_texture_authoring import review_palette,apply_palette
import test_worldmap_texture_authoring as native

class WorldPaletteReviewTests(TestCase):
 def test_review_apply_history_noop_and_stale_receipt(self):
  fixture=native.WorldTextureAdapterTests();fixture.setUp();context=fixture.load();identifier='texture://map01/kingdom/0000'
  with TemporaryDirectory() as raw,fixture.scope('importer.texture_authoring._disc_context'),patch('importer.worldmap_texture_authoring.load_worldmap_texture_authoring_context',return_value=context),patch('sdk.worldmap_authoring.state_key',return_value='a'*64):
   p=ProjectService(Path(raw));p.disc_path='fixture';source=p.texture_palette_source(identifier,0)
   request=dict(texture_id=identifier,source_key='a'*64,member_sha256=source['source_sha256'],palette_index=0,entry_index=1,word=source['words'][1]^1,effective_sha256=source['effective_sha256'])
   before=deepcopy(p._document());receipt=review_palette(p,request);self.assertEqual(p._document(),before);self.assertTrue(receipt['changed']);self.assertEqual(receipt['retail_word'],source['retail_words'][1]);self.assertEqual(receipt['current_word'],source['words'][1])
   with self.assertRaises(ProjectError):apply_palette(p,request,'0'*64)
   self.assertEqual(p._document(),before)
   apply_palette(p,request,receipt['review_key']);self.assertEqual(p.texture_palette_source(identifier,0)['words'][1],request['word']);self.assertEqual(len(p.undo_stack),1)
   with self.assertRaises(ProjectError):apply_palette(p,request,receipt['review_key'])
   p.undo();self.assertEqual(p.texture_overrides,{})
   p.redo();reopened=ProjectService.open(p.save());self.assertEqual(reopened.texture_overrides,p.texture_overrides)
   p.undo();noop={**request,'word':source['words'][1]};receipt=review_palette(p,noop);self.assertFalse(receipt['changed']);apply_palette(p,noop,receipt['review_key']);self.assertEqual(p.texture_overrides,{})
   for key,value in [('word',True),('word',65536),('entry_index',True),('entry_index',256),('palette_index',True),('member_sha256','0'*64),('effective_sha256','0'*64),('source_key','0'*64),('extra',True)]:
    with self.subTest(key=key),self.assertRaises(ProjectError):review_palette(p,{**request,key:value})
   p.mode='live'
   with self.assertRaises(ProjectError):review_palette(p,request)
