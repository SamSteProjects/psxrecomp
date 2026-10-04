"""Reviewed content replacement on a retained clip, with atomic reference updates."""
from copy import copy,deepcopy
from hashlib import sha256
from importer.animation import animation_record_ranges
from importer.animation_allocation import allocate_animation_record
from importer.animation_authoring import patch_animation_channels
from .animation_record_ledger import validate,verified_source,compose
from .animation_allocation import pose_saved_record
from .allocated_animation_assignment import validate_binding
from .scene_preview import source_key
from .project import ProjectError,digest


def options(project,scene_id,record_id,expected_source_key):
    key=source_key(project)
    if project.mode!='edit' or scene_id!=project.active_scene or not key or key!=expected_source_key:
        raise ProjectError('Retained editor requires the current editable scene source')
    ledger=validate(project,scene_id,project.overrides.get(scene_id,{}).get('AnimationRecords'),verify_disc=True)
    entry=next((row for row in ledger['records'] if row['record_id']==record_id),None)
    if entry is None:raise ProjectError('Retained editor requires an existing clip identity')
    other=sum(len(row['source_frame_indices'])*row['object_count'] for row in ledger['records'] if row['record_id']!=record_id)
    if source_key(project)!=key:raise ProjectError('Source changed while loading retained editor')
    return dict(schema_version='legaia.animation-record-edit-options.v1',scene_id=scene_id,record_id=record_id,
        project_source_key=key,entry=entry,active=record_id not in ledger['removed_record_ids'],revision=ledger['revision'],
        maximum_frame_count=min(512,(4096-other)//entry['object_count']),edit_available=ledger['revision']<64,
        referencing_actors=sorted(actor for actor,value in project.overrides.items()
            if value.get('ActorAllocatedAnimation',{}).get('scene_id')==scene_id and
            value.get('ActorAllocatedAnimation',{}).get('record_id')==record_id),gameplay_verified=False)


def prepare(project,scene_id,record_id,source_frame_indices,edits,expected_source_key):
    key=source_key(project)
    if project.mode!='edit' or scene_id!=project.active_scene or not key or key!=expected_source_key:
        raise ProjectError('Retained clip edit requires the current active editable scene source')
    ledger=validate(project,scene_id,project.overrides.get(scene_id,{}).get('AnimationRecords'),verify_disc=True)
    entry=next((row for row in ledger['records'] if row['record_id']==record_id),None)
    if entry is None:raise ProjectError('Retained clip edit requires an existing record identity')
    before=deepcopy(entry)
    source,_=verified_source(project,scene_id)
    index=int(entry['donor_animation_id'].rsplit('/',1)[1]);start,end=animation_record_ranges(source)[index]
    captured,_=patch_animation_channels(source[start:end],entry['donor_record_sha256'],entry['donor_edits'])
    record,native=allocate_animation_record(captured,entry['effective_donor_record_sha256'],source_frame_indices,edits)
    entry.update(source_frame_indices=deepcopy(source_frame_indices),edits=deepcopy(edits),record_sha256=sha256(record).hexdigest())
    changed=before!=entry
    if changed:ledger['revision']+=1
    validate(project,scene_id,ledger)
    view=copy(project);view.overrides=deepcopy(project.overrides)
    view.overrides.setdefault(scene_id,{})['AnimationRecords']=ledger
    updates={}
    for actor,components in sorted(project.overrides.items()):
        binding=components.get('ActorAllocatedAnimation')
        if binding and binding['scene_id']==scene_id and binding['record_id']==record_id:
            validate_binding(project,actor,binding,verify_disc=True)
            after=dict(binding,record_sha256=entry['record_sha256'])
            view.overrides[actor]['ActorAllocatedAnimation']=after
            updates[actor]=dict(before=deepcopy(binding),after=deepcopy(after))
    bank,allocation=compose(view,scene_id)
    for actor in updates:validate_binding(view,actor,view.overrides[actor]['ActorAllocatedAnimation'],verify_disc=True)
    if source_key(project)!=key:raise ProjectError('Project changed during retained clip edit Review')
    report=dict(schema_version='legaia.animation-record-edit-review.v1',scene_id=scene_id,record_id=record_id,
        project_source_key=key,before=before,after=deepcopy(entry),proposed_ledger=ledger,assignment_updates=updates,
        candidate_record_sha256=entry['record_sha256'],candidate_bank_sha256=sha256(bank).hexdigest(),
        allocation=allocation,native_edit=native,project_change=changed,project_changed=False,gameplay_verified=False,
        limitations=['Frame mappings refer to the frozen captured donor, not later shared channel edits.',
            'Axes replace this retained record contribution; untouched axes inherit the captured donor frame.',
            'Every referencing initial assignment receives the new record hash in the same Undo entry.',
            'Retired clips remain retired; timing, scripts and gameplay remain unverified.'])
    report['review_key']=digest(report)
    return view,report


def apply(project,command):
    fields={'type','scene_id','record_id','source_frame_indices','edits','expected_source_key','review_key'}
    if set(command)!=fields:raise ProjectError('Retained edit Apply requires the exact reviewed frame/axis request')
    view,report=prepare(project,command['scene_id'],command['record_id'],command['source_frame_indices'],command['edits'],command['expected_source_key'])
    if command['review_key']!=report['review_key']:raise ProjectError('Retained clip edit changed after Review; review again')
    if not report['project_change']:return report
    owners=[command['scene_id'],*report['assignment_updates']]
    before={actor:deepcopy(project.overrides.get(actor)) for actor in owners}
    after={actor:deepcopy(view.overrides.get(actor)) for actor in owners}
    for actor,value in after.items():project.overrides[actor]=value
    project.undo_stack.append(dict(target='entity_overrides',before=before,after=after))
    project.redo_stack.clear()
    return report


def pose(project,request):
    view,report=prepare(project,request['scene_id'],request['record_id'],request['source_frame_indices'],request['edits'],request['expected_source_key'])
    if report['review_key']!=request['review_key']:raise ProjectError('Retained edit pose differs from Review')
    animation,asset=pose_saved_record(view,request['scene_id'],request['record_id'],source_key(view))
    animation.update(representation='allocated_record_edit_preview',clip_id='allocated-record-edit-preview',
        label='Proposed retained clip content',edit_proposal=report)
    return animation,asset,report
