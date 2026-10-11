"""Relocate a saved scripted UUID without changing its shared native script."""
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
import struct
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError,digest
from .worldmap_scripted_placement_allocation import source,_inputs,_fresh,_bounded
from .worldmap_scripted_placement_binding import COMPONENT,owner,read_base,validate,merge_current,replay


def review(project,scene,key,placement_id,target_cell):
    if type(target_cell) is not int or not 0<=target_cell<16384:
        raise ProjectError('Scripted relocation requires a native target cell 0..16383')
    receipt=source(project,scene,key);before=receipt['binding']
    selected=next((a for a in receipt['authored_scripted_placements'] if a['placement_id']==placement_id),None)
    if before is None or selected is None:raise ProjectError('Scripted relocation requires a saved authored UUID')
    old_cell=selected['target_cell']
    if target_cell!=old_cell and target_cell not in receipt['target_cells']:
        raise ProjectError('Scripted relocation target has another Current owner')
    base=read_base(project,before);binding=deepcopy(before);found=0;dependents=[]
    for operation in binding['operations']:
        # Donor cells address the input of an operation, not requests in that same operation.
        for request in operation['requests']:
            if found and request['donor_cell']==old_cell:
                request['donor_cell']=target_cell;dependents.append(request['placement_id'])
        for request in operation['requests']:
            if request['placement_id']==placement_id:request['target_cell']=target_cell;found+=1
    if found!=1:raise ProjectError('Scripted relocation has ambiguous retained request ownership')
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    _,old_audits=replay(base,fallback,man,floor,before)
    canonical=base;audits=[];destination_environment=None
    for operation in binding['operations']:
        if any(r['placement_id']==placement_id for r in operation['requests']):
            record=struct.unpack_from('<H',canonical,0x8000+target_cell*2)[0]&511
            destination_environment=canonical[record*32+20:record*32+24]
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,operation['requests'],relocation_offset=operation['relocation_offset'],allow_model_override=binding['schema_version']=='legaia.worldmap-scripted-placement-ledger.v2')
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    validate(project,owner(scene),binding)
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits)
    current=b64decode(receipt['current_map_base64']);expected=bytearray(current)
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    edited=next(a for a in allocations if a['placement_id']==placement_id)
    if edited['script_id']!=selected['script_id'] or edited['record_index']!=selected['record_index']:
        raise ProjectError('Scripted relocation changed its model record or shared script')
    # Independent literal native patch: restore the old footprint, link the new
    # footprint, inherit destination environment bytes, and move the UUID bind
    # row in every retained primary-table copy. Other table bytes stay exact.
    for cell in {old_cell,selected['anchor_cell']}:
        at=0x8000+cell*2;expected[at:at+2]=normal[at:at+2]
    at=0x8000+target_cell*2;word=struct.unpack_from('<H',normal,at)[0]
    struct.pack_into('<H',expected,at,(word&~511)|selected['record_index'])
    at=0x8000+edited['anchor_cell']*2
    struct.pack_into('<H',expected,at,struct.unpack_from('<H',expected,at)[0]|0x400)
    at=selected['record_index']*32;expected[at+20:at+24]=destination_environment
    bind_index=None
    for old,new in zip(old_audits,audits):
        ob,nb=old['bind_allocation'],new['bind_allocation']
        if ob['proposed_table_offset']!=nb['proposed_table_offset'] or ob['proposed_row_count']!=nb['proposed_row_count']:
            raise ProjectError('Scripted relocation changed retained bind-table capacity')
        for allocation in ob['allocations']:
            if allocation['bind_id']==selected['bind_id']:bind_index=allocation['record_index']
        if bind_index is not None:
            at=0x10000+nb['proposed_table_offset']+4*bind_index
            expected[at:at+2]=bytes((edited['anchor_cell']%128,edited['anchor_cell']//128))
    if bind_index is None or candidate!=bytes(expected):
        raise ProjectError('Scripted relocation changed unrelated bytes or donor descendants')
    original=decode_worldmap_placements(current,floor,scene=scene)
    decoded=decode_worldmap_placements(candidate,floor,scene=scene);seeds={s['source_cell']:s for s in decoded['placements']}
    if (decoded['coverage']!=original['coverage'] or decoded['unresolved']!=original['unresolved']
            or set(seeds)!=({s['source_cell'] for s in original['placements']}-{old_cell})|{target_cell}
            or any(seeds.get(s['source_cell'])!=s for s in original['placements'] if s['source_cell']!=old_cell)):
        raise ProjectError('Scripted relocation changed other native placements or coverage')
    for allocation in allocations:allocation['native_seed']=deepcopy(seeds[allocation['target_cell']])
    edited=next(a for a in allocations if a['placement_id']==placement_id)
    result=dict(schema_version='legaia.worldmap-scripted-relocation-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=receipt['source_record'],placement_id=placement_id,target_cell=target_cell,
        current_map_sha256=receipt['current_map_sha256'],current_man_sha256=receipt['current_man_sha256'],
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=b64encode(candidate).decode('ascii'),
        before_binding=deepcopy(before),binding=binding,audit=dict(before=deepcopy(selected),after=edited,
            dependent_donor_placements=dependents,authored_scripted_placements=allocations,scope='authored-scripted-relocation-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_id','target_cell','review_key'} or command['type']!='relocate_worldmap_scripted_placement':
        raise ProjectError('Scripted relocation Apply requires exact reviewed identity and target cell')
    result=review(project,command['scene'],command['source_key'],command['placement_id'],command['target_cell'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted relocation Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    if before==after:return
    _fresh(project,command['source_key']);project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
