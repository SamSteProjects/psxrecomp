"""Bounded rigid GLB replacement candidates for an existing physical ME stream."""
from hashlib import sha256
import math
import struct
from .animation_glb import (_read_glb,_Accessors,_nodes,_hierarchy_order,_tracks,
                            _sample_hierarchy,_quantize_rotation,_nearest,_orientation_error)
from .core import ImportError
from .me_archive import entries,replace_entry
from .player_battle import decode_part
from .player_art_authoring import _source


def import_player_art_glb(original,catalog,archive_id,stream_id,current,expected_current_sha256,parts,content,*,fps,animation_index=None,object_node_indices=None):
    stream,row=_source(original,catalog,archive_id,stream_id)
    if not isinstance(current,bytes) or len(current)!=len(original) or sha256(current).hexdigest()!=expected_current_sha256:
        raise ImportError('Art GLB Current slot changed')
    original_rows=entries(original);current_rows=entries(current)
    if len(current_rows)!=len(original_rows) or any(any(a[k]!=b[k] for k in ('size_word','byte_offset','byte_length')) for a,b in zip(original_rows,current_rows)):
        raise ImportError('Art GLB Current changed the original archive layout')
    decoded=current_rows[stream['stream_index']]['decoded'];count,frames=decoded[:2]
    if (count,frames)!=(stream['part_count'],stream['frame_count']):raise ImportError('Art GLB cannot change native part/frame counts')
    if not isinstance(parts,list) or not 1<=len(parts)<=64 or any(type(p) is not int or not 0<=p<count for p in parts) or set(parts)!=set(range(count)):
        raise ImportError('Art GLB assembly must cover every native part')
    if type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120:raise ImportError('Art GLB requires an explicit interchange rate 1–120')
    doc,payload=_read_glb(content);accessors=_Accessors(doc,payload)
    mapping,static,parents,_=_nodes(doc,len(parts),object_node_indices);order=_hierarchy_order(mapping,parents,frames)
    tracks=_tracks(doc,accessors,mapping,frames/fps,animation_index,hierarchy_nodes=order)
    proposed=bytearray(decoded);edits=[];aliases=0;maximum_translation=maximum_angle=0.
    for frame in range(frames):
        time=struct.unpack('<f',struct.pack('<f',frame/fps))[0];poses=_sample_hierarchy(order,parents,static,tracks,time);chosen={}
        for obj,part in enumerate(parts):
            t,q=poses[mapping[obj]]
            if part in chosen:
                old_t,old_q=chosen[part]
                if any(abs(a-b)>1e-4 for a,b in zip(t,old_t)) or _orientation_error(q,old_q)>1e-5:
                    raise ImportError('Art GLB attachment aliases disagree for one native part')
                aliases+=1
            else:chosen[part]=(t,q)
        for part,(t,q) in sorted(chosen.items()):
            at=2+(frame*count+part)*9;before=decode_part(decoded[at:at+9]);native_t=[t[0],-t[1],t[2]]
            if any(not -2048<=v<=2047 for v in native_t):raise ImportError('Art GLB translation exceeds native twelve-bit bounds')
            translation=[_nearest(v) for v in native_t];rotation,error=_quantize_rotation(q,before['rotation_psx'],rotation_step=1,maximum_degrees=.15)
            maximum_angle=max(maximum_angle,error);maximum_translation=max(maximum_translation,max(abs(a-b) for a,b in zip(native_t,translation)))
            after=dict(translation=translation,rotation_psx=rotation)
            if after==before:continue
            edits.append(dict(frame_index=frame,part_index=part,**after));values=translation+rotation
            for pair in range(3):
                a,b=values[pair*2:pair*2+2];proposed[at+pair*3:at+pair*3+3]=bytes((a&255,b&255,((a>>8)&15)|((b>>4)&240)))
    candidate=replace_entry(current,stream['stream_index'],bytes(proposed))
    return candidate,dict(schema_version='legaia.player-art-glb-import.v1',stream_id=stream_id,glb_sha256=sha256(content).hexdigest(),
                          current_slot_sha256=expected_current_sha256,proposed_slot_sha256=sha256(candidate).hexdigest(),
                          proposed_decoded_sha256=sha256(proposed).hexdigest(),fps=float(fps),frame_count=frames,part_count=count,
                          object_part_indices=list(parts),attachment_alias_checks=aliases,edits=edits,rotation_step_psx=1,
                          maximum_translation_error=maximum_translation,maximum_angular_error_degrees=maximum_angle,
                          timing_evidence='caller_selected_rate_not_verified_retail_timing',allocation=False,gameplay_verified=False)
