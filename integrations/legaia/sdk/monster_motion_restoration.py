"""Reviewed removal of one whole monster action's native motion ownership."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,digest
from .battle_character_resources import _fresh
from .monster_motion_authoring import snapshot
from .monster_motions import current_clip,validate
from importer.monster_motion import frame
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError


def _prepare(project,animation_id,frame_index,expected_current_block_sha256,**context):
    clip,original,current,raw,used,_,stream=snapshot(project,animation_id,frame_index,0,**context)
    if sha256(current).hexdigest()!=expected_current_block_sha256:
        raise ProjectError('Monster Current slot changed; inspect before restoring its action')
    owner=project.monster_motion_overrides.get(animation_id)
    if not owner:
        raise ProjectError('Selected monster action has no authored motion to restore')
    source=clip['source_record'];start=source['byte_offset'];end=start+source['byte_length']
    retail=original[start:end]
    if stream==retail:
        raise ProjectError('Monster whole-action restoration has no native changes')
    candidate=current[:start]+retail+current[end:]
    if candidate[start:end]!=retail or candidate[:start]!=current[:start] or candidate[end:]!=current[end:]:
        raise ProjectError('Monster restoration changed bytes outside the complete Retail action')
    after=deepcopy(project.monster_motion_overrides);after.pop(animation_id)
    validate(project,after)
    try:
        compressed=source['compressed_stream_offset']
        _,capacity=serialize_lzs_decoded(raw[compressed:compressed+used],len(original),candidate,'monster-action-restoration')
    except NativeError as e:
        raise ProjectError(str(e)) from e
    projection=dict(schema_version='legaia.monster-action-restoration-projection.v1',animation_id=animation_id,
        byte_offset=start,byte_length=len(retail),source_block_sha256=sha256(current).hexdigest(),candidate_block_sha256=sha256(candidate).hexdigest(),
        source_motion_sha256=sha256(stream).hexdigest(),candidate_motion_sha256=sha256(retail).hexdigest(),
        source_entry_sha256=sha256(current[source['entry_offset']:source['entry_end']]).hexdigest(),candidate_entry_sha256=sha256(candidate[source['entry_offset']:source['entry_end']]).hexdigest(),
        unchanged_neighbor_sha256=sha256(current[:start]+current[end:]).hexdigest(),
        byte_change_count=sum(a!=b for a,b in zip(stream,retail)),
        restored_part_frame_count=sum(stream[at:at+9]!=retail[at:at+9] for at in range(2,len(stream),9)),
        removed_active_input_sha256=owner.get('glb_import',{}).get('glb_sha256'))
    value=dict(schema_version='legaia.monster-action-restoration-review.v1',operation='restore_retail_action',
        project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],
        asset_id=context['asset_id'],clip=clip,frame_index=frame_index,projection=projection,capacity=capacity,
        owner_before=deepcopy(owner),source_motion_base64=b64encode(stream).decode(),retail_motion_base64=b64encode(retail).decode(),candidate_motion_base64=b64encode(retail).decode(),
        current_block_base64=b64encode(current).decode(),candidate_block_base64=b64encode(candidate).decode(),
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value)
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return value,after,clip,original,current,candidate


def review(project,**args):
    return _prepare(project,**args)[0]


def apply(project,review_key,**args):
    value,after,_,_,_,_=_prepare(project,**args)
    if value['review_key']!=review_key or not value['projection']['byte_change_count']:
        raise ProjectError('Monster action restoration requires its exact fresh changed Review')
    before=deepcopy(project.monster_motion_overrides)
    project.monster_motion_overrides=after
    project.undo_stack.append(dict(target='monster_motion_overrides',before=before,after=deepcopy(after),label='Restore Retail Monster Action'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.monster-action-restoration-apply.v1',animation_id=args['animation_id'],
        removed_active_input_sha256=value['projection']['removed_active_input_sha256'],history_steps=1,project_changed=True,gameplay_verified=False)


def proposed_pose(project,review_key,**args):
    from .monster_archive import current_pose
    from importer.animation import pose_vertices
    value,_,clip,_,_,candidate=_prepare(project,**args)
    if value['review_key']!=review_key:
        raise ProjectError('Monster restoration preview requires its exact fresh Review')
    context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')}
    before=current_pose(project,**context,animation_id=clip['semantic_id'],frame_index=args['frame_index'])
    derived=current_clip(candidate,clip);transforms,stream=frame(candidate,derived,args['frame_index'])
    proposed=deepcopy(before);geometry=deepcopy(before['base_preview']['geometry'])
    geometry['vertices']=pose_vertices(geometry['vertices'],geometry['objects'],transforms)
    geometry.pop('triangle_normals',None);geometry.pop('normal_preview',None)
    geometry.update(posed=True,coordinate_system='retail_psx_actor_local_y_down',bounds=dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],max=[max(v[i] for v in geometry['vertices']) for i in range(3)]))
    proposed.update(geometry=geometry,object_transforms=transforms,source_motion_base64=b64encode(stream).decode(),
        source_entry_base64=b64encode(candidate[clip['source_record']['entry_offset']:clip['source_record']['entry_end']]).decode(),
        motion_binding=None,current_clip=derived,layer='proposed_native_frame')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.monster-action-restoration-pose.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
        review_key=review_key,review=value,frame_index=args['frame_index'],current_pose=before,proposed_pose=proposed,
        layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
