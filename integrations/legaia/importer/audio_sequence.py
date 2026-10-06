"""Source SEQ events and declared tick timing; no playback or fake terminators."""
from collections import Counter
from .core import ImportError, validate_metadata_only
from .audio_catalog import _sequence, MAX_ENTRY_BYTES

MAX_EVENTS = 32768
MAX_TICKS = 0x7fffffff
KINDS = {0x80:'note_off',0x90:'note_on',0xa0:'poly_aftertouch',0xb0:'control_change',
         0xc0:'program_change',0xd0:'channel_aftertouch',0xe0:'pitch_bend'}
LIMITATIONS = [
    'Times integrate declared SEQ ticks and tempo changes; they do not establish runtime playback cadence, duration or loop behavior.',
    'Encoded note/program/controller operands do not resolve waveform instruments or scene playback assignments.',
    'Unknown/truncated events stop decoding at their source record; no end-of-track or event length is invented.',
    'Source sequence inspection is read-only; waveform synthesis, playback and audio authoring are not implemented.',
]


def inspect_sequence(body, *, max_events=MAX_EVENTS):
    if not isinstance(body, bytes) or len(body)>MAX_ENTRY_BYTES or type(max_events) is not int or not 1<=max_events<=MAX_EVENTS:
        raise ImportError('SEQ inspection requires bounded immutable bytes and an event budget')
    header=_sequence(body);pos=header['header_size'];running=None;events=[];ticks=0;seconds=0.;tempo=header['initial_tempo_us_per_quarter'];reason=None;stop=None;ended=False
    while pos<len(body):
        start=pos
        try:
            if len(events)>=max_events:raise ImportError('Event budget reached')
            delta=0
            for i in range(4):
                if pos>=len(body):raise ImportError('Truncated delta-time')
                word=body[pos];pos+=1;delta=(delta<<7)|(word&127)
                if word<128:break
            else:raise ImportError('Delta-time exceeds four-byte VLQ')
            if ticks+delta>MAX_TICKS:raise ImportError('Accumulated ticks exceed the inspection budget')
            if pos>=len(body):raise ImportError('Missing event after delta-time')
            status=body[pos];reused=status<128
            if reused:
                if running is None:raise ImportError('Running status has no preceding channel event')
                status=running
            else:pos+=1
            channel=None;values=[]
            if status==255:
                if pos>=len(body):raise ImportError('Truncated meta event')
                meta=body[pos];pos+=1
                if meta==0x51:
                    if pos+3>len(body):raise ImportError('Truncated tempo event')
                    value=int.from_bytes(body[pos:pos+3],'big');pos+=3
                    if value==0:raise ImportError('Tempo event declares zero microseconds per quarter')
                    kind='set_tempo';values=[value]
                elif meta==0x2f:kind='end_of_track'
                else:raise ImportError(f'Unknown meta event 0x{meta:02x}; length unresolved')
            elif status&0xf0 in KINDS:
                running=status;channel=status&15;kind=KINDS[status&0xf0]
                length=1 if status&0xf0 in (0xc0,0xd0) else 2
                if pos+length>len(body):raise ImportError('Truncated channel event')
                values=list(body[pos:pos+length]);pos+=length
                if any(v>=128 for v in values):raise ImportError('Channel operand is not a seven-bit value')
            else:raise ImportError(f'Unsupported system status 0x{status:02x}; length unresolved')
            ticks+=delta;seconds+=delta*tempo/header['ppqn']/1000000
            events.append(dict(index=len(events),offset=start,end_offset=pos,delta_ticks=delta,ticks=ticks,
                               time_seconds=seconds,status=status,channel=channel,kind=kind,
                               values=values,running_status=reused))
            if kind=='set_tempo':tempo=values[0]
            if kind=='end_of_track':ended=True;break
        except ImportError as exc:
            reason=str(exc);stop=start;break
    if not ended and reason is None:reason='Sequence extent ended without an encoded end-of-track';stop=pos
    decoded_end=events[-1]['end_offset'] if events else header['header_size']
    counts=dict(sorted(Counter(e['kind'] for e in events).items()))
    result=dict(header=header,events=events,event_count=len(events),event_counts=counts,
                channels=sorted({e['channel'] for e in events if e['channel'] is not None}),
                complete=ended,encoded_end_of_track=ended,stop_reason=reason,stop_offset=stop,
                decoded_byte_end=decoded_end,unparsed_bytes=len(body)-decoded_end,
                decoded_ticks=ticks,decoded_time_seconds=seconds,limitations=list(LIMITATIONS))
    validate_metadata_only(result);return result
