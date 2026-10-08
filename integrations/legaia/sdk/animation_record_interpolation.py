"""Stage complete native rigid poses between effective retained frame endpoints."""
from copy import deepcopy
from hashlib import sha256
from importer.animation import animation_record_ranges,decode_animation_record
from importer.animation_authoring import patch_animation_channels
from importer.animation_allocation import allocate_animation_record
from .animation_record_edit import options,prepare
from .animation_record_ledger import verified_source
from .scene_preview import source_key
from .project import ProjectError


def interpolate_axis(kind,first,last,index,span,curve='linear'):
    if (type(curve) is not str or curve not in ('linear','ease_in','ease_out','smoothstep')
            or type(span) is not int or not 1<=span<=511 or type(index) is not int or not 0<=index<=span
            or kind not in ('translation','rotation_psx')
            or any(type(v) is not int or not (-2048<=v<=2047 if kind=='translation' else 0<=v<=4080 and v%16==0) for v in (first,last))):
        raise ProjectError('Interpolation requires qualified native axes, bounded frame indices and a supported curve')
    if curve=='ease_in':index,span=index*index,span*span
    elif curve=='ease_out':index,span=2*index*span-index*index,span*span
    elif curve=='smoothstep':index,span=index*index*(3*span-2*index),span*span*span
    def rounded(numerator):
        return (2*numerator+span)//(2*span)
    if kind=='translation':
        return rounded(first*(span-index)+last*index)
    delta=(last//16-first//16)%256
    if delta>128:
        delta-=256
    return (rounded(first//16*span+delta*index)%256)*16


def stage(project,scene_id,record_id,source_frame_indices,edits,object_index,start,end,expected_source_key,all_objects=False,curve='linear'):
    if type(curve) is not str or curve not in ('linear','ease_in','ease_out','smoothstep'):
        raise ProjectError('Choose a supported native interpolation curve')
    current=options(project,scene_id,record_id,expected_source_key);entry=current['entry']
    if (type(all_objects) is not bool or not current['edit_available'] or not isinstance(source_frame_indices,list)
            or not 2<=len(source_frame_indices)<=current['maximum_frame_count']
            or type(object_index) is not int or not 0<=object_index<entry['object_count']
            or type(start) is not int or type(end) is not int or not 0<=start<end<len(source_frame_indices)):
        raise ProjectError('Effective interpolation requires two distinct output frames and an existing rigid object')
    source,_=verified_source(project,scene_id);index=int(entry['donor_animation_id'].rsplit('/',1)[1]);a,b=animation_record_ranges(source)[index]
    captured,_=patch_animation_channels(source[a:b],entry['donor_record_sha256'],entry['donor_edits'])
    before,_=allocate_animation_record(captured,entry['effective_donor_record_sha256'],source_frame_indices,edits)
    frames=decode_animation_record(before)['frames']
    def pose(frame,obj=object_index):
        transform=frames[frame]['object_transforms'][obj]
        return {kind:dict(zip('xyz',transform[kind])) for kind in ['translation','rotation_psx']}
    selected_objects=range(entry['object_count']) if all_objects else [object_index]
    endpoints={obj:(pose(start,obj),pose(end,obj)) for obj in selected_objects}
    result=deepcopy(edits);rows={(r['frame_index'],r['object_index']):r for r in result};poses=[]
    for frame in range(start,end+1):
        for obj in selected_objects:
            first,last=endpoints[obj]
            after={kind:{axis:interpolate_axis(kind,first[kind][axis],last[kind][axis],frame-start,end-start,curve) for axis in 'xyz'} for kind in ['translation','rotation_psx']}
            row=rows.get((frame,obj))
            if row is None:
                row=dict(frame_index=frame,object_index=obj);result.append(row)
            row.update(deepcopy(after));evidence=dict(frame_index=frame,before=pose(frame,obj),after=after)
            if all_objects:evidence['object_index']=obj
            poses.append(evidence)
    result.sort(key=lambda r:(r['frame_index'],r['object_index']))
    _,review=prepare(project,scene_id,record_id,source_frame_indices,result,expected_source_key)
    if source_key(project)!=expected_source_key:
        raise ProjectError('Effective interpolation source changed during staging')
    report=dict(schema_version='legaia.animation-record-interpolation.v1',scene_id=scene_id,record_id=record_id,project_source_key=expected_source_key,source_frame_indices=deepcopy(source_frame_indices),before_edits=deepcopy(edits),edits=result,object_index=object_index,start=start,end=end,poses=poses,before_record_sha256=sha256(before).hexdigest(),after_record_sha256=review['candidate_record_sha256'],project_changed=False,gameplay_verified=False)
    if all_objects:report.update(schema_version='legaia.animation-record-interpolation.v2',all_objects=True,object_count=entry['object_count'])
    if curve!='linear':report.update(schema_version='legaia.animation-record-interpolation.v4' if all_objects else 'legaia.animation-record-interpolation.v3',curve=curve)
    return report
