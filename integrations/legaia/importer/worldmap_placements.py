"""Pinned sparse walk MAP source seeds; scripts and live visibility are not run."""
from copy import deepcopy
from hashlib import sha256
import math
import struct

from .assets import decode_tmd
from .core import ImportError
from .textures import associate_material

MAX_GRAPH_ASSETS = 128
MAX_GRAPH_ENTITIES = 512
MAX_GRAPH_TRIANGLES = 200000
MAX_GRAPH_TEXTURE_BYTES = 16 * 1024 * 1024
IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def decode_worldmap_placements(map_data, floor_lut, *, scene):
    if scene not in ('map01', 'map02', 'map03'):
        raise ImportError('World-map placements require a supported walk kingdom')
    if not isinstance(map_data, bytes) or len(map_data) != 0x12000:
        raise ImportError('World-map placements require a complete immutable MAP')
    if (not isinstance(floor_lut, list) or len(floor_lut) != 16 or
            any(type(value) is not int or not -32768 <= value <= 32767 for value in floor_lut)):
        raise ImportError('World-map placements require sixteen source floor heights')
    placements, unresolved, excluded = [], [], []
    for cell_index in range(16384):
        cell = struct.unpack_from('<H', map_data, 0x8000 + cell_index * 2)[0]
        record_index = cell & 511
        at = record_index * 32
        record = map_data[at:at+32]
        model, flags = struct.unpack_from('<2H', record, 16)
        placed = bool(flags & 4)
        decoration = bool(cell & 0x1000 and record_index != 0 and model != 0 and flags & 2 and not placed)
        if not placed and not decoration:
            if model:
                excluded.append(dict(cell_index=cell_index, object_record_index=record_index,
                                     model_pool_index=model, reason='Source walk decoration/placed gates are not satisfied'))
            continue
        col, row = cell_index % 128, cell_index // 128
        x, y, z = struct.unpack_from('<3h', record)
        dc, dr = struct.unpack_from('<2b', record, 6)
        rx, ry, rz = struct.unpack_from('<3H', record, 8)
        tier = map_data[0x4000 + cell_index] & 15
        position = dict(x=col*128+x+64, y=-floor_lut[tier]+y, z=row*128-z+64)
        anchor_col, anchor_row = col+dc, row+dr
        seed = dict(entity_id=f'scene://{scene}/worldmap/placements/{cell_index:04x}',
                    source_cell=cell_index, object_record_index=record_index, model_pool_index=model,
                    source_record_sha256=sha256(record).hexdigest(),
                    source_cell_sha256=sha256(map_data[0x8000+cell_index*2:0x8002+cell_index*2]).hexdigest(),
                    source_position=position, source_rotation_psx=dict(x=rx,y=ry,z=rz),
                    source_floor_tier=tier, source_cell_flags=cell, source_record_flags=flags,
                    source_layer='placed' if placed else 'decoration',
                    source_anchor=dict(col=anchor_col, row=anchor_row),
                    placement_scope='source_spawn_seed', runtime_visibility='not_evaluated',
                    runtime_resting_position='unknown')
        reason = None
        if placed and not (0 <= anchor_col < 128 and 0 <= anchor_row < 128):
            reason = 'Source placed footprint anchor is outside the MAP grid'
        elif placed and record_index in (1,2,3):
            reason = 'Source placed actor record uses a non-kingdom actor model pool'
        elif rx or rz:
            reason = 'Source X/Z tilt has no qualified sparse kingdom transform'
        if reason:
            unresolved.append(dict(seed, reason=reason))
            continue
        if decoration:
            anchor_col, anchor_row = min(127,max(0,anchor_col)), min(127,max(0,anchor_row))
            seed['source_anchor'] = dict(col=anchor_col, row=anchor_row)
        anchor_cell = struct.unpack_from('<H', map_data, 0x8000+(anchor_row*128+anchor_col)*2)[0]
        seed['source_anchor']['cell_flags'] = anchor_cell
        seed['source_bind_owner'] = 'init_bind' if anchor_cell & 0x400 else 'subarea_unbound'
        angle = (ry & 0xFFF) * math.tau / 4096
        c, s = math.cos(angle), math.sin(angle)
        seed['source_to_world'] = [c,0,-s,0, 0,1,0,0, s,0,c,0, position['x'],position['y'],position['z'],1]
        placements.append(seed)
    return dict(placements=placements, unresolved=unresolved,
                coverage=dict(candidate_count=len(placements)+len(unresolved),
                              resolved_count=len(placements), unresolved_count=len(unresolved),
                              excluded_count=len(excluded), unresolved=unresolved, excluded=excluded,
                              inspected_cell_count=16384))


