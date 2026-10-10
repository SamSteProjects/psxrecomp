from contextlib import nullcontext
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import struct,unittest
from importer.core import ImportError,parse_scene_assets,decompress_lzs
from importer.worldmap_texture_authoring import load_worldmap_texture_authoring_context
from test_importer_texture_authoring import fixture,literals

class WorldTextureAdapterTests(unittest.TestCase):
 def setUp(self):
  _,_,_,pack=fixture(compressed=True);self.pack=pack;stream=literals(pack);raw=bytearray(64);struct.pack_into('<I',raw,0,7)
  for i in range(7):struct.pack_into('<II',raw,8+i*8,((i+1)<<24)|(len(pack) if i==0 else 1),64 if i==0 else 64+len(stream)+8+(i-1)*2)
  raw.extend(stream+b'OPAQUE!!'+b'\xffZ'*6);raw.extend(bytes(-len(raw)%2048));self.raw=bytes(raw);self.bundle=parse_scene_assets(self.raw,86);entry=SimpleNamespace(index=86,start_lba=100,size_sectors=len(raw)//2048)
  self.archive=SimpleNamespace(node=SimpleNamespace(extent_lba=20),entry=lambda i:entry,read_entry=lambda e,**kw:self.raw)
  self.scope=lambda name:patch(name,side_effect=lambda _:nullcontext((None,'a'*64,{},self.archive)))
 def load(self):
  with self.scope('importer.worldmap_texture_authoring._disc_context'),patch('importer.worldmap_texture_authoring._bounded_scene_range',return_value=(83,87)),patch('importer.worldmap_texture_authoring._kingdom_table',return_value=(204800,86,0,self.bundle,self.raw)):
   return load_worldmap_texture_authoring_context('fixture','map01')
 def test_native_ids_reuse_exact_codec_and_preserve_whole_pack_and_neighbors(self):
  context=self.load();id='texture://map01/kingdom/0000'
  with self.scope('importer.texture_authoring._disc_context'):
   options=context.options(id);self.assertTrue(options['supported']);self.assertEqual(options['source_record']['prot_entry_index'],86);original=context.original_tim(id);changed=bytearray(original);changed[-1]^=1;changed=bytes(changed)
   overlays,audit,requests=context.build_patch({id:changed});self.assertFalse(requests);self.assertEqual(len(overlays),1);self.assertEqual(len(audit),1);overlay=overlays[0];decoded=decompress_lzs(overlay['payload'],len(self.pack))[0];source=context._source(id);expected=bytearray(self.pack);expected[source['byte_offset']:source['byte_offset']+len(changed)]=changed;self.assertEqual(decoded,bytes(expected));self.assertEqual(overlay['offset'],(100+20)*2048+64);self.assertEqual(context.original_tim(id),original)
   for bad in [changed+b'X',bytes([0])+changed[1:]]:
    with self.assertRaises(ImportError):context.validate_replacement(id,bad)
   no_op=context.build_patch({id:original});self.assertEqual(no_op,([],[],[]))
 def test_entry_head_range_and_disc_identity_gates(self):
  with self.assertRaises(ImportError):load_worldmap_texture_authoring_context('fixture','town01')
  with self.scope('importer.worldmap_texture_authoring._disc_context'),patch('importer.worldmap_texture_authoring._bounded_scene_range',return_value=(0,87)):
   with self.assertRaises(ImportError):load_worldmap_texture_authoring_context('fixture','map01')
  with self.scope('importer.worldmap_texture_authoring._disc_context'),patch('importer.worldmap_texture_authoring._bounded_scene_range',return_value=(83,87)),patch('importer.worldmap_texture_authoring._kingdom_table',return_value=(204800,86,2048,self.bundle,self.raw)):
   with self.assertRaises(ImportError):load_worldmap_texture_authoring_context('fixture','map01')
  context=self.load()
  with patch('importer.texture_authoring._disc_context',side_effect=lambda _:nullcontext((None,'b'*64,{},self.archive))):
   with self.assertRaises(ImportError):context.original_tim('texture://map01/kingdom/0000')
if __name__=='__main__':unittest.main()
