"""Project-scoped source-only PLAYER equipment inspection."""
from importer import player_battle as native
from importer.core import ImportError as RetailImportError
from .project import ProjectError
from .battle_character_resources import _fresh,_disc
from base64 import b64encode


def _pixels(geometry):
    for t in geometry.get('textures',[]):
        for key in ('rgba','stp'):
            if key in t:t[key+'_base64']=b64encode(t.pop(key)).decode('ascii')


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=native.discover(project.disc_path)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.player-battle-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,model,geometry,assembly=native.preview(project.disc_path,asset_id,catalog_source_key,equipped)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key);_pixels(geometry)
    return dict(schema_version='legaia.player-battle-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=model,geometry=geometry,assembly=assembly,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped,action_slot,frame_index):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,model,geometry,assembly,clip,transforms=native.pose(project.disc_path,asset_id,catalog_source_key,equipped,action_slot,frame_index)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key);_pixels(geometry)
    return dict(schema_version='legaia.player-battle-pose.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=model,geometry=geometry,assembly=assembly,clip=clip,object_transforms=transforms,action_slot=action_slot,frame_index=frame_index,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def export(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped,mode,action_slot,frame_index,fps):
    import math
    from importer.export import encode_model_glb
    if mode not in ('object-local','pose','clip'):raise ProjectError('Choose a supported PLAYER GLB export mode')
    if mode=='object-local' and any(v is not None for v in (action_slot,frame_index,fps)):raise ProjectError('Object-local export accepts no action, frame or rate')
    if mode!='object-local' and (type(action_slot) is not int or not 0<=action_slot<12):raise ProjectError('Choose a stored PLAYER action slot')
    if mode=='pose' and fps is not None:raise ProjectError('Baked pose export accepts no playback rate')
    if mode=='clip' and (frame_index is not None or type(fps) not in (int,float) or not math.isfinite(fps) or not 1<=fps<=120):raise ProjectError('Full clip requires a chosen interchange rate 1–120 fps and no selected frame')
    receipt=preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped);geometry=receipt['geometry'];geometry['representation']='retail-selected-player-equipment-assembly';geometry['source_record']={**receipt['record']['source_record'],'player_assembly':receipt['assembly']};clip=None
    if mode!='object-local':
        clip=receipt['record']['actions'][action_slot]
        if not clip['preview_supported']:raise ProjectError('Empty PLAYER action has no exportable frames')
        geometry['animation']=dict(semantic_id=clip['semantic_id'],source_record=clip['source_record'],timing=clip['timing'],runtime_state='not_observed',**({'source_frame_index':frame_index} if mode=='pose' else {}))
        if mode=='pose':
            posed=pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,equipped,action_slot,frame_index)
            if posed['assembly']!=receipt['assembly']:raise ProjectError('PLAYER assembly changed during export')
            geometry['frames']=[dict(posed['geometry'],object_transforms=posed['object_transforms'])]
        else:
            try:geometry['frames']=native.action_frames(project.disc_path,receipt['record'],receipt['assembly'],clip)
            except RetailImportError as e:raise ProjectError(str(e)) from e
    try:content,audit=encode_model_glb(geometry,0 if mode=='pose' else None,clip_fps=fps if mode=='clip' else None)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _fresh(project,expected_project_path,expected_source_key)
    suffix='object-local' if mode=='object-local' else f'action-{action_slot}-frame-{frame_index}' if mode=='pose' else f'action-{action_slot}-clip'
    return dict(schema_version='legaia.player-battle-export.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=receipt['record'],assembly=receipt['assembly'],mode=mode,action_slot=action_slot,frame_index=frame_index,fps=fps,clip=clip,filename=f'player-{receipt["record"]["player_index"]}-'+ '-'.join(str(i) for i in equipped)+'-'+suffix+'.glb',glb_base64=b64encode(content).decode('ascii'),audit=audit,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)
