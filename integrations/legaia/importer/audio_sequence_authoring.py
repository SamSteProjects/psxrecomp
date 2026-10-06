"""Fixed-width SEQ operands; preserve native event boundaries and opaque bytes.

This codec is not an SDK command or runtime playback implementation. Event
identity is its source byte offset, never a display index or inferred note pair.
"""
from hashlib import sha256
from .core import ImportError
from .audio_catalog import decode_audio_entry
from .audio_sequence import inspect_sequence

MAX_EDITS = 256


def _hash(body):
    return sha256(body).hexdigest()


def _structure(report):
    return (report['header'], report['complete'], report['stop_reason'],
            report['stop_offset'], report['decoded_byte_end'],
            [(e['offset'], e['end_offset'], e['delta_ticks'], e['ticks'],
              e['status'], e['channel'], e['kind'], e['running_status'])
             for e in report['events']])


def _operand(event):
    if event['channel'] is not None:
        return event['end_offset'] - len(event['values']), len(event['values']), 127
    if event['kind'] == 'set_tempo':
        return event['end_offset'] - 3, 3, 0xffffff
    raise ImportError('Only reached channel operands and tempo events are writable')


def replace_sequence_operands(original, current, *, expected_source_sha256,
                              expected_current_sha256, edits):
    """Return qualified bytes and audit, without mutating inputs.

    Partial streams permit edits only to fully decoded events; their unresolved
    suffix remains byte-identical. Existing Current edits must themselves be
    confined to qualified source operand spans. Timing is re-inspected after
    tempo changes; no delta, status, header, EOT or event insertion is allowed.
    """
    source = inspect_sequence(original)
    effective = inspect_sequence(current)
    if _hash(original) != expected_source_sha256 or _hash(current) != expected_current_sha256:
        raise ImportError('SEQ source or Current hash differs from the reviewed bytes')
    if len(original) != len(current) or _structure(source) != _structure(effective):
        raise ImportError('Current SEQ must retain source event structure and header')
    allowed = bytearray(len(original))
    by_offset = {}
    for event in source['events']:
        if event['channel'] is None and event['kind'] != 'set_tempo':
            continue
        start, width, maximum = _operand(event)
        allowed[start:start+width] = b'\1' * width
        by_offset[event['offset']] = (event, start, width, maximum)
    if any(a != b and not allowed[i] for i, (a, b) in enumerate(zip(original, current))):
        raise ImportError('Current SEQ changes bytes outside qualified operands')
    if not isinstance(edits, list) or not 1 <= len(edits) <= MAX_EDITS:
        raise ImportError('SEQ authoring requires one to 256 explicit event edits')
    output = bytearray(current)
    seen = set()
    audit = []
    effective_by_offset = {e['offset']: e for e in effective['events']}
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {'event_offset', 'values'}:
            raise ImportError('SEQ edits require exactly event_offset and values')
        offset, values = edit['event_offset'], edit['values']
        if type(offset) is not int or offset not in by_offset or offset in seen:
            raise ImportError('Choose unique reached writable source event offsets')
        seen.add(offset)
        event, start, width, maximum = by_offset[offset]
        count = 1 if event['kind'] == 'set_tempo' else width
        minimum = 1 if event['kind'] == 'set_tempo' else 0
        if (not isinstance(values, list) or len(values) != count or
                any(type(v) is not int or not minimum <= v <= maximum for v in values)):
            raise ImportError('SEQ operands exceed their encoded integer bounds')
        encoded = values[0].to_bytes(3, 'big') if event['kind'] == 'set_tempo' else bytes(values)
        output[start:start+width] = encoded
        audit.append(dict(event_offset=offset, operand_offset=start, width=width,
                          kind=event['kind'], channel=event['channel'],
                          source_values=list(event['values']),
                          before_values=list(effective_by_offset[offset]['values']),
                          after_values=list(values)))
    output = bytes(output)
    decoded = inspect_sequence(output)
    if _structure(source) != _structure(decoded):
        raise ImportError('Authored SEQ failed its source event structure readback')
    return output, dict(source_sha256=_hash(original), before_sha256=_hash(current),
                        after_sha256=_hash(output), edits=audit,
                        changed_byte_offsets=[i for i, (a, b) in enumerate(zip(current, output)) if a != b],
                        complete=decoded['complete'], stop_reason=decoded['stop_reason'],
                        decoded_time_seconds=decoded['decoded_time_seconds'])


def replace_audio_entry_sequence(original, current, *, expected_source_sha256,
                                 expected_current_sha256, edits):
    """Serialize a standalone SEQ or aligned VAB+SEQ physical PROT carrier.

    Bank/sample chunks, chunk declarations, physical padding and entry length
    are preserved exactly. This returns a native entry, not a disc patch.
    """
    source = decode_audio_entry(original)
    effective = decode_audio_entry(current)
    if _hash(original) != expected_source_sha256 or _hash(current) != expected_current_sha256:
        raise ImportError('Audio carrier source or Current hash changed')
    if source['sequence'] is None or source['format'] != effective['format'] or len(original) != len(current):
        raise ImportError('Audio authoring requires an unchanged supported SEQ carrier')
    if source['format'] == 'SEQ':
        start, size = 0, len(original)
    else:
        chunk = source['chunks'][2]
        start, size = chunk['payload_offset'], chunk['size_bytes']
        if [(c['kind'], c['payload_offset'], c['size_bytes']) for c in source['chunks']] != [(c['kind'], c['payload_offset'], c['size_bytes']) for c in effective['chunks']]:
            raise ImportError('Current audio carrier changed native chunk ownership')
    end = start + size
    if original[:start] != current[:start] or original[end:] != current[end:]:
        raise ImportError('Current audio carrier changed bank, samples or physical padding')
    seq_source, seq_current = original[start:end], current[start:end]
    replacement, audit = replace_sequence_operands(
        seq_source, seq_current, expected_source_sha256=_hash(seq_source),
        expected_current_sha256=_hash(seq_current), edits=edits)
    output = current[:start] + replacement + current[end:]
    decode_audio_entry(output)
    return output, dict(source_entry_sha256=_hash(original), before_entry_sha256=_hash(current),
                        after_entry_sha256=_hash(output), sequence_offset=start,
                        sequence_size_bytes=size,
                        changed_entry_byte_offsets=[start+i for i in audit['changed_byte_offsets']],
                        sequence=audit)
