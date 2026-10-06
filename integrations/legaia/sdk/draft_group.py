"""Reviewed atomic X/Z layouts and removal of project-local NPC drafts."""
from copy import copy, deepcopy
from importer.core import ImportError as RetailImportError
from .project import ProjectError, digest
from .project_copy import source_key
from .scene_preview import source_key as preview_source_key


def review(project, request):
    if project.mode != 'edit' or project.active_scene not in project.imports:
        raise ProjectError('NPC draft group editing requires an imported active scene in Edit mode')
    if not isinstance(request, dict) or set(request) not in ({'entity_ids', 'delta'}, {'entity_ids', 'layout'}, {'entity_ids','remove'}):
        raise ProjectError('NPC draft group review accepts draft identities and an X/Z delta, layout or removal only')
    removing='remove' in request
    if removing and request['remove'] is not True:
        raise ProjectError('NPC group removal requires remove=true')
    ids, delta, layout = request['entity_ids'], request.get('delta'), request.get('layout')
    if (not isinstance(ids, list) or not 2 <= len(ids) <= 128 or
            any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids)):
        raise ProjectError('Choose2 through128 unique NPC drafts in the active scene')
    if 'delta' in request and (not isinstance(delta, dict) or set(delta) != {'x', 'z'} or
            any(type(v) is not int or v % 64 or abs(v) > 16320 for v in delta.values())):
        raise ProjectError('NPC group offsets require X/Z integer multiples of64 within -16320..16320')
    if 'layout' in request:
        if not isinstance(layout, dict) or layout.get('kind') not in ('align','distribute','rotate','scale','mirror'):
            raise ProjectError('Choose a supported NPC group layout')
        kind=layout['kind']
        fields={'kind','axis'} if kind=='distribute' else {'kind','anchor_entity_id','quarter_turns'} if kind=='rotate' else {'kind','anchor_entity_id','percent'} if kind=='scale' else {'kind','axis','anchor_entity_id'}
        if set(layout)!=fields or (kind!='distribute' and layout['anchor_entity_id'] not in ids):
            raise ProjectError('NPC group layout requires exact fields and a selected anchor')
        if kind in ('align','distribute','mirror') and layout['axis'] not in ('x','z'):
            raise ProjectError('NPC group layout requires X or Z')
        if kind=='rotate' and (type(layout['quarter_turns']) is not int or layout['quarter_turns'] not in (-1,1,2)):
            raise ProjectError('NPC group rotation requires -1, 1 or 2 quarter turns')
        if kind=='scale' and (type(layout['percent']) is not int or not 1<=layout['percent']<=1000):
            raise ProjectError('NPC group spacing scale requires 1..1000 integer percent')
    before = source_key(project)
    targets = []
    for identifier in sorted(ids):
        draft = project.actor_drafts.get(identifier)
        if not isinstance(draft, dict) or draft.get('scene_id') != project.active_scene:
            raise ProjectError('NPC draft group includes an unavailable or other-scene draft')
        project._validate_actor_draft(identifier, draft)
        proposed = {axis: draft['position'][axis] + (delta[axis] if delta is not None else 0) for axis in ('x', 'z')}
        targets.append(dict(entity_id=identifier, draft=deepcopy(draft), proposed=None if removing else proposed))
    if layout is not None:
        axis=layout.get('axis')
        if layout['kind']=='align':
            anchor=next(row for row in targets if row['entity_id']==layout['anchor_entity_id'])
            for row in targets:row['proposed'][axis]=anchor['draft']['position'][axis]
        elif layout['kind'] in ('rotate','scale','mirror'):
            anchor=next(row['draft']['position'] for row in targets if row['entity_id']==layout['anchor_entity_id'])
            for row in targets:
                current=row['draft']['position']
                if layout['kind']=='rotate':
                    dx,dz=current['x']-anchor['x'],current['z']-anchor['z'];turns=layout['quarter_turns']
                    x,z=(-dz,dx) if turns==1 else (dz,-dx) if turns==-1 else (-dx,-dz)
                    row['proposed']=dict(x=anchor['x']+x,z=anchor['z']+z)
                elif layout['kind']=='mirror':
                    row['proposed'][axis]=2*anchor[axis]-current[axis]
                else:
                    for a in ('x','z'):
                        n=anchor[a]*100+(current[a]-anchor[a])*layout['percent']
                        units=(abs(n)+3200)//6400
                        row['proposed'][a]=(-units if n<0 else units)*64
        else:
            ordered=sorted(targets,key=lambda row:(row['draft']['position'][axis],row['entity_id']))
            low,high=ordered[0]['draft']['position'][axis]//64,ordered[-1]['draft']['position'][axis]//64
            span,intervals=high-low,len(ordered)-1
            if span<intervals:raise ProjectError('NPC distribution requires at least one64-unit interval per gap')
            for i,row in enumerate(ordered):row['proposed'][axis]=(low+(2*span*i+intervals)//(2*intervals))*64
    for row in ([] if removing else targets):
        identifier,draft,proposed=row['entity_id'],row['draft'],row['proposed']
        value = {**deepcopy(draft), 'position': proposed}
        try:
            project._validate_actor_draft(identifier, value)
        except RetailImportError as exc:
            raise ProjectError(f'{draft["name"]}: {exc}') from exc
    scene_key = preview_source_key(project)
    if source_key(project) != before:
        raise ProjectError('Project changed during NPC draft group review')
    normalized = dict(entity_ids=sorted(ids), **({'remove':True} if removing else {'layout':deepcopy(layout)} if layout is not None else {'delta':deepcopy(delta)}))
    return dict(schema_version='legaia.draft-group-review.v1', scene_id=project.active_scene,
                project_source_key=before, scene_preview_source_key=scene_key,
                request=normalized, targets=targets, changed_count=sum(row['draft']['position']!=row['proposed'] for row in targets),
                review_key=digest(dict(source=before, request=normalized, algorithm='draft-group-remove.v1' if removing else 'draft-group-native-layout.v1' if layout is not None and layout['kind'] in ('rotate','scale','mirror') else 'draft-group-layout.v1' if layout is not None else 'draft-group-offset.v1')),
                gameplay_verified=False, limitations=[
                    'Removes selected authored NPC drafts only; one Undo restores their identities and all metadata.' if removing else 'Moves existing authored NPC drafts only; imported actors, donors and unselected drafts remain unchanged.',
                    'X/Z use retail placement precision. Preview elevation is sampled source scenery, not authored height.',
                    'Removal changes the project candidate only; imported donor actors remain unchanged. Build acceptance and gameplay remain separate.' if removing else 'Movement adds no runtime spawning, scheduling, collision or gameplay acceptance.'])


def proposal_view(project, report):
    if review(project, report['request']) != report:
        raise ProjectError('NPC draft group changed since review')
    view = copy(project)
    view.actor_drafts = deepcopy(project.actor_drafts)
    for row in report['targets']:
        if report['request'].get('remove'):
            del view.actor_drafts[row['entity_id']]
        else:
            view.actor_drafts[row['entity_id']]['position'] = deepcopy(row['proposed'])
    return view


def apply(project, command):
    field='remove' if 'remove' in command else 'layout' if 'layout' in command else 'delta'
    if set(command) != {'type', 'entity_ids', field, 'review_key'} or command.get('type') != ('delete_actor_drafts' if field=='remove' else 'layout_actor_drafts' if field=='layout' else 'offset_actor_drafts'):
        raise ProjectError('NPC draft group command requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_ids', field)})
    if command['review_key'] != report['review_key']:
        raise ProjectError('Project changed since NPC draft group review; review again')
    if not report['changed_count']:
        return
    before = {row['entity_id']: deepcopy(row['draft']) for row in report['targets']}
    after = {row['entity_id']: None if field=='remove' else {**deepcopy(row['draft']), 'position': deepcopy(row['proposed'])}
             for row in report['targets']}
    if field=='remove':
        for identifier in before:del project.actor_drafts[identifier]
    else:
        project.actor_drafts.update(after)
    project.undo_stack.append(dict(target='actor_draft_batch', before=before, after=deepcopy(after),
                                   source_entity_ids=sorted({draft['donor_entity_id'] for draft in before.values()})))
    project.redo_stack.clear()
