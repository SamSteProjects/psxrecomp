"""Read-only source-qualified scene textures for material binding drafts."""
from hashlib import sha256
from .project import ProjectError
from .model_materials import _current,_bounded
from .scene_preview import source_key


def _context(project,expected):
    key=source_key(project);binding=dict(scene_id=project.active_scene,project_source_key=key)
    if not key or key!=expected:raise ProjectError('Texture binding source changed; reopen material editing')
    _current(project,binding)
    return binding


def catalog(project,expected_source_key):
    from importer.pipeline import _disc_context,import_scene
    from importer.texture_catalog import load_texture_asset_catalog
    binding=_context(project,expected_source_key);doc=project.imports.get(project.active_scene)
    if not doc or not project.disc_path:raise ProjectError('Texture bindings require an imported scene')
    with _disc_context(project.disc_path):
        if import_scene(project.disc_path,doc['scene']['name'])!=doc:
            raise ProjectError('Texture catalog differs from freshly verified scene evidence')
        imported=load_texture_asset_catalog(project.disc_path,doc['scene']['name'])
    if len(imported['assets'])>4096:raise ProjectError('Texture binding catalog exceeds 4096 textures')
    rows=[dict(asset_id=row['semantic_id'],label=row['name']) for row in imported['assets']]
    from .texture_slots import current_items
    rows.extend(dict(asset_id=i,label=b['label']) for i,b,_ in current_items(project))
    if len(rows)>4096:raise ProjectError('Texture binding catalog exceeds 4096 textures')
    if len({row['asset_id'] for row in rows})!=len(rows):raise ProjectError('Texture binding catalog has duplicate source identities')
    result=dict(schema_version='legaia.material-texture-catalog.v1',**binding,textures=rows,project_changed=False)
    _bounded(result,'Texture binding catalog');_current(project,binding);return result


def source(project,asset_id,expected_source_key,palette_index):
    from importer.texture_material_binding import texture_material_pages
    from .texture_resize import image_layout
    binding=_context(project,expected_source_key)
    if asset_id in project.texture_additions:
        from .texture_slots import current_items
        selected=next((row for row in current_items(project) if row[0]==asset_id),None)
        if selected is None:raise ProjectError('New texture is outside the active scene')
        effective=retail=selected[2]
    else:
        context=project._texture_context(asset_id)
        retail=context.original_tim(asset_id);override=project.texture_overrides.get(asset_id)
        effective=project.read_texture_replacement(override) if override else retail
        project.validate_effective_texture(asset_id,effective,context=context)
    pages=texture_material_pages(effective,palette_index)
    result=dict(schema_version='legaia.material-texture-source.v1',**binding,asset_id=asset_id,
        source_sha256=sha256(retail).hexdigest(),effective_sha256=sha256(effective).hexdigest(),
        image_layout=image_layout(effective),palette_index=palette_index,**pages,project_changed=False)
    _bounded(result,'Texture binding source');_current(project,binding);return result
