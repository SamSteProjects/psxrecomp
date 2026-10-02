"""Portable named imported-scene selections; never modify game placements."""
from copy import deepcopy
import re
import uuid

from .project import ProjectError, digest
from .project_copy import source_key

COMMANDS = {'create_scene_selection_set', 'rename_scene_selection_set',
            'update_scene_selection_set', 'delete_scene_selection_set'}


def _members(project, scene, identifiers):
    if not isinstance(scene, str) or scene not in project.imports:
        raise ProjectError('Selection set requires an imported scene')
    if (not isinstance(identifiers, list) or not 1 <= len(identifiers) <= 128 or
            any(not isinstance(item, str) for item in identifiers) or len(set(identifiers)) != len(identifiers)):
        raise ProjectError('Selection set requires 1..128 unique imported identities')
    actors = {actor['semantic_id'] for actor in project.imports[scene]['actors']}
    prefix = 'environment://' + scene.removeprefix('scene://') + '/field-map/decorations/'
    decorations = []
    for identifier in identifiers:
        if identifier in actors:
            continue
        suffix = identifier.removeprefix(prefix)
        if not identifier.startswith(prefix) or not re.fullmatch(r'[0-9]{5}', suffix) or int(suffix) >= 16384:
            raise ProjectError('Selection set contains an identity outside its imported scene')
        decorations.append(identifier)
    return sorted(identifiers), sorted(decorations)


def _name(value):
    if not isinstance(value, str):
        raise ProjectError('Selection set name must be text')
    value = value.strip()
    if not 1 <= len(value) <= 80 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ProjectError('Selection set name requires 1..80 printable characters')
    return value


def validate(project, identifier, value):
    """Validate portable metadata without opening a retail disc."""
    prefix = 'scene-selection://'
    try:
        if not isinstance(identifier, str) or not identifier.startswith(prefix) or str(uuid.UUID(identifier[len(prefix):])) != identifier[len(prefix):]:
            raise ValueError()
    except ValueError:
        raise ProjectError('Invalid scene selection identity') from None
    if (not isinstance(value, dict) or set(value) != {'id', 'name', 'scene_id', 'import_sha256', 'map_sha256', 'entity_ids'} or
            value['id'] != identifier or not isinstance(value['scene_id'], str) or value['scene_id'] not in project.imports or
            value['import_sha256'] != digest(project.imports[value['scene_id']])):
        raise ProjectError('Selection set differs from its imported scene binding')
    if _name(value['name']) != value['name']:
        raise ProjectError('Selection set name must be trimmed')
    identities, decorations = _members(project, value['scene_id'], value['entity_ids'])
    if identities != value['entity_ids']:
        raise ProjectError('Saved selection identities must be canonically sorted')
    if (decorations and (not isinstance(value['map_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', value['map_sha256']))) or (not decorations and value['map_sha256'] is not None):
        raise ProjectError('Selection set MAP binding does not match its member types')


def review_key(root, value):
    # pathlib.Path also exposes .root (the drive), so distinguish project instances.
    return digest(dict(project_root=str(root.root if hasattr(root, 'imports') else root), scene_selection_set=value))


def source_binding(project, scene, identifiers):
    """Prove current static membership against verified source MAP bytes."""
    if project.mode != 'edit' or scene != project.active_scene:
        raise ProjectError('Selection set requires the active imported scene in Edit mode')
    _, decorations = _members(project, scene, identifiers)
    before = source_key(project)
    map_hash = None
    if decorations:
        from .environment_group import _prepare
        map_hash = _prepare(project, scene, decorations, minimum=1)['source_hash']
    if source_key(project) != before:
        raise ProjectError('Project changed while proving selection membership')
    return dict(import_sha256=digest(project.imports[scene]), map_sha256=map_hash)


def _saved(project, identifier, key):
    if not isinstance(identifier, str) or identifier not in project.scene_selection_sets:
        raise ProjectError('Saved scene selection is unavailable')
    value = deepcopy(project.scene_selection_sets[identifier])
    validate(project, identifier, value)
    if key != review_key(project, value):
        raise ProjectError('Saved scene selection changed since review; reopen it')
    return value


def review(project, selection_set_id, key):
    value = _saved(project, selection_set_id, key)
    before = source_key(project)
    binding = source_binding(project, value['scene_id'], value['entity_ids'])
    if binding != {field: value[field] for field in ('import_sha256', 'map_sha256')}:
        raise ProjectError('Saved scene selection source changed; recall rejected')
    if source_key(project) != before:
        raise ProjectError('Project changed while recalling selection')
    return dict(schema_version='legaia.scene-selection-review.v1', project_source_key=before,
                **value, review_key=review_key(project, value), read_only=True)


def command(project, body):
    if project.mode != 'edit' or not isinstance(body, dict) or body.get('type') not in COMMANDS:
        raise ProjectError('Selection set command requires Edit mode and a supported operation')
    kind = body['type']
    if kind == 'create_scene_selection_set':
        if set(body) != {'type', 'scene_id', 'import_sha256', 'map_sha256', 'name', 'entity_ids'}:
            raise ProjectError('Save selection requires exact scene/source, name and membership fields')
        if len(project.scene_selection_sets) >= 128:
            raise ProjectError('Project is limited to 128 saved scene selections')
        binding = source_binding(project, body['scene_id'], body['entity_ids'])
        if binding != {field: body[field] for field in binding}:
            raise ProjectError('Scene selection source changed before saving')
        identifier = 'scene-selection://' + str(uuid.uuid4())
        before = None
        after = dict(id=identifier, name=_name(body['name']), scene_id=body['scene_id'],
                     **binding, entity_ids=sorted(body['entity_ids']))
    else:
        fields = {'type', 'selection_set_id', 'review_key'} | ({'name'} if kind == 'rename_scene_selection_set' else {'entity_ids'} if kind == 'update_scene_selection_set' else set())
        if set(body) != fields:
            raise ProjectError('Selection set command has unsupported fields')
        identifier = body['selection_set_id']
        before = _saved(project, identifier, body['review_key'])
        after = deepcopy(before)
        if kind == 'rename_scene_selection_set':
            after['name'] = _name(body['name'])
        elif kind == 'update_scene_selection_set':
            # Prove the saved source before replacing membership, including removal of all decorations.
            review(project, identifier, body['review_key'])
            after.update(source_binding(project, before['scene_id'], body['entity_ids']))
            after['entity_ids'] = sorted(body['entity_ids'])
        else:
            after = None
    if after is not None:
        validate(project, identifier, after)
        if any(key != identifier and row['scene_id'] == after['scene_id'] and row['name'].casefold() == after['name'].casefold() for key, row in project.scene_selection_sets.items()):
            raise ProjectError('A saved selection with this name already exists in the scene')
    if before == after:
        return
    if after is None:
        project.scene_selection_sets.pop(identifier)
    else:
        project.scene_selection_sets[identifier] = after
    project.undo_stack.append(dict(target='scene_selection_sets', selection_set_id=identifier,
        scene_id=(after or before)['scene_id'], entity_ids=sorted(set((before or {}).get('entity_ids', []) + (after or {}).get('entity_ids', []))),
        before=before, after=deepcopy(after)))
    project.redo_stack.clear()
