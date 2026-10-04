"""Ledger-qualified model pack and scene-resource relocation, not a disc export."""
from hashlib import sha256
import struct

from .core import (ImportError, _pack_ranges, _tmd_extent, parse_scene_assets,
                   decompress_lzs)
from .model_face_ledger import replay_face_ledger
from .serialization import compress_lzs


def _base_model(original, binding, payload):
    if binding is None:
        if payload is not None:
            raise ImportError('Model pack base payload requires its qualified binding')
        return original
    formats = {'tmd-shape', 'tmd-content-v1', 'tmd-content-v2', 'tmd-content-v3', 'tmd-face-removal-v1'}
    removal = isinstance(binding, dict) and binding.get('format') == 'tmd-face-removal-v1'
    fields = {'format', 'source_sha256', 'asset_sha256', 'byte_length', 'source_scene_id'} | ({'removed_faces'} if removal else set())
    if (not isinstance(binding, dict) or set(binding) != fields or binding.get('format') not in formats
            or not isinstance(payload, bytes) or type(binding['byte_length']) is not int
            or binding['byte_length'] != len(payload) or len(payload) != len(original)
            or binding['source_sha256'] != sha256(original).hexdigest()
            or binding['asset_sha256'] != sha256(payload).hexdigest()
            or not isinstance(binding['source_scene_id'], str)):
        raise ImportError('Model pack retained base schema, source or payload changed')
    if removal:
        from .model_face_removal import qualify_face_removal
        qualify_face_removal(original, binding['source_sha256'], payload, binding['removed_faces'])
    else:
        from .model_authoring import replace_model_shape, replace_model_content
        if binding['format'] == 'tmd-shape':
            replace_model_shape(original, binding['source_sha256'], payload)
        else:
            replace_model_content(original, binding['source_sha256'], payload,
                allow_materials=binding['format'] in ('tmd-content-v2', 'tmd-content-v3'),
                allow_normal_references=binding['format'] == 'tmd-content-v3')
    return payload

MAX_PACK_BYTES = 4 * 1024 * 1024
MAX_PACK_SLOTS = 240
MAX_REPLACEMENTS = 32


def _qualified_pack(data):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_PACK_BYTES or len(data) % 4:
        raise ImportError('Model pack must be bounded and word-aligned')
    ranges = _pack_ranges(data)
    if not 0 < len(ranges) <= MAX_PACK_SLOTS or ranges[0][0] != 4 + 4 * len(ranges):
        raise ImportError('Model pack requires an explicit canonical slot directory')
    members = []
    for start, end in ranges:
        extent = _tmd_extent(data[start:end], 0) if start < end else None
        if extent is None:
            raise ImportError('Model pack contains an invalid or aliased TMD slot')
        members.append((start, end, extent[0]))
    return members


