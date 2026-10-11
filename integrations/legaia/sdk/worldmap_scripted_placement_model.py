"""Native model assignment preserving scripted UUIDs, shared scripts and donor descendants."""
from base64 import b64decode, b64encode
from copy import deepcopy
from hashlib import sha256
import struct

from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError, digest
from .worldmap_scripted_placement_allocation import source, _inputs, _fresh, _bounded
from .worldmap_scripted_placement_binding import COMPONENT, MODEL_SCHEMA, owner, read_base, validate, merge_current


def review(project,scene,key,placement_ids,model_pool_index):
    if (not isinstance(placement_ids,list) or not 1<=len(placement_ids)<=32
            or any(not isinstance(i,str) for i in placement_ids)
            or placement_ids!=sorted(set(placement_ids))):
        raise ProjectError('Scripted model assignment requires 1..32 sorted unique saved UUIDs')
    if type(model_pool_index) is not int or not 1<=model_pool_index<512:
        raise ProjectError('Scripted model assignment requires a nonzero native model index')
    receipt=source(project,scene,key);before=receipt['binding']
    selected={a['placement_id']:a for a in receipt['authored_scripted_placements']}
    if before is None or not set(placement_ids).issubset(selected):
        raise ProjectError('Scripted model assignment requires saved authored UUID ownership')
    from .worldmap_geometry import inspect
    geometry=inspect(project,scene,key,texture_layer='current',model_layer='current')
    asset_id=f'asset://{scene}/worldmap/models/{model_pool_index:04d}'
    asset=next((a for a in geometry['scene_graph']['assets'] if a['asset_id']==asset_id),None)
    if asset is None or not asset['preview'].get('vertices') or not asset['preview'].get('triangles'):
        raise ProjectError('Choose a qualified drawable Current kingdom model')
    base=read_base(project,before);binding=deepcopy(before)
    current=b64decode(receipt['current_map_base64'])
    models={i:struct.unpack_from('<H',current,a['record_index']*32+16)[0] for i,a in selected.items()}
    changed={i for i in placement_ids if models[i]!=model_pool_index}
    cells={selected[i]['target_cell'] for i in changed};pinned=[];found=[]
    if changed:
        binding['schema_version']=MODEL_SCHEMA
        for operation in binding['operations']:
            for request in operation['requests']:
                identifier=request['placement_id']
                if identifier in changed:
                    request['model_pool_index']=model_pool_index;found.append(identifier)
                elif identifier not in placement_ids and request['donor_cell'] in cells:
                    request['model_pool_index']=models[identifier]
                    pinned.append(dict(placement_id=identifier,model_pool_index=models[identifier]))
        if len(found)!=len(changed) or set(found)!=changed:
            raise ProjectError('Scripted model assignment has ambiguous retained request ownership')
    fallback=b64decode(receipt['fallback_base64']);man=b64decode(receipt['current_man_base64']);floor=receipt['floor_lut']
    canonical=base;audits=[]
    for operation in binding['operations']:
        canonical,audit=allocate_scripted_placements(canonical,fallback,man,floor,scene,
            operation['requests'],relocation_offset=operation['relocation_offset'],allow_model_override=binding['schema_version']=='legaia.worldmap-scripted-placement-ledger.v2')
        operation['proposed_map_sha256']=sha256(canonical).hexdigest();audits.append(audit)
    validate(project,owner(scene),binding)
    normal=_inputs(project,scene,key,include_scripted=False)[3]
    candidate=merge_current(base,canonical,normal,floor,scene,audits)
    expected=bytearray(current);native_ids=set()
    for identifier in placement_ids:
        allocation=selected[identifier];native_ids.add(allocation['native_seed']['entity_id'])
        struct.pack_into('<H',expected,allocation['record_index']*32+16,model_pool_index)
    if candidate!=bytes(expected):
        raise ProjectError('Scripted model assignment changed unrelated bytes or a donor descendant')
    decoded=decode_worldmap_placements(candidate,floor,scene=scene);seeds={s['entity_id']:s for s in decoded['placements']}
    original=decode_worldmap_placements(current,floor,scene=scene)
    if (decoded['coverage']!=original['coverage'] or decoded['unresolved']!=original['unresolved']
            or set(seeds)!={s['entity_id'] for s in original['placements']}
            or any(seeds[s['entity_id']]!=s for s in original['placements'] if s['entity_id'] not in native_ids)):
        raise ProjectError('Scripted model assignment transform changed native membership or another placement')
    allocations=[deepcopy(a) for audit in audits for a in audit['allocations']]
    for allocation in allocations:
        allocation['native_seed']=deepcopy(seeds[allocation['native_seed']['entity_id']])
        old=selected[allocation['placement_id']]
        if allocation['script_id']!=old['script_id'] or allocation['target_cell']!=old['target_cell']:
            raise ProjectError('Scripted model assignment transform changed a shared script or anchor owner')
    result=dict(schema_version='legaia.worldmap-scripted-model-review.v1',
        project_path=str(project.root),scene=scene,source_key=key,source_record=receipt['source_record'],
        placement_ids=deepcopy(placement_ids),model_pool_index=model_pool_index,asset_id=asset_id,
        model_source_record=deepcopy(asset['source_record']),current_map_sha256=receipt['current_map_sha256'],
        current_man_sha256=receipt['current_man_sha256'],proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=b64encode(candidate).decode('ascii'),before_binding=deepcopy(before),binding=binding,
        audit=dict(before=[deepcopy(selected[i]) for i in placement_ids],
            after=[deepcopy(a) for i in placement_ids for a in allocations if a['placement_id']==i],
            authored_scripted_placements=allocations,retained_child_models=pinned,scope='authored-scripted-model-only',
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result);_fresh(project,key)
    return _bounded(result)


def apply(project,command):
    if (not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_ids','model_pool_index','review_key'}
            or command['type']!='assign_worldmap_scripted_models'):
        raise ProjectError('Scripted model assignment Apply requires exact reviewed UUIDs and values')
    result=review(project,command['scene'],command['source_key'],command['placement_ids'],command['model_pool_index'])
    if result['review_key']!=command['review_key']:raise ProjectError('Scripted model assignment Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    if before==after:return
    _fresh(project,command['source_key']);project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
