"""Remove one authored seed, rebasing recipe donors without moving survivors."""
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
    raw,provenance,floor,current,allocations=_context(project,scene,key)
    before=deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT))
    selected=next((a for a in allocations if a['placement_id']==placement_id),None)
    if before is None or selected is None:raise ProjectError('Removal requires an existing authored decoration')
    binding,rebases=removed_binding(raw,floor,before,placement_id)
    _,_,_,_,_,_,transformed,_=context(project,scene)
    if binding is None:candidate,remaining=transformed,[]
    else:
        validate(project,owner(scene),binding)
        candidate,remaining=compose(project,scene,raw,provenance,floor,transformed,binding)
    expected=bytearray(current);at=selected['record_index']*32;cell_at=0x8000+selected['target_cell']*2
    if raw[at:at+32]!=bytes(32):raise ProjectError('Removed decoration no longer owns an original unused zero record')
    expected[at:at+32]=raw[at:at+32];expected[cell_at:cell_at+2]=raw[cell_at:cell_at+2]
    if candidate!=bytes(expected):raise ProjectError('Removal or donor rebasing changed another native record, cell or opaque byte')
    old=decode_worldmap_placements(current,floor,scene=scene);new=decode_worldmap_placements(candidate,floor,scene=scene)
    old_seeds={p['entity_id']:p for p in old['placements']};new_seeds={p['entity_id']:p for p in new['placements']}
    native_id=selected['native_seed']['entity_id']
    if (set(new_seeds)!=set(old_seeds)-{native_id} or old['unresolved']!=new['unresolved']
            or old['coverage']['excluded']!=new['coverage']['excluded']
            or any(seed!=new_seeds[i] for i,seed in old_seeds.items() if i!=native_id)):
        raise ProjectError('Removal changed a surviving seed or unresolved native coverage')
    result=dict(schema_version='legaia.worldmap-decoration-removal-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=provenance,placement_id=placement_id,current_map_sha256=sha256(current).hexdigest(),
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=base64.b64encode(candidate).decode('ascii'),
        before_binding=before,binding=binding,audit=dict(removed=selected,rebased_donors=rebases,remaining_allocations=remaining,
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            scope='authored-decoration-removal-only',gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>2*1024*1024:raise ProjectError('Decoration removal Review exceeds its response budget')
    _fresh(project,key)
    return result


def apply(project, command):
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_id','review_key'} or command['type']!='remove_worldmap_authored_placement':
        raise ProjectError('Decoration removal requires exact reviewed identity')
    result=review(project,command['scene'],command['source_key'],command['placement_id'])
    if result['review_key']!=command['review_key']:raise ProjectError('Decoration removal Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier))
    after={COMPONENT:deepcopy(result['binding'])} if result['binding'] is not None else None
    if after is None:project.overrides.pop(identifier,None)
    else:project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
