"""Named source-bound editor camera views; no game transforms or runtime authority."""
from copy import deepcopy
import math
import uuid
from .project import ProjectError, digest

COMMANDS = {'create_scene_view', 'rename_scene_view', 'update_scene_view', 'delete_scene_view'}

def display(value):
    if not isinstance(value, dict) or set(value) != {'camera', 'representation', 'layers'}:
        raise ProjectError('Scene view requires camera, representation and layers only')
    camera = value['camera']
    if not isinstance(camera, dict) or set(camera) != {'projection', 'yaw', 'pitch', 'distance', 'target'}:
        raise ProjectError('Invalid scene view camera')
    def number(item, low, high):
        return type(item) in (int, float) and low <= item <= high and math.isfinite(item)
    target = camera['target']
    if (camera['projection'] not in ('perspective', 'orthographic') or
            not number(camera['yaw'], -1e12, 1e12) or
            not number(camera['pitch'], 0 if camera['projection'] == 'orthographic' else .12, math.pi / 2) or
            not number(camera['distance'], 20, 1e8) or
            not isinstance(target, dict) or set(target) != {'x', 'y', 'z'} or
            any(not number(item, -1e12, 1e12) for item in target.values())):
        raise ProjectError('Scene view camera exceeds supported display limits')
    if value['representation'] not in ('authored', 'retail'):
        raise ProjectError('Invalid scene view representation')
    layers = value['layers']
    if not isinstance(layers, dict) or set(layers) != {'actors', 'scenery', 'ground'} or any(type(item) is not bool for item in layers.values()):
        raise ProjectError('Invalid scene view layers')
    return deepcopy(value)

def validate(project, identifier, value):
    try:
        if not isinstance(identifier, str) or not identifier.startswith('view://') or str(uuid.UUID(identifier[7:])) != identifier[7:]:
            raise ValueError()
    except ValueError:
        raise ProjectError('Invalid scene view identity') from None
    if (not isinstance(value, dict) or set(value) != {'id', 'name', 'scene_id', 'import_sha256', 'display'} or
            value['id'] != identifier or not isinstance(value['name'], str) or
            value['name'] != value['name'].strip() or not 1 <= len(value['name']) <= 80 or
            not isinstance(value['scene_id'], str) or value['scene_id'] not in project.imports or
            value['import_sha256'] != digest(project.imports[value['scene_id']])):
        raise ProjectError('Scene view differs from its imported scene binding')
    display(value['display'])

def review_key(project, value):
    return digest({'project_root': str(project.root), 'scene_view': value})

def command(project, body):
    kind = body['type']
    if kind == 'create_scene_view':
        if set(body) != {'type', 'scene_id', 'import_sha256', 'name', 'display'}:
            raise ProjectError('Save scene view requires scene/source identity, name and display only')
        if not isinstance(body['scene_id'], str) or body['scene_id'] != project.active_scene or body['scene_id'] not in project.imports or body['import_sha256'] != digest(project.imports[body['scene_id']]):
            raise ProjectError('Scene changed before saving the view')
        if len(project.scene_views) >= 128:
            raise ProjectError('Project is limited to 128 saved scene views')
        identifier = 'view://' + str(uuid.uuid4())
        before = None
        after = dict(id=identifier, name=body['name'].strip() if isinstance(body['name'], str) else body['name'], scene_id=body['scene_id'], import_sha256=body['import_sha256'], display=display(body['display']))
    else:
        fields = {'type', 'view_id', 'review_key'} | ({'name'} if kind == 'rename_scene_view' else {'display'} if kind == 'update_scene_view' else set())
        if set(body) != fields:
            raise ProjectError('Scene view command has unsupported fields')
        identifier = body['view_id']
        if not isinstance(identifier, str) or identifier not in project.scene_views:
            raise ProjectError('Saved scene view is unavailable')
        before = deepcopy(project.scene_views[identifier])
        validate(project, identifier, before)
        if body['review_key'] != review_key(project, before):
            raise ProjectError('Scene view changed since review; reopen it')
        after = deepcopy(before)
        if kind == 'rename_scene_view':
            after['name'] = body['name'].strip() if isinstance(body['name'], str) else body['name']
        elif kind == 'update_scene_view':
            if before['scene_id'] != project.active_scene:
                raise ProjectError('Recall the scene before replacing its view')
            after['display'] = display(body['display'])
        else:
            after = None
    if after is not None:
        validate(project, identifier, after)
        if any(key != identifier and row['scene_id'] == after['scene_id'] and row['name'].casefold() == after['name'].casefold() for key, row in project.scene_views.items()):
            raise ProjectError('A saved view with this name already exists in the scene')
    if before == after:
        return
    if after is None:
        project.scene_views.pop(identifier)
    else:
        project.scene_views[identifier] = after
    project.undo_stack.append(dict(target='scene_views', view_id=identifier, scene_id=(after or before)['scene_id'], before=before, after=deepcopy(after)))
    project.redo_stack.clear()