def _pack_spans(data):
    if not isinstance(data, bytes) or not 8 <= len(data) <= 4*1024*1024:
        raise ImportError('World-map model pack exceeds its source bounds')
    count = struct.unpack_from('<I', data)[0]
    table_end = 4 + count * 4
    if not 1 <= count <= 128 or table_end > len(data):
        raise ImportError('World-map model pack count/table exceeds its bounds')
    offsets = [value*4 for value in struct.unpack_from(f'<{count}I', data, 4)]
    if offsets[0] < table_end or offsets[-1] >= len(data) or any(a >= b for a,b in zip(offsets,offsets[1:])):
        raise ImportError('World-map model pack pointers are aliased, unordered or outside source')
    return list(zip(offsets, offsets[1:]+[len(data)]))


def build_worldmap_scene_graph(ground, map_data, model_pack, model_source, texture_catalog):
    scene = ground['scene']
    decoded = decode_worldmap_placements(map_data, ground['floor_height_lut'], scene=scene)
    spans = _pack_spans(model_pack)
    ground_id = ground['semantic_id']
    assets = [dict(asset_id=ground_id, preview=ground['preview'], source_record=deepcopy(ground['source_record']))]
    entities = [dict(entity_id=f'scene://{scene}/worldmap/ground', asset_id=ground_id,
                     source_position=dict(x=0,y=0,z=0), source_to_world=list(IDENTITY),
                     placement_scope='source_ground', runtime_visibility='not_evaluated',
                     runtime_resting_position='unknown', renderable=True)]
    models, failures = {}, {}
    texture_bytes = ground['metrics']['texture_output_bytes']
    stored_triangles = ground['metrics']['triangle_count']
    drawn_triangles = stored_triangles
    unresolved = list(decoded['unresolved'])
    for seed in decoded['placements']:
        index = seed['model_pool_index']
        if index not in models and index not in failures:
            if not 0 <= index < len(spans):
                failures[index] = 'Source model reference is outside the kingdom model pack'
            else:
                at, stop = spans[index]
                payload = model_pack[at:stop]
                try:
                    preview = decode_tmd(payload)
                    if preview.get('diagnostics'):
                        raise ImportError('Source TMD primitive declarations do not match their decoded layout')
                    if not preview['vertices'] or not preview['triangles']:
                        raise ImportError('Source TMD model has no supported drawable geometry')
                    bounds = {}
                    for material, points in zip(preview['triangle_materials'],preview['triangle_uvs']):
                        if points is None:
                            continue
                        box = bounds.setdefault(material,[255,255,0,0])
                        for u,v in points:
                            box[:] = [min(box[0],u),min(box[1],v),max(box[2],u),max(box[3],v)]
                    preview['textures'] = [dict(associate_material(texture_catalog, material, tuple(bounds.get(i,[0,0,255,255]))),
                                                material_index=i) for i,material in enumerate(preview['materials'])]
                except ImportError as error:
                    failures[index] = str(error)
                else:
                    texture_bytes += sum(len(item.get('rgba',b''))+len(item.get('stp',b'')) for item in preview['textures'])
                    stored_triangles += len(preview['triangles'])
                    asset_id = f'asset://{scene}/worldmap/models/{index:04d}'
                    source = dict(deepcopy(model_source), pack_slot=index, decoded_member_offset=at,
                                  decoded_member_span_end=stop, decoded_member_sha256=sha256(payload).hexdigest())
                    models[index] = dict(asset_id=asset_id,preview=preview,source_record=source)
                    assets.append(models[index])
        if index in failures:
            unresolved.append(dict(seed,reason=failures[index]))
            continue
        asset = models[index]
        drawn_triangles += len(asset['preview']['triangles'])
        entities.append(dict(seed,asset_id=asset['asset_id'],renderable=True))
        if (len(assets)>MAX_GRAPH_ASSETS or len(entities)>MAX_GRAPH_ENTITIES or
                stored_triangles>MAX_GRAPH_TRIANGLES or drawn_triangles>MAX_GRAPH_TRIANGLES or
                texture_bytes>MAX_GRAPH_TEXTURE_BYTES):
            raise ImportError('World-map scene graph exceeds its asset/entity/triangle/texture budget')
    coverage = dict(decoded['coverage'],resolved_count=len(entities)-1,rendered_count=len(entities)-1,
                    unresolved_count=len(unresolved),unresolved=unresolved)
    return dict(schema_version='legaia.worldmap-scene-graph.v1',matrix_convention='column-major-affine',
                coordinate_system='retail_field_y_down',assets=assets,entities=entities,coverage=coverage,
                source_record=deepcopy(model_source),
                metrics=dict(asset_count=len(assets),entity_count=len(entities),
                             stored_triangle_count=stored_triangles,drawn_triangle_count=drawn_triangles,
                             texture_output_bytes=texture_bytes),
                limitations=['Sparse model transforms are source spawn seeds, not evaluated retail resting transforms.',
                             'Placed bind scripts, source/runtime visibility and animation are not evaluated.'])
