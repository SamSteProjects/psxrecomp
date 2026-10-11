"""Native walk-decoration allocation; no script, collision or live evaluation.

PIN d6e64c68 field_objects.rs: 512 records, low-nine-bit grid owners,
walk-visible cell gate, draw/placed flags and record terrain selectors.
"""
from copy import deepcopy
from hashlib import sha256
import re
import struct

from .core import ImportError
from .worldmap_placements import decode_worldmap_placements


def inventory(data, floor, scene):
    decoded = decode_worldmap_placements(data, floor, scene=scene)
    cells = list(struct.unpack_from('<16384H', data, 0x8000))
    used = {word & 511 for word in cells}
    free = [i for i in range(4, 512) if i not in used and data[i*32:i*32+32] == bytes(32)]
    donors = [deepcopy(p) for p in decoded['placements'] if p['source_layer'] == 'decoration']
    anchors = {p['source_anchor']['row']*128+p['source_anchor']['col']
               for p in decoded['placements'] + decoded['unresolved']
               if 0 <= p['source_anchor']['row'] < 128 and 0 <= p['source_anchor']['col'] < 128}
    targets = []
    for index, word in enumerate(cells):
        at = (word & 511)*32
        model, flags = struct.unpack_from('<2H', data, at+16)
        if word & 0x1000 and model == 0 and not flags & 4 and index not in anchors:
            targets.append(index)
    return dict(donors=donors, free_record_indices=free, target_cells=targets,
                current_placements=decoded['placements'])


def allocate(data, floor, scene, requests):
    source = inventory(data, floor, scene)
    if not isinstance(requests, list) or not 1 <= len(requests) <= 32:
        raise ImportError('World placement allocation requires one to thirty-two clones')
    if len(source['current_placements']) + len(requests) > 511:
        raise ImportError('World placement allocation exceeds the scene entity budget')
    donors = {p['source_cell']: p for p in source['donors']}
    free, targets = set(source['free_record_indices']), set(source['target_cells'])
    ids, claimed_records, claimed_cells = set(), set(), set()
    result = bytearray(data)
    allocations = []
    for request in requests:
        if not isinstance(request, dict) or set(request) not in ({
                'placement_id', 'donor_cell', 'target_cell', 'record_index', 'values'}, {
                'placement_id', 'donor_cell', 'target_cell', 'record_index', 'values', 'model_pool_index'}):
            raise ImportError('World placement clone requires exact native ownership and values')
        if 'model_pool_index' in request and (type(request['model_pool_index']) is not int or not 1 <= request['model_pool_index'] < 512):
            raise ImportError('World placement model override requires a nonzero native pool index')
        identifier = request['placement_id']
        if (not isinstance(identifier, str) or not re.fullmatch(
                r'placement://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', identifier)
                or identifier in ids):
            raise ImportError('World placement clone requires a distinct authored UUID')
        donor_cell, cell, record = (request[k] for k in ('donor_cell', 'target_cell', 'record_index'))
        if (any(type(v) is not int for v in (donor_cell, cell, record)) or donor_cell not in donors
                or cell not in targets or cell in claimed_cells or record not in free or record in claimed_records):
            raise ImportError('World placement donor, empty visible cell or unused zero record is unavailable')
        value = request['values']
        if (not isinstance(value, dict) or set(value) != {'offset', 'yaw_units'}
                or not isinstance(value['offset'], dict) or set(value['offset']) != {'x', 'y', 'z'}
                or any(type(v) is not int or not -32768 <= v <= 32767 for v in value['offset'].values())
                or type(value['yaw_units']) is not int or not 0 <= value['yaw_units'] < 4096):
            raise ImportError('World placement clone requires signed16 offsets and yaw0..4095')
        donor = donors[donor_cell]
        donor_at, target_at = donor['object_record_index']*32, record*32
        cell_at = 0x8000+cell*2
        cell_word = struct.unpack_from('<H', data, cell_at)[0]
        previous_at = (cell_word & 511)*32
        payload = bytearray(data[donor_at:donor_at+32])
        # The object grid also selects ground tile/page/CLUT. Preserve the
        # target cell's four terrain bytes rather than importing donor ground.
        payload[20:24] = data[previous_at+20:previous_at+24]
        struct.pack_into('<3h', payload, 0, *(value['offset'][a] for a in ('x', 'y', 'z')))
        yaw = struct.unpack_from('<H', payload, 10)[0]
        struct.pack_into('<H', payload, 10, (yaw & 0xf000) | value['yaw_units'])
        if 'model_pool_index' in request:
            struct.pack_into('<H', payload, 16, request['model_pool_index'])
        result[target_at:target_at+32] = payload
        struct.pack_into('<H', result, cell_at, (cell_word & ~511) | record)
        ids.add(identifier); claimed_records.add(record); claimed_cells.add(cell)
        allocations.append(dict(placement_id=identifier, donor_cell=donor_cell, target_cell=cell,
            record_index=record, donor_record_index=donor['object_record_index'],
            donor_record_sha256=sha256(data[donor_at:donor_at+32]).hexdigest(),
            previous_cell_sha256=sha256(data[cell_at:cell_at+2]).hexdigest(),
            allocated_record_sha256=sha256(payload).hexdigest(), model_pool_index=struct.unpack_from('<H',payload,16)[0],
            preserved_terrain_hex=payload[20:24].hex()))
    candidate = bytes(result)
    decoded = decode_worldmap_placements(candidate, floor, scene=scene)
    by_cell = {p['source_cell']: p for p in decoded['placements']}
    originals = {p['source_cell']: p for p in source['current_placements']}
    if (set(by_cell) != set(originals) | claimed_cells or
            any(by_cell[cell] != seed for cell, seed in originals.items())):
        raise ImportError('World placement allocation changed existing seeds or omitted an authored clone')
    before = decode_worldmap_placements(data, floor, scene=scene)
    if decoded['unresolved'] != before['unresolved'] or decoded['coverage']['excluded'] != before['coverage']['excluded']:
        raise ImportError('World placement allocation changed unresolved or excluded source coverage')
    allowed = {record*32+n for record in claimed_records for n in range(32)}
    allowed.update(0x8000+cell*2+n for cell in claimed_cells for n in (0, 1))
    changes = [dict(byte_offset=i, before_byte=a, after_byte=b) for i, (a,b) in enumerate(zip(data,candidate)) if a != b]
    if len(candidate) != len(data) or any(row['byte_offset'] not in allowed for row in changes):
        raise ImportError('World placement allocation altered unrelated native MAP bytes')
    for allocation in allocations:
        allocation['native_seed'] = deepcopy(by_cell[allocation['target_cell']])
    return candidate, dict(source_sha256=sha256(data).hexdigest(), proposed_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate), allocations=allocations, changed_bytes=changes,
        original_placement_count=len(originals), proposed_placement_count=len(by_cell),
        scope='walk-decoration-cell-allocation', gameplay_verified=False)
