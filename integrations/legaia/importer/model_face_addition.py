"""Native packet growth with explicit authored IDs and object pointer rebasing.

This codec does not install assets or relocate their surrounding carrier.
New packets inherit an existing group/donor layout and use existing vectors.
"""
from hashlib import sha256
import struct
from uuid import UUID
from .assets import MAX_MODEL_BYTES
from .core import ImportError
from .model_primitives import _qualified_model, patch_model_primitives
from .model_face_removal import _groups

MAX_NEW_FACES = 512


def add_model_faces(data, expected_sha256, additions):
    inspection, _ = _qualified_model(data)
    if sha256(data).hexdigest() != expected_sha256:
        raise ImportError('New-face source hash changed')
    if not isinstance(additions, list) or not 0 < len(additions) <= MAX_NEW_FACES:
        raise ImportError(f'New-face codec requires 1..{MAX_NEW_FACES} authored faces')
    groups, object_groups = {}, {}
    for owner, start, count, stride, first in _groups(data, inspection):
        rows = object_groups.setdefault(owner, [])
        groups[owner, len(rows)] = (start, count, stride, first)
        rows.append((start, count, stride, first))
    packets, ids = {}, set()
    for addition in additions:
        if not isinstance(addition, dict) or set(addition) != {'face_id', 'object_index', 'group_index', 'donor_primitive_index', 'fields'}:
            raise ImportError('New faces require authored identity, exact group/donor and typed fields')
        face_id = addition['face_id']
        try:
            token = UUID(face_id.removeprefix('face://authored/'))
            valid = token.version == 4 and face_id == 'face://authored/'+str(token)
        except (ValueError, AttributeError):
            valid = False
        if not valid or face_id in ids:
            raise ImportError('New-face authored identity is invalid or duplicated')
        ids.add(face_id)
        if any(type(addition[k]) is not int for k in ('object_index', 'group_index', 'donor_primitive_index')):
            raise ImportError('New-face group and donor identities must be integers')
        owner, group = addition['object_index'], addition['group_index']
        if (owner, group) not in groups:
            raise ImportError('New-face native group is missing')
        start, count, stride, first = groups[owner, group]
        donor = addition['donor_primitive_index']
        fields = addition['fields']
        if not first <= donor < first+count or not isinstance(fields, dict) or 'vertices' not in fields or not set(fields) <= {'vertices', 'uvs', 'colors', 'normal_indices'}:
            raise ImportError('New-face donor must belong to its group and fields must include vertices')
        edited, _ = patch_model_primitives(data, expected_sha256,
            [dict(object_index=owner, primitive_index=donor, **fields)])
        at = start+8+(donor-first)*stride
        packets.setdefault((owner, group), []).append((face_id, edited[at:at+stride], donor))
    insertions = []
    for identity, rows in packets.items():
        start, count, stride, _ = groups[identity]
        if count+len(rows) > 65535:
            raise ImportError('New faces exceed native group count')
        insertions.append((start+8+count*stride, b''.join(packet for _, packet, _ in rows)))
    insertions.sort()
    growth = sum(len(payload) for _, payload in insertions)
    if len(data)+growth > MAX_MODEL_BYTES:
        raise ImportError('New faces exceed the model byte budget')
    relocate = lambda offset: offset+sum(len(payload) for at, payload in insertions if at <= offset)
    candidate = bytearray();previous = 0
    for at, payload in insertions:
        candidate.extend(data[previous:at]);candidate.extend(payload);previous = at
    candidate.extend(data[previous:])
    new_faces, mapping, pointers = [], [], []
    for obj in inspection['objects']:
        owner = obj['object_index'];count = 0
        for group, (start, old_count, stride, first) in enumerate(object_groups.get(owner, [])):
            extra = packets.get((owner, group), [])
            struct.pack_into('<H', candidate, relocate(start), old_count+len(extra))
            for index in range(old_count):
                mapping.append(dict(object_index=owner, source_primitive_index=first+index, current_primitive_index=count+index))
            for index, (face_id, packet, donor) in enumerate(extra):
                new_faces.append(dict(face_id=face_id, object_index=owner, group_index=group,
                    current_primitive_index=count+old_count+index, donor_primitive_index=donor,
                    byte_offset=relocate(start)+8+(old_count+index)*stride, packet_sha256=sha256(packet).hexdigest()))
            count += old_count+len(extra)
        header = 12+owner*28
        struct.pack_into('<I', candidate, header+20, count)
        for field in (0, 8, 16):
            old = struct.unpack_from('<I', data, header+field)[0]
            used = field == 16 or struct.unpack_from('<I', data, header+field+4)[0] != 0
            new = relocate(old+12)-12 if used else old
            struct.pack_into('<I', candidate, header+field, new)
            pointers.append(dict(object_index=owner, table_field_offset=field, source_offset=old, current_offset=new))
    candidate = bytes(candidate);_qualified_model(candidate)
    return candidate, dict(source_sha256=expected_sha256, proposed_sha256=sha256(candidate).hexdigest(),
        source_byte_length=len(data), proposed_byte_length=len(candidate), growth_bytes=growth,
        new_faces=new_faces, retained_faces=mapping, pointer_relocations=pointers)


def qualify_model_face_additions(data, expected_sha256, candidate, additions):
    expected, audit = add_model_faces(data, expected_sha256, additions)
    if candidate != expected:
        raise ImportError('New-face candidate changed unowned bytes or differs from its authored faces')
    return audit
