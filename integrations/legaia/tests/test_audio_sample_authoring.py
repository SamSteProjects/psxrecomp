"""Independent PCM readback and source-owned flags/allocation for WAV edits."""
from hashlib import sha256
import math,os,struct,unittest
from importer.core import ImportError
from importer.audio_sample_authoring import replace_sample_wav,replace_audio_sample_wav,read_pcm_wav
from importer.audio_bank import bank_from_entry,inspect_bank
from importer.audio_catalog import load_audio_asset_catalog
from importer.pipeline import _disc_context
from test_audio_bank import source_bank
from test_audio_catalog import chunk,seq

def digest(body):return sha256(body).hexdigest()
def wav(frames,rate=22050):
    pcm=struct.pack('<'+str(len(frames))+'h',*frames)
    fmt=struct.pack('<HHIIHH',1,1,rate,rate*2,2,16)
    body=b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(pcm))+pcm
    return b'RIFF'+struct.pack('<I',len(body))+body
def block(flags=0,header=0,data=0):return bytes([header,flags])+bytes([data])*14
def encode(body,frames,current=None):
    current=body if current is None else current
    return replace_sample_wav(body,current,wav(frames),expected_source_sha256=digest(body),expected_current_sha256=digest(current))
def independent_decode(body):
    # Literal coefficients and arithmetic, independent of encoder imports.
    coefficients=((0,0),(60,0),(115,-52),(98,-55),(122,-60));prior=older=0;frames=[]
    for at in range(0,len(body),16):
        header,flags=body[at:at+2];a,b=coefficients[header>>4];shift=header&15;shift=shift if shift<=12 else 9
        for byte in body[at+2:at+16]:
            for nibble in (byte&15,byte>>4):
                signed=nibble if nibble<8 else nibble-16
                value=max(-32768,min(32767,(signed<<(12-shift))+((prior*a+older*b+32)>>6)))
                frames.append(value);older,prior=prior,value
        if flags&1:break
    return frames

