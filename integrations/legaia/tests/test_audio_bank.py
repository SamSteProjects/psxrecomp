import os,struct,unittest
from importer.audio_bank import inspect_bank,bank_from_entry,read_audio_bank
from importer.audio_catalog import load_audio_asset_catalog
from importer.core import ImportError
from importer.pipeline import _disc_context
from test_audio_catalog import bank,chunk


def source_bank():
    raw=bytearray(3120);raw[:32]=bank(3120);raw[32+12*16]=1
    struct.pack_into('<hh',raw,2080+20,12,1);struct.pack_into('<H',raw,2592+2,2)
    return bytes(raw)


class AudioBank(unittest.TestCase):
    def test_sparse_slots_and_packed_pages_remain_distinct(self):
        r=inspect_bank(source_bank());self.assertEqual(r['used_program_slots'],[12]);self.assertTrue(r['declared_program_count_matches_used_slots'])
        self.assertEqual(r['tones'][0]['page'],0);self.assertEqual(r['tones'][0]['program_operand'],12)
        self.assertEqual(r['tones'][0]['sample_index'],0);self.assertIsNone(r['tones'][1]['sample_index'])
        self.assertEqual(r['samples'][0]['offset'],3104);self.assertEqual(r['samples'][0]['size_bytes'],16)
        self.assertEqual(r['samples'][0]['table_index'],1);self.assertEqual(r['remaining_bank_bytes'],0)

    def test_fixed_sections_and_sample_sizes_cannot_borrow_neighbor_bytes(self):
        for field,value in ((12,3103),(2594,3)):
            raw=bytearray(source_bank());struct.pack_into('<I' if field==12 else '<H',raw,field,value)
            with self.assertRaises(ImportError):inspect_bank(bytes(raw))
        raw=bytearray(source_bank());raw[32]=17
        with self.assertRaises(ImportError):inspect_bank(bytes(raw))
        with self.assertRaises(ImportError):inspect_bank(source_bank()[:-1])

    def test_contiguous_and_split_carriers_qualify_without_sequence_assumptions(self):
        raw=source_bank()
        for carrier,kind in ((raw,'standalone-vab'),(chunk(0,raw),'leading-contiguous-vab-chunk'),(chunk(0,raw[:3104])+chunk(1,raw[3104:])+bytes(16),'split-vab-header-samples')):
            actual,pieces,decoded_kind=bank_from_entry(carrier);self.assertEqual(actual,raw);self.assertEqual(decoded_kind,kind)
            self.assertEqual(sum(p['size_bytes'] for p in pieces),len(raw));self.assertEqual(pieces[0]['bank_offset'],0)
        with self.assertRaises(ImportError):bank_from_entry(chunk(0,raw[:3104])+chunk(1,raw[3104:-4]))
        # Nonzero size-table spacer stays an uninterpreted source word.
        changed=bytearray(raw);struct.pack_into('<H',changed,2592,9)
        self.assertEqual(inspect_bank(bytes(changed))['sample_table_spacer'],9)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_all_retail_bank_carriers_keep_independent_coverage(self):
        disc=os.environ['LEGAIA_DISC_BIN'];reports=[];unavailable=[]
        with _disc_context(disc):
            r=load_audio_asset_catalog(disc,'town01')
            for row in r['assets']:
                if row['bank_inspection']['status']!='available':unavailable.append(row);continue
                bank=read_audio_bank(disc,row['semantic_id'],row['source_record']['sha256']);self.assertEqual(bank['bank_sha256'],row['bank_inspection']['bank_sha256']);reports.append(bank)
        self.assertEqual(len(reports),202);self.assertEqual(len(unavailable),16)
        self.assertTrue(all(x['declared_program_count_matches_used_slots'] for x in reports))
        self.assertTrue(all(x['remaining_bank_bytes']==0 for x in reports))
        row=next(x for x in r['assets'] if x['semantic_id']=='audio://legaia/prot/0877')
        with self.assertRaisesRegex(ImportError,'hash'):read_audio_bank(disc,row['semantic_id'],'f'*64)

if __name__=='__main__':unittest.main()
