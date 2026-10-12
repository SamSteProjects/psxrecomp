"""Existing-layout PLAYER GLB tracks to full twelve-bit native action channels.

Uses the shared bounded glTF parser and rigid hierarchy sampler. Native PLAYER
part ownership comes from freshly decoded equipment assembly, never GLB extras.
Objects sharing a part must sample the same pose; no attachment may silently
replace a body track. Import does not establish runtime cadence or allocate.
"""
from hashlib import sha256
import math,struct
from .animation_glb import (_read_glb,_Accessors,_nodes,_hierarchy_order,_tracks,
    _sample_hierarchy,_quantize_rotation,_nearest,_orientation_error)
from .core import ImportError
from .player_battle import actions,assemble,decode_part
from .player_animation_authoring import patch_player_action


def import_player_action_glb(raw,expected_file_sha256,player_index,action_slot,
                            expected_action_sha256,equipped,content,*,fps,
                            animation_index=None,object_node_indices=None):
    if not isinstance(raw,bytes) or sha256(raw).hexdigest()!=expected_file_sha256:
        raise ImportError('PLAYER GLB source file changed')
    if type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120:
        raise ImportError('PLAYER GLB requires an explicit interchange rate from 1 to 120 fps')
    clips,bank=actions(raw,player_index,'0'*64)
    if type(action_slot) is not int or not 0<=action_slot<len(clips):raise ImportError('PLAYER GLB action slot is unsupported')
    clip=clips[action_slot]
    if not clip['preview_supported'] or clip['source_record']['sha256']!=expected_action_sha256:
        raise ImportError('PLAYER GLB action is empty or its source changed')
    _,assembly=assemble(raw,equipped);parts=assembly['animation_part_indices'];count=clip['part_count']
    if set(parts)!=set(range(count)) or clip['frame_count']*count>4096:
        raise ImportError('PLAYER GLB selected assembly must cover every native part within its budget')
    doc,payload=_read_glb(content);accessors=_Accessors(doc,payload)
    mapping,static,parents,_=_nodes(doc,len(parts),object_node_indices)
    order=_hierarchy_order(mapping,parents,clip['frame_count'])
    tracks=_tracks(doc,accessors,mapping,clip['frame_count']/fps,animation_index,hierarchy_nodes=order)
    edits=[];maximum_translation=maximum_angle=0.;alias_checks=0
    for fi in range(clip['frame_count']):
        time=struct.unpack('<f',struct.pack('<f',fi/fps))[0]
        poses=_sample_hierarchy(order,parents,static,tracks,time);chosen={}
        for obj,part in enumerate(parts):
            t,q=poses[mapping[obj]]
            if part in chosen:
                old_t,old_q=chosen[part]
                if any(abs(a-b)>1e-4 for a,b in zip(t,old_t)) or _orientation_error(q,old_q)>1e-5:
                    raise ImportError('PLAYER GLB attachment and body tracks conflict for one native part')
                alias_checks+=1
            else:chosen[part]=(t,q)
        for part,(t,q) in sorted(chosen.items()):
            offset=clip['source_record']['byte_offset']+2+(fi*count+part)*9
            before=decode_part(bank[offset:offset+9]);native_t=[t[0],-t[1],t[2]]
            if any(not -2048<=v<=2047 for v in native_t):raise ImportError('PLAYER GLB translation exceeds signed twelve-bit bounds')
            rounded=[_nearest(v) for v in native_t]
            rotation,error=_quantize_rotation(q,before['rotation_psx'],rotation_step=1,maximum_degrees=.15)
            maximum_angle=max(maximum_angle,error);maximum_translation=max(maximum_translation,max(abs(a-b) for a,b in zip(native_t,rounded)))
            edit=dict(frame_index=fi,part_index=part)
            for field,after in [('translation',rounded),('rotation_psx',rotation)]:
                axes={axis:value for axis,value,old in zip('xyz',after,before[field]) if value!=old}
                if axes:edit[field]=axes
            if len(edit)>2:edits.append(edit)
    candidate,projection=patch_player_action(raw,expected_file_sha256,player_index,action_slot,expected_action_sha256,edits)
    return candidate,dict(schema_version='legaia.player-action-glb-import.v1',glb_sha256=sha256(content).hexdigest(),fps=float(fps),frame_count=clip['frame_count'],part_count=count,object_count=len(parts),object_part_indices=parts,attachment_alias_checks=alias_checks,edits=edits,projection=projection,maximum_translation_error=maximum_translation,maximum_angular_error_degrees=maximum_angle,rotation_step_psx=1,timing_evidence='caller_selected_rate_not_verified_retail_timing',scope='PLAYER-existing-action-channels-only',gameplay_verified=False)