class SampleCodec(unittest.TestCase):
    def test_deterministic_exact_silence_low_nibble_order_and_lossy_error_audit(self):
        body=block(4)+block(3)+b'opaque post-end bytes'
        silence,audit=encode(body,[0]*56);self.assertEqual(silence,body);self.assertEqual(audit['maximum_absolute_error'],0)
        frames=[int(math.sin(i*.31)*26000) for i in range(56)]
        candidate,audit=encode(body,frames);again,second=encode(body,frames)
        self.assertEqual(candidate,again);self.assertEqual(audit,second)
        decoded=independent_decode(candidate[:32]);errors=[a-b for a,b in zip(frames,decoded)]
        self.assertEqual(audit['sum_squared_error'],sum(v*v for v in errors));self.assertEqual(audit['maximum_absolute_error'],max(abs(v) for v in errors))
        self.assertEqual(audit['decoded_pcm_sha256'],digest(struct.pack('<56h',*decoded)))
        self.assertEqual(candidate[1:32:16],body[1:32:16]);self.assertEqual(candidate[32:],body[32:]);self.assertIsNone(audit['native_sample_rate'])
        unit,_=encode(block(1),[1,-1]*14);self.assertEqual(independent_decode(unit),[1,-1]*14);self.assertEqual(unit[2:],b'\xf1'*14)
        for value in (-32768,32767):
            result,report=encode(block(1),[value]*28)
            self.assertEqual(report['maximum_absolute_error'],max(abs(value-v) for v in independent_decode(result)))

    def test_current_flags_tail_and_unknown_boundaries_reject(self):
        original=block(4)+block(3)+b'padding';frames=[500]*56;candidate,_=encode(original,frames)
        self.assertEqual(encode(original,frames,candidate)[0],candidate)
        for changed in (candidate[:1]+b'\0'+candidate[2:],candidate[:-1]+b'X',bytes([0x70])+candidate[1:]):
            with self.assertRaises(ImportError):encode(original,frames,changed)
        for source in (b'',b'12345678',block(0,0x70),block(8),block()*4097):
            with self.assertRaises(ImportError):encode(source,[0]*28)
        with self.assertRaises(ImportError):replace_sample_wav(original,original,wav(frames),expected_source_sha256='f'*64,expected_current_sha256=digest(original))
        with self.assertRaises(ImportError):encode(original,[0]*28)
        reserved,_=encode(block(1,13,0x11),[8]*28);self.assertEqual(independent_decode(reserved),[8]*28);self.assertLessEqual(reserved[0]&15,12)

    def test_pcm_wav_chunks_width_rate_count_and_duplicate_validation(self):
        source=wav([100]*28);pcm,rate=read_pcm_wav(source,28);self.assertEqual(rate,22050);self.assertEqual(pcm,struct.pack('<28h',*[100]*28))
        for change in (lambda b:b.__setitem__(slice(20,22),b'\x03\0'),lambda b:b.__setitem__(slice(22,24),b'\x02\0'),lambda b:b.__setitem__(slice(34,36),b'\x08\0'),lambda b:b.__setitem__(slice(28,32),b'\0'*4),lambda b:b.__setitem__(slice(4,8),b'\0'*4)):
            bad=bytearray(source);change(bad)
            with self.assertRaises(ImportError):read_pcm_wav(bytes(bad),28)
        for bad in (source[:-1],source+b'extra',bytearray(source),wav([0]*28,7999),wav([0]*28,192001)):
            with self.assertRaises(ImportError):read_pcm_wav(bad,28)
        extra=source[8:]+b'JUNK'+struct.pack('<I',3)+b'abc\0';extended=b'RIFF'+struct.pack('<I',len(extra))+extra
        self.assertEqual(read_pcm_wav(extended,28),(pcm,rate))
        duplicate=source[8:]+source[12:36];duplicate=b'RIFF'+struct.pack('<I',len(duplicate))+duplicate
        with self.assertRaises(ImportError):read_pcm_wav(duplicate,28)
        with self.assertRaises(ImportError):read_pcm_wav(source,True)

    def test_three_native_carriers_preserve_other_tables_and_sequence(self):
        bank=source_bank();report=inspect_bank(bank);span=report['samples'][0];raw=bank[span['offset']:span['offset']+span['size_bytes']]
        frames=[int(math.sin(i*.7)*10000) for i in range(span['size_bytes']//16*28)];input=wav(frames)
        expected_sample,_=replace_sample_wav(raw,raw,input,expected_source_sha256=digest(raw),expected_current_sha256=digest(raw))
        expected=bank[:span['offset']]+expected_sample+bank[span['offset']+span['size_bytes']:]
        for entry in (bank,chunk(0,bank)+chunk(2,seq()),chunk(0,bank[:span['offset']])+chunk(1,bank[span['offset']:])+chunk(2,seq())+b'entry padding'):
            candidate,audit=replace_audio_sample_wav(entry,entry,input,expected_source_sha256=digest(entry),expected_current_sha256=digest(entry),expected_bank_sha256=digest(bank),sample_index=0,expected_sample_sha256=digest(raw),expected_current_sample_sha256=digest(raw))
            reread,pieces,_=bank_from_entry(candidate);self.assertEqual(reread,expected)
            at=audit['sample_entry_byte_offset'];self.assertEqual(candidate[:at],entry[:at]);self.assertEqual(candidate[at+span['size_bytes']:],entry[at+span['size_bytes']:])
            arguments=dict(expected_source_sha256=digest(entry),expected_current_sha256=digest(candidate),expected_bank_sha256=digest(bank),sample_index=0,expected_sample_sha256=digest(raw),expected_current_sample_sha256=digest(expected_sample))
            self.assertEqual(replace_audio_sample_wav(entry,candidate,input,**arguments)[0],candidate)
            for key in ('expected_source_sha256','expected_current_sha256','expected_bank_sha256','expected_sample_sha256','expected_current_sample_sha256'):
                with self.assertRaises(ImportError):replace_audio_sample_wav(entry,candidate,input,**{**arguments,key:'f'*64})
            changed=bytearray(candidate);changed[pieces[0]['entry_offset']+24]^=1
            with self.assertRaises(ImportError):replace_audio_sample_wav(entry,bytes(changed),input,**{**arguments,'expected_current_sha256':digest(changed)})
            with self.assertRaises(ImportError):replace_audio_sample_wav(entry,entry,input,expected_source_sha256=digest(entry),expected_current_sha256=digest(entry),expected_bank_sha256=digest(bank),sample_index=True,expected_sample_sha256=digest(raw),expected_current_sample_sha256=digest(raw))

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_retail_entry_first_sample_exact_native_readback(self):
        disc=os.environ['LEGAIA_DISC_BIN'];row=next(r for r in load_audio_asset_catalog(disc,'town01')['assets'] if r['semantic_id']=='audio://legaia/prot/0877')
        with _disc_context(disc) as (image,_,_,archive):
            index=877;start,end=archive.toc[index+2:index+4];entry=image.read_user(archive.node.extent_lba,start*2048,(end-start)*2048,archive.node.size)
        bank,pieces,_=bank_from_entry(entry);report=inspect_bank(bank);sample=report['samples'][0];raw=bank[sample['offset']:sample['offset']+sample['size_bytes']]
        frames=independent_decode(raw);input=wav([int(value*.5) for value in frames],32000)
        candidate,audit=replace_audio_sample_wav(entry,entry,input,expected_source_sha256=digest(entry),expected_current_sha256=digest(entry),expected_bank_sha256=digest(bank),sample_index=0,expected_sample_sha256=digest(raw),expected_current_sample_sha256=digest(raw))
        output,_,_=bank_from_entry(candidate);encoded=output[sample['offset']:sample['offset']+sample['size_bytes']]
        decoded=independent_decode(encoded);self.assertEqual(audit['sample']['decoded_pcm_sha256'],digest(struct.pack('<'+str(len(decoded))+'h',*decoded)))
        offset=audit['sample_entry_byte_offset'];self.assertEqual(candidate[:offset],entry[:offset]);self.assertEqual(candidate[offset+sample['size_bytes']:],entry[offset+sample['size_bytes']:])
        self.assertEqual(encoded[1:audit['sample']['consumed_bytes']:16],raw[1:audit['sample']['consumed_bytes']:16]);self.assertEqual(len(output),len(bank))

if __name__=='__main__':unittest.main()
