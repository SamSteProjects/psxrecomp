"""AssetDB metadata for verified retained clips; no runtime assignment assertion."""
from copy import copy, deepcopy
from .project import ProjectError, digest
from .scene_preview import source_key


def records(project):
    from .animation_allocation import record_library
    from .allocated_animation_assignment import validate_binding
    scene=project.active_scene;ledger=project.overrides.get(scene,{}).get('AnimationRecords')
    if ledger is None:return []
    key=source_key(project)
    view=copy(project);view.mode='edit'
    library=record_library(view,scene,key)
    entries={row['record_id']:row for row in ledger['records']}
    assigned={}
    for owner,parts in sorted(project.overrides.items()):
        value=parts.get('ActorAllocatedAnimation')
        if value is not None and value.get('scene_id')==scene:
            validate_binding(project,owner,value)
            assigned.setdefault(value['record_id'],[]).append(owner)
    result=[]
    for row in library['records']:
        entry=entries[row['record_id']]
        result.append(dict(semantic_id=row['animation_id'],asset_kind='animation',
            name=project.animation_labels.get(row['animation_id'],{}).get('name','Retained clip '+row['record_id']),scope='authored-retained',authored_animation_record=True,
            frame_count=row['frame_count'],bone_count=row['object_count'],model_asset_id=row['donor_asset_id'],
            retained_record={**deepcopy(row),'assigned_actor_ids':assigned.get(row['record_id'],[])},
            source_record=dict(source_kind='authored_animation_record',record_id=row['record_id'],
                record_sha256=row['record_sha256'],ledger_sha256=digest(ledger),
                donor_record_sha256=entry['donor_record_sha256'],donor_animation_id=entry['donor_animation_id']),
            limitations=['Captured donor channel/model association; playback timing and runtime assignment are unresolved.',
                        'Retired clips remain source-inspectable but are absent from the generated native bank.']))
    if source_key(project)!=key:raise ProjectError('Retained animation asset source changed during discovery')
    return result


def preview(project,asset_id,expected_source_key):
    from .animation_allocation import pose_saved_record
    key=source_key(project)
    if not key or key!=expected_source_key:raise ProjectError('Retained animation source changed; refresh assets')
    record=next((row for row in records(project) if row['semantic_id']==asset_id),None)
    if record is None:raise ProjectError('Choose a retained clip from the active scene Asset Database')
    view=copy(project);view.mode='edit'
    animation,asset=pose_saved_record(view,project.active_scene,record['retained_record']['record_id'],key)
    if animation['semantic_id']!=asset_id or asset['semantic_id']!=record['model_asset_id']:
        raise ProjectError('Retained preview differs from its registered clip/model source')
    animation['asset_source']=deepcopy(record)
    if source_key(project)!=key:raise ProjectError('Retained animation source changed during preview')
    return animation,asset,view
