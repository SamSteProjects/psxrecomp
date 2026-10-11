"""Atomic relative transforms of retained authored decoration identities."""
from copy import deepcopy
from hashlib import sha256
import base64
import json
import struct

from importer.worldmap_placement_allocation import allocate
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError, digest
from .worldmap_placements import context, values
from .worldmap_placement_allocation import _context, _fresh
from .worldmap_placement_allocation_binding import COMPONENT, owner, validate
from .worldmap_placement_allocation_binding import compose


def arguments(placement_ids, delta):
    if (not isinstance(placement_ids, list) or not 1 <= len(placement_ids) <= 32
            or any(not isinstance(i, str) for i in placement_ids)
            or placement_ids != sorted(set(placement_ids))):
        raise ProjectError('Decoration group requires 1..32 sorted unique retained identities')
    if (not isinstance(delta, dict) or set(delta) != {'x', 'y', 'z', 'yaw_units'}
            or any(type(delta[a]) is not int or not -65535 <= delta[a] <= 65535 for a in ('x', 'y', 'z'))
            or type(delta['yaw_units']) is not int or not -4095 <= delta['yaw_units'] <= 4095):
        raise ProjectError('Decoration group requires bounded integer XYZ and yaw deltas')
    if not any(delta.values()):
        raise ProjectError('Decoration group transform is unchanged')


def revised_binding(raw, floor, binding, placement_ids, delta):
    arguments(placement_ids, delta)
    if not isinstance(binding, dict):
        raise ProjectError('Decoration group requires retained authored allocations')
    result = deepcopy(binding)
    requests = [r for op in result['operations'] for r in op['requests']]
    selected = {i: [r for r in requests if r['placement_id'] == i] for i in placement_ids}
    if any(len(rows) != 1 for rows in selected.values()):
        raise ProjectError('Decoration group contains an unavailable authored identity')
    for rows in selected.values():
        request = rows[0]; current = values(request['values'])
        request['values'] = values(dict(
            offset={a: current['offset'][a] + delta[a] for a in ('x', 'y', 'z')},
            yaw_units=(current['yaw_units'] + delta['yaw_units']) % 4096))
    current = raw
    for op in result['operations']:
        current, audit = allocate(current, floor, result['scene'], op['requests'])
        op['proposed_map_sha256'] = audit['proposed_sha256']
    return result


def review(project, scene, key, placement_ids, delta):
    arguments(placement_ids, delta)
    raw, provenance, floor, current, allocations = _context(project, scene, key)
    before = deepcopy(project.overrides.get(owner(scene), {}).get(COMPONENT))
    binding = revised_binding(raw, floor, before, placement_ids, delta)
    validate(project, owner(scene), binding)
    _, _, _, _, _, _, transformed, _ = context(project, scene)
    candidate, after_allocations = compose(project, scene, raw, provenance, floor, transformed, binding)
    old = {a['placement_id']: a for a in allocations}
    new = {a['placement_id']: a for a in after_allocations}
    expected = bytearray(current); changes = []
    for identifier in placement_ids:
        at = old[identifier]['record_index'] * 32
        offset = dict(zip(('x', 'y', 'z'), struct.unpack_from('<3h', current, at)))
        yaw = struct.unpack_from('<H', current, at + 10)[0]
        proposed = values(dict(offset={a: offset[a] + delta[a] for a in offset},
                               yaw_units=((yaw & 4095) + delta['yaw_units']) % 4096))
        struct.pack_into('<3h', expected, at, *(proposed['offset'][a] for a in ('x', 'y', 'z')))
        struct.pack_into('<H', expected, at + 10, (yaw & 0xf000) | proposed['yaw_units'])
        changes.append(dict(placement_id=identifier, before=old[identifier], after=new[identifier],
                            current_values=dict(offset=offset, yaw_units=yaw & 4095), values=proposed))
    if candidate != bytes(expected):
        raise ProjectError('Decoration group changed unrelated native bytes or unselected clones')
    before_decoded = decode_worldmap_placements(current, floor, scene=scene)
    after_decoded = decode_worldmap_placements(candidate, floor, scene=scene)
    old_seeds = {p['entity_id']: p for p in before_decoded['placements']}
    new_seeds = {p['entity_id']: p for p in after_decoded['placements']}
    selected_native = {old[i]['native_seed']['entity_id'] for i in placement_ids}
    if (set(old_seeds) != set(new_seeds) or before_decoded['coverage'] != after_decoded['coverage']
            or before_decoded['unresolved'] != after_decoded['unresolved']
            or any(seed != new_seeds[i] for i, seed in old_seeds.items() if i not in selected_native)):
        raise ProjectError('Decoration group changed native membership or an unselected seed')
    result = dict(schema_version='legaia.worldmap-decoration-group-review.v1', project_path=str(project.root),
        scene=scene, source_key=key, source_record=provenance, placement_ids=list(placement_ids), delta=deepcopy(delta),
        current_map_sha256=sha256(current).hexdigest(), proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=base64.b64encode(candidate).decode('ascii'), before_binding=before, binding=binding,
        audit=dict(placements=changes, changed_bytes=[dict(byte_offset=i, before_byte=a, after_byte=b)
            for i, (a, b) in enumerate(zip(current, candidate)) if a != b],
            scope='authored-decoration-group-transform-only', gameplay_verified=False),
        read_only=True, project_changed=False, gameplay_verified=False, build_ready=False)
    result['review_key'] = digest(result)
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 2 * 1024 * 1024:
        raise ProjectError('Decoration group Review exceeds its response budget')
    _fresh(project, key)
    return result


def apply(project, command):
    if (not isinstance(command, dict)
            or set(command) != {'type', 'scene', 'source_key', 'placement_ids', 'delta', 'review_key'}
            or command['type'] != 'transform_worldmap_authored_placements'):
        raise ProjectError('Decoration group Apply requires exact reviewed identities and delta')
    result = review(project, command['scene'], command['source_key'], command['placement_ids'], command['delta'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration group Review changed; review again')
    identifier = owner(command['scene']); before = deepcopy(project.overrides.get(identifier))
    after = {COMPONENT: deepcopy(result['binding'])}
    project.overrides[identifier] = after
    project.undo_stack.append(dict(entity_id=identifier, before=before, after=deepcopy(after)))
    project.redo_stack.clear()
