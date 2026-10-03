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
    if not isinstance(result, dict) or result.get('schema_version') != 'legaia.worldmap-geometry.v2' or result.get('scene') not in ('map01', 'map02', 'map03') or not _hash(source_key):
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
    drawn = grounds = 0
    for entity in graph['entities']:
        if not isinstance(entity, dict):
            raise ImportError('World export source entity is invalid')
        ground = entity.get('placement_scope') == 'source_ground'
        identity = entity.get('entity_id')
        owner_valid = (isinstance(identity, str) and
            (identity == f'scene://{scene}/worldmap/ground' and entity.get('asset_id') == ground_id if ground else
             re.fullmatch(re.escape(f'scene://{scene}/worldmap/placements/') + r'[0-3][0-9a-f]{3}', identity)))
        if not owner_valid:
            raise ImportError('World export source entity identity is invalid')
        if (identity in seen or entity.get('asset_id') not in assets or entity.get('placement_scope') not in ('source_ground', 'source_spawn_seed') or
                entity.get('runtime_visibility') != 'not_evaluated' or entity.get('runtime_resting_position') != 'unknown' or
                entity.get('renderable') is not True or not ground and not _hash(entity.get('source_record_sha256'))):
            raise ImportError('World export source entity confidence or binding is invalid')
        matrix, position = entity.get('source_to_world'), entity.get('source_position')
        if (not isinstance(matrix, list) or len(matrix) != 16 or not all(_finite(v) for v in matrix) or
                [matrix[i] for i in (3, 7, 11, 15)] != [0, 0, 0, 1] or not isinstance(position, dict) or
                any(not _finite(position.get(axis)) or matrix[12 + i] != position[axis] for i, axis in enumerate('xyz'))):
            raise ImportError('World export affine transform differs from its source seed')
        seen.add(identity); grounds += ground
        drawn += len(assets[entity['asset_id']]['preview']['triangles'])
        display = [matrix[col * 4 + row] * (-1 if row == 1 else 1) for row in range(4) for col in range(4)]
        entities.append(dict(deepcopy(entity), geometry_key=entity['asset_id'], model_to_scene=display))
    coverage, metrics = graph.get('coverage'), graph.get('metrics')
    if (grounds != 1 or drawn > 200000 or not isinstance(metrics, dict) or
            any(type(metrics.get(key)) is not int or metrics.get(key) != value for key, value in dict(asset_count=len(assets), entity_count=len(entities), stored_triangle_count=triangles, drawn_triangle_count=drawn, texture_output_bytes=texture_bytes).items()) or
            not isinstance(coverage, dict) or type(coverage.get('resolved_count')) is not int or coverage.get('resolved_count') != len(entities) - 1 or type(coverage.get('rendered_count')) is not int or coverage.get('rendered_count') != len(entities) - 1 or
            type(coverage.get('unresolved_count')) is not int or coverage['unresolved_count'] < 0 or
            type(coverage.get('candidate_count')) is not int or coverage.get('candidate_count') != coverage['resolved_count'] + coverage['unresolved_count']):
        raise ImportError('World export coverage differs from its source geometry')
    scene_preview = dict(schema='legaia.scene-preview.v1', coordinate_system='editor_field_y_up_source_units',
        scene_id='scene://' + scene, source_key=source_key, project_source_key=source_key, representation='retail-source',
        assets=list(assets.values()), entities=entities, limits=list(result.get('limitations', [])) + list(graph.get('limitations', [])), export_scope=scope)
    if scope != 'source-scene':
        scene_preview = select_scene_export_instance(scene_preview, f'scene://{scene}/worldmap/ground' if scope == 'ground' else entity_id)
        scene_preview['export_scope'] = scope
        scene_preview['selected_entity_id'] = entity_id if scope == 'selected' else None
    return scene_preview


def encode_worldmap_glb(result, source_key, scope='source-scene', entity_id=None):
    scene = adapt_worldmap_scene(result, source_key, scope, entity_id)
    raw, audit = encode_scene_glb(scene)
    provenance = dict(scene=result['scene'], scope=scope, entity_id=entity_id,
        source_record=deepcopy(result['source_record']), coverage=deepcopy(result['scene_graph']['coverage']),
        metrics=deepcopy(result['scene_graph']['metrics']), limitations=deepcopy(scene['limits']))
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
