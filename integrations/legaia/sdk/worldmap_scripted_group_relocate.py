"""Atomic native cell translation for saved scripted groups and donor references."""
from base64 import b64decode,b64encode
from copy import deepcopy
from hashlib import sha256
import struct
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError,digest
from .worldmap_scripted_placement_allocation import source,_inputs,_fresh,_bounded
from .worldmap_scripted_placement_binding import COMPONENT,owner,read_base,validate,merge_current,replay


def review(project,scene,key,placement_ids,delta):
    if (not isinstance(placement_ids,list) or not 2<=len(placement_ids)<=32
            or any(not isinstance(i,str) for i in placement_ids) or placement_ids!=sorted(set(placement_ids))):
        raise ProjectError('Scripted group relocation requires 2..32 sorted unique saved UUIDs')
    if (not isinstance(delta,dict) or set(delta)!={'col','row'}
            or any(type(v) is not int or not -127<=v<=127 for v in delta.values())):
        raise ProjectError('Scripted group relocation requires bounded native column/row deltas')
    receipt=source(project,scene,key);before=receipt['binding']
    indexed={a['placement_id']:a for a in receipt['authored_scripted_placements']}
    if before is None or any(i not in indexed for i in placement_ids):
        raise ProjectError('Scripted group relocation requires saved authored UUID ownership')
    selected=[indexed[i] for i in placement_ids];destinations={}
    vacated={c for a in selected for c in (a['target_cell'],a['anchor_cell'])}
    for a in selected:
        col=a['target_cell']%128+delta['col'];row=a['target_cell']//128+delta['row']
        if not 0<=col<128 or not 0<=row<128:raise ProjectError('Scripted group relocation leaves the native grid')
        target=row*128+col
        if target not in receipt['target_cells'] and target not in vacated:
            raise ProjectError('Scripted group relocation target has another Current owner')
        destinations[a['placement_id']]=target
    base=read_base(project,before);binding=deepcopy(before);found=[];dependents=[];prior_moves={}
    for operation in binding['operations']:
        for request in operation['requests']:
            if request['donor_cell'] in prior_moves:
                target=prior_moves[request['donor_cell']]
                if target!=request['donor_cell']:
                    request['donor_cell']=target;dependents.append(request['placement_id'])
        for request in operation['requests']:
            if request['placement_id'] in destinations:
                request['target_cell']=destinations[request['placement_id']];found.append(request['placement_id'])
        for request in operation['requests']:
            identifier=request['placement_id']
            if identifier in destinations:prior_moves[indexed[identifier]['target_cell']]=destinations[identifier]
    if len(found)!=len(selected) or set(found)!=set(placement_ids):
        raise ProjectError('Scripted group relocation has ambiguous retained ownership')
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    _,old_audits=replay(base,fallback,man,floor,before)
    canonical=base;audits=[]
    # Destination records are unowned in the retained base. Read their literal
    # environment bytes independently of every proposed allocator output.
    environments={}
    for identifier,cell in destinations.items():
        at=(struct.unpack_from('<H',base,32768+cell*2)[0]&511)*32
        environments[identifier]=base[at+20:at+24]
    for operation in binding['operations']:
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,operation['requests'],relocation_offset=operation['relocation_offset'],allow_model_override=binding['schema_version']=='legaia.worldmap-scripted-placement-ledger.v2')
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    validate(project,owner(scene),binding)
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits)
    current=b64decode(receipt['current_map_base64']);expected=bytearray(current);anchors={}
    for a in selected:
        dc,dr=struct.unpack_from('<2b',current,a['record_index']*32+6);target=destinations[a['placement_id']]
        col=target%128+dc;row=target//128+dr
        if not 0<=col<128 or not 0<=row<128:raise ProjectError('Scripted group footprint anchor leaves the native grid')
        anchors[a['placement_id']]=row*128+col
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    after={a['placement_id']:a for a in allocations}
    for a in selected:
        edited=after[a['placement_id']]
        if (edited['script_id']!=a['script_id'] or edited['record_index']!=a['record_index']
                or edited['target_cell']!=destinations[a['placement_id']] or edited['anchor_cell']!=anchors[a['placement_id']]):
            raise ProjectError('Scripted group relocation changed a native record or shared script')
    # Restore all old footprints first, allowing the translated group to occupy
    # cells vacated by other selected members. Literal native rows are preserved.
    for cell in vacated:
        at=32768+cell*2;expected[at:at+2]=normal[at:at+2]
    for a in selected:
        at=32768+destinations[a['placement_id']]*2;word=struct.unpack_from('<H',normal,at)[0]
        struct.pack_into('<H',expected,at,(word&~511)|a['record_index'])
        at=a['record_index']*32;expected[at+20:at+24]=environments[a['placement_id']]
    for a in selected:
        at=32768+anchors[a['placement_id']]*2
        struct.pack_into('<H',expected,at,struct.unpack_from('<H',expected,at)[0]|1024)
    bind_indices={};by_bind={a['bind_id']:a for a in selected}
    for old,new in zip(old_audits,audits):
        ob,nb=old['bind_allocation'],new['bind_allocation']
        if ob['proposed_table_offset']!=nb['proposed_table_offset'] or ob['proposed_row_count']!=nb['proposed_row_count']:
            raise ProjectError('Scripted group relocation changed retained bind-table capacity')
        for a in ob['allocations']:
            if a['bind_id'] in by_bind:bind_indices[a['bind_id']]=a['record_index']
        for bind_id,index in bind_indices.items():
            cell=anchors[by_bind[bind_id]['placement_id']]
            at=65536+nb['proposed_table_offset']+4*index;expected[at:at+2]=bytes((cell%128,cell//128))
    if set(bind_indices)!=set(by_bind) or candidate!=bytes(expected):
        raise ProjectError('Scripted group relocation changed unrelated bytes or donor descendants')
    original=decode_worldmap_placements(current,floor,scene=scene)
    decoded=decode_worldmap_placements(candidate,floor,scene=scene);seeds={s['source_cell']:s for s in decoded['placements']}
    if (decoded['coverage']!=original['coverage'] or decoded['unresolved']!=original['unresolved']
            or set(seeds)!=({s['source_cell'] for s in original['placements']}-{a['target_cell'] for a in selected})|set(destinations.values())
            or any(seeds.get(s['source_cell'])!=s for s in original['placements'] if s['source_cell'] not in {a['target_cell'] for a in selected})):
        raise ProjectError('Scripted relocation changed other native placements or coverage')
    for allocation in allocations:allocation['native_seed']=deepcopy(seeds[allocation['target_cell']])
    result=dict(schema_version='legaia.worldmap-scripted-group-relocation-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=receipt['source_record'],placement_ids=deepcopy(placement_ids),delta=deepcopy(delta),
        current_map_sha256=receipt['current_map_sha256'],current_man_sha256=receipt['current_man_sha256'],
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=b64encode(candidate).decode('ascii'),
        before_binding=deepcopy(before),binding=binding,audit=dict(before=deepcopy(selected),after=[deepcopy(a) for i in placement_ids for a in allocations if a['placement_id']==i],
            dependent_donor_placements=dependents,authored_scripted_placements=allocations,scope='authored-scripted-group-relocation-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_ids','delta','review_key'} or command['type']!='relocate_worldmap_scripted_group':
        raise ProjectError('Scripted group relocation Apply requires exact reviewed UUIDs and grid delta')
    result=review(project,command['scene'],command['source_key'],command['placement_ids'],command['delta'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted relocation Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    if before==after:return
    _fresh(project,command['source_key']);project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
