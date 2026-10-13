"""Fresh native monster frame inspection and unsaved typed Review."""
from base64 import b64encode
from hashlib import sha256
from .project import ProjectError,digest
from .battle_character_resources import _fresh
from .monster_model_authoring import snapshot as model_snapshot
from importer.monster_archive import decode_catalog
from importer.monster_motion import frame
from importer.monster_motion_authoring import patch
from importer.core import ImportError as NativeError
from importer.serialization import serialize_lzs_decoded


def snapshot(project,animation_id,frame_index,part_index,**context):
    record,texture,original,current,raw,used=model_snapshot(project,**context)
    catalog=decode_catalog(raw,record['source_record']['disc']['sha256'])
    clip=next((c for c in catalog['animations'] if c['semantic_id']==animation_id and c['model_asset_id']==record['semantic_id']),None)
    if clip is None:raise ProjectError('Monster action belongs to another model or source')
    try:transforms,stream=frame(current,clip,frame_index)
    except NativeError as e:raise ProjectError(str(e)) from e
    if type(part_index) is not int or not 0<=part_index<clip['part_count']:raise ProjectError('Choose an existing native monster part')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return clip,original,current,raw,used,transforms[part_index],stream


def inspect(project,animation_id,frame_index,part_index,**context):
    clip,_,current,_,_,channels,stream=snapshot(project,animation_id,frame_index,part_index,**context)
    return dict(schema_version='legaia.monster-frame-inspection.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],clip=clip,frame_index=frame_index,part_index=part_index,channels=channels,current_block_sha256=sha256(current).hexdigest(),source_motion_base64=b64encode(stream).decode(),layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,animation_id,frame_index,part_index,expected_current_block_sha256,translation,rotation_psx,**context):
    clip,original,current,raw,used,_,stream=snapshot(project,animation_id,frame_index,part_index,**context)
    if sha256(current).hexdigest()!=expected_current_block_sha256:raise ProjectError('Monster Current slot changed; inspect its channels again')
    try:
        candidate,projection=patch(current,clip,frame_index,part_index,translation,rotation_psx);at=clip['source_record']['compressed_stream_offset'];_,capacity=serialize_lzs_decoded(raw[at:at+used],len(original),candidate,'monster-motion')
    except NativeError as e:raise ProjectError(str(e)) from e
    start=clip['source_record']['byte_offset'];end=start+clip['source_record']['byte_length']
    value=dict(schema_version='legaia.monster-frame-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],clip=clip,frame_index=frame_index,part_index=part_index,projection=projection,capacity=capacity,source_motion_base64=b64encode(stream).decode(),candidate_motion_base64=b64encode(candidate[start:end]).decode(),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,context['expected_project_path'],context['expected_source_key']);return value
