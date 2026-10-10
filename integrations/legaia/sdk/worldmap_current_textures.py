"""Reassociate native materials against exact-layout authored kingdom TIMs."""
from copy import deepcopy
from hashlib import sha256
from importer.textures import TextureCatalog,parse_tim,associate_material
from .project import ProjectError
from .worldmap_texture_authoring import scene_for,context,validate


def compose(project,geometry,*,force=False):
    scene=geometry['scene'];source=geometry['source_record']
    bindings={identifier:binding for identifier,binding in project.texture_overrides.items() if scene_for(identifier)==scene}
    edits=[]
    if bindings or force or geometry.get('model_authoring',{}).get('schema_version') in ('legaia.worldmap-current-models.v2','legaia.worldmap-current-models.v3','legaia.worldmap-current-models.v4'):
        identifiers=geometry['preview'].get('texture_catalog',{}).get('textures',[])
        identifier=next(iter(bindings)) if bindings else next((t['semantic_id'] for t in identifiers if scene_for(t.get('semantic_id'))==scene),None)
        if identifier is None:raise ProjectError('Current World material association requires a native kingdom texture catalog')
        ctx=context(project,identifier)
        if ctx._digest!=source['disc_sha256']:
            raise ProjectError('World texture and geometry disc identities differ')
        catalog=TextureCatalog(scene,ctx._digest)
        catalog.textures=deepcopy(ctx._catalog.textures)
        replacements={}
        for identifier,binding in sorted(bindings.items()):
            validate(project,binding,identifier);project._validate_texture_binding(binding)
            original=ctx.original_tim(identifier)
            if binding['source_disc_sha256']!=ctx._digest or binding['source_sha256']!=sha256(original).hexdigest():
                raise ProjectError('World geometry texture binding lost its immutable Retail source')
            content=project.read_texture_replacement(binding);ctx.validate_replacement(identifier,content)
            replacements[identifier]=parse_tim(content)
            if content!=original:edits.append(dict(texture_id=identifier,source_tim_sha256=sha256(original).hexdigest(),effective_tim_sha256=sha256(content).hexdigest()))
        catalog.textures=[(replacements.get(record['semantic_id'],tim),record) for tim,record in catalog.textures]
        previews=[geometry['preview']]+[asset['preview'] for asset in geometry['scene_graph']['assets']];seen=set()
        for preview in previews:
            if id(preview) in seen:continue
            seen.add(id(preview));bounds={}
            for index,uv in zip(preview['triangle_materials'],preview['triangle_uvs']):
                if uv is None:continue
                b=bounds.setdefault(index,[255,255,0,0])
                for u,v in uv:b[:]=[min(b[0],u),min(b[1],v),max(b[2],u),max(b[3],v)]
            textures=[]
            for index,material in enumerate(preview['materials']):
                if not material.get('textured') or material.get('source_selector_supported') is False or index not in bounds:
                    old=preview.get('textures',[])
                    textures.append(deepcopy(old[index]) if index<len(old) else dict(associate_material(catalog,material),material_index=index));continue
                textures.append(dict(associate_material(catalog,material,tuple(bounds[index])),material_index=index))
            preview['textures']=textures
        metrics=geometry['metrics'];metrics['texture_output_bytes']=sum(len(t.get('rgba',b''))+len(t.get('stp',b'')) for t in geometry['preview']['textures'])
        metrics['matched_texture_count']=sum(t['status']=='address_match' for t in geometry['preview']['textures'])
        metrics['unsupported_texture_count']=len(geometry['preview']['textures'])-metrics['matched_texture_count']
        geometry['scene_graph']['metrics']['texture_output_bytes']=sum(len(t.get('rgba',b''))+len(t.get('stp',b'')) for a in geometry['scene_graph']['assets'] for t in a['preview']['textures'])
    if geometry['scene_graph']['metrics']['texture_output_bytes']>16*1024*1024:
        raise ProjectError('Current World textures exceed the viewport byte budget')
    geometry['texture_layer']='current'
    geometry['texture_authoring']=dict(schema_version='legaia.worldmap-current-textures.v1',scene=scene,disc_sha256=source['disc_sha256'],edits=edits,scope='exact-layout-TIM-payloads-static-material-association',gameplay_verified=False)
    return geometry
