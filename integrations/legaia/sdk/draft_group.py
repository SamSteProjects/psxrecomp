"""Reviewed atomic X/Z offsets of existing project-local NPC drafts."""
from copy import copy, deepcopy
from importer.core import ImportError as RetailImportError
from .project import ProjectError, digest
from .project_copy import source_key
from .scene_preview import source_key as preview_source_key


def review(project, request):
    if project.mode != 'edit' or project.active_scene not in project.imports:
        raise ProjectError('NPC draft group movement requires an imported active scene in Edit mode')
    if not isinstance(request, dict) or set(request) != {'entity_ids', 'delta'}:
        raise ProjectError('NPC draft group review accepts draft identities and X/Z delta only')
    ids, delta = request['entity_ids'], request['delta']
    if (not isinstance(ids, list) or not 2 <= len(ids) <= 128 or
            any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids)):
        raise ProjectError('Choose2 through128 unique NPC drafts in the active scene')
    if (not isinstance(delta, dict) or set(delta) != {'x', 'z'} or
            any(type(v) is not int or v % 64 or abs(v) > 16320 for v in delta.values())):
        raise ProjectError('NPC group offsets require X/Z integer multiples of64 within -16320..16320')
    before = source_key(project)
    targets = []
    for identifier in sorted(ids):
        draft = project.actor_drafts.get(identifier)
        if not isinstance(draft, dict) or draft.get('scene_id') != project.active_scene:
            raise ProjectError('NPC draft group includes an unavailable or other-scene draft')
        project._validate_actor_draft(identifier, draft)
        proposed = {axis: draft['position'][axis] + delta[axis] for axis in ('x', 'z')}
        value = {**deepcopy(draft), 'position': proposed}
        try:
            project._validate_actor_draft(identifier, value)
        except RetailImportError as exc:
            raise ProjectError(f'{draft["name"]}: {exc}') from exc
        targets.append(dict(entity_id=identifier, draft=deepcopy(draft), proposed=proposed))
    scene_key = preview_source_key(project)
    if source_key(project) != before:
        raise ProjectError('Project changed during NPC draft group review')
    normalized = dict(entity_ids=sorted(ids), delta=deepcopy(delta))
    return dict(schema_version='legaia.draft-group-review.v1', scene_id=project.active_scene,
                project_source_key=before, scene_preview_source_key=scene_key,
                request=normalized, targets=targets, changed_count=len(targets) if any(delta.values()) else 0,
                review_key=digest(dict(source=before, request=normalized, algorithm='draft-group-offset.v1')),
                gameplay_verified=False, limitations=[
                    'Moves existing authored NPC drafts only; imported actors, donors and unselected drafts remain unchanged.',
                    'X/Z use retail placement precision. Preview elevation is sampled source scenery, not authored height.',
                    'Movement adds no runtime spawning, scheduling, collision or gameplay acceptance.'])


def proposal_view(project, report):
    if review(project, report['request']) != report:
        raise ProjectError('NPC draft group changed since review')
    view = copy(project)
    view.actor_drafts = deepcopy(project.actor_drafts)
    for row in report['targets']:
        view.actor_drafts[row['entity_id']]['position'] = deepcopy(row['proposed'])
    return view


def apply(project, command):
    if set(command) != {'type', 'entity_ids', 'delta', 'review_key'}:
        raise ProjectError('NPC draft group command requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_ids', 'delta')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('Project changed since NPC draft group review; review again')
    if not report['changed_count']:
        return
    before = {row['entity_id']: deepcopy(row['draft']) for row in report['targets']}
    after = {row['entity_id']: {**deepcopy(row['draft']), 'position': deepcopy(row['proposed'])}
             for row in report['targets']}
    project.actor_drafts.update(after)
    project.undo_stack.append(dict(target='actor_draft_batch', before=before, after=deepcopy(after),
                                   source_entity_ids=sorted({draft['donor_entity_id'] for draft in before.values()})))
    project.redo_stack.clear()
