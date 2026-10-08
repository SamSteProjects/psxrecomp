"""Bounded SMF0 input mapping onto qualified, fixed-layout native SEQ events.

This is an interchange parser, not sequence allocation or game synthesis.
Unknown MIDI metadata is refused rather than silently discarded.
"""
from .core import ImportError
from .audio_sequence import inspect_sequence

MAX_MIDI_BYTES = 512 * 1024 + 22
KINDS = {0x80: 'note_off', 0x90: 'note_on', 0xa0: 'poly_aftertouch',
         0xb0: 'control_change', 0xc0: 'program_change',
         0xd0: 'channel_aftertouch', 0xe0: 'pitch_bend'}


def decode_midi(raw):
    """Return a detached complete track with explicit channel status."""
    if not isinstance(raw, bytes) or not 26 <= len(raw) <= MAX_MIDI_BYTES:
        raise ImportError('MIDI input exceeds the bounded complete-track extent')
    if (raw[:4] != b'MThd' or int.from_bytes(raw[4:8], 'big') != 6
            or raw[8:12] != b'\0\0\0\1' or raw[14:18] != b'MTrk'
            or int.from_bytes(raw[18:22], 'big') != len(raw)-22):
        raise ImportError('MIDI import requires one complete format-0 track without extra chunks')
    ppqn = int.from_bytes(raw[12:14], 'big')
    if not 1 <= ppqn <= 32767:
        raise ImportError('MIDI import requires metrical PPQN; SMPTE is unsupported')
    pos, ticks, running = 22, 0, None

    def byte():
        nonlocal pos
        if pos >= len(raw):
            raise ImportError('Truncated MIDI event')
        result = raw[pos]
        pos += 1
        return result

    def vlq():
        result = 0
        for _ in range(4):
            value = byte()
            result = result*128+(value & 127)
            if value < 128:
                return result
        raise ImportError('MIDI variable-length value exceeds four bytes')

    events = []
    while pos < len(raw):
        delta = vlq()
        ticks += delta
        if ticks > 0x7fffffff:
            raise ImportError('MIDI timing exceeds the native inspection budget')
        status = byte()
        if status < 128:
            if running is None:
                raise ImportError('MIDI running status has no preceding channel status')
            pos -= 1
            status = running
        channel = None
        if status == 255:
            running = None
            kind, length = byte(), vlq()
            if length > len(raw)-pos:
                raise ImportError('Truncated MIDI meta event')
            data = raw[pos:pos+length]
            pos += length
            if kind == 0x51 and length == 3:
                kind, values = 'set_tempo', [int.from_bytes(data, 'big')]
                if not values[0]:
                    raise ImportError('MIDI tempo must be positive')
            elif kind == 0x58 and length == 4:
                kind, values = 'time_signature', list(data)
            elif kind == 0x2f and length == 0:
                kind, values = 'end_of_track', []
                if pos != len(raw):
                    raise ImportError('MIDI bytes follow end-of-track')
            else:
                raise ImportError('Unsupported MIDI meta event; metadata is not discarded')
        else:
            kind = KINDS.get(status & 240)
            if kind is None:
                raise ImportError('MIDI system messages and SysEx are unsupported')
            running, channel = status, status & 15
            values = [byte() for _ in range(1 if status & 240 in (0xc0, 0xd0) else 2)]
            if any(value > 127 for value in values):
                raise ImportError('MIDI channel operands must be seven-bit values')
        events.append(dict(status=status, channel=channel, kind=kind, values=values,
                           delta_ticks=delta, ticks=ticks))
        if len(events) > 32770:
            raise ImportError('MIDI event count exceeds the import budget')
    if not events or events[-1]['kind'] != 'end_of_track':
        raise ImportError('MIDI track lacks a complete encoded ending')
    return dict(ppqn=ppqn, events=events, decoded_ticks=ticks)


def midi_operand_edits(raw, sequence):
    """Derive existing source offsets from bytes, never caller supplied DTOs."""
    current = inspect_sequence(sequence)
    h = current['header']
    if (not current['complete'] or not current['encoded_end_of_track']
            or current['stop_reason'] is not None or not h or not 1 <= h['ppqn'] <= 32767):
        raise ImportError('MIDI import requires a complete native SEQ with metrical PPQN')
    track = decode_midi(raw)
    if track['ppqn'] != h['ppqn']:
        raise ImportError('MIDI PPQN must match Current; timing conversion is unsupported')
    rows = track['events']
    if (len(rows) < 3 or rows[0]['kind'] != 'set_tempo' or rows[0]['ticks'] != 0
            or rows[0]['values'] != [h['initial_tempo_us_per_quarter']]
            or rows[1]['kind'] != 'time_signature' or rows[1]['ticks'] != 0
            or rows[1]['values'] != [h['time_signature_numerator'], h['time_signature_denominator_power'], 24, 8]):
        raise ImportError('MIDI must retain the exported initial tempo and time-signature anchors')
    rows = rows[2:]
    if len(rows) != len(current['events']):
        raise ImportError('MIDI event count must match Current; event insertion/removal is unsupported')
    edits = []
    for i, (row, native) in enumerate(zip(rows, current['events'])):
        if any(row[key] != native[key] for key in ('status', 'channel', 'kind', 'delta_ticks', 'ticks')):
            raise ImportError(f'MIDI event {i} changes native event identity or timing')
        if row['values'] != native['values']:
            edits.append(dict(event_offset=native['offset'], values=list(row['values'])))
    if len(edits) > 256:
        raise ImportError('MIDI import exceeds the native limit of 256 changed events')
    return edits
