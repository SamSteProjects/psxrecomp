"""Reviewed source MAP trigger cells, without evaluating payload or activation."""
from copy import deepcopy
from hashlib import sha256
import re

from importer.core import ImportError
from .project import ProjectError, digest
from .project_copy import source_key

_CELLS = ('tile_x', 'tile_z')
_HASH = re.compile(r'[0-9a-f]{64}')
_IDENTITY = re.compile(r'trigger://([^/]+)/field-map/primary/kind-[01]/[0-9]{4}')


def _values(value):
    if (not isinstance(value, dict) or set(value) != set(_CELLS) or
            any(type(value[key]) is not int or not 0 <= value[key] <= 255 for key in _CELLS)):
        raise ProjectError('Trigger cells require exactly two integer tile bytes in 0..255')
    return {key: value[key] for key in _CELLS}


def _world_bounds(tiles):
    return {key: value * 128 for key, value in tiles.items()}


def _binding(project, scene):
    components = project.overrides.get(scene, {})
    if not isinstance(components, dict):
        raise ProjectError('Trigger cell scene components are invalid')
    if 'TriggerCells' not in components:
        return None
    authored = components['TriggerCells']
    if (not isinstance(authored, dict) or
            set(authored) != {'source_sha256', 'edits'} or
            not isinstance(authored['source_sha256'], str) or
            not _HASH.fullmatch(authored['source_sha256']) or
            not isinstance(authored['edits'], list)):
        raise ProjectError('Trigger cells require a source SHA256 and qualified cell edits only')
    return deepcopy(authored)


def _context(project, scene):
    """Qualify every retained edit against the same freshly read source MAP."""
    from importer.trigger_authoring import trigger_authoring_options, patch_field_triggers
    if not isinstance(scene, str) or scene not in project.imports:
        raise ProjectError('Trigger cells require an imported scene')
    document = project.imports[scene]
    name = document['scene']['name']
    if scene != 'scene://' + name:
        raise ProjectError('Trigger cell scene identity differs from imported evidence')
    before = source_key(project)
    original = project._environment_source(scene)
    original_hash = sha256(original).hexdigest()
    authored = _binding(project, scene)
    try:
        imported = trigger_authoring_options(original, name)
        effective = (patch_field_triggers(original, authored['source_sha256'], name,
                                          authored['edits'])[0] if authored is not None else original)
        current = trigger_authoring_options(effective, name)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    if imported['source_sha256'] != original_hash:
        raise ProjectError('Trigger options differ from the verified source MAP')
    return dict(project_key=before, scene=scene, name=name, original=original,
                source_hash=original_hash, authored=authored, imported=imported, current=current)


def _check_current(project, context):
    if source_key(project) != context['project_key']:
        raise ProjectError('Project changed while reviewing trigger cells')
    if sha256(project._environment_source(context['scene'])).hexdigest() != context['source_hash']:
        raise ProjectError('Trigger MAP source changed while reviewing cells')
    if source_key(project) != context['project_key']:
        raise ProjectError('Project changed while reviewing trigger cells')


def _cells(record):
    return {key: record['encoded'][key] for key in _CELLS}


def _indexed(document):
    return {record['trigger_id']: record for record in document['records']}


