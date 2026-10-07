"""Whole audio owner relocation and shared archive composition qualification."""
import os,struct,unittest
from hashlib import sha256
from importer.core import ImportError
from importer.audio_bank_growth import rebuild_audio_bank_entry
from importer.audio_sample_allocation import repack_audio_samples,allocate_audio_sample_wav
from importer.audio_bank import bank_from_entry,inspect_bank
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from importer.pipeline import _disc_context
import test_audio_sample_allocation as allocation
import test_audio_sample_authoring as fixed
from test_audio_catalog import chunk,seq

def digest(body):return sha256(body).hexdigest()

def fixture():
    bank,samples=allocation.bank_fixture()
    entry=(chunk(0,bank[:3104])+chunk(1,bank[3104:])+chunk(2,seq())+b'OPAQUE').ljust(4096,b'\0')
    header=bytearray(2048);struct.pack_into('<ii',header,4,6,1);struct.pack_into('<6I',header,16,1,3,5,6,7,0)
    source=bytes(header)+entry+entry+b'A'*2048+b'B'*2048+b'Z'*(8*2048)
    replacement=fixed.block()*149+fixed.block(1)+bytes(8)
    candidate,audit=repack_audio_samples(entry,{0:replacement},expected_entry_sha256=digest(entry))
    return source,entry,candidate

def request(index,entry,candidate):return dict(kind='audio-sample-bank',entry_index=index,expected_entry_sha256=digest(entry),candidate=candidate)

class AudioBankGrowth(unittest.TestCase):
    def test_whole_owner_growth_toc_neighbor_and_shrink_keeps_physical_size(self):
        source,entry,candidate=fixture()
        output,audit=rebuild_audio_bank_entry(source,digest(source),0,digest(entry),candidate)
        size=len(candidate)+(-len(candidate)%2048);delta=size-len(entry)
        self.assertEqual(output[2048:2048+len(candidate)],candidate)
        self.assertEqual(output[2048+len(candidate):2048+size],bytes(size-len(candidate)))
        self.assertEqual(output[2048+size:],source[2048+len(entry):])
        before=_archive(source);after=_archive(output)
        self.assertEqual(after.entry(0).start_lba,before.entry(0).start_lba)
        for index in (1,2,3):self.assertEqual(after.entry(index).start_lba,before.entry(index).start_lba+delta//2048)
        self.assertEqual(audit['archive']['growth_sectors'],delta//2048);self.assertTrue(audit['reopened_audio_bank_verified'])
        smaller,_=repack_audio_samples(entry,{0:fixed.block(1)+bytes(8)},expected_entry_sha256=digest(entry))
        shrunk,proof=rebuild_audio_bank_entry(source,digest(source),0,digest(entry),smaller)
        self.assertEqual(len(shrunk),len(source));self.assertEqual(_archive(shrunk).toc,before.toc)
        self.assertEqual(shrunk[2048:2048+len(smaller)],smaller);self.assertEqual(shrunk[2048+len(smaller):6144],bytes(4096-len(smaller)))
        self.assertEqual(shrunk[6144:],source[6144:]);self.assertEqual(proof['archive']['growth_sectors'],0)

    def test_composition_two_audio_owners_and_external_patch_survive(self):
        source,entry,candidate=fixture();offset=5*2048+9;patch=b'EDIT'
        output,audit=compose_model_pack_archive(source,digest(source),[request(0,entry,candidate),request(1,entry,candidate)],
            [dict(offset=offset,source_sha256=digest(source[offset:offset+4]),payload=patch)])
        archive=_archive(output)
        for index in (0,1):
            at=archive.entry(index).start_lba*2048;self.assertEqual(output[at:at+len(candidate)],candidate)
        at=archive.entry(2).start_lba*2048;self.assertEqual(output[at+9:at+13],patch)
        self.assertTrue(audit['final_audio_banks_verified']);self.assertFalse(audit['gameplay_verified'])
        self.assertEqual(len(audit['resources']),2);self.assertEqual(audit['patch_count'],1)

    def test_conflicting_physical_ownership_and_stale_source_refuse(self):
        source,entry,candidate=fixture();base=request(0,entry,candidate)
        for rows in ([base,base],[base,dict(kind='streaming-man',entry_index=0,chunk_header_offset=0,source_man_sha256='f'*64,candidate=b'bad')],
                     [dict(base,expected_entry_sha256='f'*64)], [dict(base,entry_index=True)], [dict(base,extra=True)]):
            with self.assertRaises(ImportError):compose_model_pack_archive(source,digest(source),rows)
        # Fixed families must already be composed into the whole audio request.
        patch=dict(offset=2048+28,source_sha256=digest(source[2076:2077]),payload=b'X')
        with self.assertRaises(ImportError):compose_model_pack_archive(source,digest(source),[base],[patch])
        for args in ((digest(source),0,'f'*64,candidate,0),(digest(source),0,digest(entry),b'bad',0),
                     ('f'*64,0,digest(entry),candidate,0),(digest(source),True,digest(entry),candidate,0),
                     (digest(source),0,digest(entry),candidate,2048)):
            h,index,eh,body,header=args
            with self.assertRaises(ImportError):rebuild_audio_bank_entry(source,h,index,eh,body,header_offset=header)

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_retail_whole_archive_relocation_preserves_every_physical_neighbor(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,archive):
            source=image.read_user(archive.node.extent_lba,0,archive.node.size,archive.node.size)
            start,end=archive.toc[879:881];entry=source[start*2048:end*2048];header=archive.header_offset
        bank,_,_=bank_from_entry(entry);row=inspect_bank(bank)['samples'][0];raw=bank[row['offset']:row['offset']+row['size_bytes']]
        frames=fixed.independent_decode(raw);frames=[v//2 for v in frames]+[0]*28
        candidate,_=allocate_audio_sample_wav(entry,entry,fixed.wav(frames),expected_source_sha256=digest(entry),
            expected_current_sha256=digest(entry),expected_bank_sha256=digest(bank),sample_index=0,
            expected_sample_sha256=digest(raw),expected_current_sample_sha256=digest(raw))
        output,audit=compose_model_pack_archive(source,digest(source),[request(877,entry,candidate)],header_offset=header)
        before=_archive(source);after=_archive(output);by_index={e.index:e for e in before.entries};neighbors=0
        for index,old in by_index.items():
            following=by_index.get(index+1)
            if index==877 or following is None or old.start_lba>=following.start_lba:continue
            new=after.entry(index);next_new=after.entry(index+1)
            self.assertEqual(output[new.start_lba*2048:next_new.start_lba*2048],source[old.start_lba*2048:following.start_lba*2048]);neighbors+=1
        self.assertGreater(neighbors,1200)
        target=after.entry(877);self.assertEqual(output[target.start_lba*2048:target.start_lba*2048+len(candidate)],candidate)
        self.assertEqual(audit['growth_bytes'],2048);self.assertTrue(audit['final_audio_banks_verified'])

if __name__=='__main__':unittest.main()
