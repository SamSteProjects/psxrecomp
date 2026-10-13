"""Pure existing-stream numeric candidates; not a registered writable SDK API."""
from copy import deepcopy
from hashlib import sha256
from .core import ImportError
from .me_archive import entries, replace_entry
from .player_battle import decode_part


def _source(original, catalog, archive_id, stream_id):
    if not isinstance(original, bytes) or len(original) != 0x10800:
        raise ImportError('Art ownership requires the complete original streaming slot')
    archive = next((r for r in catalog['archives'] if r['semantic_id'] == archive_id), None)
    stream = next((r for r in catalog['streams'] if r['semantic_id'] == stream_id), None)
    if archive is None or stream is None or stream['archive_asset_id'] != archive_id:
        raise ImportError('Art stream belongs to another source archive')
    rows = entries(original); source = stream['source_record']; index = stream['stream_index']
    if type(index) is not int or not 0 <= index < len(rows):
        raise ImportError('Art stream index exceeds its original size table')
    row = rows[index]; start, size = row['byte_offset'], row['byte_length']
    if (archive['entry_count'] != len(rows) or archive['slot_sha256'] != sha256(original).hexdigest() or
            source['slot_sha256'] != archive['slot_sha256'] or source['slot_index'] != archive['slot_index'] or
            source['slot_offset'] != archive['slot_index'] * 0x10800 or source['slot_byte_length'] != 0x10800 or
            source['byte_offset'] != source['slot_offset'] + start or source['byte_length'] != size or
            source['size_word'] != row['size_word'] or source['compressed'] != row['compressed'] or
            source['sha256'] != sha256(original[start:start+size]).hexdigest() or
            source['decoded_sha256'] != sha256(row['decoded']).hexdigest() or
            source['decoded_byte_length'] != len(row['decoded']) or
            (stream['part_count'], stream['frame_count']) != tuple(row['decoded'][:2])):
        raise ImportError('Art ownership differs from its original slot, body or decoded stream')
    return stream, row


def _channels(decoded, edits):
    parts, frames = decoded[:2]
    if not isinstance(edits, list) or not 1 <= len(edits) <= parts * frames:
        raise ImportError('Art ownership requires bounded nonempty numeric part edits')
    result = bytearray(decoded); previous = (-1, -1)
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {'frame_index', 'part_index', 'translation', 'rotation_psx'}:
            raise ImportError('Art ledger requires complete native part channels')
        frame, part = edit['frame_index'], edit['part_index']
        if type(frame) is not int or type(part) is not int or not 0 <= frame < frames or not 0 <= part < parts or (frame, part) <= previous:
            raise ImportError('Art ledger frames/parts are invalid, duplicated or unsorted')
        for field, low, high in [('translation', -2048, 2047), ('rotation_psx', 0, 4095)]:
            values = edit[field]
            if not isinstance(values, list) or len(values) != 3 or any(type(v) is not int or not low <= v <= high for v in values):
                raise ImportError('Art channels exceed their exact twelve-bit native range')
        at = 2 + (frame * parts + part) * 9
        baseline = decode_part(decoded[at:at+9])
        if all(edit[k] == baseline[k] for k in ('translation', 'rotation_psx')):
            raise ImportError('Art ledger contains an unchanged Retail part')
        values = edit['translation'] + edit['rotation_psx']
        packed = bytearray()
        for i in (0, 2, 4):
            a, b = values[i:i+2]
            packed.extend((a & 255, b & 255, ((a >> 8) & 15) | ((b >> 4) & 0xf0)))
        result[at:at+9] = packed; previous = frame, part
    return bytes(result)


def owner(original, catalog, archive_id, stream_id, edits):
    stream, row = _source(original, catalog, archive_id, stream_id)
    decoded = _channels(row['decoded'], edits)
    candidate = replace_entry(original, stream['stream_index'], decoded)
    start, size = row['byte_offset'], row['byte_length']
    return dict(schema_version='legaia.player-art-override.v1', asset_id=stream_id,
                source_record=deepcopy(stream['source_record']), edits=deepcopy(edits),
                decoded_sha256=sha256(decoded).hexdigest(),
                current_body_sha256=sha256(candidate[start:start+size]).hexdigest())


def compose(original, catalog, archive_id, values):
    if not isinstance(values, dict) or len(values) > 87:
        raise ImportError('Art stream ownership exceeds its bounded source catalogue')
    candidate = original
    for stream_id, binding in sorted(values.items()):
        if not isinstance(binding, dict) or set(binding) != {'schema_version', 'asset_id', 'source_record', 'edits', 'decoded_sha256', 'current_body_sha256'}:
            raise ImportError('Art ownership has unsupported fields')
        expected = owner(original, catalog, archive_id, stream_id, binding['edits'])
        if binding != expected:
            raise ImportError('Art ownership source, canonical channels or replay hashes changed')
        stream, row = _source(original, catalog, archive_id, stream_id)
        candidate = replace_entry(candidate, stream['stream_index'], _channels(row['decoded'], binding['edits']))
    return candidate
