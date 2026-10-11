"""Saved scripted UUID transforms through complete retained recipe replay."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import struct
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError,digest
from .worldmap_placements import values
from .worldmap_scripted_placement_allocation import source,_inputs,_fresh,_bounded
from .worldmap_scripted_placement_binding import COMPONENT,owner,read_base,validate,merge_current


def review(project,scene,key,placement_id,value):
    value=values(value)
    receipt=source(project,scene,key);before=receipt['binding']
    selected=next((a for a in receipt['authored_scripted_placements'] if a['placement_id']==placement_id),None)
    if before is None or selected is None:raise ProjectError('Scripted transform requires a saved authored UUID')
    base=read_base(project,before);binding=deepcopy(before);found=0
    for operation in binding['operations']:
        for request in operation['requests']:
            if request['placement_id']==placement_id:request['values']=deepcopy(value);found+=1
    if found!=1:raise ProjectError('Scripted transform has ambiguous retained request ownership')
    from base64 import b64decode
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    canonical=base;audits=[]
    for operation in binding['operations']:
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,operation['requests'],relocation_offset=operation['relocation_offset'])
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    validate(project,owner(scene),binding)
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits)
    current=b64decode(receipt['current_map_base64']);at=selected['record_index']*32
    expected=bytearray(current);struct.pack_into('<3h',expected,at,*(value['offset'][axis] for axis in ('x','y','z')))
    yaw=struct.unpack_from('<H',current,at+10)[0];struct.pack_into('<H',expected,at+10,(yaw&0xf000)|value['yaw_units'])
    if candidate!=bytes(expected):raise ProjectError('Scripted transform changed unrelated bytes or a later donor descendant')
    decoded=decode_worldmap_placements(candidate,floor,scene=scene);seeds={s['entity_id']:s for s in decoded['placements']}
    original=decode_worldmap_placements(current,floor,scene=scene);native_id=selected['native_seed']['entity_id']
    if (decoded['coverage']!=original['coverage'] or decoded['unresolved']!=original['unresolved']
            or set(seeds)!={s['entity_id'] for s in original['placements']}
            or any(seeds[s['entity_id']]!=s for s in original['placements'] if s['entity_id']!=native_id)):
        raise ProjectError('Scripted transform changed native membership or another placement')
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    for allocation in allocations:allocation['native_seed']=deepcopy(seeds[allocation['native_seed']['entity_id']])
    edited=next(a for a in allocations if a['placement_id']==placement_id)
    if edited['script_id']!=selected['script_id'] or edited['target_cell']!=selected['target_cell']:
        raise ProjectError('Scripted transform changed its shared script or anchor owner')
    result=dict(schema_version='legaia.worldmap-scripted-transform-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=receipt['source_record'],placement_id=placement_id,values=deepcopy(value),
        current_values=dict(offset=dict(zip(('x','y','z'),struct.unpack_from('<3h',current,at))),yaw_units=yaw&4095),
        current_map_sha256=receipt['current_map_sha256'],current_man_sha256=receipt['current_man_sha256'],
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=b64encode(candidate).decode('ascii'),
        before_binding=deepcopy(before),binding=binding,audit=dict(before=deepcopy(selected),after=edited,
            authored_scripted_placements=allocations,scope='authored-scripted-transform-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_id','values','review_key'} or command['type']!='set_worldmap_scripted_placement':
        raise ProjectError('Scripted transform Apply requires exact reviewed identity and values')
    result=review(project,command['scene'],command['source_key'],command['placement_id'],command['values'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted transform Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    if before==after:return
    _fresh(project,command['source_key']);project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
