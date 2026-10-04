"""Allocate native packet groups from qualified same-object donor layouts.

Descriptors and opaque footers are inherited exactly, not synthesized. This
codec supplies allocation bytes/audit; project publication belongs to the SDK.
"""
from hashlib import sha256
import struct
from uuid import UUID
from .assets import MAX_MODEL_BYTES
from .core import ImportError
from .model_face_addition import MAX_NEW_FACES
from .model_face_removal import _groups
from .model_primitives import _qualified_model, patch_model_primitives

MAX_NEW_GROUPS = 64


def _identity(value, prefix, seen):
    try:
        token = UUID(value.removeprefix(prefix))
        valid = token.version == 4 and value == prefix + str(token)
    except (AttributeError, ValueError):
        valid = False
    if not valid or value in seen:
        raise ImportError('Allocated group/face identity is invalid or duplicated')
    seen.add(value)


def allocate_model_groups(data, expected_sha256, requests):
    inspection, _ = _qualified_model(data)
    if sha256(data).hexdigest() != expected_sha256:
        raise ImportError('Group allocation source hash changed')
    if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_NEW_GROUPS:
        raise ImportError(f'Group allocation requires 1..{MAX_NEW_GROUPS} groups')
    groups = {}
    for owner, start, count, stride, first in _groups(data, inspection):
        groups.setdefault(owner, []).append((start, count, stride, first))
    pending, group_ids, face_ids, total_faces = {}, set(), set(), 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {'group_id', 'object_index', 'donor_group_index', 'faces'}:
            raise ImportError('Group allocation requires exact identity, object, donor and typed faces')
        _identity(request['group_id'], 'group://authored/', group_ids)
        owner, donor_group = request['object_index'], request['donor_group_index']
        if (type(owner) is not int or type(donor_group) is not int
                or owner not in groups or not 0 <= donor_group < len(groups[owner])):
            raise ImportError('Group allocation requires an existing same-object donor group')
        faces = request['faces']
        if not isinstance(faces, list) or not faces or len(faces) + total_faces > MAX_NEW_FACES:
            raise ImportError(f'Group allocation requires at most {MAX_NEW_FACES} new faces')
        total_faces += len(faces)
        start, count, stride, first = groups[owner][donor_group]
        descriptor = bytearray(data[start:start + 8])
        struct.pack_into('<H', descriptor, 0, len(faces))
        packets = []
        for face in faces:
            if not isinstance(face, dict) or set(face) != {'face_id', 'donor_primitive_index', 'fields'}:
                raise ImportError('Allocated group faces require exact identity, donor and typed fields')
            _identity(face['face_id'], 'face://authored/', face_ids)
            donor, fields = face['donor_primitive_index'], face['fields']
            if (type(donor) is not int or not first <= donor < first + count
                    or not isinstance(fields, dict) or 'vertices' not in fields
                    or not set(fields) <= {'vertices', 'uvs', 'colors', 'normal_indices'}):
                raise ImportError('Allocated face must use its group donor and supported typed fields')
            edited, _ = patch_model_primitives(data, expected_sha256,
                [dict(object_index=owner, primitive_index=donor, **fields)])
            at = start + 8 + (donor - first) * stride
            packets.append((face['face_id'], edited[at:at + stride], donor))
        footer = data[start + 8 + count * stride:start + 8 + (count + 1) * stride]
        payload = bytes(descriptor) + b''.join(packet for _, packet, _ in packets) + footer
        pending.setdefault(owner, []).append((request['group_id'], donor_group, stride, packets, payload))
    insertions = []
    for owner, rows in pending.items():
        start, count, stride, _ = groups[owner][-1]
        terminal = start + 8 + (count + 1) * stride
        if data[terminal:terminal + 4] != bytes(4):
            raise ImportError('Group allocation requires a qualified explicit terminator')
        insertions.append((terminal, owner, b''.join(row[4] for row in rows)))
    insertions.sort()
    growth = sum(len(payload) for _, _, payload in insertions)
    if len(data) + growth > MAX_MODEL_BYTES:
        raise ImportError('Group allocation exceeds the model byte budget')
    relocate = lambda at: at + sum(len(payload) for pos, _, payload in insertions if pos <= at)
    candidate, previous = bytearray(), 0
    for at, _, payload in insertions:
        candidate.extend(data[previous:at]); candidate.extend(payload); previous = at
    candidate.extend(data[previous:])
    pointers, retained, new_groups, new_faces = [], [], [], []
    insertion_positions = {owner: at for at, owner, _ in insertions}
    for obj in inspection['objects']:
        owner = obj['object_index']; old_count = len(obj['primitives'])
        header = 12 + owner * 28
        struct.pack_into('<I', candidate, header + 20,
                         old_count + sum(len(row[3]) for row in pending.get(owner, [])))
        for field in (0, 8, 16):
            old = struct.unpack_from('<I', data, header + field)[0]
            used = field == 16 or struct.unpack_from('<I', data, header + field + 4)[0] != 0
            new = relocate(old + 12) - 12 if used else old
            struct.pack_into('<I', candidate, header + field, new)
            pointers.append(dict(object_index=owner, table_field_offset=field, source_offset=old, current_offset=new))
        retained.extend(dict(object_index=owner, source_primitive_index=i, current_primitive_index=i)
                        for i in range(old_count))
        if owner not in pending: continue
        # New groups begin before the moved terminator, after earlier objects' growth.
        source_at = insertion_positions[owner]
        at = source_at + sum(len(payload) for pos, _, payload in insertions if pos < source_at)
        primitive = old_count
        for ordinal, (identity, donor, stride, packets, payload) in enumerate(pending[owner]):
            group_index = len(groups[owner]) + ordinal
            new_groups.append(dict(group_id=identity, object_index=owner, group_index=group_index,
                donor_group_index=donor, byte_offset=at, byte_length=len(payload),
                descriptor_sha256=sha256(payload[:8]).hexdigest(), footer_sha256=sha256(payload[-stride:]).hexdigest()))
            for index, (face_id, packet, face_donor) in enumerate(packets):
                new_faces.append(dict(face_id=face_id, group_id=identity, object_index=owner,
                    group_index=group_index, current_primitive_index=primitive + index,
                    donor_primitive_index=face_donor, byte_offset=at + 8 + index * stride,
                    packet_sha256=sha256(packet).hexdigest()))
            primitive += len(packets); at += len(payload)
    candidate = bytes(candidate)
    _qualified_model(candidate)
    return candidate, dict(source_sha256=expected_sha256, proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(data), proposed_byte_length=len(candidate), growth_bytes=growth,
        new_groups=new_groups, new_faces=new_faces, retained_faces=retained, pointer_relocations=pointers)


def qualify_model_group_allocation(data, expected_sha256, candidate, requests):
    expected, audit = allocate_model_groups(data, expected_sha256, requests)
    if candidate != expected:
        raise ImportError('Group allocation changed unowned bytes or differs from typed requests')
    return audit