def grow_model_pack(source, expected_sha256, replacements):
    members = _qualified_pack(source)
    if sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Model pack source hash changed')
    if not isinstance(replacements, list) or not 0 < len(replacements) <= MAX_REPLACEMENTS:
        raise ImportError('Model pack requires a bounded nonempty replacement batch')
    proposed, audits = {}, {}
    for row in replacements:
        enriched = isinstance(row, dict) and set(row) == {'slot_index', 'ledger', 'source_model_byte_length', 'base_binding', 'base_payload'}
        if (not isinstance(row, dict) or not (set(row) == {'slot_index', 'ledger'} or enriched)
                or type(row['slot_index']) is not int or not 0 <= row['slot_index'] < len(members)
                or row['slot_index'] in proposed):
            raise ImportError('Model pack replacement slot is invalid or duplicated')
        slot = row['slot_index'];start, end, length = members[slot]
        owned_length = row['source_model_byte_length'] if enriched else length
        if type(owned_length) is not int or not length <= owned_length <= end-start or owned_length % 4:
            raise ImportError('Model pack imported model ownership exceeds its slot or changes alignment')
        original = source[start:start+owned_length]
        base = _base_model(original, row['base_binding'], row['base_payload']) if enriched else original
        candidate, audit = replay_face_ledger(base, row['ledger'])
        if len(candidate) % 4:
            raise ImportError('Model pack candidate changed word alignment')
        proposed[slot], audits[slot] = (candidate, owned_length), audit
    total_growth = sum(len(payload)-owned_length for payload, owned_length in proposed.values())
    if len(source)+total_growth > MAX_PACK_BYTES:
        raise ImportError('Model pack growth exceeds decoded byte budget')
    result = bytearray(source[:4+4*len(members)])
    records = []
    for slot, (start, end, length) in enumerate(members):
        offset = len(result)
        payload, owned_length = proposed.get(slot, (source[start:start+length], length))
        tail = source[start+owned_length:end]
        struct.pack_into('<I', result, 4+slot*4, offset//4)
        result.extend(payload);result.extend(tail)
        records.append(dict(slot_index=slot, source_byte_offset=start, proposed_byte_offset=offset,
            source_byte_length=end-start, proposed_byte_length=len(payload)+len(tail),
            source_sha256=sha256(source[start:end]).hexdigest(),
            proposed_sha256=sha256(payload+tail).hexdigest(), replacement=slot in proposed,
            trailing_bytes_preserved=True))
    candidate = bytes(result)
    reopened = _qualified_pack(candidate)
    for slot, (start, end, length) in enumerate(reopened):
        old_start, old_end, old_length = members[slot]
        if slot in proposed:
            payload, owned_length = proposed[slot]
            if candidate[start:start+len(payload)] != payload or candidate[start+len(payload):end] != source[old_start+owned_length:old_end]:
                raise ImportError('Model pack changed qualified payload or member trailing bytes')
        elif candidate[start:end] != source[old_start:old_end]:
            raise ImportError('Model pack changed an unselected neighbor')
    return candidate, dict(source_sha256=expected_sha256, proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(source), proposed_byte_length=len(candidate), growth_bytes=total_growth,
        slot_count=len(members), members=records,
        replacements=[dict(slot_index=slot, ledger_audit=audits[slot]) for slot in sorted(audits)],
        build_ready=False)


def grow_scene_model_pack(source, expected_sha256, descriptor_index, expected_pack_sha256,
                          replacements, *, allow_growth=False):
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Scene model carrier source hash changed')
    if type(allow_growth) is not bool or type(descriptor_index) is not int:
        raise ImportError('Scene model carrier requires typed descriptor and growth policy')
    table = parse_scene_assets(source, 0)
    if table is None or not 0 <= descriptor_index < len(table.descriptors):
        raise ImportError('Scene model carrier descriptor is missing')
    descriptor = table.descriptors[descriptor_index]
    if descriptor.type_byte != 2 or not descriptor.size:
        raise ImportError('Scene model carrier target must be a nonempty TMD pack descriptor')
    table_end = 8+8*len(table.descriptors)
    if any(not table_end <= d.data_offset <= len(source)
           or d.size and d.data_offset == len(source) for d in table.descriptors):
        raise ImportError('Scene model carrier descriptor overlaps its table or exceeds bounds')
    start = descriptor.data_offset
    end = min([d.data_offset for d in table.descriptors if d.data_offset > start]+[len(source)])
    if start >= end or sum(d.data_offset == start for d in table.descriptors) != 1:
        raise ImportError('Scene model carrier target is aliased or empty')
    original, consumed = decompress_lzs(source[start:end], descriptor.size)
    pack, pack_audit = grow_model_pack(original, expected_pack_sha256, replacements)
    stream = source[start:start+consumed] if pack == original else compress_lzs(pack)
    growth = (max(0, len(stream)-(end-start))+3)&~3
    if growth and not allow_growth:
        raise ImportError('Scene model carrier requires compressed-slot relocation')
    decoded, used = decompress_lzs(stream, len(pack))
    if decoded != pack or used != len(stream):
        raise ImportError('Scene model carrier compression did not roundtrip')
    result = bytearray(source[:end]+bytes(growth)+source[end:])
    result[start:start+len(stream)] = stream
    struct.pack_into('<I', result, 8+descriptor_index*8, (2 << 24)|len(pack))
    moved = []
    for row in table.descriptors:
        if growth and row.data_offset >= end:
            struct.pack_into('<I', result, 12+row.index*8, row.data_offset+growth)
            moved.append(dict(descriptor_index=row.index, source_byte_offset=row.data_offset,
                              proposed_byte_offset=row.data_offset+growth))
    candidate = bytes(result)
    reopened = parse_scene_assets(candidate, 0)
    if reopened is None or candidate[end+growth:] != source[end:]:
        raise ImportError('Scene model carrier changed following payload bytes')
    for before, after in zip(table.descriptors, reopened.descriptors):
        if (after.type_byte != before.type_byte
                or after.size != (len(pack) if before.index == descriptor_index else before.size)
                or after.data_offset != before.data_offset+(growth if before.data_offset >= end else 0)):
            raise ImportError('Scene model carrier descriptor relocation did not roundtrip')
    verified, _ = decompress_lzs(candidate[start:start+len(stream)], len(pack))
    if verified != pack:
        raise ImportError('Scene model carrier emitted stream differs from qualified pack')
    return candidate, dict(source_sha256=expected_sha256, proposed_sha256=sha256(candidate).hexdigest(),
        descriptor_index=descriptor_index, compressed_size=len(stream), source_capacity=end-start,
        growth_bytes=growth, moved_descriptors=moved, pack_audit=pack_audit,
        following_payload_preserved=True, external_container_size_update_required=bool(growth),
        build_ready=False)
