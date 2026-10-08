"""Review destination edits against the source NPC without changing scenes."""
from copy import copy, deepcopy
from importer.transition_authoring import encode_transition_arrival
from .project import ProjectError, digest
from .project_copy import source_key as copy_key
from .scene_preview import source_key as scene_key
from .npc_arrival_preview import inspect, source_key
from .npc_transitions import review as native_review

FIELDS = {'entity_id','transition_id','project_inputs_key','destination_source_key','arrival'}


def source_view(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if not isinstance(draft, dict) or draft['scene_id'] not in project.imports:
        raise ProjectError('NPC arrival authoring requires an imported source NPC')
    view = copy(project)
    view.active_scene = draft['scene_id']
    return view


def review(project, request):
    if not isinstance(request, dict) or set(request) != FIELDS:
        raise ProjectError('NPC arrival Review requires exact source, destination and arrival fields')
    if (project.mode != 'edit' or request['project_inputs_key'] != source_key(project) or
            request['destination_source_key'] != scene_key(project)):
        raise ProjectError('NPC arrival authoring project or destination changed')
    view = source_view(project, request['entity_id'])
    preview = inspect(view, dict(entity_id=request['entity_id'],transition_id=request['transition_id'],project_source_key=copy_key(view)))
    if project.active_scene != preview['destination_scene_id'] or preview['destination_source_key'] != request['destination_source_key']:
        raise ProjectError('NPC arrival authoring requires the qualified destination scene')
    row = next(r for r in preview['source']['options']['transitions'] if r['semantic_id'] == request['transition_id'])
    encoded = encode_transition_arrival(request['arrival'], row['effective_values'])
    entries = deepcopy(preview['source']['draft'].get('transitions', {}).get('entries', {}))
    entries[request['transition_id']] = encoded
    native = native_review(view, dict(entity_id=request['entity_id'], entries=entries))
    if request['project_inputs_key'] != source_key(project) or request['destination_source_key'] != scene_key(project):
        raise ProjectError('NPC arrival source changed during Review')
    result = dict(schema_version='legaia.npc-arrival-review.v1',read_only=True,
                  request=deepcopy(request),preview=preview,proposed_encoded=encoded,
                  native_review=native,authored_change=native['current'] != native['proposed'])
    result['review_key'] = digest(result)
    return result


def apply(project, command):
    if not isinstance(command, dict) or set(command) != FIELDS | {'type','review_key'} or command['type'] != 'set_actor_draft_arrival':
        raise ProjectError('NPC destination arrival Apply requires the exact reviewed command')
    report = review(project, {k:command[k] for k in FIELDS})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC arrival Review changed; review again')
    if not report['authored_change']:
        return
    # The ordinary source-scene command runs on detached ownership/history.
    # Commit only its qualified NPC collections; destination navigation stays held.
    view = source_view(project, command['entity_id'])
    view.actor_drafts, view.undo_stack, view.redo_stack = deepcopy((project.actor_drafts, project.undo_stack, project.redo_stack))
    original_history = deepcopy((project.undo_stack, project.redo_stack))
    native = report['native_review']
    view.command(dict(type='set_actor_draft_transitions',entity_id=command['entity_id'],
                      entries=native['proposed']['transitions']['entries'],review_key=native['review_key']))
    if view.actor_drafts[command['entity_id']] != native['proposed'] or len(view.undo_stack) != len(project.undo_stack)+1:
        raise ProjectError('NPC destination arrival differs from its reviewed source command')
    if command['project_inputs_key'] != source_key(project) or command['destination_source_key'] != scene_key(project) or original_history != (project.undo_stack, project.redo_stack):
        raise ProjectError('NPC arrival inputs or history changed during Apply')
    project.actor_drafts, project.undo_stack, project.redo_stack = view.actor_drafts, view.undo_stack, view.redo_stack
