"""Move a retained decoration's native cell without changing its identity or offsets."""
from copy import deepcopy
from hashlib import sha256
import base64
import json
import struct

from importer.worldmap_placement_allocation import allocate, inventory
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError, digest
from .worldmap_placements import context
from .worldmap_placement_allocation import _context, _fresh
from .worldmap_placement_allocation_binding import COMPONENT, owner, validate, compose


def relocated_binding(raw, floor, binding, placement_id, target_cell):
    if type(target_cell) is not int or not 0 <= target_cell < 16384:
        raise ProjectError('Decoration cell must be an integer in the native 128 by 128 grid')
    result = deepcopy(binding)
    matches = [r for op in result['operations'] for r in op['requests'] if r['placement_id'] == placement_id]
    if len(matches) != 1:
        raise ProjectError('Choose one retained authored decoration to relocate')
    selected = matches[0]
    previous = selected['target_cell']
    if previous == target_cell:
        raise ProjectError('Decoration native cell is unchanged')
    rebases = []
    for op in result['operations']:
        for request in op['requests']:
            if request['placement_id'] != placement_id and request['donor_cell'] == previous:
                rebases.append(dict(placement_id=request['placement_id'],before_donor_cell=previous,after_donor_cell=target_cell))
                request['donor_cell'] = target_cell
    selected['target_cell'] = target_cell
    current = raw
    for op in result['operations']:
        current, audit = allocate(current, floor, result['scene'], op['requests'])
        op['proposed_map_sha256'] = audit['proposed_sha256']
    return result, rebases


def review(project, scene, key, placement_id, target_cell):
    raw, provenance, floor, current, allocations = _context(project, scene, key)
    before = deepcopy(project.overrides.get(owner(scene), {}).get(COMPONENT))
    selected = next((a for a in allocations if a['placement_id'] == placement_id), None)
    if before is None or selected is None:
        raise ProjectError('Cell relocation requires an existing authored decoration')
    if type(target_cell) is not int or target_cell not in inventory(current, floor, scene)['target_cells']:
        raise ProjectError('Choose an unoccupied eligible native walk-decoration cell')
    binding, rebases = relocated_binding(raw, floor, before, placement_id, target_cell)
    validate(project, owner(scene), binding)
    _, _, _, _, _, _, transformed, _ = context(project, scene)
    candidate, remaining = compose(project, scene, raw, provenance, floor, transformed, binding)
    # Complete independent literal oracle: only the two grid selectors and the
    # retained record's destination terrain selectors may change.
    expected = bytearray(current)
    previous_at = 0x8000 + selected['target_cell'] * 2
    destination_at = 0x8000 + target_cell * 2
    destination_word = struct.unpack_from('<H', current, destination_at)[0]
    record_at = selected['record_index'] * 32
    terrain_at = (destination_word & 511) * 32 + 20
    expected[previous_at:previous_at+2] = raw[previous_at:previous_at+2]
    struct.pack_into('<H', expected, destination_at, (destination_word & ~511) | selected['record_index'])
    expected[record_at+20:record_at+24] = current[terrain_at:terrain_at+4]
    if candidate != bytes(expected):
        raise ProjectError('Cell relocation changed offsets, another decoration or unrelated native bytes')
    old = decode_worldmap_placements(current, floor, scene=scene)
    new = decode_worldmap_placements(candidate, floor, scene=scene)
    old_seeds = {p['entity_id']:p for p in old['placements']}
    new_seeds = {p['entity_id']:p for p in new['placements']}
    previous_id = selected['native_seed']['entity_id']
    destination_id = f'scene://{scene}/worldmap/placements/{target_cell:04x}'
    if (set(new_seeds) != (set(old_seeds) - {previous_id}) | {destination_id}
            or old['unresolved'] != new['unresolved'] or old['coverage']['excluded'] != new['coverage']['excluded']
            or old['coverage']['candidate_count'] != new['coverage']['candidate_count']
            or any(seed != new_seeds[i] for i,seed in old_seeds.items() if i != previous_id)):
        raise ProjectError('Cell relocation changed another seed, footprint binding or native coverage')
    relocated = next(a for a in remaining if a['placement_id'] == placement_id)
    if relocated['native_seed'] != new_seeds[destination_id]:
        raise ProjectError('Relocated decoration has no complete final native seed')
    result = dict(schema_version='legaia.worldmap-decoration-cell-review.v1',project_path=str(project.root),
        scene=scene,source_key=key,source_record=provenance,placement_id=placement_id,target_cell=target_cell,
        current_map_sha256=sha256(current).hexdigest(),proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=base64.b64encode(candidate).decode('ascii'),before_binding=before,binding=binding,
        audit=dict(before=selected,after=relocated,rebased_donors=rebases,
            changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,candidate)) if a!=b],
            scope='authored-decoration-native-cell-only',gameplay_verified=False),
        read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key'] = digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('Decoration cell Review exceeds its response budget')
    _fresh(project,key)
    return result


def apply(project, command):
    if (not isinstance(command,dict) or set(command) != {'type','scene','source_key','placement_id','target_cell','review_key'}
            or command['type'] != 'relocate_worldmap_authored_placement'):
        raise ProjectError('Decoration cell Apply requires exact reviewed identity and destination')
    result = review(project,command['scene'],command['source_key'],command['placement_id'],command['target_cell'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration cell Review changed; review again')
    identifier = owner(command['scene'])
    before = deepcopy(project.overrides.get(identifier))
    after = {COMPONENT:deepcopy(result['binding'])}
    project.overrides[identifier] = after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()
