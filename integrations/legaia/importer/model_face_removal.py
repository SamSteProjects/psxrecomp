"""Count-changing removal of existing primitives, retaining source allocation.

Evidence: pinned d6e64c68 docs/formats/tmd.md and renderer group/count readers.
Objects, vector arrays and group descriptors keep their source identities.
"""
from hashlib import sha256
import struct
from .core import ImportError
from .model_primitives import _qualified_model
from .model_authoring import replace_model_content

FORMAT = 'tmd-face-removal-v1'


def _selection(inspection, removed):
    if not isinstance(removed, list) or len(removed) > 4096:
        raise ImportError('Face removal requires at most 4096 complete source identities')
    identities = set()
    for row in removed:
        if not isinstance(row, dict) or set(row) != {'object_index', 'primitive_index'} or any(type(v) is not int for v in row.values()):
            raise ImportError('Face removal requires exact integer object and primitive identities')
        obj, primitive = row['object_index'], row['primitive_index']
        if not 0 <= obj < len(inspection['objects']) or not 0 <= primitive < len(inspection['objects'][obj]['primitives']) or (obj, primitive) in identities:
            raise ImportError('Removed source face is missing or duplicated')
        identities.add((obj, primitive))
    return identities


def _groups(data, inspection):
    for obj in inspection['objects']:
        position = 12 + struct.unpack_from('<I', data, 12 + obj['object_index'] * 28 + 16)[0]
        primitive = 0
        while True:
            count, flags = struct.unpack_from('<HH', data, position)
            if count == flags == 0:
                break
            stride = data[position + 5] * 4
            yield obj['object_index'], position, count, stride, primitive
            primitive += count
            position += 8 + (count + 1) * stride


def _encode(original, expanded, inspection, removed):
    result = bytearray(original)
    for start, stop, *_ in _qualified_model(original)[1]:
        result[start:stop] = expanded[start:stop]
    positions = {}
    for obj, start, count, stride, first in _groups(expanded, inspection):
        at = positions.setdefault(obj, start)
        keep = [i for i in range(count) if (obj, first + i) not in removed]
        if not keep:
            continue
        group = bytearray(expanded[start:start + 8])
        struct.pack_into('<H', group, 0, len(keep))
        for i in keep:
            group.extend(expanded[start + 8 + i * stride:start + 8 + (i + 1) * stride])
        group.extend(expanded[start + 8 + count * stride:start + 8 + (count + 1) * stride])
        result[at:at + len(group)] = group
        positions[obj] = at + len(group)
    for obj in inspection['objects']:
        identity = obj['object_index']
        # Explicit terminal word; bytes beyond it retain the qualified expanded source.
        at = positions.get(identity, 12 + struct.unpack_from('<I', expanded, 12 + identity * 28 + 16)[0])
        result[at:at + 4] = bytes(4)
        struct.pack_into('<I', result, 12 + identity * 28 + 20,
                         len(obj['primitives']) - sum(o == identity for o, _ in removed))
    return bytes(result)


def qualify_face_removal(original, expected_sha256, candidate, removed):
    if not isinstance(original, bytes) or sha256(original).hexdigest() != expected_sha256 or not isinstance(candidate, bytes) or len(candidate) != len(original):
        raise ImportError('Face removal source hash or model allocation changed')
    inspection, vectors = _qualified_model(original)
    identities = _selection(inspection, removed)
    _qualified_model(candidate)
    expanded = bytearray(original)
    for start, stop, *_ in vectors:
        expanded[start:stop] = candidate[start:stop]
    positions = {}
    for obj, start, count, stride, first in _groups(original, inspection):
        at = positions.setdefault(obj, start)
        keep = [i for i in range(count) if (obj, first + i) not in identities]
        if not keep:
            continue
        # Shared ABE remains a qualified material field; other descriptor bytes are immutable.
        expanded[start + 7] = candidate[at + 7]
        for j, i in enumerate(keep):
            expanded[start + 8 + i * stride:start + 8 + (i + 1) * stride] = candidate[at + 8 + j * stride:at + 8 + (j + 1) * stride]
        positions[obj] = at + 8 + (len(keep) + 1) * stride
    expanded, changes = replace_model_content(original, expected_sha256, bytes(expanded), allow_normal_references=True)
    if _encode(original, expanded, inspection, identities) != candidate:
        raise ImportError('Face removal changed unowned layout, footer, padding or discarded bytes')
    return expanded, changes


def remove_faces(original, effective, previous, selections):
    source_hash = sha256(original).hexdigest()
    expanded, _ = qualify_face_removal(original, source_hash, effective, previous)
    source = _qualified_model(original)[0]
    removed = _selection(source, previous)
    current = _qualified_model(effective)[0]
    requested = _selection(current, selections)
    for obj in source['objects']:
        remaining = [row['primitive_index'] for row in obj['primitives'] if (obj['object_index'], row['primitive_index']) not in removed]
        removed.update((obj['object_index'], remaining[index]) for owner, index in requested if owner == obj['object_index'])
    if len(removed) > 4096:
        raise ImportError('Face removal exceeds 4096 source identities')
    candidate = _encode(original, expanded, source, removed)
    metadata = [dict(object_index=obj, primitive_index=primitive) for obj, primitive in sorted(removed)]
    qualify_face_removal(original, source_hash, candidate, metadata)
    return candidate, metadata


def restore_faces(original, effective, previous, selections):
    """Restore selected omitted Retail packets, retaining all current owned fields."""
    expanded, _ = qualify_face_removal(original, sha256(original).hexdigest(), effective, previous)
    inspection = _qualified_model(original)[0]
    removed = _selection(inspection, previous)
    requested = _selection(inspection, selections)
    if not requested <= removed:
        raise ImportError('Only removed Retail faces can be restored')
    remaining = removed - requested
    candidate = _encode(original, expanded, inspection, remaining)
    metadata = [dict(object_index=obj, primitive_index=primitive) for obj, primitive in sorted(remaining)]
    qualify_face_removal(original, sha256(original).hexdigest(), candidate, metadata)
    return candidate, metadata
