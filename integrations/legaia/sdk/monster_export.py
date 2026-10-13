"""Private monster GLB interchange, separate from native authoring/delivery."""
import math
from copy import deepcopy
from base64 import b64encode
from importer.export import encode_model_glb
from importer.core import ImportError as NativeError
from importer.pipeline import _disc_context
from importer.monster_archive import block,decode_catalog
from importer.monster_motion import frame
from .monster_archive import preview,pose,current_preview,current_pose
from .battle_character_resources import _fresh
from .project import ProjectError


def export(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,mode,animation_id,frame_index,fps,texture_layer='retail'):
    if texture_layer not in ('retail','current'):raise ProjectError('Choose Retail or Current monster textures')
    if mode not in ('object-local','stored-pose','full-clip'):raise ProjectError('Choose object-local, stored pose or full clip export')
    if mode=='object-local':
        if animation_id is not None or frame_index is not None or fps is not None:raise ProjectError('Object-local export accepts no motion selection')
    elif mode=='stored-pose':
        if not isinstance(animation_id,str) or type(frame_index) is not int or fps is not None:raise ProjectError('Pose export requires its selected whole native frame')
    elif not isinstance(animation_id,str) or frame_index is not None or type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120:
        raise ProjectError('Full clip export requires an explicit interchange rate from 1 to 120 fps')
    base=(current_preview if texture_layer=='current' else preview)(project,expected_project_path,expected_source_key,asset_id,catalog_source_key)
    geometry=deepcopy(base['geometry']);geometry['representation']='retail-monster-source-interchange'
    geometry['source_record']=dict(geometry['source_record'],**({'monster_palette_binding':deepcopy(base['palette_binding']),'monster_model_binding':deepcopy(base.get('model_binding')),'monster_motion_bindings':deepcopy(base.get('motion_bindings',{}))} if texture_layer=='current' else {}),monster_texture_source=deepcopy(base['texture_record']['source_record']) if base['texture_record'] else None)
    clip=None
    try:
        if mode=='stored-pose':
            selected=(current_pose if texture_layer=='current' else pose)(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,animation_id,frame_index)
            clip=selected['clip'];geometry['frames']=[dict(selected['geometry'],object_transforms=selected['object_transforms'])]
        elif mode=='full-clip':
            with _disc_context(project.disc_path) as (_,digest,_,archive):
                raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,digest)
                if catalog['source_key']!=catalog_source_key:raise NativeError('Monster motion source changed before export')
                clip=next((r for r in catalog['animations'] if r['semantic_id']==animation_id),None)
                if clip is None or clip['model_asset_id']!=asset_id or not clip['preview_supported']:raise NativeError('Monster clip has no matching qualified model parts')
                data,_=block(raw,clip['monster_id'])
                sampled=clip
                if texture_layer=='current':
                    from .monster_motions import compose,current_clip
                    data=compose(data,catalog,clip['monster_id'],project.monster_motion_overrides);sampled=current_clip(data,clip)
                geometry['frames']=[dict(object_transforms=frame(data,sampled,index)[0]) for index in range(clip['frame_count'])]
        if clip:geometry['animation']=dict(semantic_id=clip['semantic_id'],source_record=deepcopy(clip['source_record']),
            source_frame_index=frame_index,timing='stored_rate_byte_not_runtime_cadence',runtime_state='not_observed',rate_byte=clip['rate_byte'],mapping=clip['mapping'])
        content,audit=encode_model_glb(geometry,0 if mode=='stored-pose' else None,clip_fps=fps if mode=='full-clip' else None)
    except NativeError as e:raise ProjectError(str(e)) from e
    _fresh(project,expected_project_path,expected_source_key)
    suffix='object-local' if mode=='object-local' else f'entry-{clip["entry_index"]}-frame-{frame_index}' if mode=='stored-pose' else f'entry-{clip["entry_index"]}-clip'
    return dict(schema_version='legaia.monster-export.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog_source_key=catalog_source_key,asset_id=asset_id,mode=mode,animation_id=animation_id,frame_index=frame_index,fps=fps,clip=clip,
        texture_layer=texture_layer,filename=('current-palette-' if texture_layer=='current' else '')+f'monster-{base["record"]["monster_id"]}-{suffix}.glb',glb_base64=b64encode(content).decode(),audit=audit,
        layer='current_palette_interchange' if texture_layer=='current' else 'retail_source_interchange',read_only=True,project_changed=False,gameplay_verified=False)
