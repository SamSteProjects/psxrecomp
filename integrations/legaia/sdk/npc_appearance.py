"""Qualified initial appearance edits for allocated NPC clones.

Reviewed project commands retain the retail script donor separately from the
initial model/animation witness. Native serialization rewrites no script bytes.
"""
from hashlib import sha256
from importer.core import parse_man
from importer.man_layout import read_man_layout
from .project import ProjectError, digest
from .project_copy import source_key
from copy import copy, deepcopy

def appearance_donor(draft):
    return draft.get('appearance',{}).get('donor_entity_id',draft['donor_entity_id'])

def validate(project,draft):
    if 'appearance' not in draft:return
    value=draft['appearance']
    if not isinstance(value,dict) or set(value)!={'script_donor_entity_id','donor_entity_id'} or value['script_donor_entity_id']!=draft['donor_entity_id']:
        raise ProjectError('NPC appearance belongs to its script donor; clear appearance before changing script donor')
    if not any(a['semantic_id']==value['donor_entity_id'] for a in project.imports[draft['scene_id']]['actors']):
        raise ProjectError('NPC appearance witness must belong to the imported scene')

def source(project,identifier):
    draft=project.actor_drafts.get(identifier) if isinstance(identifier,str) else None
    if project.mode!='edit' or not isinstance(draft,dict) or draft['scene_id']!=project.active_scene:
        raise ProjectError('NPC appearance requires an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier,draft);key=source_key(project)
    options=project.appearance_options(draft['donor_entity_id'])
    if 'appearance' in draft and not any(o['donor_entity_id']==appearance_donor(draft) for o in options['options']):
        raise ProjectError('Current NPC appearance witness is not source-qualified')
    if source_key(project)!=key:raise ProjectError('Project changed during NPC appearance inspection')
    return dict(schema_version='legaia.npc-appearance-source.v1',entity_id=identifier,scene_id=draft['scene_id'],project_source_key=key,draft=deepcopy(draft),options=options,gameplay_verified=False,runtime_binding='not_asserted')

def review(project,request):
    if not isinstance(request,dict) or set(request)!={'entity_id','donor_entity_id'}:raise ProjectError('NPC appearance review requires identity and witness only')
    report=source(project,request['entity_id']);draft=report['draft'];donor=request['donor_entity_id'];proposed=deepcopy(draft)
    if donor is None:proposed.pop('appearance',None)
    else:
        if not isinstance(donor,str) or not any(o['donor_entity_id']==donor for o in report['options']['options']):raise ProjectError('NPC appearance witness is not a qualified initial pair')
        proposed['appearance']=dict(script_donor_entity_id=draft['donor_entity_id'],donor_entity_id=donor)
    project._validate_actor_draft(request['entity_id'],proposed)
    return dict(schema_version='legaia.npc-appearance-review.v1',entity_id=request['entity_id'],project_source_key=report['project_source_key'],request=deepcopy(request),current=draft,proposed=proposed,review_key=digest(dict(source=report['project_source_key'],request=request,algorithm='npc-initial-appearance.v1')),gameplay_verified=False,runtime_binding='not_asserted')

def apply(project,command):
    if set(command)!={'type','entity_id','donor_entity_id','review_key'}:raise ProjectError('NPC appearance Apply requires exact reviewed fields')
    report=review(project,{k:command[k] for k in ('entity_id','donor_entity_id')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC appearance changed; review again')
    if report['current']==report['proposed']:return
    project.actor_drafts[command['entity_id']]=deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts',entity_id=command['entity_id'],before=report['current'],after=deepcopy(report['proposed'])))
    project.redo_stack.clear()

def proposal_view(project,report):
    """Detached preview inputs; never publish the reviewed binding or history."""
    if review(project,report['request'])!=report:
        raise ProjectError('NPC appearance changed since scene review')
    view=copy(project);view.actor_drafts=deepcopy(project.actor_drafts)
    view.actor_drafts[report['entity_id']]=deepcopy(report['proposed'])
    return view

def patch_project(project,scene_id,context,candidate,allocations):
    actors={a['semantic_id']:a for a in project.imports[scene_id]['actors']}
    requests=[]
    for row in allocations['drafts']:
        draft=project.actor_drafts[row['draft_id']]
        if 'appearance' not in draft:continue
        validate(project,draft)
        requests.append(dict(draft_id=row['draft_id'],appearance_donor_record_index=actors[appearance_donor(draft)]['source_record']['record_index']))
    return patch_allocated_appearance(context,candidate,allocations,requests) if requests else (candidate,None)

def patch_allocated_appearance(context, candidate, allocations, requests):
    """Apply source-qualified donor pairs to exact appended record identities.

    ``context`` is a verified ManAssignmentContext, ``allocations`` is the
    append-actor audit, and requests contain stable draft IDs plus retail donor
    record indices. Clients never supply native model/animation numbers or bytes.
    """
    if not isinstance(candidate,bytes) or not 0<len(candidate)<=4*1024*1024:
        raise ProjectError('NPC appearance requires a bounded immutable MAN candidate')
    if not isinstance(allocations,dict) or not isinstance(allocations.get('drafts'),list):
        raise ProjectError('NPC appearance requires an actor allocation audit')
    if not isinstance(requests,list) or not 1<=len(requests)<=128:
        raise ProjectError('NPC appearance requires 1 through 128 donor requests')
    original,_=context.patch({});source={a.record_index:a for a in parse_man(original).actors}
    layout=read_man_layout(candidate);actors={a.record_index:a for a in parse_man(candidate).actors}
    rows={}
    for row in allocations['drafts']:
        if not isinstance(row,dict) or not isinstance(row.get('draft_id'),str) or row['draft_id'] in rows:
            raise ProjectError('NPC appearance allocation identities are ambiguous')
        rows[row['draft_id']]=row
    output=bytearray(candidate);audit=[];seen=set();indices=set()
    for request in requests:
        if not isinstance(request,dict) or set(request)!={'draft_id','appearance_donor_record_index'}:
            raise ProjectError('NPC appearance accepts only draft identity and a retail donor index')
        identifier=request['draft_id'];donor_index=request['appearance_donor_record_index']
        if not isinstance(identifier,str) or identifier in seen or identifier not in rows or type(donor_index) is not int or donor_index not in source:
            raise ProjectError('NPC appearance draft or donor is unavailable or duplicated')
        seen.add(identifier);allocation=rows[identifier];index=allocation.get('record_index');script_index=allocation.get('donor',{}).get('record_index')
        if type(index) is not int or index in source or index in indices or index not in actors or type(script_index) is not int or script_index not in source:
            raise ProjectError('NPC appearance must target a unique appended actor, never a retail record')
        indices.add(index);actor=actors[index];script=source[script_index];donor=source[donor_index]
        if actor.byte_length!=script.byte_length or actor.local_count!=script.local_count or actor.byte_length!=allocation.get('byte_length'):
            raise ProjectError('NPC appearance allocation extent differs from its script donor')
        if sum(row['byte_offset']==actor.byte_offset for row in layout['records'])!=1:
            raise ProjectError('NPC appearance cannot write an aliased appended record')
        pair=dict(model_index=donor.model_index,animation_id=donor.animation_id)
        options=context.options(script_index)
        if not any(row['model_index']==donor.model_index and row['animation_id']==donor.animation_id and donor_index in row['donor_records'] for row in options['pairs']):
            raise ProjectError('NPC appearance donor pair is not source-qualified for this script donor')
        # Reuse native model/channel and alias guards, including exact preimages.
        _,changes=context.patch({script_index:pair})
        offset=actor.byte_offset+1+actor.local_count*2
        if (actor.model_index,actor.animation_id)!=(script.model_index,script.animation_id):
            raise ProjectError('NPC appearance header preimage differs from its retail script donor')
        for change in changes:
            relative=change['decoded_byte_offset']-script.byte_offset
            target=actor.byte_offset+relative
            if target not in (offset,offset+1) or output[target]!=change['before_byte']:
                raise ProjectError('NPC appearance header ownership or preimage differs')
            output[target]=change['after_byte']
            audit.append(dict(change,draft_id=identifier,record_index=index,
                script_donor_record_index=script_index,appearance_donor_record_index=donor_index,
                source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=target))
    result=bytes(output)
    if read_man_layout(result)!=layout:
        raise ProjectError('NPC appearance changed MAN structure')
    reparsed={a.record_index:a for a in parse_man(result).actors}
    for request in requests:
        actor=reparsed[rows[request['draft_id']]['record_index']];donor=source[request['appearance_donor_record_index']]
        if (actor.model_index,actor.animation_id)!=(donor.model_index,donor.animation_id):
            raise ProjectError('NPC appearance native pair did not round-trip')
    return result,dict(schema_version='legaia.npc-appearance-native.v1',
        source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),
        result_man_sha256=sha256(result).hexdigest(),changes=audit,
        scope='appended_initial_model_animation_header_only',gameplay_verified=False,
        script_compatibility='not_asserted',runtime_binding='not_asserted')
