"""Replayable model-only additions, with stable source and authored identities.

This record is not an SDK asset override. Carrier allocation, removal and GLB
composition must qualify this record before they can adopt it.
"""
from copy import deepcopy
from hashlib import sha256

from .core import ImportError
from .model_face_addition import add_model_faces, MAX_NEW_FACES
from .model_face_removal import _groups
from .model_primitives import _qualified_model

SCHEMA = 'legaia.model-face-addition-ledger.v1'
MAX_BATCHES = 8
MAX_LEDGER_FACES = MAX_NEW_FACES
REQUEST_KEYS = {'face_id', 'donor_face_id', 'fields'}


def create_face_ledger(original):
    _qualified_model(original)
    return dict(schema_version=SCHEMA, source_sha256=sha256(original).hexdigest(),
                source_byte_length=len(original), batches=[])


def _source_faces(original, source_hash):
    inspection, _ = _qualified_model(original)
    groups, faces = {}, {}
    for owner, _, count, _, first in _groups(original, inspection):
        group = groups.get(owner, 0)
        groups[owner] = group + 1
        for index in range(first, first + count):
            face_id = f'face://source/{source_hash}/{owner}/{index}'
            faces[face_id] = dict(face_id=face_id, origin='source', object_index=owner,
                group_index=group, source_primitive_index=index, current_primitive_index=index)
    return faces


def _apply_batch(current, faces, requests):
    if not isinstance(requests, list) or not 0 < len(requests) <= MAX_NEW_FACES:
        raise ImportError('Face ledger requires a bounded nonempty addition batch')
    additions, pending = [], set()
    for request in requests:
        if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
            raise ImportError('Face ledger requires exact stable face and donor identities and fields')
        face_id, donor_id = request['face_id'], request['donor_face_id']
        if not isinstance(face_id, str) or face_id in faces or face_id in pending:
            raise ImportError('Face ledger authored identity is invalid or already exists')
        if not isinstance(donor_id, str) or donor_id not in faces:
            raise ImportError('Face ledger donor identity is missing from the preceding model')
        pending.add(face_id)
        donor = faces[donor_id]
        additions.append(dict(face_id=face_id, object_index=donor['object_index'],
            group_index=donor['group_index'], donor_primitive_index=donor['current_primitive_index'],
            fields=deepcopy(request['fields'])))
    candidate, audit = add_model_faces(current, sha256(current).hexdigest(), additions)
    remap = {(row['object_index'], row['source_primitive_index']): row['current_primitive_index']
             for row in audit['retained_faces']}
    updated = deepcopy(faces)
    for face in updated.values():
        face['current_primitive_index'] = remap[face['object_index'], face['current_primitive_index']]
    donors = {row['face_id']: row['donor_face_id'] for row in requests}
    for face in audit['new_faces']:
        updated[face['face_id']] = dict(face_id=face['face_id'], origin='authored',
            object_index=face['object_index'], group_index=face['group_index'],
            current_primitive_index=face['current_primitive_index'], donor_face_id=donors[face['face_id']])
    return candidate, updated


def replay_face_ledger(original, ledger):
    source_hash = sha256(original).hexdigest()
    if (not isinstance(ledger, dict) or set(ledger) != {'schema_version', 'source_sha256', 'source_byte_length', 'batches'}
            or ledger['schema_version'] != SCHEMA or ledger['source_sha256'] != source_hash
            or type(ledger['source_byte_length']) is not int or ledger['source_byte_length'] != len(original)
            or not isinstance(ledger['batches'], list) or len(ledger['batches']) > MAX_BATCHES):
        raise ImportError('Face ledger schema or source binding changed')
    faces = _source_faces(original, source_hash)
    current, total = original, 0
    for batch in ledger['batches']:
        if (not isinstance(batch, dict) or set(batch) != {'input_sha256', 'proposed_sha256', 'additions'}
                or batch['input_sha256'] != sha256(current).hexdigest()
                or not isinstance(batch['additions'], list)):
            raise ImportError('Face ledger batch chain or schema changed')
        total += len(batch['additions'])
        if total > MAX_LEDGER_FACES:
            raise ImportError('Face ledger exceeds its authored face budget')
        current, faces = _apply_batch(current, faces, batch['additions'])
        if batch['proposed_sha256'] != sha256(current).hexdigest():
            raise ImportError('Face ledger proposed model hash changed')
    return current, dict(source_sha256=source_hash, proposed_sha256=sha256(current).hexdigest(),
        source_byte_length=len(original), proposed_byte_length=len(current),
        growth_bytes=len(current)-len(original), batch_count=len(ledger['batches']),
        authored_face_count=total, faces=list(faces.values()))


def append_face_ledger(original, ledger, requests):
    current, audit = replay_face_ledger(original, ledger)
    if len(ledger['batches']) >= MAX_BATCHES or not isinstance(requests, list) or audit['authored_face_count'] + len(requests) > MAX_LEDGER_FACES:
        raise ImportError('Face ledger exceeds its batch or authored face budget')
    candidate, _ = _apply_batch(current, {row['face_id']: row for row in audit['faces']}, requests)
    result = deepcopy(ledger)
    result['batches'].append(dict(input_sha256=sha256(current).hexdigest(),
        proposed_sha256=sha256(candidate).hexdigest(), additions=deepcopy(requests)))
    qualified, final_audit = replay_face_ledger(original, result)
    return qualified, result, final_audit


def qualify_face_ledger(original, ledger, candidate):
    expected, audit = replay_face_ledger(original, ledger)
    if candidate != expected:
        raise ImportError('Face ledger candidate differs from the complete replayed model')
    return audit
