"""Fixed-allocation mono PCM WAV replacement of a qualified SPU sample.

The existing source decoder supplies the pinned native integer semantics.
Input rate is metadata only; this module neither resamples nor assigns pitch.
"""
from hashlib import sha256
import struct
from .core import ImportError
from .audio_waveform import _decode_waveform,COEFFICIENTS,MAX_BLOCKS
from .audio_bank import bank_from_entry,inspect_bank,MAX_ENTRY_BYTES

MAX_WAV_BYTES=1048576
def _hash(body):return sha256(body).hexdigest()

def _read_pcm_wav(body):
    if (not isinstance(body,bytes) or not 44<=len(body)<=MAX_WAV_BYTES or body[:4]!=b'RIFF'
            or body[8:12]!=b'WAVE' or int.from_bytes(body[4:8],'little')!=len(body)-8):
        raise ImportError('Choose a bounded complete RIFF/WAVE PCM input')
    chunks={};at=12
    while at<len(body):
        if at+8>len(body):raise ImportError('Incomplete WAV chunk header')
        kind=body[at:at+4];size=int.from_bytes(body[at+4:at+8],'little');start=at+8;end=start+size
        if end+(size&1)>len(body):raise ImportError('WAV chunk exceeds its declared input')
        if kind in (b'fmt ',b'data'):
            if kind in chunks:raise ImportError('WAV has duplicate format or data chunks')
            chunks[kind]=body[start:end]
        at=end+(size&1)
    fmt,data=chunks.get(b'fmt '),chunks.get(b'data')
    if fmt is None or data is None or len(fmt) not in (16,18) or len(fmt)==18 and fmt[16:]!=b'\0\0':
        raise ImportError('Choose standard mono signed16 PCM WAV format')
    encoding,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',fmt)
    if encoding!=1 or channels!=1 or bits!=16 or align!=2 or byte_rate!=rate*2 or not 8000<=rate<=192000:
        raise ImportError('WAV must be mono signed16 PCM with a declared 8000–192000 Hz input rate')
    return data,rate

def read_pcm_wav(body,expected_frames):
    data,rate=_read_pcm_wav(body)
    if type(expected_frames) is not int or not 1<=expected_frames<=MAX_BLOCKS*28 or len(data)!=expected_frames*2:
        raise ImportError('WAV frame count must exactly match the qualified source sample prefix')
    return data,rate

def read_allocation_pcm_wav(body):
    """Separate allocation contract; fixed-size callers retain exact-frame checks."""
    data,rate=_read_pcm_wav(body)
    if not 56<=len(data)<=MAX_BLOCKS*28*2 or len(data)%56:
        raise ImportError('Allocated WAV needs 1–4096 complete 28-frame ADPCM blocks')
    return data,rate

