"""Complete Current/Proposed native World seeds with distinct authored entities."""
from copy import deepcopy
from hashlib import sha256
import base64

from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_placements import context, patch
from .worldmap_placement_allocation_binding import COMPONENT, owner, compose as compose_map

_DEFAULT = object()


def compose(project, geometry, *, transform_entries=None, allocation_binding=_DEFAULT):
    scene = geometry['scene']
    raw,provenance,records,_,floor,transform_binding,transformed,_ = context(project,scene)
    source = geometry['source_record']
    if (source['disc_sha256'] != provenance['source_disc_sha256']
            or source['map_sha256'] != provenance['source_map_sha256']
            or source['floor_lut_sha256'] != provenance['source_floor_lut_sha256']):
        raise ProjectError('Current World placement geometry and native source provenance differ')
    held_binding = project.overrides.get(owner(scene),{}).get(COMPONENT)
    current_map,_ = compose_map(project,scene,raw,provenance,floor,transformed)
    active = held_binding if allocation_binding is _DEFAULT else allocation_binding
    entries = (transform_binding or {}).get('entries',{}) if transform_entries is None else transform_entries
    exported_base,_,_ = patch(raw,records,entries,scene=scene,floor=floor)
    # An explicit null allocation view must not accidentally pick the current
    # binding via the map helper's default lookup.
    exported_map,allocations = compose_map(project,scene,raw,provenance,floor,exported_base,active) if active else (exported_base,[])
    indexed = {p['entity_id']:p for p in decode_worldmap_placements(exported_map,floor,scene=scene)['placements']}
    graph = geometry['scene_graph'];assets = {a['asset_id']:a for a in graph['assets']}
    if len(assets) != len(graph['assets']):
        raise ProjectError('Current World placement assets have ambiguous native owners')
    changed = 0
    for entity in graph['entities']:
        if entity['placement_scope'] == 'source_ground': continue
        seed = indexed.get(entity['entity_id']);record=f"{entity['object_record_index']:04d}";row=records.get(record)
        if (not seed or not row or seed['object_record_index'] != entity['object_record_index']
                or seed['model_pool_index'] != entity['model_pool_index']
                or entity['source_record_sha256'] != row['source_record_sha256']):
            raise ProjectError('Current World placement changed an original native seed owner')
        changed += seed['source_to_world'] != entity['source_to_world']
        entity.update(retail_source_position=deepcopy(entity['source_position']),retail_source_to_world=list(entity['source_to_world']),
            source_position=deepcopy(seed['source_position']),source_to_world=list(seed['source_to_world']),
            source_rotation_psx=deepcopy(seed['source_rotation_psx']),
            authored_source_transform=dict(record_id=record,retail_record_sha256=row['source_record_sha256'],
                exported_record_sha256=seed['source_record_sha256'],values=deepcopy(entries.get(record,{}).get('values'))))
    existing_ids = {e['entity_id'] for e in graph['entities']}
    for allocation in allocations:
        seed = indexed.get(allocation['native_seed']['entity_id'])
        asset_id=f"asset://{scene}/worldmap/models/{allocation['model_pool_index']:04d}"
        if (not seed or seed != allocation['native_seed'] or asset_id not in assets
                or seed['entity_id'] in existing_ids):
            raise ProjectError('Allocated World placement has no complete qualified native model or seed')
        uuid = allocation['placement_id'].rsplit('/',1)[1]
        entity_id=f'scene://{scene}/worldmap/authored-placements/{uuid}'
        if entity_id in existing_ids: raise ProjectError('Allocated World scene identity is duplicated')
        graph['entities'].append(dict(deepcopy(seed),entity_id=entity_id,native_entity_id=seed['entity_id'],
            asset_id=asset_id,renderable=True,placement_scope='authored_spawn_seed',
            retail_source_position=None,retail_source_to_world=None,authored_placement=deepcopy(allocation)))
        existing_ids.add(entity_id)
    drawn=sum(len(assets[e['asset_id']]['preview']['triangles']) for e in graph['entities'])
    if len(graph['entities']) > 512 or drawn > 200000:
        raise ProjectError('Current World allocations exceed the entity or drawn triangle budget')
    graph['metrics'].update(entity_count=len(graph['entities']),drawn_triangle_count=drawn)
    graph['coverage'].update(candidate_count=graph['coverage']['candidate_count']+len(allocations),
        resolved_count=len(graph['entities'])-1,rendered_count=len(graph['entities'])-1)
    graph['limitations'].append('Authored decorations use native source seeds; collision, script behavior and live visibility remain unevaluated.')
    geometry['placement_layer']='current'
    geometry['authored_geometry']=bool(geometry.get('authored_geometry') or allocations or changed)
    geometry['placement_authoring']=dict(schema_version='legaia.worldmap-placement-scene.v1',scene=scene,
        source_key=state_key(project),source_record=deepcopy(provenance),source_map_sha256=sha256(raw).hexdigest(),
        current_map_sha256=sha256(current_map).hexdigest(),exported_map_sha256=sha256(exported_map).hexdigest(),
        retail_map_base64=base64.b64encode(raw).decode('ascii'),current_map_base64=base64.b64encode(current_map).decode('ascii'),
        exported_map_base64=base64.b64encode(exported_map).decode('ascii'),floor_lut=list(floor),
        authored_records=deepcopy(entries),allocation_binding=deepcopy(active),authored_allocations=deepcopy(allocations),
        changed_source_entity_count=changed,authored_entity_count=len(allocations),read_only=True,project_changed=False,
        gameplay_verified=False)
    return geometry['placement_authoring']


