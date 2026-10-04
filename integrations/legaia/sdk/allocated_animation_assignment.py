"""Reviewed persistent initial clip identities; Build MAN composition is separate."""
from copy import deepcopy
from hashlib import sha256

from importer.man_assignments import load_man_assignment_context
from importer.pipeline import _disc_context
from .animation_record_ledger import validate as validate_ledger,compose
from .animation_allocation import pose_saved_record
from .project import ProjectError,digest
from .scene_preview import source_key


def validate_binding(project,entity_id,value,*,verify_disc=False):
    fields={'scene_id','record_id','record_sha256','model_asset_id'}
    if not isinstance(value,dict) or set(value)!=fields or not isinstance(value['scene_id'],str):
        raise ProjectError('ActorAllocatedAnimation requires exact scene, retained record/hash and model identity')
    scene=value['scene_id'];document=project.imports.get(scene)
    actor=next((a for a in (document or {}).get('actors',[]) if a['semantic_id']==entity_id),None)
    if actor is None or 'ActorAnimation' in project.overrides.get(entity_id,{}):
        raise ProjectError('Allocated initial clip requires an imported actor without a competing initial clip assignment')
    ledger=project.overrides.get(scene,{}).get('AnimationRecords')
    validate_ledger(project,scene,ledger)
    entry=next((row for row in ledger['records'] if row['record_id']==value['record_id']),None)
    if (entry is None or value['record_id'] in ledger['removed_record_ids'] or
            value['record_sha256']!=entry['record_sha256'] or value['model_asset_id']!=entry['donor_asset_id']):
        raise ProjectError('Allocated initial clip must reference an active retained capture with its exact hash/model')
    model=project.appearance_source_actor(entity_id,verify_disc=False)
    if model['model_reference'].get('asset_semantic_id')!=entry['donor_asset_id']:
        raise ProjectError('Allocated initial clip conflicts with the actor inherited appearance model')
    if verify_disc:
        from copy import copy
        view=copy(project);view.active_scene=scene
        checked=review(view,entity_id,value['record_id'],source_key(view))
        if checked['proposed_component']!=value:
            raise ProjectError('Allocated initial clip differs from current verified source')
    return deepcopy(entry)


def review(project,entity_id,record_id,expected_source_key):
    scene=project.active_scene;document=project.imports.get(scene);key=source_key(project)
    actor=next((a for a in (document or {}).get('actors',[]) if a['semantic_id']==entity_id),None)
    if project.mode!='edit' or actor is None or not key or key!=expected_source_key:
        raise ProjectError('Allocated initial clip review requires the current imported actor and editable scene source')
    before=deepcopy(project.overrides.get(entity_id,{}).get('ActorAllocatedAnimation'))
    if record_id is None:
        if before is None:
            raise ProjectError('Actor has no allocated initial clip to clear')
        with _disc_context(project.disc_path):
            model=project.appearance_source_actor(entity_id,verify_disc=True)
            context=load_man_assignment_context(project.disc_path,document['scene']['name'])
            candidate,changes=context.patch({actor['source_record']['record_index']:dict(
                model_index=model['model_reference']['model_index'],animation_id=model['placement_fields']['animation_id'])})
        result=dict(schema_version='legaia.allocated-animation-assignment-review.v1',scene_id=scene,entity_id=entity_id,
            record_id=None,project_source_key=key,before=before,proposed_component=None,animation_id=None,
            native_animation_id=model['placement_fields']['animation_id'],candidate_man_sha256=sha256(candidate).hexdigest(),
            changes=changes,project_change=True,project_changed=False,gameplay_verified=False,
            capabilities=dict(review=True,pose_preview=False,apply=True,build_assignment=False),
            limitations=['Clear restores the inherited appearance initial clip; scripts and gameplay remain unverified.'])
        if source_key(project)!=key:
            raise ProjectError('Project changed during allocated initial clip clear review')
        result['review_key']=digest(result)
        return result
    ledger=project.overrides.get(scene,{}).get('AnimationRecords')
    validate_ledger(project,scene,ledger,verify_disc=True)
    entry=next((row for row in ledger['records'] if row['record_id']==record_id),None)
    if entry is None or record_id in ledger['removed_record_ids']:
        raise ProjectError('Allocated initial clip must name an active retained record')
    with _disc_context(project.disc_path):
        model=project.appearance_source_actor(entity_id,verify_disc=True)
        if model['model_reference'].get('asset_semantic_id')!=entry['donor_asset_id']:
            raise ProjectError('Allocated initial clip requires its exact captured model source; retargeting is unsupported')
        bank,allocation=compose(project,scene)
        row=next(item for item in allocation['allocated_records'] if item['record_id']==record_id)
        context=load_man_assignment_context(project.disc_path,document['scene']['name'])
        donor=next(a for a in document['actors'] if a['semantic_id']==entry['channel_owner_entity_id'])
        candidate,changes=context.patch_allocated(bank,sha256(bank).hexdigest(),{
            actor['source_record']['record_index']:dict(donor_record_index=donor['source_record']['record_index'],
                allocated_record_index=row['record_index'],record_sha256=entry['record_sha256'])})
    if source_key(project)!=key:
        raise ProjectError('Project changed while reviewing allocated initial animation')
    report=dict(schema_version='legaia.allocated-animation-assignment-review.v1',scene_id=scene,
        entity_id=entity_id,record_id=record_id,project_source_key=key,
        animation_id=f"animation://{document['scene']['name']}/authored-record/{record_id}",
        proposed_component=dict(scene_id=scene,record_id=record_id,record_sha256=entry['record_sha256'],model_asset_id=entry['donor_asset_id']),
        model_source_entity_id=model['semantic_id'],channel_owner_entity_id=entry['channel_owner_entity_id'],
        native_animation_id=row['record_index']+1,native_record_index=row['record_index'],
        effective_bank_sha256=sha256(bank).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),
        man_source=context.provenance(),changes=changes,frame_count=len(entry['source_frame_indices']),
        object_count=entry['object_count'],project_changed=False,gameplay_verified=False,
        before=before,project_change=before!=dict(scene_id=scene,record_id=record_id,record_sha256=entry['record_sha256'],model_asset_id=entry['donor_asset_id'])
            or 'ActorAnimation' in project.overrides.get(entity_id,{}),
        displaced_initial_assignment=deepcopy(project.overrides.get(entity_id,{}).get('ActorAnimation')),
        capabilities=dict(review=True,pose_preview=True,apply=True,build_assignment=False),
        limitations=['Initial MAN header only; scripts can later select another model or clip.',
            'The stable record identity is portable; its current MAN byte selector must be re-resolved after ledger changes.',
            'Persistent actor identities are supported; normal Build MAN assignment composition is not implemented yet.',
            'Cadence, looping, script compatibility and gameplay suitability remain unverified.'])
    report['review_key']=digest(report)
    return report


