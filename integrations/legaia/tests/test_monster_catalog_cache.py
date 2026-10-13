"""Source identity and copy isolation for derived Retail archive metadata."""
from copy import deepcopy
from hashlib import sha256
import os,time,unittest
from unittest.mock import patch
from importer import monster_archive as native
from importer.core import ImportError


class MonsterCatalogCacheTests(unittest.TestCase):
 def setUp(self):native._catalog_cache=None
 def tearDown(self):native._catalog_cache=None

 def test_full_source_disc_identity_and_returned_metadata_are_isolated(self):
  source=b'archive-one';disc='a'*64
  def decode(data,identity):return dict(animations=[],records=[dict(name='Original')],source_disc_sha256=identity,source_archive_sha256=sha256(data).hexdigest())
  with patch.object(native,'_decode_catalog_uncached',side_effect=decode) as parser:
   first=native.decode_catalog(source,disc);original=deepcopy(first);first['records'][0]['name']='Edited';first['animations'].append('foreign')
   self.assertEqual(native.decode_catalog(bytes(source),disc),original);self.assertEqual(parser.call_count,1)
   self.assertNotEqual(native.decode_catalog(source+b'changed',disc)['source_archive_sha256'],original['source_archive_sha256']);self.assertEqual(parser.call_count,2)
   self.assertEqual(native.decode_catalog(source,'b'*64)['source_disc_sha256'],'b'*64);self.assertEqual(parser.call_count,3)
   native.decode_catalog(source,disc);self.assertEqual(parser.call_count,4)
   for data,identity in [(bytearray(source),disc),(b'bad',disc),(source,'bad'),(source,'A'*64)]:
    with self.assertRaises(ImportError):native.decode_catalog(data,identity)
   self.assertEqual(parser.call_count,4)

 @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
 def test_real_catalog_matches_uncached_and_altered_source_requalifies(self):
  from importer.pipeline import _disc_context
  with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,disc,_,archive):raw=archive.read_entry(archive.entry(867))
  started=time.perf_counter();expected=native._decode_catalog_uncached(raw,disc);cold=time.perf_counter()-started
  native.decode_catalog(raw,disc);started=time.perf_counter();cached=native.decode_catalog(raw,disc);warm=time.perf_counter()-started
  self.assertEqual(cached,expected);self.assertEqual(len(cached['models']),186);self.assertEqual(len(cached['animations']),1811)
  cached['records'][0]['stored_stats']['hp']+=1
  self.assertEqual(native.decode_catalog(raw,disc),expected)
  changed=raw[:-1]+bytes([raw[-1]^1]);different=native.decode_catalog(changed,disc)
  self.assertNotEqual(different['source_key'],expected['source_key'])
  self.assertEqual(different,native._decode_catalog_uncached(changed,disc))
  print(f'Retail catalog equality/isolation/invalidation passed; uncached {cold:.3f}s, warm {warm:.3f}s (observed, not a threshold)')


if __name__=='__main__':unittest.main()
