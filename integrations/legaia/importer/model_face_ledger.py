"""Replayable model-only additions, with stable source and authored identities.

The SDK retains this record beside its independently qualified base binding.
V1 addition batches remain readable; V2 chains typed content edits between
additions without changing stable face identities. V3 also replays typed stable
face removals, retaining historical authored identities and allocation ownership.
V4 restores deleted identities from qualified replay-derived packet preimages.
V5 allocates bounded new native vertex/normal rows before further face edits.
V6 allocates stable authored groups without assigning them Retail group ownership.
Restoration commands require separate project/editor integration.
"""
import json
from copy import deepcopy
from hashlib import sha256

from .core import ImportError
from .model_face_addition import add_model_faces, MAX_NEW_FACES
from .model_face_removal import _groups
from .model_primitives import _qualified_model

SCHEMA = 'legaia.model-face-addition-ledger.v1'
CONTENT_SCHEMA = 'legaia.model-face-addition-ledger.v2'
REMOVAL_SCHEMA = 'legaia.model-face-addition-ledger.v3'
RESTORATION_SCHEMA = 'legaia.model-face-addition-ledger.v4'
VECTOR_SCHEMA = 'legaia.model-face-addition-ledger.v5'
GROUP_SCHEMA = 'legaia.model-face-addition-ledger.v6'
VECTOR_VERSIONS = (VECTOR_SCHEMA,GROUP_SCHEMA)
REMOVAL_VERSIONS = (REMOVAL_SCHEMA,RESTORATION_SCHEMA,*VECTOR_VERSIONS)
RESTORATION_VERSIONS = (RESTORATION_SCHEMA,*VECTOR_VERSIONS)
MAX_LEDGER_VECTORS = 4096
MAX_OPERATIONS = 64
MAX_METADATA_BYTES = 2*1024*1024
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


def _apply_batch(current, faces, requests, reserved=()):
    if not isinstance(requests, list) or not 0 < len(requests) <= MAX_NEW_FACES:
        raise ImportError('Face ledger requires a bounded nonempty addition batch')
    additions, pending = [], set()
    for request in requests:
        if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
            raise ImportError('Face ledger requires exact stable face and donor identities and fields')
        face_id, donor_id = request['face_id'], request['donor_face_id']
        if not isinstance(face_id, str) or face_id in faces or face_id in pending or face_id in reserved:
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


def _operations(ledger):
    if not isinstance(ledger, dict):
        raise ImportError('Face ledger requires an object')
    version = ledger.get('schema_version')
    member = 'batches' if version == SCHEMA else 'operations'
    if (version not in (SCHEMA, CONTENT_SCHEMA, *REMOVAL_VERSIONS)
            or set(ledger) != {'schema_version','source_sha256','source_byte_length',member}
            or not isinstance(ledger[member],list)
            or len(ledger[member]) > (MAX_BATCHES if version == SCHEMA else MAX_OPERATIONS)):
        raise ImportError('Face ledger schema or operation budget changed')
    try:
        if len(json.dumps(ledger,allow_nan=False).encode()) > MAX_METADATA_BYTES:
            raise ImportError('Face ledger exceeds metadata budget')
    except (TypeError, ValueError) as error:
        raise ImportError('Face ledger requires finite JSON metadata') from error
    if version == SCHEMA:
        if any(not isinstance(batch,dict) or set(batch) != {'input_sha256','proposed_sha256','additions'} for batch in ledger['batches']):
            raise ImportError('Face ledger batch schema changed')
        return [dict(batch,kind='add_faces') for batch in ledger['batches']]
    return ledger['operations']


def _reserved_faces(operations):
    reserved=set()
    for operation in operations:
        if operation['kind']=='add_faces':
            reserved.update(row['face_id'] for row in operation['additions'])
        elif operation['kind']=='allocate_groups':
            reserved.update(face['face_id'] for group in operation['requests'] for face in group['faces'])
    return reserved


