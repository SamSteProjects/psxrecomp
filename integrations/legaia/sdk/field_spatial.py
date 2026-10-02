"""Adapt freshly verified field MAP metadata into source X/Z footprints.

Evidence at d6e64c68ede25813d35db20980da82a1a025549b:
engine-core/src/field_regions.rs, blob 8f54e88895ecdf0ca3fe1fc5602ce583911c5feb,
lines 38-39 and 410-432: region tile bias and half-open normalization.
engine-core/src/world/field_movement.rs, blob
12ce75c6990cfd5df489a28cb17c6fb33a719f26, lines 131-132: region caller.
engine-core/src/scene/host/scene_entry.rs, blob
0cf4e43f69fa6f5a547e2b3fd7696306c340fd0a, lines 1267-1291: kind-0/1
dispatch uses raw world >> 7, unlike region refresh. That dispatcher rejects
tiles outside 0..127; source rows outside that range remain visible metadata,
with no claim that they activate. Kind-1 gate-0 rows are object lookup keys,
not proven player contact volumes. Display Y=0 is a plane, not terrain height.
No MAP decoding, script execution, or live navigation occurs here.
"""
from copy import deepcopy
from hashlib import sha256
import re

from importer.pipeline import REFERENCE_COMMIT
from .project import ProjectError

MAX_FIELD_SPATIAL_RECORDS = 4096
_HASH = re.compile(r'[0-9a-f]{64}')
_SCENE = re.compile(r'collision://([A-Za-z0-9_-]{1,128})/field-map')
_SOURCE_FIELDS = {'disc', 'iso_file', 'prot_entry_index', 'prot_entry_name',
                  'prot_start_lba', 'byte_offset', 'byte_length', 'byte_coordinate_space',
                  'sha256', 'containing_span_sha256', 'containing_span_byte_offset',
                  'containing_span_byte_length'}
_TABLE_FIELDS = {'table_source', 'table_kind', 'record_index'}
_ASSET_FIELDS = {'semantic_id', 'asset_kind', 'name', 'table_source', 'table_kind',
                 'record_index', 'status', 'preview_supported', 'collision_id',
                 'reference_commit', 'source_record', 'limitations'}


def _reject(reason):
    raise ProjectError('Invalid field spatial source: ' + reason)


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _source(value, scene, table=None, kind=None, index=None):
    fields = _SOURCE_FIELDS | (_TABLE_FIELDS if table is not None else set())
    if not isinstance(value, dict) or set(value) != fields:
        _reject('source locator shape')
    disc = value['disc']
    if (not isinstance(disc, dict) or set(disc) != {'sha256', 'serial'} or
            disc['serial'] != 'SCUS-94254' or not isinstance(disc['sha256'], str) or
            not _HASH.fullmatch(disc['sha256'])):
        _reject('source disc identity')
    if (value['iso_file'] != 'PROT.DAT' or value['prot_entry_name'] != scene or
            value['byte_coordinate_space'] != 'prot_entry' or
            not _integer(value['prot_entry_index'], 0, 65535) or
            not _integer(value['prot_start_lba'], 0, 0x7fffffff) or
            any(not isinstance(value[key], str) or not _HASH.fullmatch(value[key])
                for key in ('sha256', 'containing_span_sha256'))):
        _reject('source identity or digest')
    if table is None:
        if any(type(value[key]) is not int or value[key] != expected for key, expected in
               (('byte_offset', 0x4000), ('byte_length', 0x4000),
                ('containing_span_byte_offset', 0), ('containing_span_byte_length', 0x12000))):
            _reject('collision source extent')
    else:
        base = 0x10000 if table == 'primary' else 0
        stride = 8 if kind == 3 else 4
        if (value['table_source'] != table or type(value['table_kind']) is not int or
                value['table_kind'] != kind or type(value['record_index']) is not int or
                value['record_index'] != index or
                any(type(value[key]) is not int or value[key] != expected for key, expected in
                    (('byte_length', stride), ('containing_span_byte_offset', base),
                     ('containing_span_byte_length', 0x2000))) or
                not _integer(value['byte_offset'], base + 0x12, base + 0x2000 - stride) or
                value['byte_offset'] - base - index * stride < 0x12):
            _reject('table row source extent or index')
    return value


def _world_bounds(tiles, bias):
    return {key: value * 128 + bias for key, value in tiles.items()}


