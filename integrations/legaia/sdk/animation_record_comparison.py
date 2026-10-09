"""Read-only native retained-clip comparison; output indices do not imply timing."""
from copy import deepcopy
from .animation_record_ledger import validate, verified_source, reconstruct, verify_witnesses
from .project import ProjectError
from .scene_preview import source_key
from importer.animation import decode_animation_record


def compare(project, scene_id, left_record_id, right_record_id, expected_source_key):
    key=source_key(project)
    if project.mode!='edit' or scene_id!=project.active_scene or not key or key!=expected_source_key:
        raise ProjectError('Retained comparison requires the current editable scene source')
    ledger=validate(project,scene_id,project.overrides.get(scene_id,{}).get('AnimationRecords'),verify_disc=True)
    entries={row['record_id']:row for row in ledger['records']}
    if not isinstance(left_record_id,str) or not isinstance(right_record_id,str) or left_record_id not in entries or right_record_id not in entries:
        raise ProjectError('Retained comparison requires two existing clip identities')
    left,right=entries[left_record_id],entries[right_record_id]
    if (left['donor_asset_id'],left['object_count'])!=(right['donor_asset_id'],right['object_count']):
        raise ProjectError('Retained comparison requires the same captured model and rigid object count')
    source,catalog=verified_source(project,scene_id);verify_witnesses(ledger,catalog)
    view=deepcopy(ledger);view['removed_record_ids']=[]
    payloads={row['record_id']:row['record'] for row in reconstruct(source,view)}
    a,b=payloads[left_record_id],payloads[right_record_id]
    first,second=decode_animation_record(a),decode_animation_record(b)
    paired=min(first['frame_count'],second['frame_count']);differences=[];opaque=0
    for frame in range(paired):
        for obj in range(first['bone_count']):
            x=first['frames'][frame]['object_transforms'][obj];y=second['frames'][frame]['object_transforms'][obj]
            opaque+=x['opaque_nibble']!=y['opaque_nibble']
            for field in ('translation','rotation_psx'):
                for axis,index in zip('xyz',range(3)):
                    before,after=x[field][index],y[field][index]
                    if before!=after:differences.append(dict(frame_index=frame,object_index=obj,field=field,axis=axis,left=before,right=after,delta=after-before))
    if source_key(project)!=key:raise ProjectError('Source changed during retained comparison')
    return dict(schema_version='legaia.animation-record-comparison.v1',scene_id=scene_id,project_source_key=key,
        left_entry=deepcopy(left),right_entry=deepcopy(right),left_active=left_record_id not in ledger['removed_record_ids'],right_active=right_record_id not in ledger['removed_record_ids'],
        paired_frame_count=paired,left_only_frame_count=first['frame_count']-paired,right_only_frame_count=second['frame_count']-paired,
        differences=differences,opaque_channel_difference_count=opaque,
        header_difference_count=sum(x!=y for x,y in zip(a[:8],b[:8])),
        native_byte_difference_count=sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b)),
        native_bytes_equal=a==b,project_changed=False,gameplay_verified=False,
        limitations=['Output indices are compared directly; no time alignment, frame rate or runtime cadence is inferred.',
                    'Rotation deltas are encoded scalar subtraction, not shortest-path angular distance.',
                    'Unpaired frames are reported separately; no missing poses or axes are invented.',
                    'Opaque nibble and header differences are counted without assigning semantic meaning.'])