def _apply_group_allocation(current, faces, requests, reserved, group_reserved):
    from .model_group_allocation import allocate_model_groups,MAX_NEW_GROUPS
    if not isinstance(requests,list) or not 1<=len(requests)<=MAX_NEW_GROUPS:
        raise ImportError('Face ledger group allocation requires bounded typed requests')
    native=[];pending=set();donors={};count=0
    for group in requests:
        if (not isinstance(group,dict) or set(group)!={'group_id','donor_face_id','faces'}
                or not isinstance(group['group_id'],str) or group['group_id'] in group_reserved
                or not isinstance(group['donor_face_id'],str) or group['donor_face_id'] not in faces
                or not isinstance(group['faces'],list) or not group['faces']):
            raise ImportError('Face ledger group identity or stable donor changed')
        count+=len(group['faces'])
        if count>MAX_LEDGER_FACES:
            raise ImportError('Face ledger group allocation exceeds its authored face budget')
        donor=faces[group['donor_face_id']];rows=[]
        for face in group['faces']:
            if (not isinstance(face,dict) or set(face)!=REQUEST_KEYS
                    or not isinstance(face['face_id'],str) or face['face_id'] in faces
                    or face['face_id'] in reserved or face['face_id'] in pending
                    or not isinstance(face['donor_face_id'],str) or face['donor_face_id'] not in faces):
                raise ImportError('Face ledger group face identity or stable donor changed')
            packet=faces[face['donor_face_id']]
            if any(packet[key]!=donor[key] for key in ('object_index','group_index')):
                raise ImportError('Allocated group face donors must belong to the selected Current group')
            pending.add(face['face_id']);donors[face['face_id']]=face['donor_face_id']
            rows.append(dict(face_id=face['face_id'],donor_primitive_index=packet['current_primitive_index'],
                             fields=deepcopy(face['fields'])))
        native.append(dict(group_id=group['group_id'],object_index=donor['object_index'],
                           donor_group_index=donor['group_index'],faces=rows))
    candidate,audit=allocate_model_groups(current,sha256(current).hexdigest(),native)
    updated=deepcopy(faces)
    for face in audit['new_faces']:
        updated[face['face_id']]=dict(face_id=face['face_id'],origin='authored',
            object_index=face['object_index'],group_index=face['group_index'],
            current_primitive_index=face['current_primitive_index'],donor_face_id=donors[face['face_id']])
    return candidate,updated,audit


def _apply_content(current, operation):
    from .model_authoring import replace_model_content
    runs = operation['runs']
    if not isinstance(runs,list) or not 0 < len(runs) <= 32768:
        raise ImportError('Face ledger content requires bounded changed byte runs')
    candidate = bytearray(current);end = -1
    for run in runs:
        if (not isinstance(run,dict) or set(run) != {'offset','before_hex','after_hex'}
                or type(run['offset']) is not int or run['offset'] <= end
                or not isinstance(run['before_hex'],str) or not isinstance(run['after_hex'],str)):
            raise ImportError('Face ledger content run schema or order changed')
        try:
            before,after = bytes.fromhex(run['before_hex']),bytes.fromhex(run['after_hex'])
        except ValueError as error:
            raise ImportError('Face ledger content run requires hex bytes') from error
        at = run['offset']
        if (not before or len(before)!=len(after) or before.hex()!=run['before_hex'] or after.hex()!=run['after_hex']
                or at<0 or at+len(before)>len(current) or before==after or current[at:at+len(before)]!=before):
            raise ImportError('Face ledger content preimage or span changed')
        candidate[at:at+len(after)] = after;end = at+len(before)-1
    candidate = bytes(candidate)
    replace_model_content(current,sha256(current).hexdigest(),candidate,allow_normal_references=True)
    return candidate


