"""Source-qualified world kingdom graphs adapted to the shared scene exporter."""
from copy import deepcopy
from hashlib import sha256
import json
import math
import re
import struct

from .core import ImportError
from .export import MAX_GLB_BYTES
from .scene_export import encode_scene_glb, select_scene_export_instance

MAX_WORLDMAP_GLB_BYTES = 32 * 1024 * 1024

def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and abs(value) <= 1000000


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def adapt_worldmap_scene(result, source_key, scope='source-scene', entity_id=None):
    if scope not in ('source-scene', 'ground', 'selected') or (scope == 'selected') != (entity_id is not None):
        raise ImportError('Choose source-scene, ground or one selected world source entity')
    if not isinstance(result, dict) or result.get('schema_version') not in ('legaia.worldmap-geometry.v2','legaia.worldmap-scripted-placement-scene.v1') or result.get('scene') not in ('map01', 'map02', 'map03') or not _hash(source_key):
        raise ImportError('World export requires a verified kingdom source graph and current source key')
    scene = result['scene']
    ground_id = f'asset://{scene}/worldmap/walk-ground'
    graph = result.get('scene_graph')
    if (result.get('semantic_id') != ground_id or not isinstance(result.get('source_record'), dict) or
            not isinstance(graph, dict) or graph.get('schema_version') != 'legaia.worldmap-scene-graph.v1' or
            graph.get('coordinate_system') != 'retail_field_y_down' or graph.get('matrix_convention') != 'column-major-affine' or
            not isinstance(graph.get('assets'), list) or not 1 <= len(graph['assets']) <= 128 or
            not isinstance(graph.get('entities'), list) or not 1 <= len(graph['entities']) <= 512):
        raise ImportError('World export graph schema or ownership is invalid')
    assets = {}
    triangles = texture_bytes = 0
    for asset in graph['assets']:
        if not isinstance(asset, dict):
            raise ImportError('World export asset must be source-qualified')
        identity, preview, source = asset.get('asset_id'), asset.get('preview'), asset.get('source_record')
        if (not isinstance(identity, str) or not identity.startswith(f'asset://{scene}/worldmap/') or
                identity in assets or not isinstance(source, dict) or not isinstance(preview, dict) or
                identity != ground_id and not _hash(source.get('decoded_member_sha256'))):
            raise ImportError('World export asset source identity or hash is invalid')
        vertices, faces, materials, textures = (preview.get(key) for key in ('vertices', 'triangles', 'materials', 'textures'))
        if (not isinstance(vertices, list) or not 1 <= len(vertices) <= 100000 or
                any(not isinstance(row, list) or len(row) != 3 or not all(_finite(v) for v in row) for row in vertices) or
                not isinstance(faces, list) or not 1 <= len(faces) <= 100000 or
                not isinstance(materials, list) or not 1 <= len(materials) <= 64 or
                not isinstance(textures, list) or len(textures) != len(materials)):
            raise ImportError('World export geometry exceeds its source bounds')
        for name in ('triangle_materials', 'triangle_uvs', 'triangle_colors'):
            if not isinstance(preview.get(name), list) or len(preview[name]) != len(faces):
                raise ImportError('World export triangle attributes differ from source geometry')
        for i, face in enumerate(faces):
            material, uv, colors = preview['triangle_materials'][i], preview['triangle_uvs'][i], preview['triangle_colors'][i]
            if (not isinstance(face, list) or len(face) != 3 or any(type(v) is not int or not 0 <= v < len(vertices) for v in face) or
                    type(material) is not int or not 0 <= material < len(materials) or
                    uv is not None and (not isinstance(uv, list) or len(uv) != 3 or any(not isinstance(row, list) or len(row) != 2 or any(not _finite(v) or not 0 <= v <= 256 for v in row) for row in uv)) or
                    not isinstance(colors, list) or len(colors) != 3 or any(not isinstance(row, list) or len(row) != 3 or any(not _finite(v) or not 0 <= v <= 255 for v in row) for row in colors)):
                raise ImportError('World export source triangle values are invalid')
        seen_materials = set()
        for texture in textures:
            if not isinstance(texture, dict) or type(texture.get('material_index')) is not int or not 0 <= texture['material_index'] < len(materials) or texture['material_index'] in seen_materials or texture.get('status') not in ('address_match', 'missing', 'ambiguous', 'unsupported', 'untextured'):
                raise ImportError('World export texture binding is invalid')
            seen_materials.add(texture['material_index'])
            if texture['status'] == 'address_match':
                w, h = texture.get('width'), texture.get('height')
                if type(w) is not int or type(h) is not int or not 1 <= w <= 256 or not 1 <= h <= 256:
                    raise ImportError('World export texture dimensions are invalid')
                if not isinstance(texture.get('rgba'), bytes) or len(texture['rgba']) != w * h * 4:
                    raise ImportError('World export requires verified raw texture pixels')
                texture_bytes += len(texture['rgba'])
                if 'stp' in texture:
                    if not isinstance(texture['stp'], bytes) or len(texture['stp']) != w * h or any(v > 1 for v in texture['stp']):
                        raise ImportError('World export source STP mask is invalid')
                    texture_bytes += len(texture['stp'])
            elif any(name in texture for name in ('rgba', 'stp', 'rgba_base64', 'stp_base64')):
                raise ImportError('Unsupported world source texture cannot claim pixels')
        triangles += len(faces)
        if triangles > 200000 or texture_bytes > 16 * 1024 * 1024:
            raise ImportError('World export triangle or texture budget exceeded')
        copied = deepcopy(asset)
        copied.update(geometry_key=identity, pose_kind='source_heightfield' if identity == ground_id else 'source_unposed')
        copied['preview']['source_record'] = deepcopy(source)
        expected_coordinates = 'retail_field_y_down' if identity == ground_id else 'retail_tmd_object_local'
        if preview.get('coordinate_system') != expected_coordinates or preview.get('posed', False) is not False:
            raise ImportError('World export requires unposed source object-local geometry')
        assets[identity] = copied
    if ground_id not in assets:
        raise ImportError('World export graph omits its source ground')
    entities, seen = [], set()
    drawn = grounds = authored_count = 0
    placement_meta = result.get('placement_authoring')
    scripted = result.get('schema_version') == 'legaia.worldmap-scripted-placement-scene.v1'
    if scripted:
        from .worldmap_scripted_export import qualify_source
        scripted_meta = qualify_source(result,source_key)
        allocation_rows = scripted_meta['authored_decorations'] + scripted_meta['authored_scripted_placements']
    has_authored = any(e.get('placement_scope') == 'authored_spawn_seed' for e in graph['entities'] if isinstance(e,dict))
    if has_authored and not scripted and (not isinstance(placement_meta,dict)
            or placement_meta.get('schema_version') != 'legaia.worldmap-placement-scene.v1'
            or placement_meta.get('scene') != scene or placement_meta.get('source_key') != source_key
            or placement_meta.get('source_map_sha256') != result['source_record'].get('map_sha256')
            or placement_meta.get('read_only') is not True or placement_meta.get('project_changed') is not False
            or placement_meta.get('gameplay_verified') is not False
            or result.get('representation') not in (None,'current-source','proposed-source')
            or not isinstance(placement_meta.get('authored_allocations'),list)
            or not 1 <= len(placement_meta['authored_allocations']) <= 511):
        raise ImportError('Authored World entities require complete Current placement provenance')
    for entity in graph['entities']:
        if not isinstance(entity, dict):
            raise ImportError('World export source entity is invalid')
        ground = entity.get('placement_scope') == 'source_ground'
        authored = entity.get('placement_scope') in ('authored_spawn_seed','authored_scripted_seed') if scripted else entity.get('placement_scope') == 'authored_spawn_seed'
        identity = entity.get('entity_id')
        allocation = entity.get('authored_placement')
        uuid = allocation['placement_id'].rsplit('/',1)[-1] if isinstance(allocation,dict) and isinstance(allocation.get('placement_id'),str) else ''
        native = allocation.get('native_seed') if isinstance(allocation,dict) else None
        authored_valid = (authored and isinstance(allocation,dict)
            and re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',uuid)
            and allocation.get('placement_id') == 'placement://authored/'+uuid
            and sum(row == allocation for row in (allocation_rows if scripted else placement_meta['authored_allocations'])) == 1
            and identity == f'scene://{scene}/worldmap/authored-placements/{uuid}'
            and type(allocation.get('target_cell')) is int and 0 <= allocation['target_cell'] < 16384
            and entity.get('native_entity_id') == f"scene://{scene}/worldmap/placements/{allocation['target_cell']:04x}"
            and allocation.get('record_index') == entity.get('object_record_index')
            and type(allocation.get('record_index')) is int and 4 <= allocation['record_index'] < 512
            and (allocation.get('model_pool_index') == entity.get('model_pool_index') if not scripted else isinstance(native,dict) and native.get('model_pool_index') == entity.get('model_pool_index'))
            and type(entity.get('model_pool_index')) is int and 0 <= entity['model_pool_index'] < 128
            and entity.get('asset_id') == f"asset://{scene}/worldmap/models/{entity['model_pool_index']:04d}"
            and allocation.get('allocated_record_sha256') == entity.get('source_record_sha256')
            and isinstance(native,dict) and native.get('entity_id') == entity.get('native_entity_id')
            and native.get('source_cell') == allocation['target_cell']
            and all(entity.get(k) == v for k,v in native.items() if k not in ('entity_id','placement_scope'))
            and (entity.get('retail_seed','missing') is None if scripted else
                 'retail_source_position' in entity and entity['retail_source_position'] is None
                 and 'retail_source_to_world' in entity and entity['retail_source_to_world'] is None))
        owner_valid = (isinstance(identity, str) and
            (identity == f'scene://{scene}/worldmap/ground' and entity.get('asset_id') == ground_id if ground else
             authored_valid if authored else re.fullmatch(re.escape(f'scene://{scene}/worldmap/placements/') + r'[0-3][0-9a-f]{3}', identity)))
        if not owner_valid:
            raise ImportError('World export source entity identity is invalid')
        if (identity in seen or entity.get('asset_id') not in assets or entity.get('placement_scope') not in (('source_ground', 'source_spawn_seed', 'authored_spawn_seed','authored_scripted_seed') if scripted else ('source_ground', 'source_spawn_seed', 'authored_spawn_seed')) or
                entity.get('runtime_visibility') != 'not_evaluated' or entity.get('runtime_resting_position') != 'unknown' or
                entity.get('renderable') is not True or not ground and not _hash(entity.get('source_record_sha256'))):
            raise ImportError('World export source entity confidence or binding is invalid')
        matrix, position = entity.get('source_to_world'), entity.get('source_position')
        if (not isinstance(matrix, list) or len(matrix) != 16 or not all(_finite(v) for v in matrix) or
                [matrix[i] for i in (3, 7, 11, 15)] != [0, 0, 0, 1] or not isinstance(position, dict) or
                any(not _finite(position.get(axis)) or matrix[12 + i] != position[axis] for i, axis in enumerate('xyz'))):
            raise ImportError('World export affine transform differs from its source seed')
        seen.add(identity); grounds += ground
        authored_count += authored
        drawn += len(assets[entity['asset_id']]['preview']['triangles'])
        display = [matrix[col * 4 + row] * (-1 if row == 1 else 1) for row in range(4) for col in range(4)]
        entities.append(dict(deepcopy(entity), geometry_key=entity['asset_id'], model_to_scene=display))
    coverage, metrics = graph.get('coverage'), graph.get('metrics')
    if scripted and authored_count != len(allocation_rows):
        raise ImportError('Scripted World scene coverage differs from retained native owners')
    if has_authored and not scripted and (authored_count != len(placement_meta['authored_allocations'])
            or authored_count != placement_meta.get('authored_entity_count')):
        raise ImportError('Authored World scene coverage differs from its retained allocations')
    if (grounds != 1 or drawn > 200000 or not isinstance(metrics, dict) or
            any(type(metrics.get(key)) is not int or metrics.get(key) != value for key, value in dict(asset_count=len(assets), entity_count=len(entities), stored_triangle_count=triangles, drawn_triangle_count=drawn, texture_output_bytes=texture_bytes).items()) or
            not isinstance(coverage, dict) or type(coverage.get('resolved_count')) is not int or coverage.get('resolved_count') != len(entities) - 1 or type(coverage.get('rendered_count')) is not int or coverage.get('rendered_count') != len(entities) - 1 or
            type(coverage.get('unresolved_count')) is not int or coverage['unresolved_count'] < 0 or
            type(coverage.get('candidate_count')) is not int or coverage.get('candidate_count') != coverage['resolved_count'] + coverage['unresolved_count']):
        raise ImportError('World export coverage differs from its source geometry')
    scene_preview = dict(schema='legaia.scene-preview.v1', coordinate_system='editor_field_y_up_source_units',
        scene_id='scene://' + scene, source_key=source_key, project_source_key=source_key,
        representation=result['representation'] if scripted else result.get('representation','current-source') if has_authored else 'retail-source',
        assets=list(assets.values()), entities=entities, limits=list(result.get('limitations', [])) + list(graph.get('limitations', [])), export_scope=scope)
    if scope != 'source-scene':
        scene_preview = select_scene_export_instance(scene_preview, f'scene://{scene}/worldmap/ground' if scope == 'ground' else entity_id)
        scene_preview['export_scope'] = scope
        scene_preview['selected_entity_id'] = entity_id if scope == 'selected' else None
    return scene_preview


