"""Source reference actions applied to freshly replayed authored pack models."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import math
from .project import ProjectError
from .battle_character_resources import _fresh,_disc
from .battle_pack_model_authoring import snapshot,current,_geometry
from .battle_pack_playback import playback as retail_playback
from importer.battle_pack_animation import clip_frames
from importer.battle_pack_model_authoring import source
from importer.animation import pose_vertices
from importer.export import encode_model_glb
from importer.core import ImportError as NativeError


def _base(project,expected_current_tmd_sha256,expected_current_entry_sha256,**context):
    original,catalog,record,tmd,entry=snapshot(project,**context)
    if sha256(tmd).hexdigest()!=expected_current_tmd_sha256 or sha256(entry).hexdigest()!=expected_current_entry_sha256:
        raise ProjectError('Current pack model or composed entry changed; inspect Current again')
    from .battle_pack_palettes import texture_entry
    _,geometry=source(original,record,catalog,tmd,texture_entry(project,original,catalog))
    return record,geometry


def _tracks(project,record,animation_id,animation_source_key,context):
    try:
        catalog,model,clip,frames=clip_frames(project.disc_path,record['semantic_id'],animation_id,context['catalog_source_key'],animation_source_key)
    except NativeError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog)
    if model!=record:raise ProjectError('Current pack action belongs to another source model')
    return clip,frames


def _posed(geometry,transforms):
    value=deepcopy(geometry);value['vertices']=pose_vertices(value['vertices'],value['objects'],transforms)
    value.update(posed=True,coordinate_system='retail_psx_actor_local_y_down',
        bounds=dict(min=[min(v[i] for v in value['vertices']) for i in range(3)],max=[max(v[i] for v in value['vertices']) for i in range(3)]))
    value.pop('triangle_normals',None);value.pop('normal_preview',None)
    return value


def pose(project,animation_id,animation_source_key,frame_index,expected_current_tmd_sha256,expected_current_entry_sha256,**context):
    record,geometry=_base(project,expected_current_tmd_sha256,expected_current_entry_sha256,**context)
    clip,frames=_tracks(project,record,animation_id,animation_source_key,context)
    if type(frame_index) is not int or not 0<=frame_index<len(frames):raise ProjectError('Choose an existing whole reference frame')
    inspection=current(project,**context)
    original=retail_playback(project,expected_project_path=context['expected_project_path'],expected_source_key=context['expected_source_key'],
        model_id=record['semantic_id'],model_source_key=context['catalog_source_key'],animation_id=animation_id,animation_source_key=animation_source_key)
    transforms=frames[frame_index]['object_transforms']
    value=dict(schema_version='legaia.battle-pack-current-pose.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
        inspection=inspection,retail_playback=original,clip=clip,frame_index=frame_index,object_transforms=transforms,
        geometry=_geometry(_posed(geometry,transforms)),layer='current_model_reference_action',read_only=True,project_changed=False,
        gameplay_verified=False,timing='unresolved',runtime_state='not_observed')
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def export(project,mode,animation_id,animation_source_key,frame_index,fps,expected_current_tmd_sha256,expected_current_entry_sha256,**context):
    if mode not in ('object-local','pose','clip'):raise ProjectError('Choose a supported Current pack export mode')
    if mode=='object-local' and any(v is not None for v in (animation_id,animation_source_key,frame_index,fps)):
        raise ProjectError('Current object-local export accepts no action selection')
    if mode=='pose' and fps is not None:raise ProjectError('Baked pose export accepts no interchange FPS')
    if mode=='clip' and (frame_index is not None or type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120):
        raise ProjectError('Full Current clip export requires explicit1–120 interchange FPS and no selected frame')
    record,geometry=_base(project,expected_current_tmd_sha256,expected_current_entry_sha256,**context);clip=None
    if mode!='object-local':
        clip,frames=_tracks(project,record,animation_id,animation_source_key,context)
        if mode=='pose':
            if type(frame_index) is not int or not 0<=frame_index<len(frames):raise ProjectError('Choose an existing whole reference frame')
            selected=frames[frame_index];geometry['frames']=[dict(_posed(geometry,selected['object_transforms']),object_transforms=selected['object_transforms'])]
        else:geometry['frames']=frames
        geometry['animation']=dict(semantic_id=animation_id,source_record=clip['source_record'],timing='unresolved',runtime_state='not_observed',**({'source_frame_index':frame_index} if mode=='pose' else {}))
    try:content,audit=encode_model_glb(geometry,0 if mode=='pose' else None,clip_fps=fps if mode=='clip' else None)
    except NativeError as error:raise ProjectError(str(error)) from error
    if len(content)>8*1024*1024:raise ProjectError('Current pack export exceeds8MiB')
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return dict(schema_version='legaia.battle-pack-current-export.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],
        catalog_source_key=context['catalog_source_key'],record=record,clip=clip,mode=mode,frame_index=frame_index,fps=fps,
        current_tmd_sha256=expected_current_tmd_sha256,current_entry_sha256=expected_current_entry_sha256,
        glb_base64=b64encode(content).decode(),audit=audit,filename=f'current-battle-pack-{record["pool_index"]}-{mode}.glb',
        layer='current_model_reference_action',read_only=True,project_changed=False,gameplay_verified=False)