def inspect(project, scene, key, allocation_proposal=None, allocation_edit_proposal=None, allocation_remove_proposal=None, allocation_cell_proposal=None):
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('Current World scene requires fresh Edit source inputs')
    binding=_DEFAULT
    if sum(p is not None for p in (allocation_proposal,allocation_edit_proposal,allocation_remove_proposal,allocation_cell_proposal))>1:
        raise ProjectError('Choose one proposed World allocation or decoration transform')
    if allocation_cell_proposal is not None:
        if not isinstance(allocation_cell_proposal,dict) or set(allocation_cell_proposal) != {'placement_id','target_cell','review_key'}:
            raise ProjectError('Proposed cell relocation requires exact reviewed identity and destination')
        from .worldmap_placement_relocate import review
        reviewed=review(project,scene,key,allocation_cell_proposal['placement_id'],allocation_cell_proposal['target_cell'])
        if reviewed['review_key'] != allocation_cell_proposal['review_key']:
            raise ProjectError('Proposed cell relocation Review is stale')
        binding=reviewed['binding']
    if allocation_remove_proposal is not None:
        if not isinstance(allocation_remove_proposal,dict) or set(allocation_remove_proposal)!={'placement_id','review_key'}:
            raise ProjectError('Proposed removal requires exact reviewed authored identity')
        from .worldmap_placement_remove import review
        reviewed=review(project,scene,key,allocation_remove_proposal['placement_id'])
        if reviewed['review_key']!=allocation_remove_proposal['review_key']:raise ProjectError('Proposed removal Review is stale')
        binding=reviewed['binding']
    if allocation_edit_proposal is not None:
        if not isinstance(allocation_edit_proposal,dict) or set(allocation_edit_proposal) != {'placement_id','values','review_key'}:
            raise ProjectError('Proposed decoration transform requires exact reviewed identity and values')
        from .worldmap_placement_edit import review
        reviewed=review(project,scene,key,allocation_edit_proposal['placement_id'],allocation_edit_proposal['values'])
        if reviewed['review_key'] != allocation_edit_proposal['review_key']:
            raise ProjectError('Proposed decoration transform Review is stale')
        binding=reviewed['binding']
    if allocation_proposal is not None:
        if not isinstance(allocation_proposal,dict) or set(allocation_proposal) != {'requests','review_key'}:
            raise ProjectError('Proposed World scene requires exact reviewed allocation requests')
        from .worldmap_placement_allocation import review
        reviewed=review(project,scene,key,allocation_proposal['requests'])
        if reviewed['review_key'] != allocation_proposal['review_key']:
            raise ProjectError('Proposed World allocation scene Review is stale')
        binding=reviewed['binding']
    from .worldmap_geometry import inspect as inspect_geometry
    geometry=inspect_geometry(project,scene,key,texture_layer='current',model_layer='current')
    compose(project,geometry,allocation_binding=binding)
    geometry.update(representation='proposed-source' if allocation_proposal or allocation_edit_proposal or allocation_remove_proposal or allocation_cell_proposal else 'current-source',
        allocation_proposal=deepcopy(allocation_proposal))
    if allocation_edit_proposal is not None:
        geometry['allocation_edit_proposal']=deepcopy(allocation_edit_proposal)
    if allocation_remove_proposal is not None:geometry['allocation_remove_proposal']=deepcopy(allocation_remove_proposal)
    if allocation_cell_proposal is not None:geometry['allocation_cell_proposal']=deepcopy(allocation_cell_proposal)
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('Current World scene source changed during composition')
    import json
    if len(json.dumps(geometry,allow_nan=False).encode('utf-8')) > 32*1024*1024:
        raise ProjectError('Current World scene exceeds its response budget')
    return geometry
