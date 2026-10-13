"""Equal-layout single part/frame edits in source-qualified monster streams."""
from hashlib import sha256
from .core import ImportError
from .monster_motion import frame
from .player_battle import decode_part
from .player_animation_authoring import _encode


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
