"""Focused structural audio checks; no game launch or playback."""
import os, struct, unittest
from importer.audio_catalog import decode_audio_entry, load_audio_asset_catalog
from importer.core import ImportError, validate_metadata_only
from sdk.project import AssetDatabase
from sdk.inspector_schema import inspector_schema


def bank(size=64):
    b=bytearray(32);b[:4]=b'pBAV';struct.pack_into('<III',b,4,7,1,size)
    struct.pack_into('<HHH',b,18,1,2,1);return bytes(b)


def seq(legaia=True):
    version=b'\0\0\0\1' if legaia else b'\0\1'
    return b'pQES'+version+struct.pack('>H',480)+(500000).to_bytes(3,'big')+bytes([4,2])+b'\0\xff\x2f'


def chunk(kind,body):
    body=body+b'\0'*((-len(body))%4)
    return struct.pack('<I',kind<<24|len(body))+body


class AudioCatalog(unittest.TestCase):
    def test_complete_pack_uses_bounded_source_chunks(self):
        raw=chunk(0,bank())+chunk(1,bytes(32))+chunk(2,seq())
        r=decode_audio_entry(raw);self.assertTrue(r['declared_bank_complete'])
        self.assertEqual(r['bank']['program_count'],1);self.assertEqual(r['sequence']['ppqn'],480)
        self.assertEqual([(c['kind'],c['payload_offset'],c['size_bytes']) for c in r['chunks']],[(0,4,32),(1,40,32),(2,76,20)])
        self.assertFalse(r['sequence']['event_stream_validated']);validate_metadata_only(r)
        # The terminator's declared body cannot borrow following bytes.
        with self.assertRaises(ImportError):decode_audio_entry(raw[:-1])
        broken=bytearray(raw);struct.pack_into('<I',broken,36,3<<24|32)
        with self.assertRaises(ImportError):decode_audio_entry(bytes(broken))

    def test_header_variants_and_partial_bank_are_explicit(self):
        for legaia in (False,True):
            r=decode_audio_entry(seq(legaia));self.assertEqual(r['sequence']['header_size'],15 if legaia else 13)
            self.assertEqual(r['sequence']['initial_tempo_us_per_quarter'],500000)
        self.assertFalse(decode_audio_entry(bank())['declared_bank_complete'])
        self.assertTrue(decode_audio_entry(bank()+bytes(32))['declared_bank_complete'])
        for raw in (b'pQES',b'xxpQES'+bytes(20),bytes(32)):
            with self.assertRaises(ImportError):decode_audio_entry(raw)

    def test_unaligned_walk_and_invalid_headers_reject(self):
        raw=chunk(0,bank())+chunk(1,bytes(32))+chunk(2,seq())
        malformed=bytearray(raw);struct.pack_into('<I',malformed,36,1<<24|31)
        with self.assertRaises(ImportError):decode_audio_entry(bytes(malformed))
        for offset,value in ((18,0),(22,256)):
            bad=bytearray(bank());struct.pack_into('<H',bad,offset,value)
            with self.assertRaises(ImportError):decode_audio_entry(bytes(bad))
        bad=bytearray(seq());bad[8:10]=b'\0\0'
        with self.assertRaises(ImportError):decode_audio_entry(bytes(bad))

    def test_audio_registration_and_inspector_are_read_only(self):
        db=AssetDatabase();r=db.register_resources('scene://town01','a'*64,[dict(semantic_id='audio://legaia/prot/0877',asset_kind='audio',name='Source audio')],[])
        self.assertEqual(r['records'][0]['kind'],'audio')
        schema=inspector_schema();self.assertEqual(schema['asset_inspectors']['audio'],'AssetAudio')
        self.assertEqual([a['id'] for a in schema['components']['AssetAudio']['actions']],['inspect-audio-sequence'])
        self.assertTrue(all('authoring' not in p for p in schema['components']['AssetAudio']['properties']))

    def test_unresolved_headers_do_not_borrow_outside_declared_chunk(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch
        class Image:
            def __init__(self,raw):self.raw=raw;self.reads=[]
            def read_user(self,lba,offset,size,limit):
                self.reads.append((offset,size));return self.raw[offset:offset+size]
        archive=SimpleNamespace(entries=[SimpleNamespace(index=0)],toc=[0,0,0,1],
                                node=SimpleNamespace(extent_lba=0,size=2048))
        for declared,available in ((31,False),(32,True)):
            image=Image((struct.pack('<I',declared)+bank()).ljust(2048,b'\0'))
            with patch('importer.audio_catalog._disc_context',return_value=nullcontext((image,'a'*64,{0:'source'},archive))):
                r=load_audio_asset_catalog('fixture','town01')
            self.assertEqual(image.reads,[(0,8),(0,2048)])
            self.assertEqual(r['asset_count'],int(available))
            if available:
                self.assertFalse(r['assets'][0]['container_validated'])
                self.assertIsNone(r['assets'][0]['sequence'])
            else:self.assertEqual(len(r['unavailable_entries']),1)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_retail_full_archive_discovery_keeps_partial_evidence(self):
        r=load_audio_asset_catalog(os.environ['LEGAIA_DISC_BIN'],'town01')
        self.assertEqual(r['scanned_entry_count'],1233);self.assertEqual(r['asset_count'],218)
        self.assertEqual(r['partial_container_count'],135);self.assertEqual(r['unavailable_entries'],[])
        self.assertEqual(len({x['semantic_id'] for x in r['assets']}),218)
        packs=[x for x in r['assets'] if x['container_validated']]
        self.assertEqual(len(packs),83)
        self.assertTrue(all(x['declared_bank_complete'] for x in packs))
        self.assertTrue(set(range(877,886))<={x['source_record']['prot_entry_index'] for x in packs})
        for row in r['assets']:
            self.assertEqual(row['source_record']['boundary'],'physical-next-TOC-entry')
            self.assertEqual(row['playback_assignment'],'unknown');self.assertFalse(row['preview_supported'])
            if not row['container_validated']:
                self.assertIsNone(row['sequence']);self.assertIsNone(row['declared_bank_complete'])
                self.assertTrue(row['structural_limitations'])
        validate_metadata_only(r)

if __name__=='__main__':unittest.main()