def _record(asset, scene, collision_source):
    if not isinstance(asset, dict):
        _reject('record shape')
    kind = asset.get('asset_kind')
    table, table_kind, index = (asset.get(key) for key in ('table_source', 'table_kind', 'record_index'))
    if (kind not in ('trigger', 'region') or table not in ('primary', 'fallback') or
            not _integer(table_kind, 0, 3) or not _integer(index, 0, 2047) or
            (kind == 'region' and (table != 'primary' or table_kind != 3)) or
            (kind == 'trigger' and (table_kind not in (0, 1) or table == 'fallback' and table_kind != 1))):
        _reject('record table identity')
    extras = ({'encoded', 'tile_bounds', 'bounds_semantics'} if kind == 'region' else
              {'encoded', 'trigger_type', 'destination_world', 'destination_scene'} if table_kind == 0 else
              {'encoded', 'trigger_type', 'script_reference'})
    identity = (f'region://{scene}/field-map/{table}/{index:04d}' if kind == 'region' else
                f'trigger://{scene}/field-map/{table}/kind-{table_kind}/{index:04d}')
    expected_label = f"{table.title()} {'region' if kind == 'region' else 'kind-' + str(table_kind)} {index}"
    if (set(asset) != _ASSET_FIELDS | extras or asset['semantic_id'] != identity or
            asset['collision_id'] != f'collision://{scene}/field-map' or
            asset['reference_commit'] != REFERENCE_COMMIT or asset['preview_supported'] is not False or
            asset['name'] != expected_label or not isinstance(asset['limitations'], list) or
            len(asset['limitations']) > 256 or
            any(not isinstance(row, str) or len(row) > 8192 for row in asset['limitations'])):
        _reject('record identity or metadata')
    source = _source(asset['source_record'], scene, table, table_kind, index)
    delta = 0 if table == 'primary' else 1
    if (source['disc'] != collision_source['disc'] or
            source['prot_entry_index'] != collision_source['prot_entry_index'] + delta or
            source['prot_start_lba'] != collision_source['prot_start_lba'] + delta * 36):
        _reject('record and collision source differ')
    encoded = asset['encoded']
    encoded_keys = ({'x0', 'z0', 'x1', 'z1', 'type'} if kind == 'region' else
                    {'tile_x', 'tile_z', 'dest_x', 'dest_z'} if table_kind == 0 else
                    {'tile_x', 'tile_z', 'record_index', 'gate'})
    if (not isinstance(encoded, dict) or set(encoded) != encoded_keys or
            any(not _integer(value, 0, 255) for value in encoded.values())):
        _reject('encoded tile coordinates')
    if kind == 'trigger':
        keys = ('tile_x', 'tile_z', 'dest_x', 'dest_z') if table_kind == 0 else ('tile_x', 'tile_z', 'record_index', 'gate')
        if sha256(bytes(encoded[key] for key in keys)).hexdigest() != source['sha256']:
            _reject('encoded trigger row differs from its source hash')
    if kind == 'region':
        xmin, xmax = sorted((encoded['x0'], encoded['x1']))
        zmin, zmax = sorted((encoded['z0'], encoded['z1']))
        if xmin == xmax:
            xmax += 2
        if zmin == zmax:
            zmin -= 2
        tiles = {'x_min': xmin, 'x_max': xmax, 'z_min': zmin, 'z_max': zmax}
        bounds = asset['tile_bounds']
        if (asset['status'] != 'decoded_source_record' or
                asset['bounds_semantics'] != 'half_open_tile_coordinates' or
                not isinstance(bounds, dict) or set(bounds) != set(tiles) or
                any(type(bounds[key]) is not int or bounds[key] != value for key, value in tiles.items())):
            _reject('normalized region bounds')
        trigger_type = None
        bias = 64
    else:
        tx, tz = encoded['tile_x'], encoded['tile_z']
        tiles = {'x_min': tx, 'x_max': tx + 1, 'z_min': tz, 'z_max': tz + 1}
        trigger_type = ('intra_scene_teleport' if table_kind == 0 else
                        {0: 'object_bind', 1: 'partition_2_trigger'}.get(encoded['gate'], 'unknown_gate'))
        status = 'unknown_gate' if trigger_type == 'unknown_gate' else 'decoded_source_record'
        if asset['trigger_type'] != trigger_type or asset['status'] != status:
            _reject('trigger type or gate status')
        if table_kind == 0:
            destination = {'x': encoded['dest_x'] * 64 + 64, 'z': (encoded['dest_z'] + 1) * 64}
            actual = asset['destination_world']
            if (asset['destination_scene'] is not None or not isinstance(actual, dict) or
                    set(actual) != set(destination) or
                    any(type(actual[key]) is not int or actual[key] != value for key, value in destination.items())):
                _reject('teleport destination metadata')
        else:
            expected = {'partition': {0: 0, 1: 2}.get(encoded['gate']),
                        'record_index': encoded['record_index'], 'status': 'unresolved_source_reference'}
            actual = asset['script_reference']
            if (not isinstance(actual, dict) or set(actual) != set(expected) or
                    any(type(actual[key]) is not type(value) or actual[key] != value for key, value in expected.items())):
                _reject('trigger script source reference')
        bias = 0
    world = _world_bounds(tiles, bias)
    return {'id': identity, 'kind': kind, 'label': asset['name'], 'table_source': table,
            'table_kind': table_kind, 'record_index': index, 'trigger_type': trigger_type,
            'world_bounds': world,
            'world_center': {'x': (world['x_min'] + world['x_max']) // 2, 'y': 0,
                             'z': (world['z_min'] + world['z_max']) // 2},
            'source_tile_bounds': tiles, 'source_record': deepcopy(source),
            'activation': 'not_evaluated', 'height_status': 'unknown'}


def build_field_spatial(preview):
    """Return detached source footprints from an already verified MAP preview."""
    if not isinstance(preview, dict) or preview.get('coordinate_system') != 'psx_guest_xz':
        _reject('preview coordinate system')
    collision = preview.get('asset')
    if not isinstance(collision, dict):
        _reject('collision metadata')
    identifier = collision.get('semantic_id')
    match = _SCENE.fullmatch(identifier) if isinstance(identifier, str) else None
    if (match is None or collision.get('asset_kind') != 'collision' or collision.get('scope') != 'scene' or
            collision.get('status') != 'source_baseline' or collision.get('reference_commit') != REFERENCE_COMMIT):
        _reject('collision identity')
    scene = match.group(1)
    collision_source = _source(collision.get('source_record'), scene)
    triggers, regions = preview.get('triggers'), preview.get('regions')
    if (not isinstance(triggers, list) or not isinstance(regions, list) or
            len(triggers) + len(regions) > MAX_FIELD_SPATIAL_RECORDS):
        _reject('record count or collections')
    if any(not isinstance(row, dict) or row.get('asset_kind') != expected
           for rows, expected in ((triggers, 'trigger'), (regions, 'region')) for row in rows):
        _reject('record collection kind')
    records = [_record(row, scene, collision_source) for row in triggers + regions]
    if len({record['id'] for record in records}) != len(records):
        _reject('duplicate source record identity')
    records.sort(key=lambda row: (row['table_source'] == 'fallback', row['table_kind'], row['record_index']))
    groups, tables, extents = {}, {}, {}
    for record in records:
        source = record['source_record']
        table = record['table_source']
        group = (table, record['table_kind'])
        stride = source['byte_length']
        first, count = groups.get(group, (source['byte_offset'], 0))
        if record['record_index'] != count or source['byte_offset'] != first + count * stride:
            _reject('source row sequence')
        groups[group] = first, count + 1
        witness = (source['disc']['sha256'], source['prot_entry_index'], source['prot_start_lba'],
                   source['containing_span_sha256'])
        if table in tables and tables[table] != witness:
            _reject('table containing source differs')
        tables[table] = witness
        spans = extents.setdefault(table, [])
        start, end = source['byte_offset'], source['byte_offset'] + stride
        if any(start < other_end and other_start < end for other_start, other_end in spans):
            _reject('source row extents overlap')
        spans.append((start, end))
    return {'schema_version': 'legaia.field-spatial.v1', 'scene_id': f'scene://{scene}',
            'coordinate_system': 'psx_guest_xz', 'units': 'guest_integer_world_units',
            'display_y': 0, 'height_status': 'unknown',
            'quantization': {'trigger': {'tile_size': 128, 'world_bias': 0, 'rule': 'tile = world >> 7'},
                             'region': {'tile_size': 128, 'world_bias': 64, 'rule': 'tile = (world - 64) >> 7'}},
            'records': records}
