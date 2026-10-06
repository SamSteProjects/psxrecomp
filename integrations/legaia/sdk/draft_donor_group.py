"""Reviewed retail donor changes for existing authored NPC identities."""
from copy import copy,deepcopy
from .project import ProjectError,digest
from .project_copy import source_key
from .scene_preview import source_key as preview_source_key

def review(project,request):
    if project.mode!='edit' or project.active_scene not in project.imports:
        raise ProjectError('NPC donor groups require an active imported scene in Edit mode')
    if not isinstance(request,dict) or set(request)!={'entity_ids','donor_entity_id'}:
        raise ProjectError('NPC donor review requires selected draft IDs and one retail donor')
    ids=request['entity_ids'];donor=request['donor_entity_id']
    if not isinstance(ids,list) or not 2<=len(ids)<=128 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
        raise ProjectError('Select 2 through 128 unique NPC drafts')
    actors={a['semantic_id']:a for a in project.imports[project.active_scene]['actors']}
    if not isinstance(donor,str) or donor not in actors:
        raise ProjectError('NPC donor must be an imported actor in the active scene')
    key=source_key(project);targets=[]
    for identifier in sorted(ids):
        current=project.actor_drafts.get(identifier)
        if not isinstance(current,dict) or current.get('scene_id')!=project.active_scene:
            raise ProjectError('NPC donor group contains an unavailable or other-scene draft')
        project._validate_actor_draft(identifier,current)
        proposed={**deepcopy(current),'donor_entity_id':donor};project._validate_actor_draft(identifier,proposed)
        targets.append(dict(entity_id=identifier,current=deepcopy(current),proposed=proposed))
    normalized=dict(entity_ids=sorted(ids),donor_entity_id=donor)
    scene_key=preview_source_key(project)
    if source_key(project)!=key:raise ProjectError('Project changed during NPC donor review')
    return dict(schema_version='legaia.draft-donor-group-review.v1',project_source_key=key,scene_preview_source_key=scene_key,scene_id=project.active_scene,request=normalized,donor=deepcopy(actors[donor]),targets=targets,changed_count=sum(t['current']!=t['proposed'] for t in targets),review_key=digest(dict(source=key,request=normalized,algorithm='retail-npc-donor-group.v1')),gameplay_verified=False)

def proposal_view(project,report):
    if review(project,report['request'])!=report:raise ProjectError('NPC donor group changed since review')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts)
    for row in report['targets']:view.actor_drafts[row['entity_id']]=deepcopy(row['proposed'])
    return view

def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','entity_ids','donor_entity_id','review_key'} or command['type']!='assign_actor_draft_donors':
        raise ProjectError('NPC donor assignment requires exact reviewed fields')
    report=review(project,{k:command[k] for k in ('entity_ids','donor_entity_id')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC donor group changed since review; review again')
    if not report['changed_count']:return
    before={r['entity_id']:deepcopy(r['current']) for r in report['targets']};after={r['entity_id']:deepcopy(r['proposed']) for r in report['targets']}
    project.actor_drafts.update(after);project.undo_stack.append(dict(target='actor_draft_batch',before=before,after=deepcopy(after),source_entity_ids=sorted({d['donor_entity_id'] for d in [*before.values(),*after.values()]})));project.redo_stack.clear()