def _apply_removal(current, faces, identities):
    """Remove active stable identities through the qualified allocation-preserving codec."""
    from .model_face_removal import remove_faces
    if (not isinstance(identities,list) or not 0 < len(identities) <= 4096
            or any(not isinstance(identity,str) or identity not in faces for identity in identities)
            or len(set(identities)) != len(identities)):
        raise ImportError('Face ledger removal requires unique active stable identities')
    chosen=set(identities)
    selections=[dict(object_index=faces[identity]['object_index'],
                     primitive_index=faces[identity]['current_primitive_index']) for identity in identities]
    candidate,_=remove_faces(current,current,[],selections)
    before=_qualified_model(current)[0];after=_qualified_model(candidate)[0]
    omitted={(row['object_index'],row['primitive_index']) for row in selections}
    indices={};groups={}
    for obj in before['objects']:
        owner=obj['object_index'];kept=[row for row in obj['primitives'] if (owner,row['primitive_index']) not in omitted]
        if len(kept)!=len(after['objects'][owner]['primitives']):
            raise ImportError('Face ledger removal ownership count changed')
        for old,new in zip(kept,after['objects'][owner]['primitives']):
            indices[owner,old['primitive_index']]=new['primitive_index']
            pair=(owner,old['group_index'])
            if pair in groups and groups[pair]!=new['group_index']:
                raise ImportError('Face ledger removal split an existing packet group')
            groups[pair]=new['group_index']
    updated={identity:deepcopy(face) for identity,face in faces.items() if identity not in chosen}
    for face in updated.values():
        owner=face['object_index']
        face['current_primitive_index']=indices[owner,face['current_primitive_index']]
        face['group_index']=groups[owner,face['group_index']]
    return candidate,updated


