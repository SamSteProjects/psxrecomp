"""Private Current/Proposed world GLBs composed from qualified record bindings."""
from copy import deepcopy
from hashlib import sha256
import base64,json

from importer.export import write_encoded_glb
from importer.worldmap_geometry import load_worldmap_geometry
from importer.worldmap_export import encode_worldmap_glb,MAX_WORLDMAP_GLB_BYTES
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_placements import context,review,patch
from .worldmap_export import MAX_RESPONSE_BYTES

def export(project,scene,expected_key,proposal=None,*,scope='source-scene',entity_id=None,batch_proposal=None,record_ids=None):
    if scene not in ('map01','map02','map03') or project.mode!='edit' or not project.disc_path:
        raise ProjectError('World placement export requires a supported kingdom in Edit mode')
    if scope not in ('source-scene','ground','selected','selected-records') or (scope=='selected')!=(entity_id is not None) or (scope=='selected-records')!=(record_ids is not None):
        raise ProjectError('Choose source-scene, ground or selected placement export scope')
    if record_ids is not None:
        from .worldmap_placement_batch import arguments
        arguments(record_ids,dict(x=0,y=0,z=0,yaw_units=0),False)
        record_ids=deepcopy(record_ids)
        if proposal is not None or batch_proposal is not None and (not isinstance(batch_proposal,dict) or batch_proposal.get('record_ids')!=record_ids):
            raise ProjectError('Selected record export must match the reviewed batch records')
    if entity_id is not None and (not isinstance(entity_id,str) or len(entity_id)>1024 or not entity_id.startswith(f'scene://{scene}/worldmap/')):
        raise ProjectError('Selected placement export requires a bounded entity in the same kingdom')
    key=state_key(project)
    def current():
        if expected_key!=key or project.mode!='edit' or state_key(project)!=key:
            raise ProjectError('World placement export source inputs changed; inspect again')
    current()
    representation='current-source';review_key=None;binding_override=None
    if batch_proposal is not None:
        if proposal is not None or not isinstance(batch_proposal,dict) or set(batch_proposal)!={'record_ids','delta','shared_record','review_key'}:
            raise ProjectError('Batch world export requires only the reviewed batch identity and deltas')
        from .worldmap_placement_batch import review as review_batch
        batch_proposal=deepcopy(batch_proposal)
        assessed=review_batch(project,scene,key,batch_proposal['record_ids'],batch_proposal['delta'],batch_proposal['shared_record'])
        if batch_proposal['review_key']!=assessed['review_key']:
            raise ProjectError('Batch world export review is stale; review again')
        binding_override=(assessed['after'] or {}).get('WorldMapPlacements')
        representation='proposed-source';review_key=batch_proposal['review_key']
    if proposal is not None:
        if not isinstance(proposal,dict) or set(proposal)!={'record_id','values','shared_record','review_key'}:
            raise ProjectError('Proposed world export requires only the reviewed transform and identity')
        proposal=deepcopy(proposal)
        assessed,binding_override=review(project,scene,key,proposal['record_id'],proposal['values'],proposal['shared_record'])
        if proposal['review_key']!=assessed['review']['review_key']:
            raise ProjectError('Proposed world export review is stale; review again')
        representation='proposed-source';review_key=proposal['review_key']
    geometry=deepcopy(load_worldmap_geometry(project.disc_path,scene))
    current()
    raw,provenance,records,_,floor,binding,current_map,placements=context(project,scene)
    selected_ids=None
    if record_ids is not None:
        if any(i not in records or not records[i]['writable'] for i in record_ids):
            raise ProjectError('Selected record export requires complete qualified source-cell ownership')
        selected_ids=sorted(p['entity_id'] for i in record_ids for p in records[i]['placements'])
    source=geometry['source_record']
    if (source['disc_sha256']!=provenance['source_disc_sha256'] or source['map_sha256']!=provenance['source_map_sha256'] or
            source['floor_lut_sha256']!=provenance['source_floor_lut_sha256']):
        raise ProjectError('World placement geometry and authored transform sources differ')
    active=binding_override if proposal is not None or batch_proposal is not None else binding
    exported_map,_,exported_seeds=patch(raw,records,(active or {}).get('entries',{}),scene=scene,floor=floor)
    indexed={p['entity_id']:p for p in exported_seeds}
    changed=0
    for entity in geometry['scene_graph']['entities']:
        if entity['placement_scope']=='source_ground':continue
        seed=indexed.get(entity['entity_id'])
        if seed is None or seed['object_record_index']!=entity['object_record_index'] or seed['model_pool_index']!=entity['model_pool_index']:
            raise ProjectError('World placement export changed source model/instance ownership')
        record=f"{entity['object_record_index']:04d}";row=records[record]
        if entity['source_record_sha256']!=row['source_record_sha256']:
            raise ProjectError('World placement geometry owner differs from the retail transform record')
        if seed['source_to_world']!=entity['source_to_world']:changed+=1
        entity.update(retail_source_position=deepcopy(entity['source_position']),retail_source_to_world=list(entity['source_to_world']),
            source_position=deepcopy(seed['source_position']),source_to_world=list(seed['source_to_world']),
            source_rotation_psx=deepcopy(seed['source_rotation_psx']),
            authored_source_transform=dict(record_id=record,retail_record_sha256=row['source_record_sha256'],
                exported_record_sha256=seed['source_record_sha256'],values=deepcopy((active or {}).get('entries',{}).get(record,{}).get('values'))))
    metadata=dict(schema_version='legaia.worldmap-placement-export.v1',representation=representation,source_key=key,
        current_map_sha256=sha256(current_map).hexdigest(),exported_map_sha256=sha256(exported_map).hexdigest(),
        source_map_sha256=sha256(raw).hexdigest(),review_key=review_key,proposal=deepcopy(proposal),
        authored_records=deepcopy((active or {}).get('entries',{})),changed_source_entity_count=changed,
        override_scope='WorldMapPlacements',gameplay_verified=False,project_changed=False)
    if batch_proposal is not None:metadata['batch_proposal']=deepcopy(batch_proposal)
    if record_ids is not None:metadata['selected_record_ids']=deepcopy(record_ids)
    geometry['limitations'].append('Only WorldMapPlacements record transforms are composed; geometry, textures and ground remain retail source assets.')
    glb,audit=encode_worldmap_glb(geometry,key,scope,entity_id,placement_authoring=metadata,entity_ids=selected_ids)
    current()
    if len(glb)>MAX_WORLDMAP_GLB_BYTES:raise ProjectError('World placement GLB exceeds32 MiB')
    response=dict(schema_version='legaia.worldmap-placement-export-response.v1',scene=scene,source_key=key,
        representation=representation,review_key=review_key,scope=scope,entity_id=entity_id,glb_base64=base64.b64encode(glb).decode('ascii'),
        gameplay_verified=False,project_changed=False)
    if batch_proposal is not None:response['batch_proposal']=deepcopy(batch_proposal)
    if record_ids is not None:response.update(record_ids=record_ids,entity_ids=selected_ids)
    if len(json.dumps(dict(response,audit=audit),allow_nan=False).encode())+65536>MAX_RESPONSE_BYTES:
        raise ProjectError('World placement export response exceeds64 MiB')
    current()
    return {**write_encoded_glb(glb,audit,project.root/'Exports',prefix='scene'),**response}
