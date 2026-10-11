"""Current scripted placement scene receipts, separate from decoration views."""
from base64 import b64decode
from copy import deepcopy
import json

from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_scripted_placement_allocation import source
from .worldmap_geometry import inspect as inspect_geometry


def inspect(project,scene,key):
    if project.mode!='edit' or key!=state_key(project):
        raise ProjectError('Scripted World scene requires fresh Edit source inputs')
    receipt=source(project,scene,key)
    geometry=inspect_geometry(project,scene,key,texture_layer='current',model_layer='current')
    provenance=receipt['source_record'];native=geometry['source_record']
    if any(native.get(a)!=provenance.get(b) for a,b in (
            ('disc_sha256','source_disc_sha256'),('map_sha256','source_map_sha256'),
            ('floor_lut_sha256','source_floor_lut_sha256'))):
        raise ProjectError('Scripted scene geometry differs from its immutable placement source')
    graph=geometry['scene_graph'];assets={a['asset_id']:a for a in graph['assets']}
    if len(assets)!=len(graph['assets']):raise ProjectError('Scripted scene model owners are duplicated')
    current=decode_worldmap_placements(b64decode(receipt['current_map_base64']),receipt['floor_lut'],scene=scene)
    seeds={s['entity_id']:s for s in current['placements']}
    allocations=receipt['authored_decorations']+receipt['authored_scripted_placements']
    authored={a['native_seed']['entity_id']:a for a in allocations}
    if len(authored)!=len(allocations):raise ProjectError('Authored World placements share a native seed owner')
    original={e['entity_id']:e for e in graph['entities'] if e['placement_scope']!='source_ground'}
    ground=[deepcopy(e) for e in graph['entities'] if e['placement_scope']=='source_ground']
    if len(original)+len(ground)!=len(graph['entities']) or len(ground)!=1:
        raise ProjectError('Scripted scene original entity ownership is ambiguous')
    entities=ground;seen=set();changed=0;scripted_ids={a['placement_id'] for a in receipt['authored_scripted_placements']}
    for seed in current['placements']:
        allocation=authored.get(seed['entity_id']);retail=original.get(seed['entity_id'])
        if allocation:
            if retail or seed!=allocation['native_seed']:
                raise ProjectError('Authored scripted scene seed conflicts with its native receipt')
            uuid=allocation['placement_id'].rsplit('/',1)[1]
            identity=f'scene://{scene}/worldmap/authored-placements/{uuid}'
            layer='scripted' if allocation['placement_id'] in scripted_ids else 'decoration'
            extra=dict(native_entity_id=seed['entity_id'],authored_placement=deepcopy(allocation),
                authored_placement_kind=layer,retail_seed=None,placement_scope='authored_scripted_seed' if layer=='scripted' else 'authored_spawn_seed')
        elif retail:
            identity=seed['entity_id'];extra=dict(retail_seed=deepcopy(retail))
            if seed['object_record_index']!=retail['object_record_index'] or seed['model_pool_index']!=retail['model_pool_index']:
                raise ProjectError('Current scripted scene changed an original native model owner')
            changed+=any(retail.get(k)!=v for k,v in seed.items())
        else:
            # Retail seeds whose models are unsupported remain in coverage.
            continue
        asset_id=f"asset://{scene}/worldmap/models/{seed['model_pool_index']:04d}"
        asset=assets.get(asset_id)
        if not asset or not asset['preview'].get('vertices') or not asset['preview'].get('triangles'):
            raise ProjectError('Scripted scene placement has no drawable qualified Current model')
        if identity in seen:raise ProjectError('Scripted scene authored identity is duplicated')
        seen.add(identity)
        entities.append(dict(deepcopy(seed),entity_id=identity,asset_id=asset_id,renderable=True,**extra))
    if not set(original).issubset(seeds) or not set(authored).issubset(seeds):
        raise ProjectError('Current scripted scene lost a retained placement owner')
    drawn=sum(len(assets[e['asset_id']]['preview']['triangles']) for e in entities)
    if len(entities)>512 or drawn>200000:raise ProjectError('Scripted scene exceeds its rendering budget')
    graph['entities']=entities
    graph['metrics'].update(entity_count=len(entities),drawn_triangle_count=drawn)
    # Keep the original model failure witnesses; Current decoding contributes
    # native membership and exclusions without claiming runtime visibility.
    unresolved=deepcopy(current['unresolved'])
    model_failures={e['entity_id']:e for e in graph['coverage'].get('unresolved',[]) if 'entity_id' in e}
    for seed in current['placements']:
        if seed['entity_id'] not in original and seed['entity_id'] not in authored:
            prior=model_failures.get(seed['entity_id'])
            if not prior or not isinstance(prior.get('reason'),str):
                raise ProjectError('Scripted scene lost its unsupported Retail model witness')
            unresolved.append(dict(deepcopy(prior),**seed))
    graph['coverage']=dict(current['coverage'],resolved_count=len(entities)-1,
        rendered_count=len(entities)-1,unresolved_count=len(unresolved),unresolved=unresolved)
    graph['limitations'].append('Current scripted placements retain shared scripts; runtime visibility and resting transforms are unverified.')
    geometry.update(schema_version='legaia.worldmap-scripted-placement-scene.v1',
        representation='current-scripted-placement-source',placement_source=receipt,
        authored_geometry=bool(geometry.get('authored_geometry') or allocations or changed),
        changed_source_entity_count=changed,authored_entity_count=len(allocations),
        ground_layer='retail',placement_layer='current',project_changed=False,gameplay_verified=False)
    if project.mode!='edit' or state_key(project)!=key:
        raise ProjectError('Scripted World scene changed during inspection')
    if len(json.dumps(geometry,allow_nan=False).encode('utf-8'))>32*1024*1024:
        raise ProjectError('Scripted World scene exceeds its response budget')
    return geometry
