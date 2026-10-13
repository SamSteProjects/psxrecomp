"""Literal pack CLUT words, all complete atlases, protected pixels and sparse replay."""
import os,struct,unittest
from copy import deepcopy
from hashlib import sha256
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer.battle_pack_palettes import source,effective,compose,project,preview,qualify_entry
from importer.core import ImportError


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class PackPaletteCodecTests(unittest.TestCase):
 def test_current_palette_model_export_preserves_native_profile_and_replay(self):
  from importer import battle_pack_model_authoring as models
  from test_monster_model_authoring import shifted_glb
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  catalog=decode_catalog(original,disc);values={}
  for record in catalog['textures'][:6]:
   retail=source(original,catalog,record);candidate=bytearray(retail)
   edits=[]
   for i in range(256):
    word=struct.unpack_from('<H',retail,20+i*2)[0]^0x7FFF;struct.pack_into('<H',candidate,20+i*2,word);edits.append(dict(palette_index=i//16,entry_index=i%16,word=word))
   values[record['semantic_id']]=dict(schema_version='legaia.battle-pack-palette-override.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),edits=edits,current_tim_sha256=sha256(candidate).hexdigest())
  current=compose(original,catalog,values);self.assertEqual(qualify_entry(original,catalog,current),current)
  model=catalog['models'][0];glb,binding=models.export(original,model,catalog);tmd,_=models.convert(original,model,catalog,binding,shifted_glb(glb));at=model['source_record']['byte_offset'];end=at+len(tmd);model_entry=original[:at]+tmd+original[end:];composed=compose(original,catalog,values,model_entry)
  self.assertEqual(composed[at:end],tmd);self.assertEqual(composed[:at],current[:at]);self.assertEqual(composed[end:],current[end:])
  bad_base=bytearray(model_entry);bad_base[-1]^=1
  with self.assertRaises(ImportError):compose(original,catalog,values,bytes(bad_base))
  changed_exports=0
  for record in catalog['models']:
   retail_glb,binding=models.export(original,record,catalog);current_glb,current_binding=models.export(original,record,catalog,texture_entry=current)
   self.assertEqual(binding,current_binding)
   expected,_=models.convert(original,record,catalog,binding,shifted_glb(retail_glb));actual,_=models.convert(original,record,catalog,current_binding,shifted_glb(current_glb));self.assertEqual(actual,expected)
   if current_glb!=retail_glb:changed_exports+=1
  self.assertGreater(changed_exports,0)
  for at in (0,4,catalog['textures'][0]['source_record']['byte_offset']+532,len(original)-1):
   bad=bytearray(current);bad[at]^=1
   with self.assertRaises(ImportError):qualify_entry(original,catalog,bytes(bad))

 def test_six_complete_tim_palettes_all_cells_sparse_replay_and_partial_refusal(self):
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):original=archive.read_entry(archive.entry(1204))
  catalog=decode_catalog(original,disc);values={}
  for record in catalog['textures'][:6]:
   retail=source(original,catalog,record);binding=None
   for palette in range(16):
    words=preview(retail,palette)['words'];self.assertEqual(words,list(struct.unpack_from('<16H',retail,20+palette*32)))
    for entry in range(16):
     word=words[entry]^0x8001;owner,candidate,proof=project(original,catalog,record,None,palette,entry,word);expected=bytearray(retail);struct.pack_into('<H',expected,20+palette*32+entry*2,word)
     self.assertEqual(candidate,bytes(expected));self.assertEqual(effective(original,catalog,record,owner),candidate)
     self.assertEqual(candidate[:20],retail[:20]);self.assertEqual(candidate[532:],retail[532:]);self.assertEqual(proof['candidate_tim_sha256'],sha256(expected).hexdigest())
     returned,back,_=project(original,catalog,record,owner,palette,entry,words[entry]);self.assertIsNone(returned);self.assertEqual(back,retail)
    binding,candidate,_=project(original,catalog,record,binding,palette,0,words[0]^0x801F)
   self.assertEqual(len(binding['edits']),16);values[record['semantic_id']]=binding
   # Entry0 zero/STP black and RGB extremes use the native decoder, preserving index bytes.
   for word in (0,0x8000,0x001F,0x03E0,0x7C00,0xFFFF):
    _,candidate,_=project(original,catalog,record,None,0,0,word);shown=preview(candidate,0);self.assertEqual(shown['words'][0],word);self.assertEqual(len(shown['rgba']),256*256*4);self.assertEqual(len(shown['stp']),256*256)
  current=compose(original,catalog,values)
  allowed={record['source_record']['byte_offset']+20+r['palette_index']*32+r['entry_index']*2+k for record in catalog['textures'][:6] for r in values[record['semantic_id']]['edits'] for k in (0,1)}
  self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(original,current)) if a!=b))
  with self.assertRaises(ImportError):source(original,catalog,catalog['textures'][6])
  with self.assertRaises(ImportError):compose(original,catalog,{catalog['textures'][6]['semantic_id']:values[catalog['textures'][0]['semantic_id']]})
  record=catalog['textures'][0];owner=values[record['semantic_id']]
  for changes in [lambda v:v['edits'].reverse(),lambda v:v['edits'].append(v['edits'][0]),lambda v:v['edits'][0].update(word=True),lambda v:v['edits'][0].update(palette_index=16),lambda v:v.update(current_tim_sha256='0'*64),lambda v:v['source_record'].update(byte_offset=0)]:
   bad=deepcopy(owner);changes(bad)
   with self.assertRaises(ImportError):effective(original,catalog,record,bad)
  for args in [(True,0,0),(0,False,0),(0,0,True),(16,0,0),(0,16,0),(0,0,65536),(0,0,-1)]:
   with self.assertRaises(ImportError):project(original,catalog,record,None,*args)
  altered=bytearray(original);altered[-1]^=1
  with self.assertRaises(ImportError):source(bytes(altered),catalog,record)


if __name__=='__main__':unittest.main()