def encode_worldmap_glb(result, source_key, scope='source-scene', entity_id=None, *, placement_authoring=None,entity_ids=None):
    graph = result.get('scene_graph') if isinstance(result,dict) else None
    scripted = isinstance(result,dict) and result.get('schema_version') == 'legaia.worldmap-scripted-placement-scene.v1'
    if scripted:
        from .worldmap_scripted_export import qualify_source
        if placement_authoring != qualify_source(result,source_key) or scope not in ('source-scene','ground','selected'):
            raise ImportError('Scripted World export requires exact Current native provenance and scope')
    if not scripted and isinstance(graph,dict) and isinstance(graph.get('entities'),list) and any(e.get('placement_scope') == 'authored_spawn_seed' for e in graph['entities'] if isinstance(e,dict)):
        native_meta = result.get('placement_authoring',{})
        if (not isinstance(native_meta,dict) or not isinstance(placement_authoring,dict) or placement_authoring.get('schema_version') != 'legaia.worldmap-placement-export.v2'
                or any(placement_authoring.get(k) != native_meta.get(k) for k in (
                    'current_map_sha256','exported_map_sha256','allocation_binding','authored_allocations','authored_entity_count'))):
            raise ImportError('Authored World GLB requires its exact Current allocation export provenance')
    if scope in ('selected-records','selected-authored'):
        if not isinstance(result,dict):raise ImportError('Selected world export requires a qualified source graph')
        authored=scope=='selected-authored'
        pattern=(re.escape(f"scene://{result.get('scene')}/worldmap/authored-placements/")+r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}') if authored else re.escape(f"scene://{result.get('scene')}/worldmap/placements/")+r'[0-3][0-9a-f]{3}'
        if entity_id is not None or not isinstance(entity_ids,list) or not 1<=len(entity_ids)<=(32 if authored else 511) or any(not isinstance(i,str) or not re.fullmatch(pattern,i) for i in entity_ids) or entity_ids!=sorted(set(entity_ids)):
            raise ImportError('Selected world group requires canonical complete source identities')
        if authored and (not isinstance(placement_authoring,dict) or placement_authoring.get('representation')!='current-source' or placement_authoring.get('selected_placement_ids')!=['placement://authored/'+i.rsplit('/',1)[1] for i in entity_ids]):
            raise ImportError('Authored group export requires exact Current UUID membership')
        scene=adapt_worldmap_scene(result,source_key)
        selected=[e for e in scene['entities'] if e['entity_id'] in entity_ids]
        if sorted(e['entity_id'] for e in selected)!=entity_ids:raise ImportError('Selected world source seeds are unavailable')
        keys={e['geometry_key'] for e in selected}
        scene.update(entities=selected,assets=[a for a in scene['assets'] if a['geometry_key'] in keys],export_scope=scope,selected_entity_ids=deepcopy(entity_ids))
    else:
        if entity_ids is not None:raise ImportError('Only selected-records scope accepts world source-seed identities')
        scene = adapt_worldmap_scene(result, source_key, scope, entity_id)
    if placement_authoring is not None:
        if (not isinstance(placement_authoring, dict) or placement_authoring.get('schema_version') not in ('legaia.worldmap-placement-export.v1','legaia.worldmap-placement-export.v2','legaia.worldmap-scripted-placement-export.v1') or
                not scripted and placement_authoring.get('schema_version')=='legaia.worldmap-scripted-placement-export.v1' or
                placement_authoring.get('representation') not in ('current-source', 'proposed-source','current-scripted-placement-source') or
                placement_authoring.get('source_key') != source_key or placement_authoring.get('gameplay_verified') is not False or
                not _hash(placement_authoring.get('current_map_sha256')) or not _hash(placement_authoring.get('exported_map_sha256')) or
                len(json.dumps(placement_authoring, allow_nan=False).encode()) > 512 * 1024):
            raise ImportError('World placement export requires explicit bounded source/authored provenance')
        scene['representation'] = placement_authoring['representation']
    raw, audit = encode_scene_glb(scene)
    provenance = dict(scene=result['scene'], scope=scope, entity_id=entity_id,
        source_record=deepcopy(result['source_record']), coverage=deepcopy(result['scene_graph']['coverage']),
        metrics=deepcopy(result['scene_graph']['metrics']), limitations=deepcopy(scene['limits']))
    if entity_ids is not None:provenance['entity_ids']=deepcopy(entity_ids)
    if placement_authoring is not None:
        provenance['placement_authoring'] = deepcopy(placement_authoring)
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    document['extras']['worldmap_source'] = provenance
    metadata = json.dumps(document, separators=(',', ':'), allow_nan=False).encode('utf-8')
    metadata += b' ' * (-len(metadata) % 4)
    tail = raw[20 + size:]
    length = 20 + len(metadata) + len(tail)
    if length > min(MAX_GLB_BYTES, MAX_WORLDMAP_GLB_BYTES):
        raise ImportError('World source GLB exceeds export budget')
    raw = struct.pack('<5I', 0x46546c67, 2, length, len(metadata), 0x4e4f534a) + metadata + tail
    return raw, {**audit, 'worldmap_source': provenance, 'byte_length': len(raw), 'sha256': sha256(raw).hexdigest()}
