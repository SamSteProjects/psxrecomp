"""Named source-bound editor camera views; no game transforms or runtime authority."""
from copy import deepcopy
import math
import uuid
import re
import struct
from hashlib import sha256
from .project import ProjectError, digest
from .hierarchy_views import hierarchy
from .metadata_text import metadata_name

COMMANDS = {'create_scene_view', 'rename_scene_view', 'update_scene_view', 'delete_scene_view'}

def display(value):
    if not isinstance(value, dict) or not {'camera', 'representation', 'layers'} <= set(value) or set(value) - {'camera', 'representation', 'layers', 'grid', 'visibility', 'hierarchy'}:
        raise ProjectError('Scene view requires supported camera, representation, layers and optional display visibility')
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
    if 'grid' in value and type(value['grid']) is not bool:
        raise ProjectError('Scene view grid must be a display boolean')
    if 'hierarchy' in value:hierarchy(value['hierarchy'])
    return deepcopy(value)

def _visibility(project, scene, value, *, require_available=False):
    if 'visibility' not in value:
        return []
    visibility = value['visibility']
    legacy_fields = {'hidden_entity_ids', 'isolated_entity_id', 'map_sha256'}
    group_fields = {'hidden_entity_ids', 'isolated_entity_ids', 'map_sha256'}
    if not isinstance(visibility, dict) or set(visibility) not in (legacy_fields, group_fields):
        raise ProjectError('Scene view requires exact visibility fields')
    hidden = visibility['hidden_entity_ids']
    if 'isolated_entity_ids' in visibility:
        isolated = visibility['isolated_entity_ids']
        if (not isinstance(isolated, list) or not 1 <= len(isolated) <= 128 or
                any(not isinstance(item, str) or not 1 <= len(item) <= 1024 for item in isolated) or
                isolated != sorted(set(isolated))):
            raise ProjectError('Scene view isolation requires 1..128 canonical unique instance IDs')
    else:
        identifier = visibility['isolated_entity_id']
        if identifier is not None and (not isinstance(identifier, str) or not 1 <= len(identifier) <= 1024):
            raise ProjectError('Scene view isolation requires an instance ID or null')
        isolated = [] if identifier is None else [identifier]
    if (not isinstance(hidden, list) or len(hidden) > 32768 or
            any(not isinstance(item, str) or not 1 <= len(item) <= 1024 for item in hidden) or
            hidden != sorted(set(hidden)) or
            any(identifier in hidden for identifier in isolated)):
        raise ProjectError('Scene view visibility requires canonical unique hidden IDs and a visible isolation target')
    actors = {row['semantic_id'] for row in project.imports[scene]['actors']}
    prefix = 'environment://' + scene.removeprefix('scene://') + '/field-map/'
    environment = []
    for identifier in hidden + isolated:
        if identifier in actors:
            continue
        if identifier.startswith('authored-actor://'):
            if value['representation'] != 'authored':
                raise ProjectError('Saved NPC visibility requires the Authored scene representation')
            from .scene_selection_sets import _members
            _members(project, scene, [identifier], require_available=require_available)
            continue
        suffix = identifier.removeprefix(prefix + 'decorations/')
        if identifier != prefix + 'ground' and (not identifier.startswith(prefix + 'decorations/') or not re.fullmatch(r'[0-9]{5}', suffix) or int(suffix) >= 16384):
            raise ProjectError('Saved visibility supports imported actors, NPC drafts, static decorations and ground only')
        environment.append(identifier)
    binding = visibility['map_sha256']
    if (environment and (not isinstance(binding, str) or not re.fullmatch(r'[0-9a-f]{64}', binding))) or (not environment and binding is not None):
        raise ProjectError('Scene view visibility MAP binding differs from its instance types')
    return environment


def _verify_visibility(project, scene, value):
    environment = _visibility(project, scene, value, require_available=True)
    if not environment:
        return
    source = project._environment_source(scene)
    if sha256(source).hexdigest() != value['visibility']['map_sha256']:
        raise ProjectError('Scene view visibility source MAP changed')
    for identifier in environment:
        if identifier.endswith('/ground'):
            continue
        cell = int(identifier.rsplit('/', 1)[1])
        if len(source) < 0x8000 + cell * 2 + 2:
            raise ProjectError('Scene view decoration exceeds the source MAP')
        word = struct.unpack_from('<H', source, 0x8000 + cell * 2)[0]
        record = word & 511
        if record < 4 or not word & 0x2000 or struct.unpack_from('<H', source, record * 32 + 18)[0] & 4:
            raise ProjectError('Scene view decoration is not a static source instance')


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
    metadata_name(value['name'], 'Scene view name')
    display(value['display'])
    _visibility(project, value['scene_id'], value['display'])

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
        if kind in ('create_scene_view', 'update_scene_view'):
            _verify_visibility(project, after['scene_id'], after['display'])
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
