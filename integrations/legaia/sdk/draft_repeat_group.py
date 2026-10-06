"""Independent copies of an NPC arrangement; no parenting or runtime spawning."""
from copy import copy,deepcopy
import uuid
from .project import ProjectError,digest
from .project_copy import source_key

def preview(project,request):
    fields={'entity_ids','count','step'}
    if not isinstance(request,dict) or set(request) not in (fields,fields|{'columns'}):
        raise ProjectError('NPC arrangement copies require membership, group count and X/Z spacing')
    ids=request['entity_ids']
    if project.mode!='edit' or not isinstance(ids,list) or not 2<=len(ids)<=128 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
        raise ProjectError('Select 2 through128 unique NPC drafts in Edit mode')
    count=request['count']
    if type(count) is not int or count<1 or len(project.actor_drafts)+count*len(ids)>128:
        raise ProjectError('Arrangement copies must fit the project limit of128 NPC drafts')
    key=source_key(project);normalized={**deepcopy(request),'entity_ids':sorted(ids)}
    review_key=digest(dict(source=key,request=normalized,algorithm='npc-arrangement-repeat.v1'))
    sources={};copies=[]
    from .draft_repeat import preview as single_preview
    for identifier in sorted(ids):
        original=project.actor_drafts.get(identifier)
        if not isinstance(original,dict):raise ProjectError('NPC arrangement contains an unavailable draft')
        project._validate_actor_draft(identifier,original)
        report=single_preview(project,dict(entity_id=identifier,count=count,step=request['step'],name=original['name'][:110]+' copy',**({'columns':request['columns']} if 'columns' in request else {})))
        sources[identifier]=deepcopy(original)
        for row in report['copies']:
            new_id='authored-actor://'+str(uuid.uuid5(uuid.NAMESPACE_URL,review_key+'/'+identifier+'/'+str(row['copy_index'])))
            if new_id in project.actor_drafts:raise ProjectError('NPC arrangement copy identity already exists')
            project._validate_actor_draft(new_id,row['draft'])
            copies.append(dict(entity_id=new_id,source_entity_id=identifier,copy_index=row['copy_index'],draft=deepcopy(row['draft'])))
    if source_key(project)!=key:raise ProjectError('Project changed during NPC arrangement review')
    return dict(schema_version='legaia.draft-repeat-group.v1',scene_id=project.active_scene,project_source_key=key,source_drafts=sources,request=normalized,review_key=review_key,copies=copies,limitations=['Independent copies retain each source NPC retail donor and relative X/Z arrangement.',*report['limitations'][1:]])

def proposal_view(project,report):
    if preview(project,report['request'])!=report:raise ProjectError('NPC arrangement changed since review')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts)
    for row in report['copies']:view.actor_drafts[row['entity_id']]=deepcopy(row['draft'])
    return view

def apply(project,body):
    fields={'type','entity_ids','count','step','review_key'}
    if not isinstance(body,dict) or body.get('type')!='repeat_actor_drafts' or set(body) not in (fields,fields|{'columns'}):
        raise ProjectError('NPC arrangement copies accept exact reviewed fields only')
    report=preview(project,{k:v for k,v in body.items() if k not in ('type','review_key')})
    if body['review_key']!=report['review_key']:raise ProjectError('NPC arrangement changed; review again')
    after={r['entity_id']:deepcopy(r['draft']) for r in report['copies']}
    project.actor_drafts.update(after)
    project.undo_stack.append(dict(target='actor_draft_batch',before={i:None for i in after},after=deepcopy(after),source_entity_ids=sorted({d['donor_entity_id'] for d in report['source_drafts'].values()})))
    project.redo_stack.clear()
