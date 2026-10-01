"""Project-local source-bound actor selections; never game hierarchy or transforms."""
from copy import deepcopy
import uuid
from .project import ProjectError, digest

COMMANDS = {'create_actor_selection_set', 'rename_actor_selection_set',
            'update_actor_selection_set', 'delete_actor_selection_set'}

def members(project, scene_id, actor_ids):
    document = project.imports.get(scene_id)
    allowed = {actor['semantic_id'] for actor in document['actors']} if document else set()
    if (not isinstance(actor_ids, list) or not 2 <= len(actor_ids) <= 128 or
            any(not isinstance(value, str) or value not in allowed for value in actor_ids) or
            len(set(actor_ids)) != len(actor_ids)):
        raise ProjectError('Saved selections require 2 through 128 distinct imported actors from one scene')
    return sorted(actor_ids)

def validate(project, identifier, value):
    try:
        if not isinstance(identifier, str) or not identifier.startswith('selection://') or str(uuid.UUID(identifier.removeprefix('selection://'))) != identifier.removeprefix('selection://'):
            raise ValueError()
    except ValueError:
        raise ProjectError('Invalid saved selection identity') from None
    if (not isinstance(value, dict) or set(value) != {'id', 'name', 'scene_id', 'import_sha256', 'actor_ids'} or
            value['id'] != identifier or not isinstance(value['name'], str) or
            value['name'] != value['name'].strip() or not 1 <= len(value['name']) <= 80 or
            not isinstance(value['scene_id'], str) or value['scene_id'] not in project.imports or
            value['import_sha256'] != digest(project.imports[value['scene_id']])):
        raise ProjectError('Saved selection differs from its imported scene binding')
    if value['actor_ids'] != members(project, value['scene_id'], value['actor_ids']):
        raise ProjectError('Saved selection members must use canonical source identity order')

def review_key(project, value):
    return digest({'project_root': str(project.root), 'selection': value})

def command(project, body):
    kind = body['type']
    if kind == 'create_actor_selection_set':
        if set(body) != {'type', 'scene_id', 'import_sha256', 'name', 'actor_ids'}:
            raise ProjectError('Save selection accepts scene/source identity, name and actor IDs only')
        if body['scene_id'] != project.active_scene or body['scene_id'] not in project.imports or body['import_sha256'] != digest(project.imports[body['scene_id']]):
            raise ProjectError('Scene changed before saving the actor selection')
        if len(project.actor_selection_sets) >= 128:
            raise ProjectError('Project is limited to 128 saved actor selections')
        identifier = 'selection://' + str(uuid.uuid4())
        after = {'id': identifier, 'name': body['name'].strip() if isinstance(body['name'], str) else body['name'],
                 'scene_id': body['scene_id'], 'import_sha256': body['import_sha256'],
                 'actor_ids': members(project, body['scene_id'], body['actor_ids'])}
        before = None
    else:
        fields = {'type', 'selection_set_id', 'review_key'} | ({'name'} if kind == 'rename_actor_selection_set' else {'actor_ids'} if kind == 'update_actor_selection_set' else set())
        if set(body) != fields:
            raise ProjectError('Saved selection command has unsupported fields')
        identifier = body['selection_set_id']
        if not isinstance(identifier, str) or identifier not in project.actor_selection_sets:
            raise ProjectError('Saved selection is unavailable')
        before = deepcopy(project.actor_selection_sets[identifier])
        validate(project, identifier, before)
        if body['review_key'] != review_key(project, before):
            raise ProjectError('Saved selection changed since review; reopen it')
        after = deepcopy(before)
        if kind == 'rename_actor_selection_set':
            after['name'] = body['name'].strip() if isinstance(body['name'], str) else body['name']
        elif kind == 'update_actor_selection_set':
            if before['scene_id'] != project.active_scene:
                raise ProjectError('Recall this selection before replacing its members')
            after['actor_ids'] = members(project, before['scene_id'], body['actor_ids'])
        else:
            after = None
    if after is not None:
        validate(project, identifier, after)
        if any(key != identifier and value['scene_id'] == after['scene_id'] and value['name'].casefold() == after['name'].casefold() for key, value in project.actor_selection_sets.items()):
            raise ProjectError('A saved selection with this name already exists in the scene')
    if before == after:
        return
    if after is None:
        project.actor_selection_sets.pop(identifier)
    else:
        project.actor_selection_sets[identifier] = after
    project.undo_stack.append({'target': 'actor_selection_sets', 'selection_set_id': identifier,
                               'entity_ids': sorted(set((before or {}).get('actor_ids', []) + (after or {}).get('actor_ids', []))),
                               'before': before, 'after': deepcopy(after)})
    project.redo_stack.clear()
