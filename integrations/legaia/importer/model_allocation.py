"""Source-qualified packet/vector extents, without authorizing unused bytes."""
from hashlib import sha256
import struct
from .model_primitives import _qualified_model
from .model_face_removal import _groups


def inspect_model_allocation(data):
    inspection, vectors = _qualified_model(data)
    groups = {}
    for owner, start, count, stride, first in _groups(data, inspection):
        groups.setdefault(owner, []).append(dict(group_index=len(groups.get(owner, [])),
            byte_offset=start, byte_length=8+(count+1)*stride, primitive_count=count,
            packet_stride=stride, first_primitive_index=first))
    objects = []
    for obj in inspection['objects']:
        owner = obj['object_index']
        vertex, nv, normal, nn, primitive, count, _ = struct.unpack_from('<7I', data, 12+owner*28)
        start = primitive+12
        limit = min([offset+12 for offset, n in ((vertex, nv), (normal, nn)) if n] or [len(data)])
        rows = groups.get(owner, [])
        terminal = rows[-1]['byte_offset']+rows[-1]['byte_length'] if rows else start
        objects.append(dict(object_index=owner, primitive_count=count, groups=rows,
            primitive_stream=dict(byte_offset=start, byte_limit=limit,
                terminator_offset=terminal, encoded_byte_length=terminal+4-start,
                uninterpreted_tail_bytes=limit-terminal-4),
            vectors=[dict(kind=kind, byte_offset=a, byte_length=b-a, count=n)
                     for a, b, index, kind, n in vectors if index == owner]))
    return dict(schema_version='legaia.model-allocation.v1', source_sha256=sha256(data).hexdigest(),
        byte_length=len(data), objects=objects,
        tail_policy='Uninterpreted trailing bytes are not authorized allocation space.')
