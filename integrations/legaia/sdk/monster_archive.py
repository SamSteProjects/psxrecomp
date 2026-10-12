"""Project-scoped Retail monster model discovery and object-local preview."""
from base64 import b64encode
from hashlib import sha256
from importer import monster_archive as native
from importer.core import ImportError as NativeError
from .battle_character_resources import _fresh,_disc
from .project import ProjectError


def resources(project,expected_project_path,expected_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog=native.discover(project.disc_path)
    except NativeError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog=catalog,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    _fresh(project,expected_project_path,expected_source_key)
    try:catalog,record,geometry,body=native.preview(project.disc_path,asset_id,catalog_source_key)
    except NativeError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    from importer.pipeline import _disc_context
    from importer.monster_textures import layout,material_crops
    texture=next((r for r in catalog['textures'] if r['monster_id']==record['monster_id']),None)
    pool=None
    if texture:
        with _disc_context(project.disc_path) as (_,_,_,archive):data,_=native.block(archive.read_entry(archive.entry(native.ENTRY)),record['monster_id'])
        pool,width=layout(data,texture['source_record']['byte_offset'])
        if sha256(pool).hexdigest()!=texture['source_record']['sha256']:raise ProjectError('Monster pool source changed')
        geometry['textures']=material_crops(geometry,pool,width,texture['semantic_id'])
        for crop in geometry['textures']:
            for key in ('rgba','stp'):
                if key in crop:crop[key+'_base64']=b64encode(crop.pop(key)).decode()
    else:geometry['textures']=[]
    geometry.update(semantic_id=asset_id,source_record=record['source_record'],texture_scope='monster_source_pool')
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog_source_key=catalog_source_key,record=record,geometry=geometry,texture_record=texture,source_pool_base64=b64encode(pool).decode() if pool is not None else None,source_tmd_base64=b64encode(body).decode(),
        layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


def texture_preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,palette_index):
    from importer.pipeline import _disc_context
    from importer.monster_textures import layout,pixels
    _fresh(project,expected_project_path,expected_source_key)
    try:
        with _disc_context(project.disc_path) as (_,digest,_,archive):
            raw=archive.read_entry(archive.entry(native.ENTRY));catalog=native.decode_catalog(raw,digest)
            if catalog['source_key']!=catalog_source_key:raise NativeError('Monster texture source changed')
            record=next((r for r in catalog['textures'] if r['semantic_id']==asset_id),None)
            if record is None:raise NativeError('Monster texture is absent or unsupported')
            data,_=native.block(raw,record['monster_id']);pool,width=layout(data,record['source_record']['byte_offset']);value=pixels(pool,width,palette_index)
    except NativeError as e:raise ProjectError(str(e)) from e
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    value['rgba_base64']=b64encode(value.pop('rgba')).decode();value['stp_base64']=b64encode(value.pop('stp')).decode()
    return dict(schema_version='legaia.monster-texture-preview.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog_source_key=catalog_source_key,record=record,preview=value,source_pool_base64=b64encode(pool).decode(),
        layer='retail',read_only=True,project_changed=False,gameplay_verified=False)
