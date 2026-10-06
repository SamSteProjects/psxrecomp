import os,unittest
from hashlib import sha256
from importer.audio_sequence import inspect_sequence
from importer.audio_catalog import load_audio_asset_catalog,read_audio_sequence
from importer.core import ImportError
from test_audio_catalog import seq


def source(events):return seq()[:15]+events


class AudioSequence(unittest.TestCase):
    def test_running_status_and_tempo_preserve_source_time(self):
        raw=source(bytes([0,0x90,60,100,0x83,0x60,61,0,0,0xff,0x51,0x0f,0x42,0x40,0x83,0x60,62,100,0,0xff,0x2f]))
        r=inspect_sequence(raw);self.assertTrue(r['complete']);self.assertEqual(r['decoded_ticks'],960)
        self.assertEqual([e['time_seconds'] for e in r['events']],[0,.5,.5,1.5,1.5])
        self.assertEqual([e['running_status'] for e in r['events']],[False,True,False,True,False])
        self.assertEqual([e['kind'] for e in r['events']],['note_on','note_on','set_tempo','note_on','end_of_track'])
        self.assertEqual(r['decoded_byte_end'],len(raw));self.assertIsNone(r['stop_reason'])

    def test_all_channel_message_shapes_keep_encoded_operands(self):
        raw=source(bytes([0,0x80,1,2,0,0xa1,3,4,0,0xb2,5,6,0,0xc3,7,0,0xd4,8,0,0xe5,9,10,0,0xff,0x2f]))
        r=inspect_sequence(raw);self.assertTrue(r['complete']);self.assertEqual(r['channels'],[0,1,2,3,4,5])
        self.assertEqual([e['values'] for e in r['events']],[[1,2],[3,4],[5,6],[7],[8],[9,10],[]])

    def test_unknown_and_truncated_stop_without_synthesizing_terminators(self):
        prefixes=[bytes([0,0xff,0x7f,0,0xff,0x2f]),bytes([0,0xf0,0,0xff,0x2f]),bytes([0,0x90,60]),bytes([0,0x90,128,1]),bytes([128]*5),bytes([0,0xff,0x51,0,0,0])]
        for tail in prefixes:
            r=inspect_sequence(source(bytes([0,0xc0,2])+tail));self.assertFalse(r['complete']);self.assertEqual(r['event_count'],1)
            self.assertEqual(r['stop_offset'],18);self.assertEqual(r['events'][0]['kind'],'program_change');self.assertTrue(r['stop_reason'])
        r=inspect_sequence(source(bytes([0,60,100])));self.assertFalse(r['complete']);self.assertEqual(r['event_count'],0)
        r=inspect_sequence(source(bytes([0,0xc0,2])),max_events=1);self.assertFalse(r['complete'])
        r=inspect_sequence(source(bytes([0,0xc0,2,0,0xff,0x2f])),max_events=1);self.assertEqual(r['stop_reason'],'Event budget reached')
        with self.assertRaises(ImportError):inspect_sequence(source(b''),max_events=True)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_retail_carrier_and_prefix_metadata_are_source_qualified(self):
        disc=os.environ['LEGAIA_DISC_BIN'];catalog=load_audio_asset_catalog(disc,'town01')
        row=next(x for x in catalog['assets'] if x['semantic_id']=='audio://legaia/prot/0877')
        body,source_record=read_audio_sequence(disc,row['semantic_id'],row['source_record']['sha256'])
        self.assertEqual(sha256(body).hexdigest(),source_record['sequence_sha256'])
        self.assertEqual(source_record['sequence_sha256'],row['chunks'][2]['sha256'])
        r=inspect_sequence(body);self.assertGreater(r['event_count'],100);self.assertTrue(r['complete'])
        with self.assertRaisesRegex(ImportError,'hash'):read_audio_sequence(disc,row['semantic_id'],'f'*64)
        partial=next(x for x in catalog['assets'] if not x['container_validated'])
        with self.assertRaises(ImportError):read_audio_sequence(disc,partial['semantic_id'],partial['source_record']['sha256'])

if __name__=='__main__':unittest.main()
