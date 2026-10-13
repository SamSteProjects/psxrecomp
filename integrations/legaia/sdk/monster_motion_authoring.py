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
from .monster_motions import current_clip,compose,validate
from copy import deepcopy


def snapshot(project,animation_id,frame_index,part_index,**context):
    record,texture,original,current,raw,used=model_snapshot(project,**context)
    catalog=decode_catalog(raw,record['source_record']['disc']['sha256'])
    clip=next((c for c in catalog['animations'] if c['semantic_id']==animation_id and c['model_asset_id']==record['semantic_id']),None)
    if clip is None:raise ProjectError('Monster action belongs to another model or source')
    try:transforms,stream=frame(current,current_clip(current,clip),frame_index)
    except NativeError as e:raise ProjectError(str(e)) from e
    if type(part_index) is not int or not 0<=part_index<clip['part_count']:raise ProjectError('Choose an existing native monster part')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return clip,original,current,raw,used,transforms[part_index],stream


def inspect(project,animation_id,frame_index,part_index,**context):
    clip,original,current,_,_,channels,stream=snapshot(project,animation_id,frame_index,part_index,**context)
    at=clip['source_record']['byte_offset'];end=at+clip['source_record']['byte_length']
    return dict(schema_version='legaia.monster-frame-inspection.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],clip=clip,frame_index=frame_index,part_index=part_index,channels=channels,current_block_sha256=sha256(current).hexdigest(),source_motion_base64=b64encode(stream).decode(),retail_motion_base64=b64encode(original[at:end]).decode(),motion_binding=deepcopy(project.monster_motion_overrides.get(animation_id)),layer='current',read_only=True,project_changed=False,gameplay_verified=False)


def review(project,animation_id,frame_index,part_index,expected_current_block_sha256,translation,rotation_psx,**context):
    clip,original,current,raw,used,_,stream=snapshot(project,animation_id,frame_index,part_index,**context)
    if sha256(current).hexdigest()!=expected_current_block_sha256:raise ProjectError('Monster Current slot changed; inspect its channels again')
    try:
        candidate,projection=patch(current,current_clip(current,clip),frame_index,part_index,translation,rotation_psx);at=clip['source_record']['compressed_stream_offset'];_,capacity=serialize_lzs_decoded(raw[at:at+used],len(original),candidate,'monster-motion')
    except NativeError as e:raise ProjectError(str(e)) from e
    start=clip['source_record']['byte_offset'];end=start+clip['source_record']['byte_length']
    value=dict(schema_version='legaia.monster-frame-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],clip=clip,frame_index=frame_index,part_index=part_index,projection=projection,capacity=capacity,source_motion_base64=b64encode(stream).decode(),candidate_motion_base64=b64encode(candidate[start:end]).decode(),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def apply(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key or not value['projection']['byte_change_count']:raise ProjectError('Monster frame Apply requires exact fresh changed Review')
    clip,original,current,raw,_,_,_=snapshot(project,**{k:v for k,v in args.items() if k not in ('expected_current_block_sha256','translation','rotation_psx')})
    identifier=clip['semantic_id'];before=deepcopy(project.monster_motion_overrides);after=deepcopy(before);rows={(e['frame_index'],e['part_index']):deepcopy(e) for e in before.get(identifier,{}).get('edits',[])};pair=(args['frame_index'],args['part_index']);retail,_=frame(original,clip,args['frame_index']);source=retail[args['part_index']]
    if args['translation']==source['translation'] and args['rotation_psx']==source['rotation_psx']:rows.pop(pair,None)
    else:rows[pair]=dict(frame_index=pair[0],part_index=pair[1],translation=args['translation'].copy(),rotation_psx=args['rotation_psx'].copy())
    if rows:
        candidate,_=patch(current,current_clip(current,clip),args['frame_index'],args['part_index'],args['translation'],args['rotation_psx']);derived=current_clip(candidate,clip)
        after[identifier]=dict(schema_version='legaia.monster-motion-override.v1',asset_id=identifier,source_record=deepcopy(clip['source_record']),edits=[rows[k] for k in sorted(rows)],current_motion_sha256=derived['source_record']['sha256'],current_entry_sha256=derived['source_record']['entry_sha256'])
    else:after.pop(identifier,None)
    validate(project,after);project.monster_motion_overrides=after;project.undo_stack.append(dict(target='monster_motion_overrides',before=before,after=deepcopy(after),label='Monster native motion'));project.redo_stack.clear()
    return dict(history_steps=1,project_changed=True,gameplay_verified=False)
