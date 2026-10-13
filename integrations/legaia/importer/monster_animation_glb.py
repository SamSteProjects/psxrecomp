"""Rigid GLB samples to existing monster twelve-bit part/frame channels."""
from copy import deepcopy
from hashlib import sha256
import math,struct
from .animation_glb import (_read_glb,_Accessors,_nodes,_hierarchy_order,_tracks,_sample_hierarchy,_quantize_rotation,_nearest)
from .core import ImportError
from .monster_motion import frame
from .monster_motion_authoring import patch
from .player_battle import decode_part


def import_motion(data,clip,content,*,fps,animation_index=None,object_node_indices=None):
    if type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120:raise ImportError('Monster GLB requires explicit interchange FPS from 1 to 120')
    _,stream=frame(data,clip,0);count=clip['part_count'];frames=clip['frame_count']
    if not clip['preview_supported'] or count*frames>16320:raise ImportError('Monster GLB requires a complete existing native part/frame mapping')
    doc,payload=_read_glb(content)
    identity=doc.get('extras',{}).get('asset_semantic_id') if isinstance(doc.get('extras',{}),dict) else None
    if identity is not None and identity!=clip['model_asset_id']:raise ImportError('Monster GLB retained source identity belongs to another model')
    accessors=_Accessors(doc,payload);mapping,static,parents,_=_nodes(doc,count,object_node_indices);order=_hierarchy_order(mapping,parents,frames);tracks=_tracks(doc,accessors,mapping,frames/fps,animation_index,hierarchy_nodes=order)
    cursor=data;edits=[];max_translation=max_angle=0.;source=clip['source_record'];start=source['byte_offset'];end=start+source['byte_length']
    for index in range(frames):
        time=struct.unpack('<f',struct.pack('<f',index/fps))[0];poses=_sample_hierarchy(order,parents,static,tracks,time)
        for part in range(count):
            t,q=poses[mapping[part]];native_t=[t[0],-t[1],t[2]];at=2+(index*count+part)*9;before=decode_part(stream[at:at+9])
            if any(not -2048<=v<=2047 for v in native_t):raise ImportError('Monster GLB translation exceeds signed twelve-bit bounds')
            translation=[_nearest(v) for v in native_t];rotation,error=_quantize_rotation(q,before['rotation_psx'],rotation_step=1,maximum_degrees=.15);max_translation=max(max_translation,max(abs(a-b) for a,b in zip(native_t,translation)));max_angle=max(max_angle,error)
            if translation==before['translation'] and rotation==before['rotation_psx']:continue
            current_clip=deepcopy(clip);current_clip['source_record']['sha256']=sha256(cursor[start:end]).hexdigest();cursor,_=patch(cursor,current_clip,index,part,translation,rotation);edits.append(dict(frame_index=index,part_index=part,translation=translation,rotation_psx=rotation))
    return cursor,dict(schema_version='legaia.monster-motion-glb-import.v1',glb_sha256=sha256(content).hexdigest(),fps=float(fps),frame_count=frames,part_count=count,edits=edits,source_motion_sha256=sha256(stream).hexdigest(),candidate_motion_sha256=sha256(cursor[start:end]).hexdigest(),maximum_translation_error=max_translation,maximum_angular_error_degrees=max_angle,rotation_step_psx=1,timing_evidence='caller_selected_rate_not_verified_retail_timing',scope='monster-existing-part-frame-channels-only',project_changed=False,gameplay_verified=False)
