"""Remove reviewed authored seeds, rebasing donors without moving survivors."""
from copy import deepcopy
from hashlib import sha256
import base64
import json

from importer.worldmap_placement_allocation import allocate
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError, digest
from .worldmap_placements import context
from .worldmap_placement_allocation import _context, _fresh
from .worldmap_placement_allocation_binding import COMPONENT, MODEL_SCHEMA, owner, validate, compose, replay


def removed_binding(raw, floor, binding, placement_id):
    result=deepcopy(binding)
    retained_models={a['placement_id']:a['model_pool_index'] for a in replay(raw,floor,binding)[1]} if binding['schema_version']==MODEL_SCHEMA else {}
    matches=[r for op in result['operations'] for r in op['requests'] if r['placement_id']==placement_id]
    if len(matches)!=1:raise ProjectError('Choose one retained authored decoration to remove')
    selected=matches[0];rebases=[]
    for op in result['operations']:
        for request in op['requests']:
            if request['placement_id']!=placement_id and request['donor_cell']==selected['target_cell']:
                rebases.append(dict(placement_id=request['placement_id'],before_donor_cell=request['donor_cell'],after_donor_cell=selected['donor_cell']))
                request['donor_cell']=selected['donor_cell']
                if retained_models:request['model_pool_index']=retained_models[request['placement_id']]
        op['requests']=[r for r in op['requests'] if r['placement_id']!=placement_id]
    result['operations']=[op for op in result['operations'] if op['requests']]
    if not result['operations']:return None,rebases
    current=raw
    for op in result['operations']:
        current,audit=allocate(current,floor,result['scene'],op['requests'])
        op['proposed_map_sha256']=audit['proposed_sha256']
    return result,rebases


def review(project, scene, key, placement_id):
    grouped = isinstance(placement_id, list)
    identifiers = placement_id if grouped else [placement_id]
    if (not 1 <= len(identifiers) <= 32 or any(not isinstance(i, str) for i in identifiers)
            or identifiers != sorted(set(identifiers))):
        raise ProjectError('Removal requires 1..32 sorted unique retained decoration identities')
    raw,provenance,floor,current,allocations=_context(project,scene,key)
    before=deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT))
    indexed={a['placement_id']:a for a in allocations}
    if before is None or any(i not in indexed for i in identifiers):raise ProjectError('Removal requires existing authored decorations')
    selected=[indexed[i] for i in identifiers]
    binding=before;rebases=[]
    for identifier in identifiers:
        binding,changed=removed_binding(raw,floor,binding,identifier)
        rebases.extend(changed)
    _,_,_,_,_,_,transformed,_=context(project,scene)
    if binding is None:candidate,remaining=transformed,[]
    else:
        validate(project,owner(scene),binding)
        candidate,remaining=compose(project,scene,raw,provenance,floor,transformed,binding)
    expected=bytearray(current)
    for item in selected:
        at=item['record_index']*32;cell_at=0x8000+item['target_cell']*2
        if raw[at:at+32]!=bytes(32):raise ProjectError('Removed decoration no longer owns an original unused zero record')
        expected[at:at+32]=raw[at:at+32];expected[cell_at:cell_at+2]=raw[cell_at:cell_at+2]
    if candidate!=bytes(expected):raise ProjectError('Removal or donor rebasing changed another native record, cell or opaque byte')
    old=decode_worldmap_placements(current,floor,scene=scene);new=decode_worldmap_placements(candidate,floor,scene=scene)
    old_seeds={p['entity_id']:p for p in old['placements']};new_seeds={p['entity_id']:p for p in new['placements']}
    native_ids={item['native_seed']['entity_id'] for item in selected}
    if (set(new_seeds)!=set(old_seeds)-native_ids or old['unresolved']!=new['unresolved']
            or old['coverage']['excluded']!=new['coverage']['excluded']
            or any(seed!=new_seeds[i] for i,seed in old_seeds.items() if i not in native_ids)):
        raise ProjectError('Removal changed a surviving seed or unresolved native coverage')
    result=dict(schema_version='legaia.worldmap-decoration-removal-review.v2' if grouped else 'legaia.worldmap-decoration-removal-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=provenance,**({'placement_ids':identifiers} if grouped else {'placement_id':placement_id}),current_map_sha256=sha256(current).hexdigest(),
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=base64.b64encode(candidate).decode('ascii'),
        before_binding=before,binding=binding,audit=dict(removed=selected if grouped else selected[0],rebased_donors=rebases,remaining_allocations=remaining,
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            scope='authored-decoration-group-removal-only' if grouped else 'authored-decoration-removal-only',gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>2*1024*1024:raise ProjectError('Decoration removal Review exceeds its response budget')
    _fresh(project,key)
    return result


def apply(project, command):
    grouped=isinstance(command,dict) and command.get('type')=='remove_worldmap_authored_placements'
    identity='placement_ids' if grouped else 'placement_id'
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key',identity,'review_key'} or command['type']!=('remove_worldmap_authored_placements' if grouped else 'remove_worldmap_authored_placement'):
        raise ProjectError('Decoration removal requires exact reviewed identity')
    if grouped != isinstance(command[identity],list):raise ProjectError('Removal command identity shape differs from its scope')
    result=review(project,command['scene'],command['source_key'],command[identity])
    if result['review_key']!=command['review_key']:raise ProjectError('Decoration removal Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier))
    after={COMPONENT:deepcopy(result['binding'])} if result['binding'] is not None else None
    if after is None:project.overrides.pop(identifier,None)
    else:project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
