"""Review a prospective NPC in an isolated Project, without creating persistent content."""
from copy import copy, deepcopy
from uuid import UUID
from .project import ProjectError, digest
from .project_copy import source_key
from .scene_preview import source_key as scene_key


def review(project, request):
    fields={'donor_entity_id','name','position','project_source_key'}
    if not isinstance(request,dict) or set(request)!=fields:
        raise ProjectError('NPC creation preview requires exact donor, name, X/Z and Project source')
    if project.mode!='edit' or request['project_source_key']!=source_key(project):
        raise ProjectError('NPC creation preview source changed or is not in Edit mode')
    position=request['position']
    if not isinstance(position,dict) or set(position)!={'x','z'} or any(type(v) is not int or v<64 or v>16384 or v%64 for v in position.values()):
        raise ProjectError('NPC creation preview requires native X/Z on the 64-unit grid')
    identifier='authored-actor://'+str(UUID(digest(request)[:32]))
    if identifier in project.actor_drafts:raise ProjectError('Prospective NPC identity conflicts with saved content')
    draft=dict(scene_id=project.active_scene,donor_entity_id=request['donor_entity_id'],name=request['name'],position=deepcopy(position))
    project._validate_actor_draft(identifier,draft)
    if len(project.actor_drafts)>=128:raise ProjectError('Actor draft limit reached')
    command=dict(type='create_actor_draft',donor_entity_id=draft['donor_entity_id'],name=draft['name'],position=deepcopy(position))
    report=dict(schema_version='legaia.npc-creation-review.v1',scene_id=project.active_scene,project_source_key=source_key(project),scene_preview_source_key=scene_key(project),preview_entity_id=identifier,draft=draft,command=command,identity_scope='temporary_preview_only',project_changed=False,gameplay_verified=False)
    report['review_key']=digest(report)
    return report


def proposal_view(project, report):
    request={key:deepcopy(report['command'][key]) for key in ('donor_entity_id','name','position')};request['project_source_key']=report['project_source_key']
    if review(project,request)!=report:raise ProjectError('NPC creation review changed or was altered')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts);view.overrides=deepcopy(project.overrides)
    view.undo_stack=[];view.redo_stack=[]
    view.command(deepcopy(report['command']))
    created=set(view.actor_drafts)-set(project.actor_drafts)
    if len(created)!=1:raise ProjectError('NPC creation projection did not produce exactly one prospective draft')
    draft=view.actor_drafts.pop(created.pop())
    if draft!=report['draft']:raise ProjectError('NPC creation projection differs from its reviewed donor/name/position')
    view.actor_drafts[report['preview_entity_id']]=draft;view.undo_stack=[];view.redo_stack=[]
    if source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during NPC creation projection')
    return view


def qualify_instances(current, proposed, report):
    if current.get('schema')!='legaia.scene-preview.v1' or proposed.get('schema')!=current.get('schema') or current.get('coordinate_system')!='editor_field_y_up_source_units' or proposed.get('coordinate_system')!=current.get('coordinate_system') or current.get('source_key')!=report['scene_preview_source_key'] or current.get('representation','authored')!='authored' or proposed.get('representation','authored')!='authored':
        raise ProjectError('NPC creation projection requires the current authored source scene contract')
    if current['scene_id']!=report['scene_id'] or proposed['scene_id']!=report['scene_id'] or current['assets']!=proposed['assets'] or current['position_to_display']!=proposed['position_to_display']:
        raise ProjectError('NPC creation projection changed geometry, scene or display conversion')
    before={row['entity_id']:row for row in current['entities']};after={row['entity_id']:row for row in proposed['entities']};identifier=report['preview_entity_id']
    if len(before)!=len(current['entities']) or len(after)!=len(proposed['entities']) or set(after)!=set(before)|{identifier} or identifier in before or any(after[key]!=row for key,row in before.items()):
        raise ProjectError('NPC creation projection changed or duplicated existing scene owners')
    target=after[identifier];draft=report['draft']
    if target.get('source_actor_id')!=draft['donor_entity_id'] or target.get('kind')!='actor_draft' or target.get('name')!=draft['name'] or target.get('donor_entity_id')!=draft['donor_entity_id'] or target.get('position')!={**draft['position'],'y':None} or not target.get('renderable') or target.get('geometry_key') not in {asset['geometry_key'] for asset in current['assets']}:
        raise ProjectError('Prospective NPC has no supported reviewed Retail donor scene geometry')
    return dict(schema_version='legaia.npc-creation-scene.v1',review=deepcopy(report),proposed_instance=deepcopy(target),geometry_unchanged=True,existing_instances_unchanged=True,project_changed=False,gameplay_verified=False)
