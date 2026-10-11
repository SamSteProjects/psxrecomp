"""Source-qualified native model assignment with explicit child-model retention."""
from copy import deepcopy
from hashlib import sha256
import base64,json,struct
from importer.worldmap_placement_allocation import allocate
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError,digest
from .worldmap_placement_allocation import _context,_fresh
from .worldmap_placement_allocation_binding import COMPONENT,MODEL_SCHEMA,owner,validate,compose
from .worldmap_placements import context


def reassigned_binding(raw,floor,binding,allocations,placement_id,model_pool_index):
    if type(model_pool_index) is not int or not 1<=model_pool_index<512:
        raise ProjectError('Decoration model must be a nonzero native pool index')
    result=deepcopy(binding)
    requests=[r for op in result['operations'] for r in op['requests']]
    matches=[r for r in requests if r['placement_id']==placement_id]
    selected=next((a for a in allocations if a['placement_id']==placement_id),None)
    if len(matches)!=1 or selected is None:raise ProjectError('Choose one retained decoration to assign a model')
    if selected['model_pool_index']==model_pool_index:raise ProjectError('Decoration model is unchanged')
    retained={a['placement_id']:a['model_pool_index'] for a in allocations};pinned=[]
    for request in requests:
        if request['placement_id']!=placement_id and request['donor_cell']==selected['target_cell']:
            request['model_pool_index']=retained[request['placement_id']]
            pinned.append(dict(placement_id=request['placement_id'],model_pool_index=request['model_pool_index']))
    matches[0]['model_pool_index']=model_pool_index;result['schema_version']=MODEL_SCHEMA
    current=raw
    for op in result['operations']:
        current,audit=allocate(current,floor,result['scene'],op['requests'])
        op['proposed_map_sha256']=audit['proposed_sha256']
    return result,pinned


def review(project,scene,key,placement_id,model_pool_index):
    raw,provenance,floor,current,allocations=_context(project,scene,key)
    if type(model_pool_index) is not int or not 1<=model_pool_index<512:
        raise ProjectError('Decoration model must be a nonzero native pool index')
    from .worldmap_geometry import inspect
    geometry=inspect(project,scene,key,texture_layer='current',model_layer='current')
    asset_id=f'asset://{scene}/worldmap/models/{model_pool_index:04d}'
    asset=next((a for a in geometry['scene_graph']['assets'] if a['asset_id']==asset_id),None)
    if asset is None or not asset['preview'].get('vertices') or not asset['preview'].get('triangles'):
        raise ProjectError('Choose a qualified drawable Current kingdom model')
    before=deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT))
    selected=next((a for a in allocations if a['placement_id']==placement_id),None)
    if before is None or selected is None:raise ProjectError('Model assignment requires an existing authored decoration')
    binding,pinned=reassigned_binding(raw,floor,before,allocations,placement_id,model_pool_index)
    validate(project,owner(scene),binding)
    transformed=context(project,scene)[6]
    candidate,after=compose(project,scene,raw,provenance,floor,transformed,binding)
    expected=bytearray(current);struct.pack_into('<H',expected,selected['record_index']*32+16,model_pool_index)
    if candidate!=bytes(expected):raise ProjectError('Model assignment changed another model, transform or native byte')
    old=decode_worldmap_placements(current,floor,scene=scene);new=decode_worldmap_placements(candidate,floor,scene=scene)
    old_seeds={s['entity_id']:s for s in old['placements']};new_seeds={s['entity_id']:s for s in new['placements']}
    native_id=selected['native_seed']['entity_id']
    if (set(old_seeds)!=set(new_seeds) or old['coverage']!=new['coverage'] or old['unresolved']!=new['unresolved']
            or any(seed!=new_seeds[i] for i,seed in old_seeds.items() if i!=native_id)):
        raise ProjectError('Model assignment changed native membership, coverage or another seed')
    assigned=next(a for a in after if a['placement_id']==placement_id)
    result=dict(schema_version='legaia.worldmap-decoration-model-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=provenance,placement_id=placement_id,model_pool_index=model_pool_index,
        asset_id=asset_id,model_source_record=deepcopy(asset['source_record']),before_binding=before,binding=binding,
        current_map_sha256=sha256(current).hexdigest(),proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=base64.b64encode(candidate).decode('ascii'),audit=dict(before=selected,after=assigned,
            retained_child_models=pinned,changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            scope='authored-decoration-model-only',gameplay_verified=False),read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>2*1024*1024:raise ProjectError('Decoration model Review exceeds its response budget')
    _fresh(project,key)
    return result


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','scene','source_key','placement_id','model_pool_index','review_key'} or command['type']!='assign_worldmap_authored_model':
        raise ProjectError('Decoration model Apply requires exact reviewed identity and model')
    result=review(project,command['scene'],command['source_key'],command['placement_id'],command['model_pool_index'])
    if result['review_key']!=command['review_key']:raise ProjectError('Decoration model Review changed; review again')
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])}
    project.overrides[identifier]=after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