def _replay_face_ledger(original, ledger, *, capture=False):
    source_hash = sha256(original).hexdigest()
    operations = _operations(ledger)
    if (ledger['source_sha256'] != source_hash or type(ledger['source_byte_length']) is not int
            or ledger['source_byte_length'] != len(original)):
        raise ImportError('Face ledger source binding changed')
    faces = _source_faces(original, source_hash)
    # Restoration consumes preimages in the same replay pass, never recursively.
    capture = capture or ledger['schema_version']==GROUP_SCHEMA or any(isinstance(op,dict) and op.get('kind')=='restore_faces' for op in operations)
    origins={identity:(face['object_index'],face['group_index']) for identity,face in faces.items()} if capture else {}
    ranks={identity:index for index,identity in enumerate(faces)} if capture else {}
    deleted_packets={}
    current, total, batches = original, 0, 0
    vector_total=0;vector_batches=0
    group_total=0;group_batches=0;group_records=[];group_reserved=set()
    next_group={}
    if ledger['schema_version']==GROUP_SCHEMA:
        for owner,*_ in _groups(original,_qualified_model(original)[0]):
            next_group[owner]=next_group.get(owner,0)+1
    reserved=set();removed=[]
    for operation in operations:
        if (not isinstance(operation,dict) or operation.get('input_sha256') != sha256(current).hexdigest()):
            raise ImportError('Face ledger operation chain changed')
        if operation.get('kind') == 'add_faces':
            if set(operation) != {'kind','input_sha256','proposed_sha256','additions'} or not isinstance(operation['additions'],list):
                raise ImportError('Face ledger addition schema changed')
            total += len(operation['additions']);batches += 1
            if total > MAX_LEDGER_FACES or batches > MAX_BATCHES:
                raise ImportError('Face ledger exceeds its authored face or batch budget')
            current, faces = _apply_batch(current, faces, operation['additions'],reserved)
            if capture:
                for request in operation['additions']:
                    identity=request['face_id']
                    origins[identity]=origins[request['donor_face_id']]
                    ranks[identity]=len(ranks)
            reserved.update(row['face_id'] for row in operation['additions'])
        elif operation.get('kind') == 'edit_content':
            if set(operation) != {'kind','input_sha256','proposed_sha256','runs'}:
                raise ImportError('Face ledger content schema changed')
            current = _apply_content(current, operation)
        elif operation.get('kind') == 'allocate_vectors' and ledger['schema_version'] in VECTOR_VERSIONS:
            from .model_vector_allocation import append_model_vectors
            if set(operation) != {'kind','input_sha256','proposed_sha256','requests'}:
                raise ImportError('Face ledger vector allocation schema changed')
            current,allocated=append_model_vectors(current,operation['input_sha256'],operation['requests'])
            vector_total+=sum(row['added_count'] for row in allocated['new_vectors']);vector_batches+=1
            if vector_total>MAX_LEDGER_VECTORS:
                raise ImportError('Face ledger exceeds its allocated vector budget')
        elif operation.get('kind') == 'allocate_groups' and ledger['schema_version']==GROUP_SCHEMA:
            from .model_group_allocation import MAX_NEW_GROUPS
            if set(operation)!={'kind','input_sha256','proposed_sha256','requests'}:
                raise ImportError('Face ledger group allocation schema changed')
            current,faces,allocated=_apply_group_allocation(current,faces,operation['requests'],reserved,group_reserved)
            total+=len(allocated['new_faces']);batches+=1
            group_total+=len(allocated['new_groups']);group_batches+=1
            if total>MAX_LEDGER_FACES or batches>MAX_BATCHES or group_total>MAX_NEW_GROUPS:
                raise ImportError('Face ledger exceeds its authored group, face or batch budget')
            allocated_by_id={row['group_id']:row for row in allocated['new_groups']}
            for group in operation['requests']:
                row=allocated_by_id[group['group_id']];owner=row['object_index']
                root=next_group.get(owner,0);next_group[owner]=root+1
                group_records.append(dict(group_id=group['group_id'],object_index=owner,
                    origin_group_index=root,donor_face_id=group['donor_face_id']))
                group_reserved.add(group['group_id'])
                for face in group['faces']:
                    identity=face['face_id'];origins[identity]=(owner,root)
                    ranks[identity]=len(ranks);reserved.add(identity)
        elif operation.get('kind') == 'remove_faces' and ledger['schema_version'] in REMOVAL_VERSIONS:
            if set(operation) != {'kind','input_sha256','proposed_sha256','face_ids'}:
                raise ImportError('Face ledger removal schema changed')
            prior=current if capture else None;prior_faces=faces if capture else None
            current,faces=_apply_removal(current,faces,operation['face_ids'])
            if capture:
                inspection=_qualified_model(prior)[0];groups={};group_counts={}
                for owner,start,count,stride,first in _groups(prior,inspection):
                    group=group_counts.get(owner,0);group_counts[owner]=group+1
                    groups[owner,group]=(start,count,stride,first)
                for identity in operation['face_ids']:
                    face=prior_faces[identity];owner=face['object_index']
                    start,count,stride,first=groups[owner,face['group_index']]
                    at=start+8+(face['current_primitive_index']-first)*stride
                    deleted_packets[identity]=dict(face=deepcopy(face),origin_group_index=origins[identity][1],
                        stable_order=ranks[identity],deletion_input_sha256=operation['input_sha256'],
                        source_byte_length=len(prior),packet_byte_offset=at,
                        packet=prior[at:at+stride],descriptor=prior[start:start+8],
                        footer=prior[start+8+count*stride:start+8+(count+1)*stride])
            removed.extend(operation['face_ids'])
        elif operation.get('kind') == 'restore_faces' and ledger['schema_version'] in RESTORATION_VERSIONS:
            from .model_face_reinsertion import _reinsert_faces
            if set(operation) != {'kind','input_sha256','proposed_sha256','face_ids'}:
                raise ImportError('Face ledger restoration schema changed')
            current,restored=_reinsert_faces(current,list(faces.values()),deleted_packets,origins,ranks,operation['face_ids'])
            faces={row['face_id']:row for row in restored['faces']}
            for identity in operation['face_ids']:
                deleted_packets.pop(identity)
            selected=set(operation['face_ids'])
            removed=[identity for identity in removed if identity not in selected]
        else:
            raise ImportError('Face ledger operation kind is unknown')
        if operation['proposed_sha256'] != sha256(current).hexdigest():
            raise ImportError('Face ledger proposed model hash changed')
    audit=dict(source_sha256=source_hash, proposed_sha256=sha256(current).hexdigest(),
        source_byte_length=len(original), proposed_byte_length=len(current),
        growth_bytes=len(current)-len(original), batch_count=batches, operation_count=len(operations),
        authored_face_count=total, faces=list(faces.values()))
    if ledger['schema_version'] in REMOVAL_VERSIONS:
        audit['removed_face_ids']=removed
    if ledger['schema_version'] in VECTOR_VERSIONS:
        audit.update(allocated_vector_count=vector_total,vector_allocation_count=vector_batches)
    if ledger['schema_version']==GROUP_SCHEMA:
        for group in group_records:
            active=[face for face in faces.values() if origins[face['face_id']]==(group['object_index'],group['origin_group_index'])]
            indices={face['group_index'] for face in active}
            if len(indices)>1:raise ImportError('Allocated stable group split across Current groups')
            group.update(current_group_index=next(iter(indices)) if indices else None,
                face_ids=[face['face_id'] for face in sorted(active,key=lambda row:ranks[row['face_id']])])
        audit.update(allocated_group_count=group_total,group_allocation_count=group_batches,allocated_groups=group_records)
    return current,audit,deleted_packets


