"""Stored monster action streams, with explicit per-object mapping limits.

Pinned monster_archive/animation.rs: +0x4C action offset table, entry +0x8C
stream, nine bytes per part, unsigned full-turn 12-bit Euler channels.
No cadence, interpolation, looping, activation or exact GTE rounding inferred.
"""
from hashlib import sha256
import struct
from .core import ImportError
from .pipeline import REFERENCE_COMMIT
from .player_battle import decode_part


def records(data,owner,model):
    count=owner['spell_entry_count'];table_end=0x4c+count*4
    if table_end>len(data):raise ImportError('Monster action offset table exceeds its decoded block')
    offsets=list(struct.unpack_from(f'<{count}I',data,0x4c))
    boundaries=sorted(set([*offsets,owner['name_offset'],owner['model_offset'],owner['texture_offset'],len(data)]))
    out=[]
    for index,at in enumerate(offsets):
        start=at+0x8c;bound=next((n for n in boundaries if n>at),len(data))
        if at<table_end or start+2>bound or bound>len(data):raise ImportError('Monster action entry header overlaps another source region')
        parts,frames=data[start:start+2];end=start+2+parts*frames*9
        valid=bool(parts) and bool(frames) and parts<=64 and end<=bound
        supported=valid and parts==model['preview_summary']['objects']
        status='available' if supported else 'unmatched_model_parts' if valid else 'unsupported_stream'
        length=end-start if valid else 2
        source=dict(owner['source_record'],byte_offset=start,byte_length=length,sha256=sha256(data[start:start+length]).hexdigest(),
            entry_offset=at,entry_end=bound,entry_sha256=sha256(data[at:bound]).hexdigest(),rate_byte_offset=at+0x78,action_tag_offset=at)
        out.append(dict(semantic_id=f'animation://legaia/monster-archive/{owner["monster_id"]:04d}/entry/{index:04d}',asset_kind='animation',
            name=f'Monster {owner["monster_id"]} Action Entry {index} (Tag 0x{data[at]:02X})',monster_id=owner['monster_id'],entry_index=index,
            model_asset_id=model['semantic_id'],action_tag=data[at],rate_byte=data[at+0x78],part_count=parts,frame_count=frames,
            preview_supported=supported,status=status,source_record=source,reference_commit=REFERENCE_COMMIT,
            mapping='source_object_index_equals_part_index' if supported else 'unqualified',timing='stored_rate_byte_not_runtime_cadence',runtime_state='not_observed'))
    return out


def frame(data,clip,index):
    if clip['preview_supported'] is not True or type(index) is not int or not 0<=index<clip['frame_count']:
        raise ImportError('Monster pose requires a qualified model-part mapping and whole stored frame')
    source=clip['source_record'];stream=data[source['byte_offset']:source['byte_offset']+source['byte_length']]
    if sha256(stream).hexdigest()!=source['sha256'] or stream[:2]!=bytes([clip['part_count'],clip['frame_count']]):raise ImportError('Monster motion source changed')
    transforms=[]
    for part in range(clip['part_count']):
        at=2+(index*clip['part_count']+part)*9
        transforms.append(dict(object_index=part,**decode_part(stream[at:at+9])))
    return transforms,stream
