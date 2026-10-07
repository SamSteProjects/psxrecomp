"""Allocation boundaries and complete independent native carrier expectations."""
from hashlib import sha256
import os,struct,unittest
from importer.core import ImportError
from importer.audio_bank import bank_from_entry,inspect_bank
from importer.audio_sample_allocation import allocate_sample_wav,repack_audio_samples,allocate_audio_sample_wav
from importer.audio_sample_authoring import read_allocation_pcm_wav,read_pcm_wav
from importer.pipeline import _disc_context
import test_audio_sample_authoring as fixed
from test_audio_bank import source_bank
from test_audio_catalog import chunk,seq

def digest(body):return sha256(body).hexdigest()

def bank_fixture():
    prefix=bytearray(source_bank()[:3104]);samples=(fixed.block()+fixed.block(1)+bytes(8),fixed.block(1,data=0x23),fixed.block(4)+fixed.block(3))
    struct.pack_into('<H',prefix,22,3)
    struct.pack_into('<4H',prefix,2592,11,5,2,4)
    struct.pack_into('<H',prefix,2592+20,123) # opaque unused size word
    result=prefix+b''.join(samples)+b'BANKTAIL'
    struct.pack_into('<I',result,12,len(result))
    return bytes(result),samples

class SampleAllocation(unittest.TestCase):
    def test_new_frame_counts_end_tail_determinism_and_independent_pcm(self):
        source=fixed.block()+fixed.block(1)+b'opaque!!'
        current=source
        for count in (28,84,56):
            frames=[(i*337)%22000-11000 for i in range(count)];wav=fixed.wav(frames,32000)
            candidate,audit=allocate_sample_wav(source,current,wav,expected_source_sha256=digest(source),expected_current_sha256=digest(current))
            self.assertEqual(len(candidate),count//28*16+8);self.assertEqual(candidate[-8:],source[-8:])
            self.assertEqual(candidate[1:count//28*16:16],bytes(count//28-1)+b'\1')
            values=fixed.independent_decode(candidate[:-8]);errors=[a-b for a,b in zip(frames,values)]
            self.assertEqual(audit['decoded_pcm_sha256'],digest(struct.pack('<'+str(count)+'h',*values)))
            self.assertEqual(audit['sum_squared_error'],sum(v*v for v in errors));self.assertEqual(audit['maximum_absolute_error'],max(map(abs,errors)))
            self.assertEqual(audit['decoded_frames'],count);self.assertEqual(audit['size_delta_bytes'],len(candidate)-len(current))
            self.assertIsNone(audit['native_sample_rate'])
            self.assertEqual(allocate_sample_wav(source,current,wav,expected_source_sha256=digest(source),expected_current_sha256=digest(current)),(candidate,audit))
            current=candidate

    def test_loop_unknown_flags_incomplete_budget_and_changed_tail_refuse(self):
        good=fixed.block(1)+b'tailtail';wav=fixed.wav([1]*28)
        for bad in (b'',fixed.block(),fixed.block(3),fixed.block(5),fixed.block(2)+fixed.block(1),fixed.block(8),fixed.block(1,0x70),fixed.block()*4096+fixed.block(1)):
            with self.assertRaises(ImportError):allocate_sample_wav(bad,bad,wav,expected_source_sha256=digest(bad),expected_current_sha256=digest(bad))
        bad=good[:-1]+b'X'
        with self.assertRaises(ImportError):allocate_sample_wav(good,bad,wav,expected_source_sha256=digest(good),expected_current_sha256=digest(bad))
        with self.assertRaises(ImportError):allocate_sample_wav(good,good,wav,expected_source_sha256='f'*64,expected_current_sha256=digest(good))

    def test_source_start_markers_keep_exact_block_ordinals_and_cannot_be_cut(self):
        source=fixed.block()+fixed.block(4)+fixed.block()+fixed.block(1)
        for blocks in (3,5):
            candidate,audit=allocate_sample_wav(source,source,fixed.wav([500]*(blocks*28)),expected_source_sha256=digest(source),expected_current_sha256=digest(source))
            self.assertEqual(candidate[1:blocks*16:16],bytes((0,4))+bytes(blocks-3)+b'\1')
            self.assertEqual(audit['preserved_start_blocks'],[1])
        for blocks in (1,2):
            with self.assertRaises(ImportError):allocate_sample_wav(source,source,fixed.wav([0]*(blocks*28)),expected_source_sha256=digest(source),expected_current_sha256=digest(source))
        changed=source[:17]+b'\0'+source[18:]
        with self.assertRaises(ImportError):allocate_sample_wav(source,changed,fixed.wav([0]*112),expected_source_sha256=digest(source),expected_current_sha256=digest(changed))
        bank,_=bank_fixture()
        with self.assertRaises(ImportError):repack_audio_samples(bank,{0:fixed.block(4)+fixed.block(1)+bytes(8)},expected_entry_sha256=digest(bank))

    def test_new_wav_contract_preserves_fixed_exact_frames(self):
        for count in (28,56,114688):
            body=fixed.wav([0]*count);self.assertEqual(len(read_allocation_pcm_wav(body)[0]),count*2)
        for count in (0,1,27,29,114716):
            with self.assertRaises(ImportError):read_allocation_pcm_wav(fixed.wav([0]*count))
        with self.assertRaises(ImportError):read_pcm_wav(fixed.wav([0]*56),28)
        with self.assertRaises(ImportError):read_pcm_wav(fixed.wav([0]*28),None)
        with self.assertRaises(ImportError):read_allocation_pcm_wav(fixed.wav([0]*28,7999))

    def test_three_carriers_whole_expected_bytes_and_multiple_ordinal_moves(self):
        bank,samples=bank_fixture();table_end=3104
        suffix=chunk(2,seq())+b'opaque-entry-tail'
        # Leading contiguous chunk has opaque bytes inside its declared chunk.
        entries=(bank+suffix,chunk(0,bank+b'HEADTAIL')+suffix,chunk(0,bank[:table_end])+chunk(1,bank[table_end:])+suffix)
        replacements={0:fixed.block()+fixed.block()+fixed.block(1)+bytes(8),1:fixed.block()+fixed.block(1,data=0x56)}
        prefix=bytearray(bank[:table_end]);struct.pack_into('<HH',prefix,2594,7,4)
        expected_bank=prefix+replacements[0]+replacements[1]+samples[2]+b'BANKTAIL'
        struct.pack_into('<I',expected_bank,12,len(expected_bank));expected_bank=bytes(expected_bank)
        expected_entries=(expected_bank+suffix,chunk(0,expected_bank+b'HEADTAIL')+suffix,chunk(0,expected_bank[:table_end])+chunk(1,expected_bank[table_end:])+suffix)
        for original,expected in zip(entries,expected_entries):
            candidate,audit=repack_audio_samples(original,replacements,expected_entry_sha256=digest(original))
            self.assertEqual(candidate,expected);reopened,_,_=bank_from_entry(candidate);self.assertEqual(reopened,expected_bank)
            self.assertEqual(audit['size_delta_bytes'],32);self.assertEqual(audit['samples'][2]['before_sha256'],audit['samples'][2]['after_sha256'])
            self.assertEqual(audit['samples'][2]['after_bank_byte_offset']-audit['samples'][2]['before_bank_byte_offset'],32)
            self.assertFalse(audit['gameplay_verified'])
            # Repacking the same selected spans is a byte-identical no-op.
            self.assertEqual(repack_audio_samples(candidate,replacements,expected_entry_sha256=digest(candidate))[0],candidate)

    def test_effective_bank_parameters_sequence_and_fixed_neighbor_survive(self):
        bank,samples=bank_fixture();entry=chunk(0,bank[:3104])+chunk(1,bank[3104:])+chunk(2,seq())+bytes(32)
        current=bytearray(entry);current[4+24]=83 # effective master volume
        current[4+32+12*16+1]=71 # effective program volume
        current[-36]=42 # effective SEQ/opaque suffix byte
        current=bytes(current);current_bank,_,_=bank_from_entry(current)
        output,audit=allocate_audio_sample_wav(entry,current,fixed.wav([500]*84),expected_source_sha256=digest(entry),
            expected_current_sha256=digest(current),expected_bank_sha256=digest(bank),sample_index=0,
            expected_sample_sha256=digest(samples[0]),expected_current_sample_sha256=digest(samples[0]))
        replacement=allocate_sample_wav(samples[0],samples[0],fixed.wav([500]*84),expected_source_sha256=digest(samples[0]),expected_current_sha256=digest(samples[0]))[0]
        prefix=bytearray(current_bank[:3104]);struct.pack_into('<H',prefix,2594,len(replacement)//8)
        expected_bank=prefix+replacement+samples[1]+samples[2]+b'BANKTAIL';struct.pack_into('<I',expected_bank,12,len(expected_bank))
        expected=chunk(0,bytes(expected_bank[:3104]))+chunk(1,bytes(expected_bank[3104:]))+current[4+3104+4+len(bank)-3104:]
        self.assertEqual(output,expected);self.assertEqual(audit['source_entry_sha256'],digest(entry))
        # A later resize uses Current table offsets, even after an earlier ordinal grew.
        second,audit2=allocate_audio_sample_wav(entry,output,fixed.wav([700]*56),expected_source_sha256=digest(entry),
            expected_current_sha256=digest(output),expected_bank_sha256=digest(bank),sample_index=1,
            expected_sample_sha256=digest(samples[1]),expected_current_sample_sha256=digest(samples[1]))
        now,_,_=bank_from_entry(second);rows=inspect_bank(now)['samples']
        self.assertEqual(now[rows[0]['offset']:rows[0]['offset']+rows[0]['size_bytes']],replacement)
        self.assertEqual(rows[1]['size_bytes'],32);self.assertEqual(rows[2]['source_sha256'],digest(samples[2]))

    def test_invalid_mapping_tail_hash_and_split_table_boundary_refuse(self):
        bank,samples=bank_fixture();good=fixed.block(1)+bytes(8)
        for mapping in ({},{True:good},{3:good},{0:bytearray(good)},{0:good[:-1]},{0:fixed.block(3)+bytes(8)},{0:fixed.block(1)+b'bad-tail'}):
            with self.assertRaises(ImportError):repack_audio_samples(bank,mapping,expected_entry_sha256=digest(bank))
        with self.assertRaises(ImportError):repack_audio_samples(bank,{0:good},expected_entry_sha256='f'*64)
        split=chunk(0,bank[:3120])+chunk(1,bank[3120:])
        with self.assertRaises(ImportError):repack_audio_samples(split,{0:good},expected_entry_sha256=digest(split))

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_retail_sound_pack_grow_shrink_whole_neighbors_and_sequence(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,archive):
            start,end=archive.toc[879:881];entry=image.read_user(archive.node.extent_lba,start*2048,(end-start)*2048,archive.node.size)
        bank,pieces,kind=bank_from_entry(entry);report=inspect_bank(bank);row=report['samples'][0];source=bank[row['offset']:row['offset']+row['size_bytes']]
        source_frames=fixed.independent_decode(source);current=entry
        for count in (len(source_frames)+28,84):
            frames=[source_frames[i%len(source_frames)]//2 for i in range(count)]
            candidate,audit=allocate_audio_sample_wav(entry,current,fixed.wav(frames),expected_source_sha256=digest(entry),
                expected_current_sha256=digest(current),expected_bank_sha256=digest(bank),sample_index=0,
                expected_sample_sha256=digest(source),expected_current_sample_sha256=inspect_bank(bank_from_entry(current)[0])['samples'][0]['source_sha256'])
            rebuilt,new_pieces,new_kind=bank_from_entry(candidate);self.assertEqual(kind,new_kind);new=inspect_bank(rebuilt)
            prefix=bytearray(bank[:row['offset']]);replacement=rebuilt[new['samples'][0]['offset']:new['samples'][0]['offset']+new['samples'][0]['size_bytes']]
            struct.pack_into('<I',prefix,12,len(rebuilt));struct.pack_into('<H',prefix,report['sections']['sample_table_offset']+2,len(replacement)//8)
            expected=bytes(prefix)+replacement+bank[row['offset']+row['size_bytes']:]
            self.assertEqual(rebuilt,expected)
            for old,now in zip(report['samples'][1:],new['samples'][1:]):self.assertEqual(old['source_sha256'],now['source_sha256'])
            self.assertEqual(candidate[new_pieces[-1]['entry_offset']+new_pieces[-1]['size_bytes']:],entry[pieces[-1]['entry_offset']+pieces[-1]['size_bytes']:])
            values=fixed.independent_decode(replacement);self.assertEqual(len(values),count)
            self.assertEqual(audit['sample']['decoded_pcm_sha256'],digest(struct.pack('<'+str(count)+'h',*values)))
            current=candidate

if __name__=='__main__':unittest.main()
