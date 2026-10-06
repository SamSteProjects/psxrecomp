"""Reviewed source-grid repetition of project NPC drafts; no runtime spawning."""
from copy import copy,deepcopy
import uuid
from .project import ProjectError,digest
from importer.core import ImportError as RetailImportError
from .npc_build import NORMAL_BUILD_SCOPE_NOTE

def preview(project, request):
    if not isinstance(request,dict) or set(request)!={'entity_id','count','step','name'}:
        raise ProjectError('Draft repetition requires original draft, count, X/Z step and name prefix only')
    identifier=request['entity_id'];count=request['count'];step=request['step'];name=request['name']
    if not isinstance(identifier,str) or identifier not in project.actor_drafts:
        raise ProjectError('Choose an existing NPC draft')
    original=project.actor_drafts[identifier];project._validate_actor_draft(identifier,original)
    if original['scene_id']!=project.active_scene:
        raise ProjectError('Open the original draft scene before repeating it')
    if type(count) is not int or not 1<=count<=128 or len(project.actor_drafts)+count>128:
        raise ProjectError('Copy count must fit the project limit of128 NPC drafts')
    if not isinstance(step,dict) or set(step)!={'x','z'} or any(type(v) is not int or v%64 or abs(v)>16320 for v in step.values()):
        raise ProjectError('Copy steps require X/Z integer multiples of64 within placement bounds')
    if not isinstance(name,str) or not name.strip() or len(name.strip())>116:
        raise ProjectError('Copy name prefix must contain1 through116 characters')
    normalized={**request,'name':name.strip()}
    review=digest({'project_root':str(project.root),'scene':project.active_scene,
                   'source':digest(project.imports[project.active_scene]),'drafts':project.actor_drafts,
                   'request':normalized,'algorithm':'draft-repeat.v1'})
    copies=[]
    for index in range(1,count+1):
        new_id='authored-actor://'+str(uuid.uuid5(uuid.NAMESPACE_URL,review+'/'+str(index)))
        if new_id in project.actor_drafts:raise ProjectError('Repeated draft identity already exists')
        value={**deepcopy(original),'name':f"{name.strip()} {index:03d}",
               'position':{axis:original['position'][axis]+index*step[axis] for axis in ('x','z')}}
        try:
            project._validate_actor_draft(new_id,value)
        except RetailImportError as exc:
            raise ProjectError(f'Copy {index}: {exc}') from exc
        copies.append({'entity_id':new_id,'copy_index':index,'draft':value})
    return {'schema_version':'legaia.draft-repeat.v1','scene_id':project.active_scene,
            'source_entity_id':identifier,'source_draft':deepcopy(original),'request':normalized,
            'review_key':review,'copies':copies,
            'limitations':['Project-local drafts inherit only the original retail donor binding.',
                           'Script scheduling, collision, visibility and runtime spawning remain unverified.',
                           NORMAL_BUILD_SCOPE_NOTE,
                           'Actor-pool checks reject unavoidable initial-placement overflow; scenery, other allocations and safe total headroom remain unverified. Experimental export retains separate gates.']}

def proposal_view(project, report):
    if preview(project,report['request'])!=report:
        raise ProjectError('NPC draft repetition changed since review')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts)
    for row in report['copies']:view.actor_drafts[row['entity_id']]=deepcopy(row['draft'])
    return view

def apply(project, body):
    if set(body)!={'type','entity_id','count','step','name','review_key'}:
        raise ProjectError('Repeat draft accepts reviewed repetition fields only')
    report=preview(project,{key:body[key] for key in ('entity_id','count','step','name')})
    if body['review_key']!=report['review_key']:
        raise ProjectError('NPC drafts changed since preview; review the copies again')
    after={row['entity_id']:deepcopy(row['draft']) for row in report['copies']}
    project.actor_drafts.update(after)
    project.undo_stack.append({'target':'actor_draft_batch','before':{key:None for key in after},'after':deepcopy(after),
                               'source_entity_ids':[report['source_draft']['donor_entity_id']]})
    project.redo_stack.clear()
