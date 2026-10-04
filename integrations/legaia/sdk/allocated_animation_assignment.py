"""Read-only reviewed initial MAN assignments for saved allocated clips."""
from copy import deepcopy
from hashlib import sha256

from importer.man_assignments import load_man_assignment_context
from importer.pipeline import _disc_context
from .animation_record_ledger import validate,compose
from .animation_allocation import pose_saved_record
from .project import ProjectError,digest
from .scene_preview import source_key


def review(project,entity_id,record_id,expected_source_key):
    scene=project.active_scene;document=project.imports.get(scene);key=source_key(project)
    actor=next((a for a in (document or {}).get('actors',[]) if a['semantic_id']==entity_id),None)
    if project.mode!='edit' or actor is None or not key or key!=expected_source_key:
        raise ProjectError('Allocated initial clip review requires the current imported actor and editable scene source')
    ledger=project.overrides.get(scene,{}).get('AnimationRecords')
    validate(project,scene,ledger,verify_disc=True)
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
        capabilities=dict(review=True,pose_preview=True,apply=False,build_assignment=False),
        limitations=['Initial MAN header only; scripts can later select another model or clip.',
            'The stable record identity is portable; its current MAN byte selector must be re-resolved after ledger changes.',
            'Persistent actor component, scene integration and normal Build assignment are not implemented yet.',
            'Cadence, looping, script compatibility and gameplay suitability remain unverified.'])
    report['review_key']=digest(report)
    return report


def pose_preview(project,entity_id,record_id,expected_source_key,review_key):
    report=review(project,entity_id,record_id,expected_source_key)
    if report['review_key']!=review_key:
        raise ProjectError('Allocated initial pose differs from the reviewed actor/clip assignment')
    animation,asset=pose_saved_record(project,project.active_scene,record_id,expected_source_key)
    animation.update(entity_id=entity_id,actor_semantic_id=entity_id,clip_id='allocated-assignment-preview',
        representation='allocated_assignment_preview',label='Proposed initial allocated clip',assignment_proposal=deepcopy(report))
    return animation,asset,report
