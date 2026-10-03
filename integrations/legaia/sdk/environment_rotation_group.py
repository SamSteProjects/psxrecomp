"""Reviewed integer source-axis layout and yaw for static decorations."""
from copy import deepcopy
import struct

from importer.environment_authoring import patch_environment_overrides
from .environment_group import _prepare, _merge
from .environment_rotation_math import rotate_displacement
from .project import ProjectError, digest
from .project_copy import source_key


def review(project, scene, entity_ids, operation):
    if (not isinstance(operation, dict) or set(operation) not in (
            {'anchor_id', 'quarter_turns'}, {'anchor_id', 'yaw_units'}) or
            not isinstance(operation['anchor_id'], str)):
        raise ProjectError('Decoration rotation requires a selected anchor and exactly one source yaw or quarter-turn field')
    angle_key = 'quarter_turns' if 'quarter_turns' in operation else 'yaw_units'
    angle = operation[angle_key]
    if type(angle) is not int or not 0 <= angle <= (3 if angle_key == 'quarter_turns' else 4095):
        raise ProjectError('Decoration rotation requires integer quarter turns 0..3 or source yaw units 0..4095')
    delta = angle * 1024 if angle_key == 'quarter_turns' else angle
    context = _prepare(project, scene, entity_ids)
    identities = sorted(entity_ids)
    if operation['anchor_id'] not in identities:
        raise ProjectError('Decoration rotation anchor must belong to the canonical selection')
    anchor = next(row for row in context['targets'] if row['entity_id'] == operation['anchor_id'])['current']
    proposed, yaws = {}, {}
    original_instances = deepcopy(context['instances'])
    for target in context['targets']:
        cell = target['cell_index']
        record = struct.unpack_from('<H', context['original'], 0x8000 + cell * 2)[0] & 511
        retail_yaw = struct.unpack_from('<H', context['original'], record * 32 + 10)[0]
        inherited_yaw = struct.unpack_from('<H', context['shared'], record * 32 + 10)[0]
        current_yaw = original_instances.get(cell, {}).get('rotation_psx', {}).get('y', inherited_yaw)
        yaws[cell] = dict(retail=retail_yaw % 4096, current=current_yaw % 4096,
                          proposed=(current_yaw + delta) % 4096)
        dx, dz = target['current']['x'] - anchor['x'], target['current']['z'] - anchor['z']
        dx, dz = rotate_displacement(dx, dz, delta)
        proposed[target['entity_id']] = dict(x=anchor['x'] + dx, z=anchor['z'] + dz)
    # The existing merger validates signed descriptor offsets and allocation
    # for placement first. Final yaw allocation is qualified separately below.
    merged = _merge(project, scene, context, proposed)
    if delta:
        value = deepcopy(merged['value'])
        instances = context['instances']
        for target in merged['targets']:
            cell = target['cell_index']
            entry = deepcopy(instances.get(cell, dict(cell_index=cell)))
            # Keep explicit unchanged axes, including an anchor's redundant
            # authored offset. Only axes whose source position moves are merged.
            old_offsets = original_instances.get(cell, {}).get('offset', {})
            for axis in ('x', 'z'):
                if target['proposed'][axis] == target['current'][axis] and axis in old_offsets:
                    entry.setdefault('offset', {})[axis] = old_offsets[axis]
            entry.setdefault('rotation_psx', {})['y'] = yaws[cell]['proposed']
            instances[cell] = entry
        value['instances'] = [instances[cell] for cell in sorted(instances)]
        project._validate_environment(scene, value)
        patch_environment_overrides(context['original'], value)
        if source_key(project) != context['before']:
            raise ProjectError('Project changed while reviewing decoration rotation group')
        merged['value'] = value
        merged['project_change'] = context['authored'] != value
    for target in merged['targets']:
        for layer in ('retail', 'current', 'proposed'):
            target[layer]['yaw'] = yaws[target['cell_index']][layer]
    merged['affected_count'] = sum(target['current'] != target['proposed'] for target in merged['targets'])
    normalized = {'anchor_id': operation['anchor_id'], angle_key: angle}
    key = digest(dict(project_source_key=context['before'], scene=scene,
                      source_sha256=context['source_hash'], entity_ids=identities, operation=normalized))
    return dict(schema_version='legaia.environment-rotation-group-review.v1',
                project_source_key=context['before'], source_sha256=context['source_hash'],
                review_key=key, scene_id=scene, entity_ids=identities, operation=normalized,
                **merged, scope='static-decoration-instance-layout-and-yaw-only', gameplay_verified=False)


def apply(project, command):
    if (not isinstance(command, dict) or
            set(command) != {'type', 'entity_id', 'entity_ids', 'operation', 'review_key'} or
            command['type'] != 'apply_environment_rotation_group'):
        raise ProjectError('Decoration rotation Apply requires exact owner, selection, operation and current review key')
    result = review(project, command['entity_id'], command['entity_ids'], command['operation'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration rotation group inputs changed since review')
    value = result['value']
    project.command(dict(type='set_environment_transforms', entity_id=command['entity_id'], value=value)
                    if value.get('edits') or value.get('instances') else
                    dict(type='clear_environment_transforms', entity_id=command['entity_id']))
