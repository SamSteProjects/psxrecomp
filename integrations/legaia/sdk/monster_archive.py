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
    _disc(project,catalog)
    from .monster_png import records
    retained_inputs=records(project,catalog)
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-resources.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog=catalog,retained_inputs=retained_inputs,layer='retail',read_only=True,project_changed=False,gameplay_verified=False)


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


def pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,animation_id,frame_index):
    from copy import deepcopy
    from importer.pipeline import _disc_context
    from importer.monster_motion import frame
    from importer.animation import pose_vertices
    _fresh(project,expected_project_path,expected_source_key)
    base=preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key)
    try:
        with _disc_context(project.disc_path) as (_,digest,_,archive):
            raw=archive.read_entry(archive.entry(native.ENTRY));catalog=native.decode_catalog(raw,digest)
            if catalog['source_key']!=catalog_source_key:raise NativeError('Monster motion catalog changed')
            clip=next((r for r in catalog['animations'] if r['semantic_id']==animation_id),None)
            if clip is None or clip['model_asset_id']!=asset_id:raise NativeError('Monster animation belongs to another model or source')
            data,_=native.block(raw,clip['monster_id']);transforms,stream=frame(data,clip,frame_index)
        geometry=deepcopy(base['geometry']);geometry['vertices']=pose_vertices(geometry['vertices'],geometry['objects'],transforms)
    except NativeError as e:raise ProjectError(str(e)) from e
    geometry.pop('triangle_normals',None);geometry.pop('normal_preview',None)
    geometry.update(posed=True,coordinate_system='retail_psx_actor_local_y_down',bounds=dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],max=[max(v[i] for v in geometry['vertices']) for i in range(3)]))
    _disc(project,catalog);_fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.monster-pose.v1',project_path=str(project.root),project_source_key=expected_source_key,
        catalog_source_key=catalog_source_key,base_preview=base,geometry=geometry,clip=clip,object_transforms=transforms,
        source_motion_base64=b64encode(stream).decode(),source_entry_base64=b64encode(data[clip['source_record']['entry_offset']:clip['source_record']['entry_end']]).decode(),animation_id=animation_id,frame_index=frame_index,
        layer='retail_stored_pose',read_only=True,project_changed=False,gameplay_verified=False)


def current_preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key):
    from .monster_palettes import snapshot
    from importer.monster_textures import layout,material_crops
    from copy import deepcopy
    base=preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key)
    texture=base['texture_record']
    if texture is None:raise ProjectError('Current monster palette preview requires a qualified source pool')
    catalog,record,original,current,_,_=snapshot(project,texture['semantic_id'])
    if catalog['source_key']!=catalog_source_key or record!=texture:raise ProjectError('Current monster texture owner changed')
    retail,width=layout(original,record['source_record']['byte_offset']);pool,_=layout(current,record['source_record']['byte_offset'])
    base['geometry']['textures']=material_crops(base['geometry'],pool,width,record['semantic_id'])
    for crop in base['geometry']['textures']:
        for key in ('rgba','stp'):
            if key in crop:crop[key+'_base64']=b64encode(crop.pop(key)).decode()
    base.update(layer='current_palette',retail_pool_base64=b64encode(retail).decode(),source_pool_base64=b64encode(pool).decode(),palette_binding=deepcopy(project.monster_palette_overrides.get(record['semantic_id'])))
    _fresh(project,expected_project_path,expected_source_key);return base


def current_pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,animation_id,frame_index):
    current=current_preview(project,expected_project_path,expected_source_key,asset_id,catalog_source_key)
    value=pose(project,expected_project_path,expected_source_key,asset_id,catalog_source_key,animation_id,frame_index)
    value['base_preview']=current;value['geometry']['textures']=current['geometry']['textures'];value['layer']='current_palette_stored_pose'
    _fresh(project,expected_project_path,expected_source_key);return value
