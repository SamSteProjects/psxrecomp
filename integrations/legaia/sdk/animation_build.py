"""Existing-channel animation edits as source-bound archive patches."""
from hashlib import sha256
from importer.scene_animation import load_scene_actor_animation_catalog
from importer.serialization import serialize_lzs_decoded
from .texture_build import archive_overlay_patches


def prepare_animation_patches(project,scene_id,bindings,archive):
    scene=project.imports[scene_id]['scene']['name']
    catalog=load_scene_actor_animation_catalog(project.disc_path,scene)
    changed,changes=catalog.authored_bank(bindings)
    if not changes:
        return [],dict(changes=[],carriers=[])
    source=catalog._source
    entry=archive.entry(source['prot_entry_index'])
    body=archive.read_entry(entry)
    offset=source['compressed_stream_offset']
    original=body[offset:offset+source['compressed_bytes_consumed']]
    replacement,_=serialize_lzs_decoded(original,len(catalog._body),changed,scene+' animation')
    overlays=[dict(offset=(archive.node.extent_lba+entry.start_lba)*2048+offset,
                   payload=replacement,expected_sha256=sha256(original).hexdigest())]
    patches,carriers=archive_overlay_patches(archive,overlays)
    from importer.prot_layout import locate_physical_span
    table=locate_physical_span(archive,entry.start_lba*2048+source['scene_table_offset'])
    for carrier in carriers:
        if carrier['map_entry_index']!=table['entry_index']:
            from .project import ProjectError
            raise ProjectError('Animation descriptor and carrier have different physical owners')
        carrier['descriptor_binding']=dict(table_offset=table['offset_within_span'],
            index=source['descriptor_index'],type=source['descriptor_type'])
    return patches,dict(changes=changes,carriers=carriers)
