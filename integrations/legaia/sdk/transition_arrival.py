"""Source-qualified destination arrival comparison; no source trigger or runtime pose."""
from copy import copy, deepcopy
from .project import ProjectError
from .scene_preview import source_key
from .resources import refresh_resource_catalog, _verify, project_transition_state_key
from .transition_assets import validate_transition_asset


def inspect(project, asset_id, expected_key):
    if project.mode != 'edit' or expected_key is None or expected_key != source_key(project):
        raise ProjectError('Transition arrival source changed or is outside Edit mode')
    key = project_transition_state_key(project)
    catalog = refresh_resource_catalog(project)
    records = [r for r in catalog['records'] if r['id'] == asset_id and r['kind'] == 'transition']
    if len(records) != 1:
        raise ProjectError('Transition arrival requires one verified source resource')
    record = validate_transition_asset(records[0])
    destination = record['target']
    if record['reference']['target_scene_name'] is None or destination not in project.imports:
        raise ProjectError('Import the named destination scene before inspecting arrival positions')
    _verify(project, project.imports[destination])
    view = copy(project)
    view.active_scene = destination
    destination_key = source_key(view)
    if destination_key is None:
        raise ProjectError('Destination scene preview is unavailable')
    if key != project_transition_state_key(project) or expected_key != source_key(project):
        raise ProjectError('Transition arrival project changed during inspection')
    return dict(schema_version='legaia.transition-arrival-preview.v1', read_only=True,
                asset_id=asset_id, source_scene_id=project.active_scene, source_key=expected_key,
                project_state_key=key, destination_scene_id=destination,
                destination_source_key=destination_key, resource=deepcopy(record),
                reference_y=0, height_known=False, runtime_verified=False,
                limitations=['Positions describe destination arrival operands, never source trigger locations.',
                             'Y is an explicit reference plane; source elevation and runtime pose are unknown.',
                             'Encoded scene changes do not establish execution or gameplay reachability.'])
