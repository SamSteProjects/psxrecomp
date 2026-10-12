import os,json,struct,unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from importer.field_texture_authoring import load_field_texture_authoring_context
from importer.texture_authoring import patch_tim_palette_word
from importer.core import ImportError,decompress_lzs,parse_lzs_sections
from importer.pipeline import _disc_context

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class FieldTextureAuthoringTests(unittest.TestCase):
 def test_original_members_palette_projection_and_protected_sections(self):
  disc=os.environ['LEGAIA_DISC_BIN'];context=load_field_texture_authoring_context(disc);proof=[];combined={}
  with _disc_context(disc) as (_,_,_,archive):
   entry=archive.entry(874);raw=archive.read_entry(entry,extended=True);sections=parse_lzs_sections(raw);s=sections[2];bank,consumed=decompress_lzs(raw[s.stream_offset:],s.decoded_size);location=(archive.node.extent_lba+entry.start_lba)*2048;originals=[decompress_lzs(raw[x.stream_offset:],x.decoded_size)[0] for x in sections[:2]]
   for slot in range(8):
    identifier=f'texture://legaia/field-party/874/2/{slot}';options=context.options(identifier);self.assertTrue(options['supported'],options);source=context.original_tim(identifier);self.assertEqual(context.patch({identifier:source}),([],[]));word=struct.unpack_from('<H',source,22)[0];candidate=patch_tim_palette_word(source,sha256(source).hexdigest(),0,1,word^1);combined[identifier]=candidate;validated=context.validate_replacement(identifier,candidate);self.assertTrue(validated['palette_changed']);self.assertFalse(validated['image_changed'])
    try:overlays,audit=context.patch({identifier:candidate})
    except ImportError as e:
     self.assertIn('compressed',str(e).lower());proof.append(dict(slot=slot,capacity_refused=True,reason=str(e)));continue
    self.assertEqual(len(overlays),1);o=overlays[0];self.assertEqual(o['offset'],location+s.stream_offset);self.assertEqual(o['size'],consumed);rewritten=bytearray(raw);rewritten[s.stream_offset:s.stream_offset+consumed]=o['payload'];new=decompress_lzs(o['payload'],s.decoded_size)[0];start=options['source_record']['byte_offset'];self.assertEqual(new[start:start+len(candidate)],candidate);self.assertEqual(new[:start],bank[:start]);self.assertEqual(new[start+len(candidate):],bank[start+len(candidate):]);self.assertEqual(rewritten[:s.stream_offset],raw[:s.stream_offset]);self.assertEqual(rewritten[s.stream_offset+consumed:],raw[s.stream_offset+consumed:]);self.assertEqual([decompress_lzs(rewritten[x.stream_offset:],x.decoded_size)[0] for x in sections[:2]],originals);proof.append(dict(slot=slot,capacity_refused=False,changed_words=1,other_members_and_sections_exact=True))
   overlays,audit=context.patch(combined);self.assertEqual(len(overlays),1);self.assertEqual(len(audit),8);new=decompress_lzs(overlays[0]['payload'],s.decoded_size)[0];allowed=set()
   for identifier,candidate in combined.items():
    r=context.options(identifier)['source_record'];start=r['byte_offset'];self.assertEqual(new[start:start+len(candidate)],candidate);allowed.update(range(start+22,start+24))
   self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(bank,new))))
   with patch('importer.serialization.compress_lzs',return_value=bytes(consumed+1)),patch('importer.lzs_optimal.compress_lzs_optimal',return_value=bytes(consumed+1)):
    with self.assertRaisesRegex(ImportError,'compressed'):context.build_patch(combined)
   bad=bytearray(source);bad[4]^=1
   with self.assertRaises(ImportError):context.validate_replacement(identifier,bytes(bad))
  output=os.getenv('LEGAIA_FIELD_TIM_PROOF')
  if output:Path(output).write_text(json.dumps(dict(members=proof,combined_eight_member_readback=True,capacity_refusal=True,gameplay_verified=False),indent=2),encoding='utf-8')
