"""Source VAB program/tone/sample tables; no synthesis or runtime resolution."""
from hashlib import sha256
import re,struct
from .core import ImportError,validate_metadata_only
from .audio_catalog import _bank,MAX_ENTRY_BYTES
from .pipeline import _disc_context,REFERENCE_COMMIT

LIMITATIONS=[
    'Programs are 128 source slots; tone pages are packed source pages, not interchangeable program indices.',
    'Tone sample operands resolve only to bounded source size-table spans; note selection, unused-slot aliases and runtime program assignment are not evaluated.',
    'Sample spans and hashes do not establish ADPCM validity, audible duration, pitch, waveform rate or runtime residency.',
    'Bank inspection is read-only; waveform decoding, playback and audio replacement remain unsupported.',
]


def inspect_bank(body):
    if not isinstance(body,bytes) or len(body)>MAX_ENTRY_BYTES:raise ImportError('VAB tables require bounded immutable source bytes')
    header=_bank(body);size=header['declared_size'];pages=header['program_count'];samples=header['sample_count']
    program_offset=32;tone_offset=2080;table_offset=tone_offset+pages*512;sample_offset=table_offset+512
    if size>len(body) or sample_offset>size:raise ImportError('VAB fixed sections exceed the declared bank extent')
    body=body[:size]
    programs=[]
    for slot in range(128):
        offset=program_offset+slot*16;r=body[offset:offset+16]
        if r[0]>16:raise ImportError('VAB program tone count exceeds its packed page capacity')
        programs.append(dict(slot=slot,offset=offset,tone_count=r[0],volume=r[1],priority=r[2],mode=r[3],pan=r[4],
                        attributes=struct.unpack_from('<H',r,6)[0],source_sha256=sha256(r).hexdigest()))
    tones=[]
    for page in range(pages):
        for index in range(16):
            offset=tone_offset+page*512+index*32;r=body[offset:offset+32]
            program,sample=struct.unpack_from('<hh',r,20)
            tones.append(dict(page=page,index=index,offset=offset,priority=r[0],mode=r[1],volume=r[2],pan=r[3],
                center=r[4],shift=r[5],minimum_key=r[6],maximum_key=r[7],pitch_bend_down=r[12],pitch_bend_up=r[13],
                adsr1=struct.unpack_from('<H',r,16)[0],adsr2=struct.unpack_from('<H',r,18)[0],program_operand=program,
                sample_operand=sample,sample_index=sample-1 if 1<=sample<=samples else None,
                source_sha256=sha256(r).hexdigest()))
    sizes=struct.unpack_from('<256H',body,table_offset);spans=[];cursor=sample_offset
    for index in range(samples):
        size_bytes=sizes[index+1]*8
        if cursor+size_bytes>len(body):raise ImportError('VAB sample size table exceeds its declared bank extent')
        sample=body[cursor:cursor+size_bytes]
        spans.append(dict(index=index,table_index=index+1,size_units=sizes[index+1],offset=cursor,size_bytes=size_bytes,
                          block_aligned=size_bytes%16==0,source_sha256=sha256(sample).hexdigest()))
        cursor+=size_bytes
    result=dict(header=header,bank_sha256=sha256(body).hexdigest(),bank_size_bytes=len(body),
                sections=dict(program_offset=program_offset,tone_offset=tone_offset,sample_table_offset=table_offset,sample_offset=sample_offset),
                programs=programs,tones=tones,samples=spans,sample_table_spacer=sizes[0],sample_table_unused_nonzero=sum(v!=0 for v in sizes[samples+1:]),
                used_program_slots=[p['slot'] for p in programs if p['tone_count']],
                declared_program_count_matches_used_slots=sum(p['tone_count']>0 for p in programs)==pages,
                consumed_sample_end=cursor,remaining_bank_bytes=len(body)-cursor,limitations=list(LIMITATIONS))
    validate_metadata_only(result);return result


def bank_from_entry(body):
    """Qualify a leading contiguous bank or bounded split header/sample chunks."""
    if not isinstance(body,bytes) or len(body)>MAX_ENTRY_BYTES:raise ImportError('Audio bank carrier exceeds its immutable byte budget')
    if body[:4]==b'pBAV':
        header=_bank(body);size=header['declared_size']
        if size>len(body):raise ImportError('Standalone VAB bank extent is incomplete')
        return body[:size],[dict(bank_offset=0,entry_offset=0,size_bytes=size)],'standalone-vab'
    if len(body)<36:raise ImportError('Bank carrier has no complete leading VAB header')
    word=struct.unpack_from('<I',body)[0];head_size=word&0xffffff
    if word>>24!=0 or head_size<32 or head_size%4 or 4+head_size>len(body):raise ImportError('Leading VAB chunk has invalid source boundaries')
    header=_bank(body[4:4+head_size]);size=header['declared_size']
    if size<=head_size:
        return body[4:4+size],[dict(bank_offset=0,entry_offset=4,size_bytes=size)],'leading-contiguous-vab-chunk'
    next_offset=4+head_size
    if next_offset+4>len(body):raise ImportError('VAB sample chunk is absent')
    word=struct.unpack_from('<I',body,next_offset)[0];sample_size=word&0xffffff;sample_start=next_offset+4
    if word>>24!=1 or sample_size%4 or sample_start+sample_size>len(body) or head_size+sample_size!=size:
        raise ImportError('Split VAB samples do not complete the declared bank extent')
    return body[4:4+head_size]+body[sample_start:sample_start+sample_size],[dict(bank_offset=0,entry_offset=4,size_bytes=head_size),dict(bank_offset=head_size,entry_offset=sample_start,size_bytes=sample_size)],'split-vab-header-samples'


def read_audio_bank(disc,asset_id,expected_entry_sha256):
    if not isinstance(asset_id,str) or re.fullmatch(r'audio://legaia/prot/[0-9]{4}',asset_id) is None:raise ImportError('Choose a structural source audio identity')
    if not isinstance(expected_entry_sha256,str) or re.fullmatch(r'[0-9a-f]{64}',expected_entry_sha256) is None:raise ImportError('Bank inspection requires its reviewed entry hash')
    index=int(asset_id.rsplit('/',1)[1])
    with _disc_context(disc) as (image,disc_hash,mapping,archive):
        archive.entry(index);start,end=archive.toc[index+2:index+4];offset=start*2048;size=(end-start)*2048
        if not 0<size<=MAX_ENTRY_BYTES or offset+size>archive.node.size:raise ImportError('Bank carrier exceeds physical entry bounds')
        body=image.read_user(archive.node.extent_lba,offset,size,archive.node.size)
        if sha256(body).hexdigest()!=expected_entry_sha256:raise ImportError('Audio bank entry differs from its reviewed hash')
        bank,pieces,carrier=bank_from_entry(body);report=inspect_bank(bank)
        source=dict(disc_sha256=disc_hash,iso_file='PROT.DAT',prot_entry_index=index,entry_sha256=expected_entry_sha256,
                    entry_byte_offset=offset,entry_size_bytes=size,carrier=carrier,pieces=pieces)
        return dict(source_record=source,reference_commit=REFERENCE_COMMIT,**report)
