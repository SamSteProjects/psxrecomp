"""Detached X/Z position review and source-qualified scene instance comparison."""
from copy import copy, deepcopy
from .project import ProjectError, digest
from .project_copy import source_key
from .scene_preview import source_key as scene_key


def review(project, request):
    if not isinstance(request,dict) or set(request)!={'entity_id','position','project_source_key'}:
        raise ProjectError('Position review requires exact identity, X/Z and Project source key')
    if project.mode!='edit' or request['project_source_key']!=source_key(project):
        raise ProjectError('Position review Project source changed or is not in Edit mode')
    identifier=request['entity_id'];position=request['position']
    if not isinstance(identifier,str) or not isinstance(position,dict) or set(position)!={'x','z'} or any(type(v) is not int or v<64 or v>16384 or v%64 for v in position.values()):
        raise ProjectError('Position review requires native X/Z on the 64-unit grid')
    draft=project.actor_drafts.get(identifier)
    if draft:
        project._validate_actor_draft(identifier,draft)
        if draft['scene_id']!=project.active_scene:raise ProjectError('Position target is outside the active scene')
        kind='npc';before={**draft['position'],'y':None}
    else:
        entity=next((e for e in (project.state().get('scene') or {}).get('entities',[]) if e['id']==identifier),None)
        if entity is None:raise ProjectError('Position target requires an active imported actor or NPC')
        kind='actor';before=deepcopy(entity['components']['Transform']['effective']['position'])
    command=dict(type='set_actor_draft_position' if kind=='npc' else 'set_transform',entity_id=identifier,position=deepcopy(position))
    report=dict(schema_version='legaia.actor-position-review.v1',entity_id=identifier,kind=kind,scene_id=project.active_scene,project_source_key=source_key(project),scene_preview_source_key=scene_key(project),current_position=before,proposed_position={**before,**position},command=command,project_changed=False,gameplay_verified=False,height_authoring='preserved_existing_or_unknown')
    report['review_key']=digest(report)
    return report


def proposal_view(project, report):
    request=dict(entity_id=report['entity_id'],position=report['command']['position'],project_source_key=report['project_source_key'])
    if review(project,request)!=report:raise ProjectError('Position review changed or was altered')
    view=copy(project)
    view.overrides=deepcopy(project.overrides);view.actor_drafts=deepcopy(project.actor_drafts)
    view.undo_stack=[];view.redo_stack=[]
    view.command(deepcopy(report['command']))
    if source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during position projection')
    return view


def qualify_instances(current, proposed, report):
    if current.get('schema')!='legaia.scene-preview.v1' or proposed.get('schema')!='legaia.scene-preview.v1' or current.get('coordinate_system')!='editor_field_y_up_source_units' or proposed.get('coordinate_system')!=current.get('coordinate_system') or current.get('source_key')!=report['scene_preview_source_key']:
        raise ProjectError('Position projection has an unsupported or stale source scene contract')
    if current['scene_id']!=report['scene_id'] or proposed['scene_id']!=report['scene_id'] or current['assets']!=proposed['assets'] or current['position_to_display']!=proposed['position_to_display']:
        raise ProjectError('Position projection changed geometry, source scene or display conversion')
    before={row['entity_id']:row for row in current['entities']};after={row['entity_id']:row for row in proposed['entities']}
    if len(before)!=len(current['entities']) or len(after)!=len(proposed['entities']) or set(before)!=set(after) or report['entity_id'] not in before:
        raise ProjectError('Position projection changed or duplicated scene owners')
    allowed={'position','preview_position','preview_ground_sample','display_position','preview_height_status','model_to_scene','authored_position'}
    for identifier,row in before.items():
        target=after[identifier]
        if identifier!=report['entity_id']:
            if row!=target:raise ProjectError('Position projection changed an unrelated instance')
        else:
            def retained(item):
                result={k:v for k,v in item.items() if k not in allowed}
                result['evidence']={k:v for k,v in item.get('evidence',{}).items() if k!='height'}
                return result
            if retained(row)!=retained(target) or [v for i,v in enumerate(row['model_to_scene']) if i not in (3,7,11)]!=[v for i,v in enumerate(target['model_to_scene']) if i not in (3,7,11)]:
                raise ProjectError('Position projection changed target model, orientation, animation or source ownership')
    target=after[report['entity_id']]
    if target['position']!=report['proposed_position']:raise ProjectError('Projected position differs from reviewed X/Z or preserved height')
    return dict(schema_version='legaia.actor-position-scene.v1',review=deepcopy(report),current_instance=deepcopy(before[report['entity_id']]),proposed_instance=deepcopy(target),geometry_unchanged=True,unrelated_instances_unchanged=True,project_changed=False,gameplay_verified=False)
