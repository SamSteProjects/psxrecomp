"""Read-only project-scoped battle resource discovery and private previews."""
from base64 import b64encode
from importer.battle_character_catalog import discover,preview as native_preview
from importer.core import ImportError as RetailImportError
from .project import ProjectError
from .project_assets import source_key


def _fresh(project,path,key):
    if not project.disc_path or path!=str(project.root) or key!=source_key(project):
        raise ProjectError('Battle resource inspection requires the current disc-backed project source')


def _disc(project,catalog):
    if any(d['source']['disc_identity']!='sha256:'+catalog['source_disc_sha256'] for d in project.imports.values()):
        raise ProjectError('Battle resource disc differs from imported project provenance')


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=discover(project.disc_path)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-character-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,palette_index):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,record,value=native_preview(project.disc_path,asset_id,catalog_source_key,palette_index)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    if record['asset_kind']=='tmd_model':
        value.update(semantic_id=record['semantic_id'],source_record=record['source_record'],reference_commit=record['reference_commit'])
        for texture in value['textures']:
            for field in ('rgba','stp'):
                if field in texture:texture[field+'_base64']=b64encode(texture.pop(field)).decode('ascii')
    if record['asset_kind']=='texture':
        # Private native pixels, not persistent/import metadata.
        rgba,stp=value['rgba'],value['stp'];value={k:v for k,v in value.items() if k not in ('rgba','stp')}
        value.update(rgba_base64=b64encode(rgba).decode('ascii'),stp_base64=b64encode(stp).decode('ascii'))
        _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-character-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog_source_key=catalog_source_key,record=record,preview=value,layer='retail',palette_index=palette_index,read_only=True,project_changed=False,gameplay_verified=False)


def animations(project,expected_project_path,expected_source_key):
    from importer.battle_pack_animation import discover
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=discover(project.disc_path)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-pack-animation-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def pose(project,expected_project_path,expected_source_key,model_id,animation_id,model_source_key,animation_source_key,frame_index):
    from importer.battle_pack_animation import pose as inspect
    _fresh(project,expected_project_path,expected_source_key)
    try:models,catalog,model,clip,geometry,transforms=inspect(project.disc_path,model_id,animation_id,model_source_key,animation_source_key,frame_index)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-pack-pose.v1',project_path=str(project.root),project_source_key=expected_source_key,model_source_key=model_source_key,animation_source_key=animation_source_key,model=model,clip=clip,frame_index=frame_index,geometry=geometry,object_transforms=transforms,layer='retail',read_only=True,project_changed=False,gameplay_verified=False,timing='unresolved',runtime_state='not_observed')


def export(project,expected_project_path,expected_source_key,model_id,model_source_key,animation_id,animation_source_key,frame_index):
    """Export freshly qualified source geometry or one selected pack pose."""
    from importer.export import encode_model_glb
    receipt=preview(project,expected_project_path,expected_source_key,model_id,model_source_key,0)
    if receipt['record']['asset_kind']!='tmd_model':raise ProjectError('Battle GLB export requires a model')
    geometry=receipt['preview'];geometry['representation']='retail-default-battle-pack-not-player-assembly';selected=None
    if animation_id is None:
        if animation_source_key is not None or frame_index is not None:raise ProjectError('Object-local export accepts no animation selection')
    else:
        selected=pose(project,expected_project_path,expected_source_key,model_id,animation_id,model_source_key,animation_source_key,frame_index)
        geometry['frames']=[dict(selected['geometry'],object_transforms=selected['object_transforms'])]
        geometry['animation']=dict(semantic_id=animation_id,source_record=selected['clip']['source_record'],source_frame_index=frame_index,timing='unresolved',runtime_state='not_observed')
    try:content,model_audit=encode_model_glb(geometry,0 if selected else None)
    except RetailImportError as error:raise ProjectError(str(error)) from error
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.battle-pack-export.v1',project_path=str(project.root),project_source_key=expected_source_key,model_source_key=model_source_key,model_id=model_id,animation_id=animation_id,animation_source_key=animation_source_key,frame_index=frame_index,mode='reference-pose' if selected else 'object-local',filename=f'battle-pack-{receipt["record"]["pool_index"]}-{f"frame-{frame_index}" if selected else "object-local"}.glb',glb_base64=b64encode(content).decode('ascii'),audit=model_audit,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)
