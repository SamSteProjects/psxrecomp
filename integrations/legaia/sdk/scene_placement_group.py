"""Reviewed atomic X/Z offsets across imported actors and static decorations."""
from copy import deepcopy
import math

from importer.core import ImportError
from importer.serialization import encode_placement_coordinate
from .environment_group import _prepare, _merge
from .project import ProjectError, digest
from .project_copy import source_key


def review(project, scene, entity_ids, delta):
    if project.mode != 'edit' or not isinstance(scene, str) or scene != project.active_scene or scene not in project.imports:
        raise ProjectError('Mixed placement requires the active imported scene in Edit mode')
    if (not isinstance(entity_ids, list) or not 2 <= len(entity_ids) <= 128 or
            any(not isinstance(item, str) for item in entity_ids) or len(set(entity_ids)) != len(entity_ids)):
        raise ProjectError('Mixed placement requires 2..128 unique imported actor and decoration identities')
    if (not isinstance(delta, dict) or set(delta) != {'x', 'z'} or
            any(type(v) is not int or abs(v) > 16320 or v % 64 for v in delta.values())):
        raise ProjectError('Mixed offsets require exact X/Z integer multiples of 64 within -16320..16320')
    document = project.imports[scene]
    actors = {actor['semantic_id']: actor for actor in document['actors']}
    actor_ids = sorted(identifier for identifier in entity_ids if identifier in actors)
    decoration_ids = sorted(identifier for identifier in entity_ids if identifier not in actors)
    if not actor_ids or not decoration_ids:
        raise ProjectError('Mixed placement requires at least one imported actor and one static decoration')
    context = _prepare(project, scene, decoration_ids, minimum=1)
    targets, changes = [], {}
    for identifier in actor_ids:
        actor = actors[identifier]
        retail = {axis: actor['imported_transform']['position'].get(axis) for axis in ('x', 'z')}
        before = deepcopy(project.overrides.get(identifier))
        authored = (before or {}).get('Transform', {}).get('position', {})
        current = {axis: authored.get(axis, retail[axis]) for axis in ('x', 'z')}
        proposed = {}
        for axis in ('x', 'z'):
            value = current[axis]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ProjectError(f'{identifier} has no finite {axis.upper()} placement')
            proposed[axis] = value + delta[axis]
            try:
                encode_placement_coordinate(proposed[axis], f'{identifier} proposed {axis.upper()}')
            except ImportError as exc:
                raise ProjectError(str(exc)) from exc
        after = deepcopy(before or {})
        for axis in ('x', 'z'):
            if delta[axis]:
                after.setdefault('Transform', {}).setdefault('position', {})[axis] = proposed[axis]
        after = after or None
        if before != after:
            changes[identifier] = after
        targets.append(dict(entity_id=identifier, kind='actor', retail=retail, current=current, proposed=proposed))
    merged = _merge(project, scene, context, {
        t['entity_id']: {axis: t['current'][axis] + delta[axis] for axis in ('x', 'z')}
        for t in context['targets']})
    targets.extend(dict(t, kind='decoration') for t in merged['targets'])
    if merged['project_change']:
        after = deepcopy(project.overrides.get(scene, {}))
        value = merged['value']
        if value.get('edits') or value.get('instances'):
            after['Environment'] = deepcopy(value)
        else:
            after.pop('Environment', None)
        changes[scene] = after or None
    if source_key(project) != context['before']:
        raise ProjectError('Project changed while reviewing mixed placement')
    identities = sorted(entity_ids)
    key = digest(dict(project_source_key=context['before'], scene=scene,
                      source_sha256=context['source_hash'], entity_ids=identities, delta=delta))
    return dict(schema_version='legaia.scene-placement-group-review.v1',
                project_source_key=context['before'], scene_id=scene, source_sha256=context['source_hash'],
                review_key=key, entity_ids=identities, delta=deepcopy(delta),
                targets=sorted(targets, key=lambda t: t['entity_id']), changes=changes,
                affected_count=sum(t['current'] != t['proposed'] for t in targets),
                project_change=bool(changes), scope='imported-actor-and-static-decoration-xz-only',
                gameplay_verified=False)


def apply(project, command):
    if (not isinstance(command, dict) or
            set(command) != {'type', 'entity_id', 'entity_ids', 'delta', 'review_key'} or
            command['type'] != 'apply_scene_placement_group'):
        raise ProjectError('Mixed placement Apply requires owner, selection, offset and current review key only')
    result = review(project, command['entity_id'], command['entity_ids'], command['delta'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Mixed placement inputs changed since review')
    after = deepcopy(result['changes'])
    if not after:
        return
    before = {identifier: deepcopy(project.overrides.get(identifier)) for identifier in after}
    for identifier, value in after.items():
        if value is None:
            project.overrides.pop(identifier, None)
        else:
            project.overrides[identifier] = value
    project.undo_stack.append(dict(target='entity_overrides', entity_ids=sorted(before), before=before, after=deepcopy(after)))
    project.redo_stack.clear()
