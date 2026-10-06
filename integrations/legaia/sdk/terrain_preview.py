"""Resolve source ground textures using the same authored scene texture layer."""
import base64
from importer.terrain import load_terrain
from importer.textures import load_scene_texture_catalog, associate_material
from importer.core import ImportError
from .resources import apply_texture_overrides


def terrain_preview(project, *, prepared=None, catalog=None):
    scene = project.imports[project.active_scene]["scene"]["name"]
    from copy import deepcopy
    preview = deepcopy(prepared) if prepared is not None else load_terrain(project.disc_path, scene)
    floors=getattr(project,'overrides',{}).get(project.active_scene,{}).get('FloorTiers')
    heights=getattr(project,'overrides',{}).get(project.active_scene,{}).get('FloorHeights')
    if floors or heights:
        from importer.floor_authoring import patch_floor_tiers
        from importer.terrain import decode_terrain
        from importer.environment import load_environment_placements
        source=project._environment_source(project.active_scene)
        metadata=load_environment_placements(project.disc_path,scene)
        if (floors and metadata['source_record']['map_sha256']!=floors['source_sha256']) or preview['source_record']!=metadata['source_record']:
            raise ImportError('Authored floor preview source differs from Current ground')
        changed,audit=patch_floor_tiers(source,floors['source_sha256'],floors['edits']) if floors else (source,[])
        from .floor_heights import effective_lut
        lut=effective_lut(project,project.active_scene,metadata['floor_height_lut'],metadata['source_record'].get('man_sha256'))
        preview=decode_terrain(changed,lut)
        preview['source_record']=deepcopy(metadata['source_record'])
        preview['floor_layer']={'kind':'authored','selector_count':len(floors['edits']) if floors else 0,'audited_selector_count':len(audit)}
        if heights:preview['height_layer']={'kind':'authored','tier_count':len(heights['edits'])}
        preview['limitations'].append('Current authored floor selectors; native ramps and live movement remain unverified.')
    if catalog is None:
        catalog = apply_texture_overrides(project, load_scene_texture_catalog(project.disc_path, scene))
    preview["textures"] = []
    budget = 4 * 1024 * 1024
    for index, material in enumerate(preview["materials"]):
        if index >= 64:
            raise ImportError("terrain material count exceeds preview bound")
        uvs = [uv for triangle, mat in zip(preview["triangle_uvs"], preview["triangle_materials"])
               if mat == index for uv in (triangle or [])]
        if not uvs:
            result = {"status": "unsupported", "reason": "Source terrain texture selector is missing or unsupported"}
        else:
            result = associate_material(catalog, material,
                       (min(p[0] for p in uvs), min(p[1] for p in uvs), max(p[0] for p in uvs), max(p[1] for p in uvs)))
            rgba = result.pop("rgba", None)
            result.pop("stp", None)
            if rgba is not None:
                if len(rgba) > budget:
                    raise ImportError("terrain decoded textures exceed preview byte bound")
                budget -= len(rgba)
                result["rgba_base64"] = base64.b64encode(rgba).decode("ascii")
        preview["textures"].append(dict(result, material_index=index))
    return preview
