"""Destination viewport evidence for clone-owned arrivals, never runtime travel."""
from copy import copy, deepcopy
from .project import ProjectError, digest
from .project_inputs import identity
from .project_copy import source_key as copy_key
from .scene_preview import source_key as scene_key
from .resources import _verify
from .npc_transitions import source


def source_key(project):
    return digest(identity(project))


def inspect(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'transition_id', 'project_source_key'}:
        raise ProjectError('NPC arrival preview requires exact NPC, transition and source identities')
    if project.mode != 'edit' or request['project_source_key'] != copy_key(project):
        raise ProjectError('NPC arrival preview source changed or is outside Edit mode')
    key = source_key(project)
    report = source(project, request['entity_id'])
    rows = [row for row in report['options']['transitions'] if row['semantic_id'] == request['transition_id']]
    if len(rows) != 1:
        raise ProjectError('NPC arrival preview requires one qualified donor transition')
    row = rows[0]
    destination = 'scene://' + row['destination']
    if destination not in project.imports:
        raise ProjectError('Import the named destination scene before inspecting NPC arrival positions')
    _verify(project, project.imports[destination])
    view = copy(project)
    view.active_scene = destination
    destination_key = scene_key(view)
    if destination_key is None:
        raise ProjectError('NPC arrival destination preview is unavailable')
    if key != source_key(project) or request['project_source_key'] != copy_key(project):
        raise ProjectError('NPC arrival project changed during inspection')
    return dict(schema_version='legaia.npc-arrival-preview.v1', read_only=True,
                entity_id=request['entity_id'], transition_id=request['transition_id'],
                source_scene_id=report['scene_id'], project_source_key=report['project_source_key'],
                project_inputs_key=key, destination_scene_id=destination,
                destination_source_key=destination_key, source=deepcopy(report),
                reference_y=0, height_known=False, runtime_verified=False,
                transition_activation='not_asserted')
