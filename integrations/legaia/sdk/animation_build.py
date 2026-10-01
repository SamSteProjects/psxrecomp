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
    if source.get('source_kind') == 'raw_streaming_anm':
        from importer.prot_layout import locate_physical_span
        from importer.streaming_man import replace_streaming_payload, streaming_chunks
        from .project import ProjectError
        start = entry.start_lba * 2048
        span = locate_physical_span(archive, start)
        if span['entry_index'] != entry.index or span['offset_within_span'] != 0:
            raise ProjectError('Streaming animation requires its unique physical owner')
        body = archive.image.read_user(archive.node.extent_lba, start, span['byte_length'], archive.node.size)
        offset = source['payload_offset']
        original = body[offset:offset + source['payload_byte_length']]
        if original != catalog._body or sha256(original).hexdigest() != source['payload_sha256']:
            raise ProjectError('Streaming animation preimage differs from the verified bank')
        checked, chunk_audit = replace_streaming_payload(body, sha256(body).hexdigest(),
                                                        source['chunk_header_offset'], source['payload_sha256'], changed)
        if chunk_audit['type_byte'] != 5:
            raise ProjectError('Streaming animation target is not a type-5 chunk')
        overlays = [dict(offset=archive.node.extent_lba * 2048 + start + offset,
                         payload=checked[offset:offset + len(changed)], expected_sha256=sha256(original).hexdigest())]
        patches, carriers = archive_overlay_patches(archive, overlays)
        chunks, _ = streaming_chunks(body)
        index = next(i for i, chunk in enumerate(chunks) if chunk['header_offset'] == source['chunk_header_offset'])
        for carrier in carriers:
            carrier['streaming_binding'] = dict(chunk_index=index, type_byte=5)
        return patches, dict(changes=changes, carriers=carriers, source_kind='raw_streaming_anm')
    body=archive.read_entry(entry)
    offset=source['compressed_stream_offset']
    original=body[offset:offset+source['compressed_bytes_consumed']]
    replacement,sizes=serialize_lzs_decoded(original,len(catalog._body),changed,scene+' animation')
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
    return patches,dict(changes=changes,carriers=carriers,compression=sizes)
