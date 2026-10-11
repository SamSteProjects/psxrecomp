"""Reviewed saved scripted UUID removal with explicit donor cascade."""
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
import struct
from importer.worldmap_object_bind_allocation import _tables
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError,digest
from .worldmap_scripted_placement_allocation import source,_inputs,_fresh,_bounded
from .worldmap_scripted_placement_binding import COMPONENT,owner,read_base,validate,merge_current,replay


def removal_ids(binding,placement_id):
    """Resolve donor edges against each operation's input, then close descendants."""
    grouped=isinstance(placement_id,list);ids=placement_id if grouped else [placement_id]
    if (not 1<=len(ids)<=32 or any(not isinstance(i,str) for i in ids) or ids!=sorted(set(ids))):
        raise ProjectError('Scripted removal requires 1..32 sorted unique saved UUIDs')
    prior={};children={};ordered=[]
    for operation in binding['operations']:
        for request in operation['requests']:
            identifier=request['placement_id'];ordered.append(identifier)
            donor=prior.get(request['donor_cell'])
            if donor is not None:children.setdefault(donor,[]).append(identifier)
        for request in operation['requests']:prior[request['target_cell']]=request['placement_id']
    if any(i not in ordered for i in ids):raise ProjectError('Scripted removal requires a saved authored UUID')
    removed=set(ids);queue=list(ids)
    while queue:
        for identifier in children.get(queue.pop(),[]):
            if identifier not in removed:removed.add(identifier);queue.append(identifier)
    return [identifier for identifier in ordered if identifier in removed]


def review(project,scene,key,placement_id,cascade):
    if type(cascade) is not bool:raise ProjectError('Scripted removal requires explicit boolean cascade scope')
    receipt=source(project,scene,key);before=receipt['binding']
    if before is None:raise ProjectError('Scripted removal requires a saved placement ledger')
    grouped=isinstance(placement_id,list);ids=placement_id if grouped else [placement_id]
    removed=removal_ids(before,placement_id)
    if set(removed)-set(ids) and not cascade:raise ProjectError('Scripted donor has dependent placements; explicitly review cascade removal')
    removed_set=set(removed);base=read_base(project,before);binding=deepcopy(before)
    binding['operations']=[{**operation,'requests':[r for r in operation['requests'] if r['placement_id'] not in removed_set]} for operation in binding['operations']]
    binding['operations']=[operation for operation in binding['operations'] if operation['requests']]
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    _,old_audits=replay(base,fallback,man,floor,before)
    canonical=base;audits=[]
    for operation in binding['operations']:
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,operation['requests'],relocation_offset=operation['relocation_offset'],allow_model_override=binding['schema_version']=='legaia.worldmap-scripted-placement-ledger.v2')
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    if binding['operations']:validate(project,owner(scene),binding)
    else:binding=None
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits) if audits else normal
    current=b64decode(receipt['current_map_base64']);expected=bytearray(current)
    deleted=[deepcopy(a) for a in receipt['authored_scripted_placements'] if a['placement_id'] in removed_set]
    for allocation in deleted:
        at=allocation['record_index']*32;expected[at:at+32]=normal[at:at+32]
        for cell in {allocation['target_cell'],allocation['anchor_cell']}:
            at=0x8000+cell*2;expected[at:at+2]=normal[at:at+2]
    # Rebuild complete historical primary-table copies literally from original
    # rows and the already qualified old UUID bind payloads, without using the
    # proposed allocator's output rows or change list as our oracle.
    payloads={}
    for audit in old_audits:
        b=audit['bind_allocation'];at=0x10000+b['proposed_table_offset'];end=at+4*b['proposed_row_count']
        expected[at:end]=normal[at:end]
        for allocation in b['allocations']:payloads[allocation['bind_id']]=bytes.fromhex(allocation['after_hex'])
    expected[0x10006:0x1000a]=normal[0x10006:0x1000a]
    tables,_=_tables(base[0x10000:]);rows=[bytes(row) for row in tables[1][1]]
    for operation in (binding or {}).get('operations',[]):
        rows.extend(payloads[r['placement_id'].replace('placement://','bind://',1)] for r in operation['requests'])
        at=0x10000+operation['relocation_offset'];expected[at:at+4*len(rows)]=b''.join(rows)
        struct.pack_into('<2h',expected,0x10006,operation['relocation_offset'],len(rows))
    if candidate!=bytes(expected):raise ProjectError('Scripted removal changed unrelated bytes or remaining placements')
    original=decode_worldmap_placements(current,floor,scene=scene);decoded=decode_worldmap_placements(candidate,floor,scene=scene)
    seeds={s['source_cell']:s for s in decoded['placements']};removed_cells={a['target_cell'] for a in deleted}
    if (set(seeds)!={s['source_cell'] for s in original['placements']}-removed_cells
            or decoded['unresolved']!=original['unresolved']
            or any(seeds.get(s['source_cell'])!=s for s in original['placements'] if s['source_cell'] not in removed_cells)):
        raise ProjectError('Scripted removal changed other native membership or source positions')
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    for allocation in allocations:allocation['native_seed']=deepcopy(seeds[allocation['target_cell']])
    result=dict(schema_version='legaia.worldmap-scripted-removal-review.v2' if grouped else 'legaia.worldmap-scripted-removal-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=receipt['source_record'],**({'placement_ids':deepcopy(ids)} if grouped else {'placement_id':placement_id}),cascade=cascade,
        current_map_sha256=receipt['current_map_sha256'],current_man_sha256=receipt['current_man_sha256'],
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=b64encode(candidate).decode('ascii'),
        before_binding=deepcopy(before),binding=binding,audit=dict(removed_placement_ids=removed,removed_placements=deleted,
            authored_scripted_placements=allocations,scope='authored-scripted-group-removal-only' if grouped else 'authored-scripted-removal-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    grouped=isinstance(command,dict) and command.get('type')=='remove_worldmap_scripted_placements'
    identity='placement_ids' if grouped else 'placement_id'
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key',identity,'cascade','review_key'} or command['type']!=('remove_worldmap_scripted_placements' if grouped else 'remove_worldmap_scripted_placement') or grouped!=isinstance(command[identity],list):
        raise ProjectError('Scripted removal Apply requires exact reviewed identity and cascade scope')
    result=review(project,command['scene'],command['source_key'],command[identity],command['cascade'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted removal Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])} if result['binding'] else None
    _fresh(project,command['source_key'])
    if after is None:project.overrides.pop(identifier,None)
    else:project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
