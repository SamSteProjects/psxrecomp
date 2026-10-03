"""Reviewed source-axis quarter-turn layout and yaw for static decorations."""
from copy import deepcopy
import struct

from importer.environment_authoring import patch_environment_overrides
from .environment_group import _prepare, _merge
from .project import ProjectError, digest
from .project_copy import source_key


def review(project, scene, entity_ids, operation):
    if (not isinstance(operation, dict) or set(operation) != {'anchor_id', 'quarter_turns'} or
            not isinstance(operation['anchor_id'], str) or
            type(operation['quarter_turns']) is not int or not 0 <= operation['quarter_turns'] <= 3):
        raise ProjectError('Decoration rotation requires a selected anchor and integer quarter-turn count 0..3')
    context = _prepare(project, scene, entity_ids)
    identities = sorted(entity_ids)
    if operation['anchor_id'] not in identities:
        raise ProjectError('Decoration rotation anchor must belong to the canonical selection')
    turns = operation['quarter_turns']
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
                          proposed=(current_yaw + turns * 1024) % 4096)
        dx, dz = target['current']['x'] - anchor['x'], target['current']['z'] - anchor['z']
        for _ in range(turns):
            dx, dz = dz, -dx
        proposed[target['entity_id']] = dict(x=anchor['x'] + dx, z=anchor['z'] + dz)
    # The existing merger validates signed descriptor offsets and allocation
    # for placement first. Final yaw allocation is qualified separately below.
    merged = _merge(project, scene, context, proposed)
    if turns:
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
    normalized = dict(anchor_id=operation['anchor_id'], quarter_turns=turns)
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
