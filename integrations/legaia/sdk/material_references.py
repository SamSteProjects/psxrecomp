"""Separate Retail and qualified Current material evidence without pixel payloads."""
from hashlib import sha256
from importer.core import ImportError as RetailImportError
from importer.assets import load_model_source,decode_tmd
from importer.textures import load_scene_texture_catalog,load_asset_texture_catalog,associate_material
from .project import ProjectError

def current_state_key(project):
    from .project import digest
    return digest(dict(imported_source_key=source_key(project),models=project.model_overrides,
                       textures=project.texture_overrides,texture_additions=project.texture_additions))

def _verify_current_assets(project, model_ids):
    """Reuse full owned-content qualification, including model bases and slot recipes."""
    for identifier in sorted(model_ids.intersection(project.model_overrides)):
        project.read_model_replacement(identifier,project.model_overrides[identifier])
    if any(b['source_scene_id']==project.active_scene for b in
           [*project.texture_overrides.values(),*project.texture_additions.values()]):
        from .resources import apply_texture_overrides
        catalog=load_scene_texture_catalog(project.disc_path,project.imports[project.active_scene]['scene']['name'])
        apply_texture_overrides(project,catalog)

def with_current(project, imported):
    """Keep the cached Retail census immutable; decode qualified Current edits separately."""
    from copy import deepcopy
    result=deepcopy(imported)
    ids={a['semantic_id'] for a in project.imports[project.active_scene]['assets'].get('models',[])}
    changed=bool(ids.intersection(project.model_overrides)) or any(
        b['source_scene_id']==project.active_scene for b in [*project.texture_overrides.values(),*project.texture_additions.values()])
    if not changed:return result
    key=current_state_key(project)
    cache=project.assets.current_material_reference_catalogs
    try:
        if key in cache:
            _verify_current_assets(project,ids)
            current=deepcopy(cache[key])
        else:
            current=discover(project,current=True)
            if current_state_key(project)!=key:raise ProjectError('Current material source changed during discovery')
            _verify_current_assets(project,ids)
        if current_state_key(project)!=key:raise ProjectError('Current material source changed during discovery')
    except Exception:
        cache.pop(key,None)
        raise
    result['current_models']=current['models'];result['current_state_key']=key
    result['unresolved_reference_count']+=current['unresolved_reference_count']
    result['limitations'].append('Current material edges are separately decoded from qualified saved model/texture edits. Their absence without edits means Retail inheritance; static address matches do not establish runtime residency.')
    from .project import canonical
    if max(len(canonical(current)),len(canonical(result)))>8*1024*1024:
        cache.pop(key,None)
        raise ProjectError('Current or combined material reference metadata exceeds8 MiB')
    if key in cache:cache.pop(key)
    while len(cache)>=2:cache.pop(next(iter(cache)))
    cache[key]=deepcopy(current)
    return result

def source_key(project):
    from .project import digest
    return digest(dict(version='legaia.imported-materials.v1',disc_path=project.disc_path,
                       scene_id=project.active_scene,document=project.imports[project.active_scene]))

def verified_catalog(project):
    """Request-scoped verification must precede reuse of this imported-only cache."""
    from copy import deepcopy
    from .project import canonical
    key=source_key(project)
    cache=project.assets.material_reference_catalogs
    if key in cache:
        result=cache.pop(key);cache[key]=result
        return deepcopy(result)
    result=discover(project)
    if key!=source_key(project):raise ProjectError('Imported material source changed during discovery')
    if len(canonical(result))>8*1024*1024:raise ProjectError('Material reference metadata exceeds8 MiB')
    while len(cache)>=2:cache.pop(next(iter(cache)))
    cache[key]=deepcopy(result)
    return deepcopy(result)

def discover(project, *, current=False):
    document=project.imports[project.active_scene];assets=document['assets'].get('models',[])
    if len(assets)>512:raise ProjectError('Material reference discovery exceeds512 active scene models')
    catalog=load_scene_texture_catalog(project.disc_path,document['scene']['name']);rows=[];unresolved=0;remaining=8*1024*1024
    if current:
        from .resources import apply_texture_overrides
        catalog=apply_texture_overrides(project,catalog)
    for asset in assets:
        row=dict(model_id=asset['semantic_id'],materials=[])
        try:
            data=load_model_source(project.disc_path,asset);row['retail_sha256']=sha256(data).hexdigest()
            if current and asset['semantic_id'] in project.model_overrides:
                data=project.read_model_replacement(asset['semantic_id'],project.model_overrides[asset['semantic_id']])
            preview=decode_tmd(data);row['source_sha256']=sha256(data).hexdigest()
            if len(preview['materials'])>256:raise RetailImportError('Model exceeds256 recorded material groups')
            textures=load_asset_texture_catalog(project.disc_path,asset,catalog)
            uvs={}
            for index,material_index in enumerate(preview['triangle_materials']):
                uvs.setdefault(material_index,[]).extend(preview['triangle_uvs'][index] or [])
            for index,material in enumerate(preview['materials']):
                if not material.get('textured'):continue
                entry=dict(material_index=index,tpage=material.get('tpage'),clut=material.get('clut'))
                coordinates=uvs.get(index,[])
                if not coordinates or index>=32:entry.update(status='unsupported',reason='Missing UV coordinates or material index exceeds31',source_ids=[])
                else:
                    bounds=(min(uv[0] for uv in coordinates),min(uv[1] for uv in coordinates),max(uv[0] for uv in coordinates),max(uv[1] for uv in coordinates));entry['uv_bounds']=list(bounds);count=(bounds[2]-bounds[0]+1)*(bounds[3]-bounds[1]+1)
                    if count>remaining:entry.update(status='unsupported',reason='Active scene material sampling budget exceeded',source_ids=[])
                    else:
                        remaining-=count;entry.update(associate_material(textures,material,bounds,include_pixels=False))
                if entry['status']!='address_match':unresolved+=1
                row['materials'].append(entry)
        except RetailImportError as error:
            row['unavailable_reason']=str(error);unresolved+=1
        rows.append(row)
    return dict(models=rows,unresolved_reference_count=unresolved,sampled_texels=8*1024*1024-remaining,
                limitations=['Material links describe imported model UV crops and static texture-page/CLUT address matches, not runtime uploads, palette animation or residency.',
                             'Matching source IDs are candidate word providers. Identical overlapping uploads can yield multiple sources; this does not establish upload ownership. Only supported decoded primitive material groups are covered.',
                             'Only successful unique word-value matches create edges. Missing/ambiguous/unsupported materials and unavailable models remain unresolved.',
                             'Shared party and boot texture sources can be recorded outside the navigable active scene TIM catalog. Authored pixel/shape replacements are not represented by these imported links.'])
