"""Complete supported SMF0 to native SEQ candidate; no playback inference."""
from hashlib import sha256
import struct
from .core import ImportError
from .audio_catalog import decode_audio_entry,MAX_ENTRY_BYTES
from .audio_sequence import inspect_sequence
from .audio_sequence_midi import decode_midi


def _hash(raw):return sha256(raw).hexdigest()
def _vlq(n):
    out=[n&127]
    while n>>7:
        n>>=7;out.insert(0,(n&127)|128)
    return bytes(out)

def replace_midi(current,midi,*,expected_current_sha256):
    if not isinstance(current,bytes) or _hash(current)!=expected_current_sha256:
        raise ImportError('Replacement Current audio carrier hash changed')
    carrier=decode_audio_entry(current)
    if carrier['sequence'] is None:raise ImportError('Replacement requires a supported native sequence carrier')
    if carrier['format']=='SEQ':start,size,header_at=0,len(current),None
    else:
        chunk=carrier['chunks'][2];start,size,header_at=chunk['payload_offset'],chunk['size_bytes'],chunk['header_offset']
    prior=current[start:start+size];source=inspect_sequence(prior)
    if not source['complete'] or source['stop_reason'] is not None:
        raise ImportError('Replacement requires a complete Current sequence; unknown events are not discarded')
    track=decode_midi(midi);rows=track['events'];h=source['header']
    if (len(rows)<3 or rows[0]['kind']!='set_tempo' or rows[0]['ticks']!=0
            or rows[1]['kind']!='time_signature' or rows[1]['ticks']!=0
            or not 1<=rows[1]['values'][0]<=255 or not 0<=rows[1]['values'][1]<=7
            or rows[1]['values'][2:]!=[24,8]):
        raise ImportError('Replacement requires initial tempo and supported time-signature anchors')
    events=rows[2:]
    if any(e['kind']=='time_signature' for e in events):
        raise ImportError('Native SEQ has no supported mid-track time-signature event')
    header=bytearray(prior[:h['header_size']]);offset=8 if h['header_size']==15 else 6
    header[offset:offset+2]=track['ppqn'].to_bytes(2,'big')
    header[offset+2:offset+5]=rows[0]['values'][0].to_bytes(3,'big')
    header[offset+5:offset+7]=bytes(rows[1]['values'][:2])
    semantic=lambda e:{k:e[k] for k in ('status','channel','kind','values','delta_ticks','ticks')}
    unchanged=(bytes(header)==prior[:h['header_size']] and [semantic(e) for e in events]==[semantic(e) for e in source['events']])
    tail=prior[source['decoded_byte_end']:];pad=0
    if unchanged:replacement=prior
    else:
        stream=bytearray(header)
        for e in events:
            stream.extend(_vlq(e['delta_ticks']))
            if e['kind']=='set_tempo':stream.extend(b'\xff\x51'+e['values'][0].to_bytes(3,'big'))
            elif e['kind']=='end_of_track':stream.extend(b'\xff\x2f')
            else:stream.extend(bytes([e['status'],*e['values']]))
        pad=(-(len(stream)+len(tail)))%4 if header_at is not None else 0
        replacement=bytes(stream)+bytes(pad)+tail
    if not 13<=len(replacement)<=MAX_ENTRY_BYTES:raise ImportError('Replacement sequence exceeds the native byte budget')
    decoded=inspect_sequence(replacement)
    if not decoded['complete'] or [semantic(e) for e in decoded['events']]!=[semantic(e) for e in events]:
        raise ImportError('Replacement native event readback differs from MIDI input')
    if header_at is None:output=replacement
    else:
        if len(replacement)>0xffffff:raise ImportError('Replacement SEQ chunk exceeds native size word')
        output=current[:header_at]+struct.pack('<I',2<<24|len(replacement))+replacement+current[start+size:]
    if len(output)>MAX_ENTRY_BYTES:raise ImportError('Replacement audio carrier exceeds its byte budget')
    actual=decode_audio_entry(output)
    if actual['format']!=carrier['format'] or actual['sequence']!=decoded['header']:
        raise ImportError('Replacement carrier header readback failed')
    if header_at is not None and output[:header_at]!=current[:header_at]:raise ImportError('Replacement changed bank/sample ownership')
    audit=dict(schema_version='legaia.sequence-replacement-audit.v1',before_entry_sha256=_hash(current),after_entry_sha256=_hash(output),
        before_entry_size=len(current),after_entry_size=len(output),sequence_offset=start,before_sequence_size=size,after_sequence_size=len(replacement),
        before_sequence_sha256=_hash(prior),after_sequence_sha256=_hash(replacement),before_event_count=source['event_count'],after_event_count=decoded['event_count'],
        before_ticks=source['decoded_ticks'],after_ticks=decoded['decoded_ticks'],opaque_tail_sha256=_hash(tail),opaque_tail_size=len(tail),
        added_alignment_bytes=pad,unchanged=unchanged,bank_samples_preserved=True,carrier_suffix_preserved=True)
    return output,decoded,audit


def insert_sequence(current,sequence):
    """Inject an independently qualified source-owned SEQ, preserving other families."""
    c=decode_audio_entry(current);report=inspect_sequence(sequence)
    if c['sequence'] is None or not report['complete']:raise ImportError('Sequence injection requires complete supported native ownership')
    if c['format']=='SEQ':return sequence
    chunk=c['chunks'][2];start,size=chunk['payload_offset'],chunk['size_bytes'];head=chunk['header_offset']
    if len(sequence)%4 or len(sequence)>0xffffff:raise ImportError('Injected SEQ requires aligned native chunk extent')
    output=current[:head]+struct.pack('<I',2<<24|len(sequence))+sequence+current[start+size:]
    if len(output)>MAX_ENTRY_BYTES:raise ImportError('Injected audio carrier exceeds its budget')
    decode_audio_entry(output);return output


def sequence_span(entry):
    c=decode_audio_entry(entry)
    if c['sequence'] is None:raise ImportError('No supported native SEQ in carrier')
    if c['format']=='SEQ':return 0,len(entry)
    r=c['chunks'][2];return r['payload_offset'],r['size_bytes']
