"""Reviewed source MAP region corners, separate from imported facts and runtime."""
from copy import deepcopy
from hashlib import sha256
import re

from importer.core import ImportError
from .project import ProjectError, digest
from .project_copy import source_key

_CORNERS = ('x0', 'z0', 'x1', 'z1')
_HASH = re.compile(r'[0-9a-f]{64}')
_IDENTITY = re.compile(r'region://([^/]+)/field-map/primary/([0-9]{4})')


def _values(value):
    if (not isinstance(value, dict) or set(value) != set(_CORNERS) or
            any(type(value[key]) is not int or not 0 <= value[key] <= 255 for key in _CORNERS)):
        raise ProjectError('Region bounds require exactly four integer corner bytes in 0..255')
    return {key: value[key] for key in _CORNERS}


def _world_bounds(tiles):
    return {key: value * 128 + 64 for key, value in tiles.items()}


def _binding(project, scene):
    components = project.overrides.get(scene, {})
    if not isinstance(components, dict):
        raise ProjectError('Region bounds scene components are invalid')
    if 'RegionBounds' not in components:
        return None
    authored = components['RegionBounds']
    if (not isinstance(authored, dict) or
            set(authored) != {'source_sha256', 'edits'} or
            not isinstance(authored['source_sha256'], str) or
            not _HASH.fullmatch(authored['source_sha256']) or
            not isinstance(authored['edits'], list)):
        raise ProjectError('Region bounds require a source SHA256 and qualified region edits only')
    return deepcopy(authored)


def _context(project, scene):
    """Qualify every retained edit against the same fresh source MAP."""
    from importer.region_authoring import region_authoring_options, patch_field_regions
    if not isinstance(scene, str) or scene not in project.imports:
        raise ProjectError('Region bounds require an imported scene')
    document = project.imports[scene]
    name = document['scene']['name']
    if scene != 'scene://' + name:
        raise ProjectError('Region bounds scene identity differs from imported evidence')
    before = source_key(project)
    original = project._environment_source(scene)
    original_hash = sha256(original).hexdigest()
    authored = _binding(project, scene)
    try:
        imported = region_authoring_options(original, name)
        effective = (patch_field_regions(original, authored['source_sha256'], name,
                                         authored['edits'])[0] if authored is not None else original)
        current = region_authoring_options(effective, name)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    if imported['source_sha256'] != original_hash:
        raise ProjectError('Region options differ from the verified source MAP')
    return dict(project_key=before, scene=scene, name=name, original=original,
                source_hash=original_hash, authored=authored,
                imported=imported, current=current)


def _check_current(project, context):
    if source_key(project) != context['project_key']:
        raise ProjectError('Project changed while reviewing region bounds')
    if sha256(project._environment_source(context['scene'])).hexdigest() != context['source_hash']:
        raise ProjectError('Region MAP source changed while reviewing bounds')
    if source_key(project) != context['project_key']:
        raise ProjectError('Project changed while reviewing region bounds')


def _corners(record):
    return {key: record['encoded'][key] for key in _CORNERS}


def _indexed(document):
    return {record['region_id']: record for record in document['records']}