def replay_face_ledger(original,ledger):
    current,audit,_=_replay_face_ledger(original,ledger)
    return current,audit


def deleted_face_sources(original,ledger):
    """Detached exact deletion preimages recovered only from complete qualified replay.

    These bytes are not user-provided ledger fields or restoration requests.
    Stable ordering and original group ownership survive Current compaction.
    """
    _,_,packets=_replay_face_ledger(original,ledger,capture=True)
    return deepcopy(packets)


def append_content_ledger(original, ledger, candidate):
    from .model_authoring import replace_model_content
    current, audit = replay_face_ledger(original, ledger)
    replace_model_content(current,sha256(current).hexdigest(),candidate,allow_normal_references=True)
    if candidate == current:
        return current,deepcopy(ledger),audit
    operations = _operations(ledger)
    if len(operations) >= MAX_OPERATIONS:
        raise ImportError('Face ledger exceeds its operation budget')
    runs=[];at=0
    while at < len(current):
        if current[at] == candidate[at]:
            at += 1;continue
        start=at
        while at < len(current) and current[at] != candidate[at]:at += 1
        runs.append(dict(offset=start,before_hex=current[start:at].hex(),after_hex=candidate[start:at].hex()))
    updated = dict(schema_version=ledger['schema_version'] if ledger['schema_version'] in REMOVAL_VERSIONS else CONTENT_SCHEMA,source_sha256=ledger['source_sha256'],
        source_byte_length=ledger['source_byte_length'],operations=deepcopy(operations))
    updated['operations'].append(dict(kind='edit_content',input_sha256=sha256(current).hexdigest(),
        proposed_sha256=sha256(candidate).hexdigest(),runs=runs))
    qualified,report = replay_face_ledger(original,updated)
    return qualified,updated,report


def append_face_ledger(original, ledger, requests):
    current, audit = replay_face_ledger(original, ledger)
    if audit['batch_count'] >= MAX_BATCHES or len(_operations(ledger)) >= MAX_OPERATIONS or not isinstance(requests, list) or audit['authored_face_count'] + len(requests) > MAX_LEDGER_FACES:
        raise ImportError('Face ledger exceeds its batch or authored face budget')
    reserved=_reserved_faces(_operations(ledger))
    candidate, _ = _apply_batch(current, {row['face_id']: row for row in audit['faces']}, requests,reserved)
    result = deepcopy(ledger)
    batch=dict(input_sha256=sha256(current).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),additions=deepcopy(requests))
    if result['schema_version'] == SCHEMA:
        result['batches'].append(batch)
    else:
        result['operations'].append(dict(batch,kind='add_faces'))
    qualified, final_audit = replay_face_ledger(original, result)
    return qualified, result, final_audit