def _encode_block(frames,previous,older):
    # Exhaustive bounded predictor/shift search with the same closed-loop
    # integer history used by the native decoder. Equal errors prefer the
    # lowest predictor, then the lowest encoded shift, deterministically.
    best=None
    for predictor,(first,second) in enumerate(COEFFICIENTS):
        for shift in range(13):
            step=1<<(12-shift);prior,last=older,previous;nibbles=[];decoded=[];error=0
            for target in frames:
                prediction=(last*first+prior*second+32)>>6;residual=target-prediction
                q=(residual+step//2)//step if residual>=0 else -((-residual+step//2)//step)
                q=max(-8,min(7,q));value=max(-32768,min(32767,q*step+prediction))
                error+=(target-value)**2;decoded.append(value);nibbles.append(q&15);prior,last=last,value
            if best is None or error<best[0]:best=(error,predictor,shift,nibbles,decoded,last,prior)
    _,predictor,shift,nibbles,decoded,last,prior=best
    packed=bytes(nibbles[i]|nibbles[i+1]<<4 for i in range(0,28,2))
    return predictor<<4|shift,packed,decoded,last,prior

def replace_sample_wav(original,current,wav,*,expected_source_sha256,expected_current_sha256):
    if (not isinstance(original,bytes) or not isinstance(current,bytes) or len(original)>MAX_ENTRY_BYTES
            or len(current)!=len(original) or _hash(original)!=expected_source_sha256
            or _hash(current)!=expected_current_sha256):
        raise ImportError('Sample source or Current extent/hash changed')
    source,_=_decode_waveform(original);effective,_=_decode_waveform(current)
    if (not source['decoded_frames'] or source['termination']['reason'] not in ('encoded-end','source-span-exhausted')
            or source['decoded_frames']!=effective['decoded_frames'] or source['consumed_bytes']!=effective['consumed_bytes']
            or source['termination']!=effective['termination']):
        raise ImportError('Sample authoring requires a complete bounded decoded source prefix and matching Current boundary')
    consumed=source['consumed_bytes']
    if current[consumed:]!=original[consumed:] or any(current[i+1]!=original[i+1] for i in range(0,consumed,16)):
        raise ImportError('Current sample changed source loop/end flags or trailing bytes')
    pcm,rate=read_pcm_wav(wav,source['decoded_frames']);frames=struct.unpack('<'+str(source['decoded_frames'])+'h',pcm)
    output=bytearray(original);decoded=[];previous=older=0
    for i in range(source['decoded_blocks']):
        at=i*16;header,packed,values,previous,older=_encode_block(frames[i*28:(i+1)*28],previous,older)
        output[at]=header;output[at+2:at+16]=packed;decoded.extend(values)
    output=bytes(output);reopened,readback=_decode_waveform(output);expected=struct.pack('<'+str(len(decoded))+'h',*decoded)
    if readback!=expected or reopened['consumed_bytes']!=consumed or reopened['termination']!=source['termination']:
        raise ImportError('Encoded sample failed native integer PCM/boundary readback')
    errors=[a-b for a,b in zip(frames,decoded)]
    return output,dict(source_sha256=_hash(original),before_sha256=_hash(current),after_sha256=_hash(output),
        input_wav_sha256=_hash(wav),input_pcm_sha256=_hash(pcm),decoded_pcm_sha256=_hash(readback),
        input_wav_rate=rate,native_sample_rate=None,decoded_frames=len(decoded),encoded_blocks=source['decoded_blocks'],
        consumed_bytes=consumed,remaining_bytes=len(original)-consumed,termination=source['termination'],
        sum_squared_error=sum(v*v for v in errors),maximum_absolute_error=max(abs(v) for v in errors),
        changed_sample_byte_offsets=[i for i,(a,b) in enumerate(zip(current,output)) if a!=b],
        encoder='psx-spu-adpcm-closed-loop-exhaustive-v1',runtime_state='not_observed')

def replace_audio_sample_wav(original,current,wav,*,expected_source_sha256,expected_current_sha256,
                             expected_bank_sha256,sample_index,expected_sample_sha256,expected_current_sample_sha256):
    if (not isinstance(original,bytes) or not isinstance(current,bytes) or len(original)>MAX_ENTRY_BYTES
            or len(current)!=len(original) or _hash(original)!=expected_source_sha256 or _hash(current)!=expected_current_sha256):
        raise ImportError('Sample carrier source or Current extent/hash changed')
    if type(sample_index) is not int:raise ImportError('Choose an explicit source sample index')
    bank,pieces,kind=bank_from_entry(original);effective,current_pieces,current_kind=bank_from_entry(current)
    report=inspect_bank(bank)
    if _hash(bank)!=expected_bank_sha256 or pieces!=current_pieces or kind!=current_kind or not 0<=sample_index<len(report['samples']):
        raise ImportError('Sample bank or native carrier identity changed')
    sample=report['samples'][sample_index];at,size=sample['offset'],sample['size_bytes']
    raw,prior=bank[at:at+size],effective[at:at+size]
    replacement,audit=replace_sample_wav(raw,prior,wav,expected_source_sha256=expected_sample_sha256,
                                        expected_current_sha256=expected_current_sample_sha256)
    owners=[p for p in pieces if p['bank_offset']<=at and at+size<=p['bank_offset']+p['size_bytes']]
    if len(owners)!=1:raise ImportError('Sample span has no unique native piece owner')
    position=owners[0]['entry_offset']+at-owners[0]['bank_offset']
    if current[:position]!=original[:position] or current[position+size:]!=original[position+size:]:
        raise ImportError('Current sample carrier changed bytes outside its selected source sample')
    candidate=current[:position]+replacement+current[position+size:]
    reread,reopened_pieces,reopened_kind=bank_from_entry(candidate)
    if reread[at:at+size]!=replacement or reopened_pieces!=pieces or reopened_kind!=kind:
        raise ImportError('Sample carrier failed native bank piece readback')
    return candidate,dict(source_entry_sha256=_hash(original),before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate),
        carrier=kind,pieces=pieces,sample_index=sample_index,sample_bank_byte_offset=at,sample_entry_byte_offset=position,
        sample_size_bytes=size,changed_entry_byte_offsets=[position+i for i in audit['changed_sample_byte_offsets']],sample=audit)
