"""Atomic saved scripted UUID transforms with a complete literal MAP oracle."""
from base64 import b64decode, b64encode
from copy import deepcopy
from hashlib import sha256
import struct

from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError, digest
from .worldmap_placements import values
from .worldmap_scripted_placement_allocation import source, _inputs, _fresh, _bounded
from .worldmap_scripted_placement_binding import COMPONENT, owner, read_base, validate, merge_current


def entries(value):
    if not isinstance(value, list) or not 2 <= len(value) <= 32:
        raise ProjectError('Scripted group transform requires two to thirty-two saved UUIDs')
    result=[];seen=set()
    for entry in value:
        if (not isinstance(entry,dict) or set(entry)!={'placement_id','values'}
                or not isinstance(entry['placement_id'],str) or entry['placement_id'] in seen):
            raise ProjectError('Scripted group transform requires unique UUIDs and exact values')
        seen.add(entry['placement_id'])
        result.append(dict(placement_id=entry['placement_id'],values=values(entry['values'])))
    return sorted(result,key=lambda e:e['placement_id'])


def review(project,scene,key,requested):
    requested=entries(requested)
    receipt=source(project,scene,key);before=receipt['binding']
    selected={a['placement_id']:a for a in receipt['authored_scripted_placements']}
    edits={e['placement_id']:e['values'] for e in requested}
    if before is None or not set(edits).issubset(selected):
        raise ProjectError('Scripted group transform requires saved authored UUID ownership')
    base=read_base(project,before);binding=deepcopy(before);found=[]
    for operation in binding['operations']:
        for request in operation['requests']:
            if request['placement_id'] in edits:
                request['values']=deepcopy(edits[request['placement_id']]);found.append(request['placement_id'])
    if len(found)!=len(edits) or set(found)!=set(edits):
        raise ProjectError('Scripted group transform has ambiguous retained request ownership')
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    canonical=base;audits=[]
    for operation in binding['operations']:
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,
            operation['requests'],relocation_offset=operation['relocation_offset'])
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    validate(project,owner(scene),binding)
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits)
    current=b64decode(receipt['current_map_base64']);expected=bytearray(current);current_values=[];native_ids=set()
    for entry in requested:
        allocation=selected[entry['placement_id']];at=allocation['record_index']*32;value=entry['values']
        native_id=allocation['native_seed']['entity_id']
        if native_id in native_ids:raise ProjectError('Scripted group has duplicate native record owners')
        native_ids.add(native_id)
        yaw=struct.unpack_from('<H',current,at+10)[0]
        current_values.append(dict(placement_id=entry['placement_id'],values=dict(
            offset=dict(zip(('x','y','z'),struct.unpack_from('<3h',current,at))),yaw_units=yaw&4095)))
        struct.pack_into('<3h',expected,at,*(value['offset'][axis] for axis in ('x','y','z')))
        struct.pack_into('<H',expected,at+10,(yaw&0xf000)|value['yaw_units'])
    if candidate!=bytes(expected):
        raise ProjectError('Scripted group transform changed unrelated bytes or a donor descendant')
    decoded=decode_worldmap_placements(candidate,floor,scene=scene);seeds={s['entity_id']:s for s in decoded['placements']}
    original=decode_worldmap_placements(current,floor,scene=scene)
    if (decoded['coverage']!=original['coverage'] or decoded['unresolved']!=original['unresolved']
            or set(seeds)!={s['entity_id'] for s in original['placements']}
            or any(seeds[s['entity_id']]!=s for s in original['placements'] if s['entity_id'] not in native_ids)):
        raise ProjectError('Scripted group transform changed native membership or another placement')
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    for allocation in allocations:
        allocation['native_seed']=deepcopy(seeds[allocation['native_seed']['entity_id']])
        old=selected[allocation['placement_id']]
        if allocation['script_id']!=old['script_id'] or allocation['target_cell']!=old['target_cell']:
            raise ProjectError('Scripted group transform changed a shared script or anchor owner')
    result=dict(schema_version='legaia.worldmap-scripted-group-transform-review.v1',
        project_path=str(project.root),scene=scene,source_key=key,source_record=receipt['source_record'],
        entries=requested,current_values=current_values,current_map_sha256=receipt['current_map_sha256'],
        current_man_sha256=receipt['current_man_sha256'],proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=b64encode(candidate).decode('ascii'),before_binding=deepcopy(before),binding=binding,
        audit=dict(before=[deepcopy(selected[e['placement_id']]) for e in requested],
            after=[deepcopy(a) for e in requested for a in allocations if a['placement_id']==e['placement_id']],
            authored_scripted_placements=allocations,scope='authored-scripted-group-transform-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    if (not isinstance(command,dict) or set(command)!={'type','scene','source_key','entries','review_key'}
            or command['type']!='transform_worldmap_scripted_placements'):
        raise ProjectError('Scripted group Apply requires exact reviewed UUIDs and values')
    result=review(project,command['scene'],command['source_key'],command['entries'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted group Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    if before==after:return
    _fresh(project,command['source_key']);project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
