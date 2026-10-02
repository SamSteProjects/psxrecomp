"""Imported material address evidence, without pixel payloads or runtime claims."""
from hashlib import sha256
from importer.core import ImportError as RetailImportError
from importer.assets import load_model_source,decode_tmd
from importer.textures import load_scene_texture_catalog,load_asset_texture_catalog,associate_material
from .project import ProjectError

def discover(project):
    document=project.imports[project.active_scene];assets=document['assets'].get('models',[])
    if len(assets)>512:raise ProjectError('Material reference discovery exceeds512 active scene models')
    catalog=load_scene_texture_catalog(project.disc_path,document['scene']['name']);rows=[];unresolved=0;remaining=8*1024*1024
    for asset in assets:
        row=dict(model_id=asset['semantic_id'],materials=[])
        try:
            data=load_model_source(project.disc_path,asset);preview=decode_tmd(data);row['source_sha256']=sha256(data).hexdigest()
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