def review(project, trigger_id, values=None, action='set'):
    """Review Current, replace the complete cell, or return one row to retail."""
    if project.mode != 'edit':
        raise ProjectError('Trigger cell review requires Edit mode')
    if (not isinstance(trigger_id, str) or len(trigger_id) > 1024 or
            _IDENTITY.fullmatch(trigger_id) is None):
        raise ProjectError('Trigger cells require a stable primary kind-0 or kind-1 identity')
    scene = 'scene://' + trigger_id.split('/')[2]
    if scene != project.active_scene or scene not in project.imports:
        raise ProjectError('Trigger cells require a trigger in the active imported scene')
    if action not in ('set', 'clear') or action == 'clear' and values is not None:
        raise ProjectError('Trigger cell action must be set, or clear with no requested values')
    requested = _values(values) if values is not None else None
    context = _context(project, scene)
    imported_by_id = _indexed(context['imported'])
    current_by_id = _indexed(context['current'])
    if trigger_id not in imported_by_id or trigger_id not in current_by_id:
        raise ProjectError('Trigger identity is absent from the verified source MAP')
    imported_row = imported_by_id[trigger_id]
    imported_values = _cells(imported_row)
    current_values = _cells(current_by_id[trigger_id])
    edits = {edit['trigger_id']: deepcopy(edit) for edit in
             (context['authored'] or {}).get('edits', [])}
    authored_values = {key: edits[trigger_id][key] for key in _CELLS} if trigger_id in edits else {}
    if action == 'clear' or requested == imported_values:
        edits.pop(trigger_id, None)
    elif requested is not None:
        edits[trigger_id] = {'trigger_id': trigger_id, **requested}
    binding = {'source_sha256': context['source_hash'],
               'edits': [edits[key] for key in sorted(edits)]}
    from importer.trigger_authoring import patch_field_triggers, trigger_authoring_options
    try:
        proposed_bytes, _ = patch_field_triggers(context['original'], context['source_hash'],
                                                context['name'], binding['edits'])
        proposed_row = _indexed(trigger_authoring_options(proposed_bytes, context['name']))[trigger_id]
    except ImportError as error:
        raise ProjectError(str(error)) from error
    tile_layers = {'imported': deepcopy(imported_row['tile_bounds']),
                   'current': deepcopy(current_by_id[trigger_id]['tile_bounds']),
                   'proposed': deepcopy(proposed_row['tile_bounds'])}
    proposed_values = _cells(proposed_row)
    final_component = binding if binding['edits'] else None
    # Inspecting Current never proposes sorting or normalizing project metadata.
    project_change = (False if action == 'set' and requested is None else
                      context['authored'] != final_component)
    result = dict(schema_version='legaia.trigger-cells-review.v1', read_only=True,
                  project_source_key=context['project_key'], scene_id=scene, trigger_id=trigger_id,
                  source={'map_sha256': context['source_hash'], 'row_sha256': imported_row['sha256'],
                          'table_kind': imported_row['table_kind'], 'record_index': imported_row['record_index'],
                          'byte_offset': imported_row['byte_offset'], 'byte_length': imported_row['byte_length']},
                  trigger_kind=imported_row['table_kind'],
                  values_layers={'imported': imported_values, 'authored': authored_values,
                                 'current': current_values, 'proposed': proposed_values},
                  tile_bounds_layers=tile_layers,
                  world_bounds_layers={layer: _world_bounds(bounds) for layer, bounds in tile_layers.items()},
                  requested_values=deepcopy(requested), action=action,
                  effective_change_count=sum(current_values[key] != proposed_values[key] for key in _CELLS),
                  project_change=project_change, value=binding,
                  scope='source-MAP-trigger-cell-only', height_status='unknown',
                  activation='not_evaluated', gameplay_verified=False)
    result['review_key'] = digest(result)
    _check_current(project, context)
    return result


def apply(project, command):
    """Requalify reviewed inputs before one ordinary project-history command."""
    if (not isinstance(command, dict) or set(command) !=
            {'type', 'trigger_id', 'values', 'action', 'review_key'} or
            command['type'] != 'apply_trigger_cells' or
            not isinstance(command['review_key'], str) or not _HASH.fullmatch(command['review_key'])):
        raise ProjectError('Trigger cell Apply requires exact trigger, cell, action and current review key')
    result = review(project, command['trigger_id'], command['values'], command['action'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('Trigger cell inputs or evidence changed since review')
    if result['project_change']:
        try:
            if result['value']['edits']:
                project.command({'type': 'set_trigger_cells', 'entity_id': result['scene_id'],
                                 'value': deepcopy(result['value'])})
            else:
                project.command({'type': 'clear_trigger_cells', 'entity_id': result['scene_id']})
        except ImportError as error:
            # The command rechecks source ownership; late MAP drift is still atomic.
            raise ProjectError(str(error)) from error
    return result


def effective_annotations(project, scene):
    """Return source-qualified metadata layers for edited trigger rows only."""
    if not isinstance(scene, str) or scene not in project.imports:
        raise ProjectError('Trigger cell annotations require an imported scene')
    if _binding(project, scene) is None:
        return []
    context = _context(project, scene)
    imported_by_id = _indexed(context['imported'])
    current_by_id = _indexed(context['current'])
    annotations = []
    for edit in sorted(context['authored']['edits'], key=lambda row: row['trigger_id']):
        identifier = edit['trigger_id']
        imported = imported_by_id[identifier]
        effective = current_by_id[identifier]
        annotations.append({'trigger_id': identifier, 'row_sha256': imported['sha256'],
                            'values_layers': {'imported': _cells(imported), 'authored': _values(
                                {key: edit[key] for key in _CELLS}), 'effective': _cells(effective)},
                            'tile_bounds_layers': {'imported': deepcopy(imported['tile_bounds']),
                                                   'effective': deepcopy(effective['tile_bounds'])},
                            'world_bounds_layers': {'imported': _world_bounds(imported['tile_bounds']),
                                                    'effective': _world_bounds(effective['tile_bounds'])}})
    _check_current(project, context)
    return annotations
