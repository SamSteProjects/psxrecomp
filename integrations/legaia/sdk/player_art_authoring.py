"""Fresh numeric Current art inspection, unsaved Review/pose and atomic Apply."""
from base64 import b64encode, b64decode
from copy import deepcopy
from hashlib import sha256
from importer.me_archive import entries
from importer.player_battle import decode_part
from importer.player_art_authoring import owner
from importer.core import ImportError as NativeError
from .project import ProjectError, digest
from .battle_character_resources import _fresh
from .player_art_animation import playback, frame_geometry
from .player_art_store import context as sources, composed_slots, validate


def _edit(project):
    if project.mode!='edit':raise ProjectError('Native PLAYER art channels require Edit mode')


def snapshot(project,frame_index,part_index,**context):
    _edit(project);base=playback(project,**context)
    raw,catalog,profile=sources(project);stream=base['stream'];source=stream['source_record']
    if catalog['source_key']!=context['art_source_key']:raise ProjectError('Art catalogue changed')
    if type(frame_index) is not int or not 0<=frame_index<stream['frame_count'] or type(part_index) is not int or not 0<=part_index<stream['part_count']:
        raise ProjectError('Choose an existing whole art frame and native part')
    at=source['slot_offset'];original=raw[at:at+0x10800]
    slots=composed_slots(raw,catalog,project.player_art_overrides);current=slots.get(stream['archive_asset_id'],original)
    decoded=entries(current)[stream['stream_index']]['decoded'];start=2+(frame_index*stream['part_count']+part_index)*9
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return base,raw,catalog,profile,original,current,decoded,decode_part(decoded[start:start+9])


def inspect(project,frame_index,part_index,**context):
    base,_,catalog,profile,original,current,decoded,channels=snapshot(project,frame_index,part_index,**context)
    stream=base['stream'];source=stream['source_record'];at=source['byte_offset']-source['slot_offset'];end=at+source['byte_length']
    owners={k:deepcopy(v) for k,v in project.player_art_overrides.items() if any(s['semantic_id']==k and s['archive_asset_id']==stream['archive_asset_id'] for s in catalog['streams'])}
    return dict(schema_version='legaia.player-art-frame-inspection.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
                base_playback=base,frame_index=frame_index,part_index=part_index,channels=channels,
                current_slot_sha256=sha256(current).hexdigest(),current_body_sha256=sha256(current[at:end]).hexdigest(),
                current_slot_base64=b64encode(current).decode(),current_decoded_base64=b64encode(decoded).decode(),
                owners=owners,consumer_profile=profile,motion_layer='current',geometry_layer=context['layer'],
                read_only=True,project_changed=False,gameplay_verified=False)


def review(project,frame_index,part_index,expected_current_slot_sha256,translation,rotation_psx,**context):
    inspection=inspect(project,frame_index,part_index,**context)
    if inspection['current_slot_sha256']!=expected_current_slot_sha256:raise ProjectError('Art Current slot changed; inspect again')
    for field,values,low,high in [('translation',translation,-2048,2047),('rotation',rotation_psx,0,4095)]:
        if not isinstance(values,list) or len(values)!=3 or any(type(v) is not int or not low<=v<=high for v in values):
            raise ProjectError(f'Art {field} requires three exact native twelve-bit integers')
    requested=dict(translation=translation,rotation_psx=rotation_psx)
    if requested==inspection['channels']:raise ProjectError('Art Review requires changed Current channels')
    base=inspection['base_playback'];stream=base['stream'];original=b64decode(base['source_slot_base64']);retail=entries(original)[stream['stream_index']]['decoded']
    at=2+(frame_index*stream['part_count']+part_index)*9;retail_channels=decode_part(retail[at:at+9]);identifier=stream['semantic_id']
    before=deepcopy(project.player_art_overrides);after=deepcopy(before)
    rows={(e['frame_index'],e['part_index']):deepcopy(e) for e in before.get(identifier,{}).get('edits',[])}
    if requested==retail_channels:rows.pop((frame_index,part_index),None)
    else:rows[(frame_index,part_index)]=dict(frame_index=frame_index,part_index=part_index,**deepcopy(requested))
    raw,catalog,_=sources(project)
    try:
        if rows:after[identifier]=owner(original,catalog,stream['archive_asset_id'],identifier,[rows[k] for k in sorted(rows)])
        else:after.pop(identifier,None)
    except NativeError as error:raise ProjectError(str(error)) from error
    candidate=composed_slots(raw,catalog,after).get(stream['archive_asset_id'],original)
    source=stream['source_record'];body_at=source['byte_offset']-source['slot_offset'];end=body_at+source['byte_length']
    decoded=entries(candidate)[stream['stream_index']]['decoded'];current=b64decode(inspection['current_slot_base64'])
    value=dict(schema_version='legaia.player-art-frame-review.v1',inspection=inspection,frame_index=frame_index,part_index=part_index,
               projection=dict(before=inspection['channels'],after=deepcopy(requested),byte_change_count=sum(a!=b for a,b in zip(current,candidate))),
               ownership_after=deepcopy(after.get(identifier)),candidate_slot_base64=b64encode(candidate).decode(),
               candidate_slot_sha256=sha256(candidate).hexdigest(),candidate_body_sha256=sha256(candidate[body_at:end]).hexdigest(),
               candidate_decoded_base64=b64encode(decoded).decode(),capacity=dict(original_body_size=source['byte_length'],decoded_byte_count=len(decoded),growth=False),
               motion_layer='proposed',geometry_layer=context['layer'],persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_edit(project);_fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def proposed_pose(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Art Proposed pose requires exact fresh Review')
    base=value['inspection']['base_playback'];stream=base['stream'];frame=args['frame_index']
    current,ct=frame_geometry(base['base_inspection'],stream,b64decode(value['inspection']['current_decoded_base64']),frame)
    proposed,pt=frame_geometry(base['base_inspection'],stream,b64decode(value['candidate_decoded_base64']),frame)
    return dict(schema_version='legaia.player-art-frame-pose.v1',review=value,review_key=review_key,
                current_pose=dict(geometry=current,object_transforms=ct,frame_index=frame),
                proposed_pose=dict(geometry=proposed,object_transforms=pt,frame_index=frame),
                motion_layer='proposed',geometry_layer=args['layer'],persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)


def apply(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key or not value['projection']['byte_change_count']:raise ProjectError('Art Apply requires exact fresh changed Review')
    identifier=args['stream_id'];before=deepcopy(project.player_art_overrides);after=deepcopy(before)
    if value['ownership_after'] is None:after.pop(identifier,None)
    else:after[identifier]=deepcopy(value['ownership_after'])
    after=validate(project,after);_edit(project);_fresh(project,args['expected_project_path'],args['expected_source_key'])
    project.player_art_overrides=after;project.undo_stack.append(dict(target='player_art_overrides',before=before,after=deepcopy(after),label='PLAYER Art Channels'));project.redo_stack.clear()
    return dict(history_steps=1,project_changed=True,stream_id=identifier,current_slot_sha256=value['candidate_slot_sha256'],gameplay_verified=False)
