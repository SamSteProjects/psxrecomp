"""All complete pack TIM PNG adapters preserve real headers, palettes and STP."""
import os,unittest,struct
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer.battle_pack_palettes import source,preview
from importer.battle_pack_png import export,convert
from importer.export import _png
from importer.core import ImportError


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPNGCodecTests(unittest.TestCase):
 def test_six_complete_atlases_exact_roundtrips_edited_pixels_modes_and_partial_refusal(self):
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  catalog=decode_catalog(original,disc);edited=0
  for record in catalog['textures'][:6]:
   retail=source(original,catalog,record)
   for palette in (0,15):
    png,mask,_=export(original,catalog,record,palette)
    for mode in ('existing','rebuild'):
     roundtrip,proof=convert(original,catalog,record,palette,png,mode,mask);self.assertEqual(roundtrip,retail);self.assertEqual(proof['byte_change_count'],0)
    # Some unused Retail palettes are uniform. A valid Current palette makes
    # every index distinguishable, including completely blank source images.
    baseline=bytearray(retail)
    for i in range(16):struct.pack_into('<H',baseline,20+palette*32+i*2,0x8000+i+1)
    baseline=bytes(baseline);pixels=preview(baseline,palette);rgba=bytearray(pixels['rgba']);stp=bytearray(pixels['stp']);old=baseline[544]&15;target=(old+1)%16;word=pixels['words'][target];r=word&31;rgba[:4]=bytes([(r<<3)|(r>>2),0,0,255]);stp[0]=1
    mask_rgba=b''.join(bytes([v*255,v*255,v*255,255]) for v in stp)
    changed_png=_png(256,256,bytes(rgba));changed_mask=_png(256,256,mask_rgba)
    for mode in ('existing','rebuild'):
     candidate,proof=convert(original,catalog,record,palette,changed_png,mode,changed_mask,current=baseline);shown=preview(candidate,palette);self.assertEqual(shown['rgba'],bytes(rgba));self.assertEqual(shown['stp'],bytes(stp));self.assertGreater(proof['byte_change_count'],0);self.assertEqual(candidate[:20],baseline[:20]);self.assertEqual(candidate[532:544],baseline[532:544]);self.assertEqual(candidate[20:20+palette*32],baseline[20:20+palette*32]);self.assertEqual(candidate[52+palette*32:532],baseline[52+palette*32:532]);edited+=1
   for args in [(True,png,'existing'),(16,png,'existing'),(0,b'foreign','existing'),(0,png,'foreign')]:
    with self.assertRaises(ImportError):convert(original,catalog,record,*args)
  self.assertEqual(edited,24)
  with self.assertRaises(ImportError):export(original,catalog,catalog['textures'][6],0)


if __name__=='__main__':unittest.main()
