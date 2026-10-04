"""Allocate independent native objects from qualified Current object layouts.

This byte codec does not publish assets or infer scene/rig/animation ownership.
The object table expands; retained bytes move together and only used pointers
rebase. Each new object receives separate vectors and exact packet/footer bytes.
"""
from hashlib import sha256
import struct
from .assets import MAX_MODEL_BYTES, MAX_OBJECTS
from .core import ImportError
from .model_group_allocation import _identity
from .model_primitives import _qualified_model

MAX_NEW_OBJECTS = 64


def allocate_model_objects(data, expected_sha256, requests):
    inspection, _ = _qualified_model(data)
    if sha256(data).hexdigest() != expected_sha256:
        raise ImportError('Object allocation source hash changed')
    old_count = len(inspection['objects'])
    if (not isinstance(requests, list) or not 1 <= len(requests) <= MAX_NEW_OBJECTS
            or old_count + len(requests) > MAX_OBJECTS):
        raise ImportError('Object allocation exceeds the native object budget')
    identities, donors = set(), []
    for request in requests:
        if not isinstance(request, dict) or set(request) != {'object_id', 'donor_object_index'}:
            raise ImportError('Object allocation requires exact stable identity and Current donor')
        _identity(request['object_id'], 'object://authored/', identities)
        donor = request['donor_object_index']
        if type(donor) is not int or not 0 <= donor < old_count:
            raise ImportError('Object allocation requires an existing Current object donor')
        fields = struct.unpack_from('<7I', data, 12 + donor * 28)
        vert, nv, normal, nn, prim, claimed, opaque = fields
        if not nv:
            raise ImportError('Object allocation donor requires a nonempty vertex table')
        # Qualification proves explicit termination and globally independent spans.
        # Preserve the complete donor primitive allocation, including opaque tail.
        end = min(offset + 12 for offset, count in ((vert, nv), (normal, nn)) if count)
        donors.append((request, fields, (prim + 12, end)))
    table_end, table_growth = 12 + old_count * 28, len(requests) * 28
    payload_growth = sum(end - start + (fields[1] + fields[3]) * 8
                         for _, fields, (start, end) in donors)
    padding = (-len(data)) % 4
    if len(data) + table_growth + padding + payload_growth > MAX_MODEL_BYTES:
        raise ImportError('Object allocation exceeds the model byte budget')
    candidate = bytearray(data[:table_end] + bytes(table_growth) + data[table_end:])
    struct.pack_into('<I', candidate, 8, old_count + len(requests))
    pointers = []
    for owner in range(old_count):
        header = 12 + owner * 28
        for field in (0, 8, 16):
            old = struct.unpack_from('<I', data, header + field)[0]
            used = field == 16 or struct.unpack_from('<I', data, header + field + 4)[0] != 0
            new = old + table_growth if used else old
            struct.pack_into('<I', candidate, header + field, new)
            pointers.append(dict(object_index=owner, table_field_offset=field,
                                 source_offset=old, current_offset=new))
    candidate.extend(bytes(padding))
    objects = []
    for ordinal, (request, fields, (start, end)) in enumerate(donors):
        vert, nv, normal, nn, prim, claimed, opaque = fields
        owner = old_count + ordinal
        primitive_at = len(candidate)
        candidate.extend(data[start:end])
        vertex_at = len(candidate)
        candidate.extend(data[vert + 12:vert + 12 + nv * 8])
        normal_at = len(candidate)
        candidate.extend(data[normal + 12:normal + 12 + nn * 8])
        header = 12 + owner * 28
        struct.pack_into('<7I', candidate, header, vertex_at - 12, nv,
                         normal_at - 12 if nn else normal, nn, primitive_at - 12, claimed, opaque)
        objects.append(dict(object_id=request['object_id'],object_index=owner,
            donor_object_index=request['donor_object_index'],header_byte_offset=header,
            primitive_count=claimed,vertex_count=nv,normal_count=nn,opaque_metadata=opaque,
            spans=[dict(kind=kind,source_byte_offset=source,byte_offset=at,byte_length=size,
                        sha256=sha256(data[source:source+size]).hexdigest())
                   for kind,source,at,size in (
                       ('primitives',start,primitive_at,end-start),
                       ('vertices',vert+12,vertex_at,nv*8),
                       ('normals',normal+12,normal_at,nn*8))]))
    candidate = bytes(candidate)
    proposed, _ = _qualified_model(candidate)
    if len(proposed['objects']) != old_count + len(requests):
        raise ImportError('Object allocation native readback differs')
    audit = dict(schema_version='legaia.model-object-allocation.v1',
        source_sha256=sha256(data).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(data),proposed_byte_length=len(candidate),growth_bytes=len(candidate)-len(data),
        source_object_count=old_count,proposed_object_count=len(proposed['objects']),
        object_table_growth_bytes=table_growth,allocation_padding_bytes=padding,
        new_objects=objects,pointer_relocations=pointers,
        retained_objects=[dict(source_object_index=i,current_object_index=i) for i in range(old_count)])
    return candidate, audit


def qualify_model_object_allocation(source, expected_sha256, candidate, requests):
    expected, audit = allocate_model_objects(source, expected_sha256, requests)
    if not isinstance(candidate, bytes) or candidate != expected:
        raise ImportError('Object allocation changed bytes outside the qualified donor layout')
    return audit
