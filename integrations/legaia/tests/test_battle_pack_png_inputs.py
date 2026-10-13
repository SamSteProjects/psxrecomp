"""Original PNG retention, replay and independently retained native index authority."""
import os,tempfile,unittest,struct
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.battle_pack_png_inputs import retain_import,effective,compose,path
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer.battle_pack_png import export
from importer.battle_pack_palettes import source
from importer.battle_pack_palettes import preview
from importer.export import _png


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPNGInputTests(unittest.TestCase):
 def test_edited_index_bytes_replay_after_later_palette_changes_and_preserve_inputs(self):
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  catalog=decode_catalog(original,disc);record=catalog['textures'][0];baseline=bytearray(source(original,catalog,record))
  for i in range(16):struct.pack_into('<H',baseline,20+i*2,0x8000+i+1)
  baseline=bytes(baseline);shown=preview(baseline,0);rgba=bytearray(shown['rgba']);index=(baseline[544]&15)+1;index%=16;r=index+1;rgba[:4]=bytes([(r<<3)|(r>>2),0,0,255]);png=_png(256,256,bytes(rgba));mask=_png(256,256,b'\xff'*262144)
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));owner,candidate,_=retain_import(p,original,catalog,record,0,png,'existing',mask,baseline)
   self.assertNotEqual(candidate[544:],baseline[544:]);self.assertEqual(effective(p,original,catalog,record,owner),candidate[544:]);files={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()}
   current=bytearray(original);at=record['source_record']['byte_offset'];current[at:at+33312]=baseline;struct.pack_into('<H',current,at+20,0x7C00)
   composed=compose(p,original,catalog,{record['semantic_id']:owner},bytes(current));self.assertEqual(composed[at+20:at+532],current[at+20:at+532]);self.assertEqual(composed[at+544:at+33312],candidate[544:]);self.assertEqual(composed[:at],current[:at]);self.assertEqual(composed[at+33312:],current[at+33312:])
   for file,data in files.items():self.assertEqual(file.read_bytes(),data)

 def test_all_six_original_pairs_replay_missing_tampered_forged_and_outside_root_refuse(self):
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  catalog=decode_catalog(original,disc)
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));owners={};retained={}
   for record in catalog['textures'][:6]:
    png,stp,_=export(original,catalog,record,0);owner,candidate,proof=retain_import(p,original,catalog,record,0,png,'existing',stp);owners[record['semantic_id']]=owner;self.assertEqual(candidate,source(original,catalog,record));self.assertEqual(effective(p,original,catalog,record,owner),candidate[544:]);self.assertEqual(path(p,owner['input']['png_sha256'],'png').read_bytes(),png);self.assertEqual(path(p,owner['input']['stp_sha256'],'png').read_bytes(),stp)
   self.assertEqual(compose(p,original,catalog,owners),original)
   record=catalog['textures'][0];owner=owners[record['semantic_id']]
   for edit in [lambda v:v.update(index_sha256='0'*64),lambda v:v['input'].update(candidate_tim_sha256='0'*64),lambda v:v['input'].update(palette_index=True),lambda v:v['input'].update(baseline_sha256='0'*64),lambda v:v['source_record'].update(byte_offset=0),lambda v:v['input'].update(stp_byte_length=None),lambda v:v.update(index_byte_length=True)]:
    bad=deepcopy(owner);edit(bad)
    with self.assertRaises(ProjectError):effective(p,original,catalog,record,bad)
   for key,kind in [(owner['input']['png_sha256'],'png'),(owner['input']['stp_sha256'],'png'),(owner['input']['baseline_sha256'],'tim'),(owner['index_sha256'],'idx')]:
    target=path(p,key,kind);saved=target.read_bytes();target.write_bytes(saved[:-1])
    with self.assertRaises(ProjectError):effective(p,original,catalog,record,owner)
    target.write_bytes(bytes([saved[0]^1])+saved[1:])
    with self.assertRaises(ProjectError):effective(p,original,catalog,record,owner)
    target.unlink()
    with self.assertRaises(ProjectError):effective(p,original,catalog,record,owner)
    target.write_bytes(saved)
   self.assertEqual(compose(p,original,catalog,owners),original)
   with self.assertRaises(ProjectError):path(p,'../outside','png')
   with self.assertRaises(ProjectError):compose(p,original,catalog,{catalog['textures'][6]['semantic_id']:owner})


if __name__=='__main__':unittest.main()
