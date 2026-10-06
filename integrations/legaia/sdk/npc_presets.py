"""Project-local frozen NPC donor/placement presets and reviewed instantiation."""
from copy import copy, deepcopy
import uuid
from .project import ProjectError, digest
from .project_copy import source_key
from .scene_preview import source_key as scene_key
SCOPE='npc-draft-preset-v1'

def validate(project, identifier, value):
    source,components=value.get('source'),value.get('components')
    if (value.get('scope')!=SCOPE or not isinstance(source,dict) or set(source)!={'disc_identity','scene_id','entity_id','capture_draft_id','import_sha256'} or
        not isinstance(components,dict) or set(components)!={'Transform','NpcDraft'} or
        not isinstance(components['Transform'],dict) or set(components['Transform'])!={'position'} or
        not isinstance(components['NpcDraft'],dict) or set(components['NpcDraft']) not in ({'name','donor_entity_id'},{'name','donor_entity_id','dialogue'})):
        raise ProjectError('NPC preset requires exact frozen donor/placement and source fields')
    if any(not isinstance(source[k],str) or not source[k] for k in source):
        raise ProjectError('NPC preset provenance fields must be nonempty strings')
    document=project.imports.get(source['scene_id'])
    if not document or source['disc_identity']!=document['source']['disc_identity'] or source['import_sha256']!=digest(document) or source['entity_id']!=components['NpcDraft']['donor_entity_id']:
        raise ProjectError('NPC preset differs from its owning import and retail donor')
    project._validate_actor_draft(source['capture_draft_id'],dict(scene_id=source['scene_id'],**components['NpcDraft'],position=components['Transform']['position']))

def capture(project,command):
    if set(command)!={'type','entity_id','name'} or command['type']!='create_npc_preset' or not isinstance(command['entity_id'],str) or command['entity_id'] not in project.actor_drafts or len(project.actor_templates)>=128:
        raise ProjectError('NPC capture requires an existing draft and space in the preset library')
    draft=deepcopy(project.actor_drafts[command['entity_id']]);project._validate_actor_draft(command['entity_id'],draft)
    key=source_key(project)
    if 'dialogue' in draft:project._dialogue_context(draft['donor_entity_id']).patch(draft['dialogue']['runs'])
    if draft['scene_id']!=project.active_scene or not isinstance(command['name'],str):raise ProjectError('NPC capture requires the active scene and a preset name')
    name=command['name'].strip()
    if any(row['name'].casefold()==name.casefold() for row in project.actor_templates.values()):raise ProjectError('A preset already uses that name')
    identifier='template://'+str(uuid.uuid4());document=project.imports[draft['scene_id']]
    value=dict(id=identifier,name=name,scope=SCOPE,source=dict(scene_id=draft['scene_id'],entity_id=draft['donor_entity_id'],capture_draft_id=command['entity_id'],disc_identity=document['source']['disc_identity'],import_sha256=digest(document)),
               components=dict(Transform=dict(position=draft['position']),NpcDraft=dict(name=draft['name'],donor_entity_id=draft['donor_entity_id'],**({'dialogue':deepcopy(draft['dialogue'])} if 'dialogue' in draft else {}))))
    project._validate_template(identifier,value)
    if source_key(project)!=key:raise ProjectError('Project changed during NPC preset capture')
    project.actor_templates[identifier]=value
    project.undo_stack.append(dict(target='actor_templates',template_id=identifier,entity_id=draft['donor_entity_id'],before=None,after=deepcopy(value)));project.redo_stack.clear()

def review(project,request):
    if project.mode!='edit' or not isinstance(request,dict) or set(request)!={'template_id','name','position','expected_source_key'}:
        raise ProjectError('NPC preset placement requires exact preset/name/position/source fields in Edit mode')
    if not isinstance(request['template_id'],str) or not isinstance(request['expected_source_key'],str):
        raise ProjectError('NPC preset and source identities must be strings')
    before=source_key(project)
    if request['expected_source_key']!=before:raise ProjectError('NPC preset project source changed; review again')
    template=project.actor_templates.get(request['template_id'])
    if not isinstance(template,dict) or template.get('scope')!=SCOPE:raise ProjectError('NPC preset is unavailable')
    project._validate_template(template['id'],template)
    if template['source']['scene_id']!=project.active_scene or len(project.actor_drafts)>=128:raise ProjectError('NPC preset requires its owning scene and space for a new draft')
    identifier='authored-actor://'+str(uuid.uuid5(uuid.NAMESPACE_URL,'npc-preset:'+digest(request)))
    if identifier in project.actor_drafts:raise ProjectError('Proposed NPC identity already exists')
    candidate=dict(scene_id=project.active_scene,donor_entity_id=template['components']['NpcDraft']['donor_entity_id'],name=request['name'],position=deepcopy(request['position']))
    if 'dialogue' in template['components']['NpcDraft']:
        candidate['dialogue']=deepcopy(template['components']['NpcDraft']['dialogue'])
        project._dialogue_context(candidate['donor_entity_id']).patch(candidate['dialogue']['runs'])
    project._validate_actor_draft(identifier,candidate)
    result=dict(schema_version='legaia.npc-preset-review.v1',project_source_key=before,scene_preview_source_key=scene_key(project),scene_id=project.active_scene,request=deepcopy(request),template=deepcopy(template),entity_id=identifier,draft=candidate,review_key=digest(dict(source=before,request=request,algorithm='npc-preset-instance.v1')),gameplay_verified=False,
                limitations=['Creates a new authored NPC from the captured retail donor and chosen native-grid placement.','Presets freeze donor, name, X/Z defaults and supported NPC-owned dialogue edits; they do not inherit authored donor appearance, other actor script edits or runtime state. Shared model/animation asset edits remain project-wide.','Review Build assesses the complete candidate; runtime spawning, script scheduling, collision and gameplay remain unverified.'])
    if source_key(project)!=before:raise ProjectError('Project changed during NPC preset review')
    return result

def proposal_view(project,report):
    if review(project,report['request'])!=report:raise ProjectError('NPC preset changed since review')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts);view.actor_drafts[report['entity_id']]=deepcopy(report['draft']);return view

def apply(project,command):
    if set(command)!={'type','template_id','name','position','expected_source_key','review_key'} or command['type']!='instantiate_npc_preset':raise ProjectError('NPC preset Apply requires exact reviewed fields')
    report=review(project,{k:command[k] for k in ('template_id','name','position','expected_source_key')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC preset review changed; review again')
    project.actor_drafts[report['entity_id']]=deepcopy(report['draft'])
    project.undo_stack.append(dict(target='actor_drafts',entity_id=report['entity_id'],before=None,after=deepcopy(report['draft'])));project.redo_stack.clear()