def apply(project,command):
    if not isinstance(command,dict) or set(command)!={'type','entity_id','record_id','expected_source_key','review_key'}:
        raise ProjectError('Allocated initial clip Apply requires the exact reviewed actor/record/source request')
    report=review(project,command['entity_id'],command['record_id'],command['expected_source_key'])
    if report['review_key']!=command['review_key']:
        raise ProjectError('Allocated initial clip changed after Review; review again')
    if not report['project_change']:
        return report
    entity=command['entity_id'];before=deepcopy(project.overrides.get(entity));after=deepcopy(before or {})
    if report['proposed_component'] is None:
        after.pop('ActorAllocatedAnimation',None)
    else:
        after.pop('ActorAnimation',None)
        after['ActorAllocatedAnimation']=deepcopy(report['proposed_component'])
    if after:
        project.overrides[entity]=after
    else:
        project.overrides.pop(entity,None)
    project.undo_stack.append(dict(entity_id=entity,before=before,after=deepcopy(after or None)))
    project.redo_stack.clear()
    return report


def pose_preview(project,entity_id,record_id,expected_source_key,review_key):
    report=review(project,entity_id,record_id,expected_source_key)
    if report['review_key']!=review_key:
        raise ProjectError('Allocated initial pose differs from the reviewed actor/clip assignment')
    if record_id is None:
        raise ProjectError('Clearing an allocated assignment has no allocated pose proposal')
    animation,asset=pose_saved_record(project,project.active_scene,record_id,expected_source_key)
    animation.update(entity_id=entity_id,actor_semantic_id=entity_id,clip_id='allocated-assignment-preview',
        representation='allocated_assignment_preview',label='Proposed initial allocated clip',assignment_proposal=deepcopy(report))
    return animation,asset,report


def assigned_pose(project,entity_id):
    value=project.overrides.get(entity_id,{}).get('ActorAllocatedAnimation')
    if value is None or value['scene_id']!=project.active_scene:
        raise ProjectError('Assigned allocated pose requires its actor in the active scene')
    validate_binding(project,entity_id,value,verify_disc=True)
    animation,asset=pose_saved_record(project,project.active_scene,value['record_id'],source_key(project))
    animation.update(entity_id=entity_id,actor_semantic_id=entity_id,clip_id='authored-allocated-animation',
        representation='allocated_initial_assignment',label='Assigned allocated initial clip',
        authored_assignment=deepcopy(value))
    return animation,asset
