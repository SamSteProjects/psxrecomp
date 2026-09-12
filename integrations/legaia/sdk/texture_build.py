"""Source-bound scene texture replacements for pre-relocation archive composition."""
from hashlib import sha256
from importer.texture_authoring import load_texture_authoring_context
from importer.pipeline import import_scene
from .project import ProjectError, digest


def prepare_texture_patches(project, scene_id, bindings, archive):
    document=project.imports[scene_id]
    scene=document['scene']['name']
    if digest(import_scene(project.disc_path,scene))!=digest(document):
        raise ProjectError('Texture export source metadata differs from retail')
    context=load_texture_authoring_context(project.disc_path,scene)
    replacements={}
    for identifier,binding in bindings.items():
        if not isinstance(binding,dict) or binding.get('source_scene_id')!=scene_id or binding.get('format')!='tim':
            raise ProjectError('Texture export requires a same-scene TIM binding')
        payload=project.read_texture_replacement(binding)
        if len(payload)!=binding['byte_length'] or sha256(payload).hexdigest()!=binding['asset_sha256']:
            raise ProjectError('Texture replacement differs from its saved binding')
        replacements[identifier]=payload
    overlays,audit=context.patch(replacements)
    patches,carriers=archive_overlay_patches(archive,overlays)
    return patches,dict(changes=audit,carriers=carriers)


def archive_overlay_patches(archive,overlays):
    """Convert verified disc overlays into bounded archive carrier patches."""
    patches=[]
    carriers=[]
    for overlay in overlays:
        offset=overlay['offset']-archive.node.extent_lba*2048
        payload=overlay['payload']
        if offset<0 or offset+len(payload)>archive.node.size:
            raise ProjectError('Asset replacement lies outside the rebuilt PROT archive')
        original=archive.image.read_user(archive.node.extent_lba,offset,len(payload),archive.node.size)
        if sha256(original).hexdigest()!=overlay['expected_sha256']:
            raise ProjectError('Asset archive preimage differs from the verified carrier')
        patches.append(dict(offset=offset,payload=payload,expected_sha256=overlay['expected_sha256']))
        from importer.prot_layout import locate_physical_span
        span=locate_physical_span(archive,offset)
        if span['offset_within_span']+len(payload)>span['byte_length']:
            raise ProjectError('Asset carrier crosses a physical archive boundary')
        carriers.append(dict(map_entry_index=span['entry_index'],relative_offset=span['offset_within_span'],
                             byte_length=len(payload),result_sha256=sha256(payload).hexdigest()))
    return patches,carriers
