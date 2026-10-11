"""Read-only complete compatible Retail-instance plan for Current World animation."""
from copy import deepcopy
import json
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_behavior_resources import inspect as resources
from .worldmap_current_placements import inspect as current_scene
from .worldmap_animation_edit import current as current_animation


def inspect(project, scene, key):
    if scene not in ('map01', 'map02', 'map03') or project.mode != 'edit' or key != state_key(project):
        raise ProjectError('World scene animation requires fresh Edit kingdom sources')
    catalog = resources(project, key)
    geometry = current_scene(project, scene, key)
    entities = {row['entity_id']: row for row in geometry['scene_graph']['entities']}
    assets = {row['asset_id']: row for row in geometry['scene_graph']['assets']}
    members, absent, seen = [], [], set()
    current_bank_hash = None
    records = [row for row in catalog['assets'] if row['kind'] == 'animation' and row['source_scene'] == scene]
    for record in records:
        for binding in record['bindings']:
            identifier = binding['entity_id']
            if identifier in seen:
                raise ProjectError('World scene animation has ambiguous source instance ownership')
            seen.add(identifier)
            entity = entities.get(identifier)
            if entity is None:
                absent.append(dict(entity_id=identifier, animation_asset_id=record['id'], reason='absent_from_current_scene'))
                continue
            if entity['asset_id'] != binding['model_asset_id'] or entity['asset_id'] not in assets:
                raise ProjectError('World scene animation model differs from its catalog binding')
            if len(members) >= 32:
                raise ProjectError('World scene animation exceeds its compatible instance budget')
            receipt = current_animation(project, scene, key, identifier, 0)
            preview = receipt['preview']
            if current_bank_hash is not None and current_bank_hash != preview['bank_sha256']:
                raise ProjectError('World scene animation instances disagree on the saved Current bank')
            current_bank_hash = preview['bank_sha256']
            source = receipt['source']['before']['preview']
            if (receipt['animation_id'] != record['authored_animation_id']
                    or source['record_sha256'] != record['source_record']['sha256']
                    or source['bank_sha256'] != record['source_record']['animation_slot']['decoded_sha256']
                    or preview['frame_count'] != record['frame_count']
                    or preview['channel_count'] != record['channel_count']
                    or receipt['source']['current_model_geometry'] != assets[entity['asset_id']]['preview']):
                raise ProjectError('World scene animation differs from complete source clip or Current model evidence')
            members.append(dict(entity_id=identifier, animation_asset_id=record['id'], current=receipt))
    kingdom = next(row for row in catalog['kingdoms'] if row['scene'] == scene)
    result = dict(schema_version='legaia.world-animation-scene.v1', project_path=str(project.root),
                  scene=scene, source_key=key, current=geometry, resources=catalog,
                  members=sorted(members, key=lambda row: row['entity_id']),
                  absent=sorted(absent, key=lambda row: row['entity_id']),
                  unsupported_bindings=deepcopy(kingdom['unsupported_animation_bindings']),
                  coverage=dict(compatible_source_instances=len(seen), current_instances=len(members),
                                absent_instances=len(absent), source_only_clips=sum(not row['bindings'] for row in records)),
                  representation='current-world-animation-scene-plan', read_only=True,
                  project_changed=False, gameplay_verified=False,
                  timing='unresolved', looping='unresolved', runtime_state='not_observed')
    if key != state_key(project):
        raise ProjectError('World scene animation inputs changed during inspection')
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 160*1024*1024:
        raise ProjectError('World scene animation exceeds its private response budget')
    return result
