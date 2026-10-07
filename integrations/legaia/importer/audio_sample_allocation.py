"""Qualified one-pass sample allocation and lossless native carrier repacking.

This is an importer transform, not a project command or a runtime allocator.
Ordinal sample identities survive; byte positions are freshly reconstructed.
"""
from hashlib import sha256
import struct
from .core import ImportError
from .audio_bank import bank_from_entry,inspect_bank,MAX_ENTRY_BYTES
from .audio_waveform import _decode_waveform
from .audio_sample_authoring import _encode_block,read_allocation_pcm_wav

MAX_REPLACEMENTS=32

def _hash(body):return sha256(body).hexdigest()

def _one_pass(raw):
    report,pcm=_decode_waveform(raw)
    consumed=report['consumed_bytes']
    if (not report['decoded_frames'] or report['termination']['reason']!='encoded-end'
            or raw[consumed-15]!=1 or any(raw[at+1] not in (0,4) for at in range(0,consumed-16,16))):
        raise ImportError('Allocation requires a bounded encoded end without repeat/sustain flags')
    return report,pcm

def allocate_sample_wav(original,current,wav,*,expected_source_sha256,expected_current_sha256):
    """Encode complete new blocks; retain the source end and opaque post-end tail."""
    if (not isinstance(original,bytes) or not isinstance(current,bytes)
            or max(len(original),len(current))>MAX_ENTRY_BYTES
            or _hash(original)!=expected_source_sha256 or _hash(current)!=expected_current_sha256):
        raise ImportError('Allocated sample source or Current hash/extent changed')
    source,_=_one_pass(original);effective,_=_one_pass(current)
    starts=[at//16 for at in range(0,source['consumed_bytes']-16,16) if original[at+1]==4]
    current_starts=[at//16 for at in range(0,effective['consumed_bytes']-16,16) if current[at+1]==4]
    if starts!=current_starts:raise ImportError('Allocated Current sample moved source start markers')
    tail=original[source['consumed_bytes']:]
    if current[effective['consumed_bytes']:]!=tail:
        raise ImportError('Allocated Current sample changed the opaque source tail')
    pcm,rate=read_allocation_pcm_wav(wav);frames=struct.unpack('<'+str(len(pcm)//2)+'h',pcm)
    blocks=len(frames)//28;output=bytearray();decoded=[];previous=older=0
    if any(index>=blocks-1 for index in starts):
        raise ImportError('Allocated WAV must retain every source start marker before the end block')
    for index in range(blocks):
        header,packed,values,previous,older=_encode_block(frames[index*28:(index+1)*28],previous,older)
        output.extend(bytes((header,1 if index==blocks-1 else 4 if index in starts else 0))+packed);decoded.extend(values)
    output=bytes(output)+tail
    reopened,readback=_one_pass(output)
    expected=struct.pack('<'+str(len(decoded))+'h',*decoded)
    if readback!=expected or output[reopened['consumed_bytes']:]!=tail:
        raise ImportError('Allocated sample failed integer PCM/end/tail readback')
    errors=[a-b for a,b in zip(frames,decoded)]
    return output,dict(schema_version='legaia.audio-sample-allocation.v1',source_sha256=_hash(original),
        before_sha256=_hash(current),after_sha256=_hash(output),source_size_bytes=len(original),
        before_size_bytes=len(current),after_size_bytes=len(output),size_delta_bytes=len(output)-len(current),
        source_decoded_frames=source['decoded_frames'],decoded_frames=len(decoded),encoded_blocks=blocks,
        consumed_bytes=reopened['consumed_bytes'],remaining_bytes=len(tail),tail_sha256=_hash(tail),
        termination=reopened['termination'],preserved_start_blocks=starts,input_wav_sha256=_hash(wav),input_pcm_sha256=_hash(pcm),
        decoded_pcm_sha256=_hash(readback),input_wav_rate=rate,native_sample_rate=None,
        sum_squared_error=sum(v*v for v in errors),maximum_absolute_error=max(abs(v) for v in errors),
        encoder='psx-spu-adpcm-closed-loop-exhaustive-v1',runtime_state='not_observed')

def repack_audio_samples(entry,replacements,*,expected_entry_sha256):
    """Repack selected one-pass samples from one freshly qualified effective entry.

    Bank/program/tone bytes and the following SEQ or opaque carrier suffix come
    from this effective entry, allowing fixed-span families to compose first.
    Only size words, selected sample spans and necessary chunk lengths change.
    """
    if (not isinstance(entry,bytes) or len(entry)>MAX_ENTRY_BYTES or _hash(entry)!=expected_entry_sha256
            or not isinstance(replacements,dict) or not 1<=len(replacements)<=MAX_REPLACEMENTS):
        raise ImportError('Audio allocation requires a bounded hashed carrier and sample mapping')
    bank,pieces,kind=bank_from_entry(entry);report=inspect_bank(bank);rows=report['samples']
    for index,raw in replacements.items():
        if (type(index) is not int or not 0<=index<len(rows) or not isinstance(raw,bytes)
                or not raw or len(raw)%8 or len(raw)//8>65535):
            raise ImportError('Allocated sample index or eight-byte size-table extent is invalid')
        row=rows[index];before=bank[row['offset']:row['offset']+row['size_bytes']]
        source,_=_one_pass(before);candidate,_=_one_pass(raw)
        source_starts=[at//16 for at in range(0,source['consumed_bytes']-16,16) if before[at+1]==4]
        candidate_starts=[at//16 for at in range(0,candidate['consumed_bytes']-16,16) if raw[at+1]==4]
        if source_starts!=candidate_starts:raise ImportError('Allocated replacement moved source start markers')
        if before[source['consumed_bytes']:]!=raw[candidate['consumed_bytes']:]:
            raise ImportError('Allocated replacement changed the qualified sample tail')
    sample_offset=report['sections']['sample_offset']
    if kind=='split-vab-header-samples' and pieces[0]['size_bytes']!=sample_offset:
        raise ImportError('Split allocation requires the complete tables/header before the sample pool')
    prefix=bytearray(bank[:sample_offset]);pool=[];moves=[];cursor=sample_offset
    for row in rows:
        at,size=row['offset'],row['size_bytes'];before=bank[at:at+size];after=replacements.get(row['index'],before)
        if row['index'] in replacements:
            struct.pack_into('<H',prefix,report['sections']['sample_table_offset']+2*row['table_index'],len(after)//8)
        pool.append(after)
        moves.append(dict(sample_index=row['index'],before_bank_byte_offset=at,after_bank_byte_offset=cursor,
            before_size_bytes=size,after_size_bytes=len(after),before_sha256=_hash(before),after_sha256=_hash(after),
            selected=row['index'] in replacements))
        cursor+=len(after)
    proposed_size=cursor+len(bank)-report['consumed_sample_end']
    if not 32<=proposed_size<=MAX_ENTRY_BYTES:
        raise ImportError('Allocated bank exceeds its bounded native header extent')
    struct.pack_into('<I',prefix,12,proposed_size)
    rebuilt=bytes(prefix)+b''.join(pool)+bank[report['consumed_sample_end']:]
    delta=len(rebuilt)-len(bank)
    if kind=='standalone-vab':
        output=rebuilt+entry[len(bank):]
    elif kind=='leading-contiguous-vab-chunk':
        head_size=int.from_bytes(entry[:4],'little')&0xffffff;new_head=head_size+delta
        if not 32<=new_head<=0xffffff or new_head%4:raise ImportError('Allocated leading chunk size is invalid')
        output=struct.pack('<I',new_head)+rebuilt+entry[4+len(bank):]
    else:
        head_size=pieces[0]['size_bytes'];sample_size=pieces[1]['size_bytes'];new_size=sample_size+delta
        if not 1<=new_size<=0xffffff or new_size%4:raise ImportError('Allocated sample chunk size is invalid')
        tail_start=pieces[1]['entry_offset']+sample_size
        output=entry[:4]+rebuilt[:head_size]+struct.pack('<I',1<<24|new_size)+rebuilt[head_size:]+entry[tail_start:]
    if len(output)>MAX_ENTRY_BYTES:raise ImportError('Allocated carrier exceeds its byte budget')
    reopened,new_pieces,new_kind=bank_from_entry(output);new_report=inspect_bank(reopened)
    if reopened!=rebuilt or new_kind!=kind or len(new_report['samples'])!=len(rows):
        raise ImportError('Allocated carrier failed complete bank/ordinal readback')
    for move,row in zip(moves,new_report['samples']):
        if (row['offset'],row['size_bytes'],row['source_sha256'])!=(move['after_bank_byte_offset'],move['after_size_bytes'],move['after_sha256']):
            raise ImportError('Allocated sample table failed complete span readback')
    return output,dict(schema_version='legaia.audio-carrier-allocation.v1',before_entry_sha256=_hash(entry),
        after_entry_sha256=_hash(output),before_size_bytes=len(entry),after_size_bytes=len(output),size_delta_bytes=delta,
        before_bank_sha256=_hash(bank),after_bank_sha256=_hash(rebuilt),carrier=kind,before_pieces=pieces,after_pieces=new_pieces,
        samples=moves,bank_size_word_offset=12,sample_table_offset=report['sections']['sample_table_offset'],
        bank_tail_sha256=_hash(bank[report['consumed_sample_end']:]),runtime_state='not_observed',gameplay_verified=False)

def allocate_audio_sample_wav(original,current,wav,*,expected_source_sha256,expected_current_sha256,
                              expected_bank_sha256,sample_index,expected_sample_sha256,expected_current_sample_sha256):
    """Source-bound wrapper; Current may already contain allocated samples."""
    if (not isinstance(original,bytes) or not isinstance(current,bytes)
            or _hash(original)!=expected_source_sha256 or _hash(current)!=expected_current_sha256):
        raise ImportError('Audio allocation source or Current carrier hash changed')
    bank,pieces,kind=bank_from_entry(original);effective,current_pieces,current_kind=bank_from_entry(current)
    source=inspect_bank(bank);now=inspect_bank(effective)
    if (type(sample_index) is not int or not 0<=sample_index<len(source['samples'])
            or _hash(bank)!=expected_bank_sha256 or kind!=current_kind
            or source['header']['program_count']!=now['header']['program_count']
            or source['header']['sample_count']!=now['header']['sample_count']
            or source['sections']!=now['sections']):
        raise ImportError('Audio allocation source bank or ordinal identity changed')
    row=source['samples'][sample_index];current_row=now['samples'][sample_index]
    raw=bank[row['offset']:row['offset']+row['size_bytes']]
    prior=effective[current_row['offset']:current_row['offset']+current_row['size_bytes']]
    replacement,sample_audit=allocate_sample_wav(raw,prior,wav,expected_source_sha256=expected_sample_sha256,
        expected_current_sha256=expected_current_sample_sha256)
    candidate,audit=repack_audio_samples(current,{sample_index:replacement},expected_entry_sha256=expected_current_sha256)
    audit.update(source_entry_sha256=expected_source_sha256,source_bank_sha256=expected_bank_sha256,
                 sample_index=sample_index,sample=sample_audit)
    return candidate,audit
