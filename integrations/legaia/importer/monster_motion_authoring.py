"""Equal-layout single part/frame edits in source-qualified monster streams."""
from hashlib import sha256
from .core import ImportError
from .monster_motion import frame
from .player_battle import decode_part
from .player_animation_authoring import _encode
from copy import deepcopy


def patch(data,clip,frame_index,part_index,translation,rotation_psx):
    _,stream=frame(data,clip,frame_index)
    if type(part_index) is not int or not 0<=part_index<clip['part_count']:raise ImportError('Choose an existing monster part index')
    for values,low,high in ((translation,-2048,2047),(rotation_psx,0,4095)):
        if not isinstance(values,list) or len(values)!=3 or any(type(v) is not int or not low<=v<=high for v in values):raise ImportError('Monster frame channels require exact native twelve-bit XYZ integers')
    source=clip['source_record'];at=source['byte_offset']+2+(frame_index*clip['part_count']+part_index)*9
    before=decode_part(data[at:at+9]);encoded=_encode(translation,rotation_psx)
    if decode_part(encoded)!=dict(translation=translation,rotation_psx=rotation_psx):raise ImportError('Monster frame channel encoding did not replay')
    candidate=data[:at]+encoded+data[at+9:]
    if len(candidate)!=len(data) or candidate[:at]!=data[:at] or candidate[at+9:]!=data[at+9:]:raise ImportError('Monster frame edit escaped its nine-byte allocation')
    end=source['byte_offset']+source['byte_length'];proposed=candidate[source['byte_offset']:end]
    return candidate,dict(schema_version='legaia.monster-frame-projection.v1',animation_id=clip['semantic_id'],frame_index=frame_index,part_index=part_index,byte_offset=at,before=before,after=dict(translation=translation,rotation_psx=rotation_psx),source_motion_sha256=sha256(stream).hexdigest(),candidate_motion_sha256=sha256(proposed).hexdigest(),byte_change_count=sum(a!=b for a,b in zip(data[at:at+9],encoded)),source_block_sha256=sha256(data).hexdigest(),candidate_block_sha256=sha256(candidate).hexdigest(),project_changed=False,gameplay_verified=False)


def patch_range(original,data,clip,frame_index,part_index,translation,rotation_psx,frame_start,frame_end,range_operation):
    if range_operation not in ('hold','offset','restore') or any(type(n) is not int for n in (frame_start,frame_end)) or not 0<=frame_start<=frame_index<=frame_end<clip['frame_count']:raise ImportError('Monster range requires inclusive existing frames containing the inspected frame')
    # Qualify target values and the selected part before generating any draft.
    _,projection=patch(data,clip,frame_index,part_index,translation,rotation_psx);reference=projection['before'];cursor=data;edits=[];source=clip['source_record'];at=source['byte_offset'];end=at+source['byte_length']
    for index in range(frame_start,frame_end+1):
        offset=at+2+(index*clip['part_count']+part_index)*9;current=decode_part(data[offset:offset+9])
        if range_operation=='restore':values=decode_part(original[offset:offset+9])
        elif range_operation=='hold':values=dict(translation=translation.copy(),rotation_psx=rotation_psx.copy())
        else:values=dict(translation=[v+translation[a]-reference['translation'][a] for a,v in enumerate(current['translation'])],rotation_psx=[(v+rotation_psx[a]-reference['rotation_psx'][a])%4096 for a,v in enumerate(current['rotation_psx'])])
        current_clip=deepcopy(clip);current_clip['source_record']['sha256']=sha256(cursor[at:end]).hexdigest()
        cursor,_=patch(cursor,current_clip,index,part_index,values['translation'],values['rotation_psx']);edits.append(dict(frame_index=index,part_index=part_index,**values))
    selected=edits[frame_index-frame_start];projection.update(after={k:selected[k] for k in ('translation','rotation_psx')},candidate_motion_sha256=sha256(cursor[at:end]).hexdigest(),candidate_block_sha256=sha256(cursor).hexdigest(),byte_change_count=sum(a!=b for a,b in zip(data[at:end],cursor[at:end])),range=dict(frame_start=frame_start,frame_end=frame_end,operation=range_operation,edits=edits))
    return cursor,projection