def review(project, region_id, values=None, action='set'):
    """Review Current, complete replacement corners, or return to retail bounds."""
    if project.mode != 'edit':
        raise ProjectError('Region bounds review requires Edit mode')
    if not isinstance(region_id, str) or len(region_id) > 1024:
        raise ProjectError('Region bounds require a stable primary region identity')
    match = _IDENTITY.fullmatch(region_id)
    if match is None:
        raise ProjectError('Region bounds require a stable primary region identity')
    scene = 'scene://' + match.group(1)
    if scene != project.active_scene or scene not in project.imports:
        raise ProjectError('Region bounds require a region in the active imported scene')
    if action not in ('set', 'clear') or action == 'clear' and values is not None:
        raise ProjectError('Region bounds action must be set, or clear with no requested values')
    requested = _values(values) if values is not None else None
    context = _context(project, scene)
    imported_by_id = _indexed(context['imported'])
    current_by_id = _indexed(context['current'])
    if region_id not in imported_by_id or region_id not in current_by_id:
        raise ProjectError('Region bounds identity is absent from the verified source MAP')
    imported_row = imported_by_id[region_id]
    imported_values = _corners(imported_row)
    current_values = _corners(current_by_id[region_id])
    edits = {edit['region_id']: deepcopy(edit) for edit in
             (context['authored'] or {}).get('edits', [])}
    authored_values = {key: edits[region_id][key] for key in _CORNERS} if region_id in edits else {}
    if action == 'clear' or requested == imported_values:
        edits.pop(region_id, None)
    elif requested is not None:
        edits[region_id] = {'region_id': region_id, **requested}
    binding = {'source_sha256': context['source_hash'],
               'edits': [edits[key] for key in sorted(edits)]}
    from importer.region_authoring import patch_field_regions, region_authoring_options
    try:
        proposed_bytes, _ = patch_field_regions(context['original'], context['source_hash'],
                                                context['name'], binding['edits'])
        proposed_row = _indexed(region_authoring_options(proposed_bytes, context['name']))[region_id]
    except ImportError as error:
        raise ProjectError(str(error)) from error
    proposed_values = _corners(proposed_row)
    tile_layers = {'imported': deepcopy(imported_row['tile_bounds']),
                   'current': deepcopy(current_by_id[region_id]['tile_bounds']),
                   'proposed': deepcopy(proposed_row['tile_bounds'])}
    final_component = binding if binding['edits'] else None
    # Inspection of Current never proposes a metadata-only sorting/normalization edit.
    project_change = (False if action == 'set' and requested is None else
                      context['authored'] != final_component)
    result = dict(schema_version='legaia.region-bounds-review.v1', read_only=True,
                  project_source_key=context['project_key'], scene_id=scene, region_id=region_id,
                  source={'map_sha256': context['source_hash'], 'row_sha256': imported_row['sha256'],
                          'record_index': imported_row['record_index'],
                          'byte_offset': imported_row['byte_offset'], 'byte_length': imported_row['byte_length']},
                  region_type=imported_row['encoded']['type'],
                  values_layers={'imported': imported_values, 'authored': authored_values,
                                 'current': current_values, 'proposed': proposed_values},
                  tile_bounds_layers=tile_layers,
                  world_bounds_layers={layer: _world_bounds(bounds) for layer, bounds in tile_layers.items()},
                  requested_values=deepcopy(requested), action=action,
                  effective_change_count=sum(current_values[key] != proposed_values[key] for key in _CORNERS),
                  project_change=project_change, value=binding,
                  scope='source-MAP-region-bounds-only', height_status='unknown',
                  activation='not_evaluated', gameplay_verified=False)
    result['review_key'] = digest(result)
    _check_current(project, context)
    return result


def apply(project, command):
    """Requalify a review and use the ordinary single-history project command."""
    if (not isinstance(command, dict) or set(command) !=
            {'type', 'region_id', 'values', 'action', 'review_key'} or
            command['type'] != 'apply_region_bounds' or
            not isinstance(command['review_key'], str) or not _HASH.fullmatch(command['review_key'])):
        raise ProjectError('Region bounds Apply requires exact region, corners, action and current review key')
    result = review(project, command['region_id'], command['values'], command['action'])
    if command['review_key'] != result['review_key']:
        raise ProjectError('Region bounds inputs or evidence changed since review')
    if result['project_change']:
        if result['value']['edits']:
            project.command({'type': 'set_region_bounds', 'entity_id': result['scene_id'],
                             'value': deepcopy(result['value'])})
        else:
            project.command({'type': 'clear_region_bounds', 'entity_id': result['scene_id']})
    return result


def effective_annotations(project, scene):
    """Return metadata-only layers for edited rows, leaving imported records intact."""
    if not isinstance(scene, str) or scene not in project.imports:
        raise ProjectError('Region bounds annotations require an imported scene')
    if _binding(project, scene) is None:
        return []
    context = _context(project, scene)
    imported_by_id = _indexed(context['imported'])
    current_by_id = _indexed(context['current'])
    annotations = []
    for edit in sorted(context['authored']['edits'], key=lambda row: row['region_id']):
        identifier = edit['region_id']
        imported = imported_by_id[identifier]
        effective = current_by_id[identifier]
        annotations.append({'region_id': identifier, 'row_sha256': imported['sha256'],
                            'values_layers': {'imported': _corners(imported), 'authored': _values(
                                {key: edit[key] for key in _CORNERS}), 'effective': _corners(effective)},
                            'tile_bounds_layers': {'imported': deepcopy(imported['tile_bounds']),
                                                   'effective': deepcopy(effective['tile_bounds'])},
                            'world_bounds_layers': {'imported': _world_bounds(imported['tile_bounds']),
                                                    'effective': _world_bounds(effective['tile_bounds'])}})
    _check_current(project, context)
    return annotations
