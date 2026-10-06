import os,unittest
from importer.audio_waveform import inspect_waveform,read_audio_waveform
from importer.audio_bank import read_audio_bank
from importer.audio_catalog import load_audio_asset_catalog
from importer.core import ImportError

def block(header=0,flags=0,data=0):return bytes([header,flags])+bytes([data])*14

class WaveformTests(unittest.TestCase):
    def test_signed_low_nibble_first_and_cross_block_history(self):
        r=inspect_waveform(block(0,0,0x81)+block(0x10,1,0))
        self.assertEqual(r['decoded_frames'],56);self.assertEqual(r['termination'],dict(reason='encoded-end',byte_offset=16))
        self.assertEqual([(b['minimum'],b['maximum']) for b in r['bins'][:2]],[(4096,4096),(-32768,-32768)])
        self.assertEqual(r['bins'][28]['minimum'],-30720)

    def test_source_stops_do_not_synthesize_silence_or_replay(self):
        for body,reason,frames in [(b'','source-span-exhausted',0),(bytes(8),'incomplete-block',0),(block(0x70),'unknown-predictor',0),(block(0,8),'unknown-flag-bits',0),(block(0,7)+block(),'encoded-end',28)]:
            r=inspect_waveform(body);self.assertEqual(r['termination']['reason'],reason);self.assertEqual(r['decoded_frames'],frames)
        r=inspect_waveform(block()*4097);self.assertEqual(r['termination']['reason'],'preview-budget');self.assertEqual(r['decoded_frames'],114688);self.assertLessEqual(len(r['bins']),512)
        for shift in (13,14,15):
            r=inspect_waveform(block(shift,1,0x11));self.assertEqual(r['bins'][0]['minimum'],8);self.assertEqual(r['markers'][0]['effective_shift'],9)
        with self.assertRaises(ImportError):inspect_waveform(bytearray(16))

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source not configured')
    def test_source_bank_sample_bindings(self):
        disc=os.environ['LEGAIA_DISC_BIN'];row=next(r for r in load_audio_asset_catalog(disc,'town01')['assets'] if r['semantic_id']=='audio://legaia/prot/0877');bank=read_audio_bank(disc,row['semantic_id'],row['source_record']['sha256']);sample=bank['samples'][0]
        args=[disc,row['semantic_id'],row['source_record']['sha256'],bank['bank_sha256'],0,sample['source_sha256']]
        r=read_audio_waveform(*args);self.assertEqual(r['source_sha256'],sample['source_sha256']);self.assertGreater(r['decoded_frames'],0)
        for position,value in ((2,'f'*64),(3,'f'*64),(4,True),(4,255),(5,'f'*64)):
            invalid=args.copy();invalid[position]=value
            with self.assertRaises(ImportError):read_audio_waveform(*invalid)

if __name__=='__main__':unittest.main()
