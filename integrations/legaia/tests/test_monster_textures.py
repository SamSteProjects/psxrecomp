import struct,unittest
from importer.monster_textures import layout,pixels,ImportError,material_crops
class MonsterTextureTests(unittest.TestCase):
 def test_exact_pool_extent_and_native_zero_stp_rules(self):
  pool=bytearray(480+64*256);struct.pack_into('<3H',pool,0,0,0x8000,0x03e0);pool[480]=0x10;pool[481]=2
  r=pixels(bytes(pool),128,0,(0,0,2,0))
  self.assertEqual(r['rgba'],bytes([0,0,0,0,0,0,0,255,0,255,0,255]));self.assertEqual(r['stp'],bytes([0,1,0]))
  data=bytes(0x4c)+bytes(pool);self.assertEqual(layout(data,0x4c),(bytes(pool),128))
  with self.assertRaises(ImportError):layout(data+b'x',0x4c)
  for palette in (-1,True,15):
   with self.assertRaises(ImportError):pixels(bytes(pool),128,palette)
  with self.assertRaises(ImportError):pixels(bytes(pool),128,0,(0,0,128,0))
  g=dict(materials=[dict(textured=True,clut=0,tpage=0)],triangle_uvs=[[[0,0],[127,0],[128,0]]],triangle_materials=[0])
  refused=material_crops(g,bytes(pool),128,'source')[0]
  self.assertEqual(refused['status'],'unsupported');self.assertNotIn('rgba',refused)