def append_removal_ledger(original, ledger, face_ids):
    current,audit=replay_face_ledger(original,ledger)
    operations=_operations(ledger)
    if len(operations)>=MAX_OPERATIONS:
        raise ImportError('Face ledger exceeds its operation budget')
    candidate,_=_apply_removal(current,{row['face_id']:row for row in audit['faces']},face_ids)
    result=dict(schema_version=ledger['schema_version'] if ledger['schema_version'] in REMOVAL_VERSIONS else REMOVAL_SCHEMA,source_sha256=ledger['source_sha256'],
                source_byte_length=ledger['source_byte_length'],operations=deepcopy(operations))
    result['operations'].append(dict(kind='remove_faces',input_sha256=sha256(current).hexdigest(),
                                    proposed_sha256=sha256(candidate).hexdigest(),face_ids=deepcopy(face_ids)))
    qualified,report=replay_face_ledger(original,result)
    return qualified,result,report


def append_restoration_ledger(original,ledger,face_ids):
    from .model_face_reinsertion import reinsert_ledger_faces
    operations=_operations(ledger)
    if len(operations)>=MAX_OPERATIONS:
        raise ImportError('Face ledger exceeds its operation budget')
    candidate,restored=reinsert_ledger_faces(original,ledger,face_ids)
    result=dict(schema_version=ledger['schema_version'] if ledger['schema_version'] in VECTOR_VERSIONS else RESTORATION_SCHEMA,source_sha256=ledger['source_sha256'],
                source_byte_length=ledger['source_byte_length'],operations=deepcopy(operations))
    result['operations'].append(dict(kind='restore_faces',input_sha256=restored['source_sha256'],
        proposed_sha256=restored['proposed_sha256'],face_ids=deepcopy(face_ids)))
    qualified,report=replay_face_ledger(original,result)
    return qualified,result,report


def append_vector_ledger(original,ledger,requests):
    from .model_vector_allocation import append_model_vectors
    current,audit=replay_face_ledger(original,ledger)
    operations=_operations(ledger)
    if len(operations)>=MAX_OPERATIONS:
        raise ImportError('Face ledger exceeds its operation budget')
    candidate,allocated=append_model_vectors(current,sha256(current).hexdigest(),requests)
    if audit.get('allocated_vector_count',0)+sum(row['added_count'] for row in allocated['new_vectors'])>MAX_LEDGER_VECTORS:
        raise ImportError('Face ledger exceeds its allocated vector budget')
    result=dict(schema_version=GROUP_SCHEMA if ledger['schema_version']==GROUP_SCHEMA else VECTOR_SCHEMA,source_sha256=ledger['source_sha256'],
                source_byte_length=ledger['source_byte_length'],operations=deepcopy(operations))
    result['operations'].append(dict(kind='allocate_vectors',input_sha256=sha256(current).hexdigest(),
        proposed_sha256=allocated['proposed_sha256'],requests=deepcopy(requests)))
    qualified,report=replay_face_ledger(original,result)
    return qualified,result,report


def append_group_ledger(original,ledger,requests):
    current,audit=replay_face_ledger(original,ledger)
    operations=_operations(ledger)
    if len(operations)>=MAX_OPERATIONS:
        raise ImportError('Face ledger exceeds its operation budget')
    reserved_groups={group['group_id'] for op in operations if op['kind']=='allocate_groups' for group in op['requests']}
    candidate,_,allocated=_apply_group_allocation(current,{row['face_id']:row for row in audit['faces']},
        requests,_reserved_faces(operations),reserved_groups)
    result=dict(schema_version=GROUP_SCHEMA,source_sha256=ledger['source_sha256'],
        source_byte_length=ledger['source_byte_length'],operations=deepcopy(operations))
    result['operations'].append(dict(kind='allocate_groups',input_sha256=sha256(current).hexdigest(),
        proposed_sha256=allocated['proposed_sha256'],requests=deepcopy(requests)))
    qualified,report=replay_face_ledger(original,result)
    return qualified,result,report


def qualify_face_ledger(original, ledger, candidate):
    expected, audit = replay_face_ledger(original, ledger)
    if candidate != expected:
        raise ImportError('Face ledger candidate differs from the complete replayed model')
    return audit
