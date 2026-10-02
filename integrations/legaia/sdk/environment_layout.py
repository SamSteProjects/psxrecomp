"""Source-bound alignment and distribution of static scenery instances."""
from copy import deepcopy

from .project import ProjectError, digest
from .environment_group import _prepare, _merge


def review(project, scene, entity_ids, operation):
    if not isinstance(operation, dict) or operation.get('kind') not in ('align', 'distribute') or operation.get('axis') not in ('x', 'z'):
        raise ProjectError('Decoration layout requires alignment or distribution on X/Z')
    expected = {'kind', 'axis', 'anchor'} if operation['kind'] == 'align' else {'kind', 'axis'}
    if set(operation) != expected:
        raise ProjectError('Decoration layout operation has unexpected or missing fields')
    context = _prepare(project, scene, entity_ids)
    axis = operation['axis']
    targets = context['targets']
    proposed = {t['entity_id']: deepcopy(t['current']) for t in targets}
    if operation['kind'] == 'align':
        anchor = operation['anchor']
        if not isinstance(anchor, str) or anchor not in proposed:
            raise ProjectError('Decoration alignment anchor must be in the selected group')
        coordinate = proposed[anchor][axis]
        for point in proposed.values():
            point[axis] = coordinate
    else:
        ordered = sorted(targets, key=lambda t: (t['current'][axis], t['entity_id']))
        low, high = ordered[0]['current'][axis], ordered[-1]['current'][axis]
        intervals = len(ordered) - 1
        span = high - low
        if span < intervals:
            raise ProjectError('Decoration distribution needs at least one integer unit per interval')
        for index, target in enumerate(ordered):
            # Round the nonnegative relative distance half up without float loss.
            proposed[target['entity_id']][axis] = low + (2 * span * index + intervals) // (2 * intervals)
    merged = _merge(project, scene, context, proposed)
    identities = sorted(entity_ids)
    key = digest(dict(project_source_key=context['before'], scene=scene,
                      source_sha256=context['source_hash'], entity_ids=identities, operation=operation))
    return dict(schema_version='legaia.environment-layout-review.v1', project_source_key=context['before'],
                scene_id=scene, source_sha256=context['source_hash'], review_key=key, entity_ids=identities,
                operation=deepcopy(operation), **merged, scope='static-decoration-instance-transform-only', gameplay_verified=False)


def apply(project, command):
    if not isinstance(command, dict) or set(command) != {'type', 'entity_id', 'entity_ids', 'operation', 'review_key'} or command['type'] != 'apply_environment_layout':
        raise ProjectError('Decoration layout Apply requires owner, selection, operation and current review key only')
    result = review(project, command['entity_id'], command['entity_ids'], command['operation'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration layout inputs changed since review')
    value = result['value']
    project.command(dict(type='set_environment_transforms', entity_id=command['entity_id'], value=value)
                    if value.get('edits') or value.get('instances') else dict(type='clear_environment_transforms', entity_id=command['entity_id']))
