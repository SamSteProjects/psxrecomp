"""Edit a retained decoration recipe; never reassign its native owner."""
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
from .worldmap_placement_allocation_binding import COMPONENT, owner, validate, compose


def revised_binding(raw, floor, binding, placement_id, value):
    value = values(value)
    result = deepcopy(binding)
    matches = [r for op in result['operations'] for r in op['requests'] if r['placement_id'] == placement_id]
    if len(matches) != 1:
        raise ProjectError('Choose one retained authored decoration')
    if matches[0]['values'] == value:
        raise ProjectError('Decoration transform is unchanged')
    matches[0]['values'] = value
    current = raw
    for op in result['operations']:
        current, audit = allocate(current, floor, result['scene'], op['requests'])
        op['proposed_map_sha256'] = audit['proposed_sha256']
    return result


def review(project, scene, key, placement_id, value):
    raw, provenance, floor, current, allocations = _context(project, scene, key)
    before = deepcopy(project.overrides.get(owner(scene), {}).get(COMPONENT))
    selected = next((a for a in allocations if a['placement_id'] == placement_id), None)
    if before is None or selected is None:
        raise ProjectError('Decoration transform requires an existing authored allocation')
    binding = revised_binding(raw, floor, before, placement_id, value)
    validate(project, owner(scene), binding)
    _, _, _, _, _, _, transformed, _ = context(project, scene)
    candidate, after_allocations = compose(project, scene, raw, provenance, floor, transformed, binding)
    # Independent complete literal patch: only this clone's six XYZ bytes and
    # low twelve yaw bits may change. Later clones retain explicit transforms.
    expected = bytearray(current); at = selected['record_index'] * 32
    struct.pack_into('<3h', expected, at, *(value['offset'][axis] for axis in ('x', 'y', 'z')))
    yaw = struct.unpack_from('<H', current, at + 10)[0]
    struct.pack_into('<H', expected, at + 10, (yaw & 0xf000) | value['yaw_units'])
    if candidate != bytes(expected):
        raise ProjectError('Decoration recipe edit changed unrelated native bytes or a later clone')
    before_decoded = decode_worldmap_placements(current, floor, scene=scene)
    after_decoded = decode_worldmap_placements(candidate, floor, scene=scene)
    old_seeds = {p['entity_id']:p for p in before_decoded['placements']}
    new_seeds = {p['entity_id']:p for p in after_decoded['placements']}
    native_id = selected['native_seed']['entity_id']
    if (set(old_seeds) != set(new_seeds) or before_decoded['coverage'] != after_decoded['coverage']
            or before_decoded['unresolved'] != after_decoded['unresolved']
            or any(seed != new_seeds[i] for i,seed in old_seeds.items() if i != native_id)):
        raise ProjectError('Decoration transform changed native membership or another seed')
    edited = next(a for a in after_allocations if a['placement_id'] == placement_id)
    current_values = dict(offset=dict(zip(('x','y','z'),struct.unpack_from('<3h',current,at))),yaw_units=yaw&4095)
    result = dict(schema_version='legaia.worldmap-decoration-transform-review.v1',project_path=str(project.root),
        scene=scene,source_key=key,source_record=provenance,placement_id=placement_id,values=values(value),
        current_values=current_values,current_map_sha256=sha256(current).hexdigest(),
        proposed_map_sha256=sha256(candidate).hexdigest(),proposed_map_base64=base64.b64encode(candidate).decode('ascii'),
        before_binding=before,binding=binding,audit=dict(before=selected,after=edited,
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            scope='authored-decoration-transform-only',gameplay_verified=False),
        read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key'] = digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('Decoration transform Review exceeds its response budget')
    _fresh(project,key)
    return result


def apply(project, command):
    if (not isinstance(command,dict) or set(command) != {'type','scene','source_key','placement_id','values','review_key'}
            or command['type'] != 'set_worldmap_authored_placement'):
        raise ProjectError('Decoration transform Apply requires exact reviewed identity and values')
    result = review(project,command['scene'],command['source_key'],command['placement_id'],command['values'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration transform Review changed; review again')
    identifier = owner(command['scene']);before = deepcopy(project.overrides.get(identifier))
    after = {COMPONENT:deepcopy(result['binding'])}
    project.overrides[identifier] = after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
