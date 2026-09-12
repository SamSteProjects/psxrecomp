"""Source-bound metadata-only actor candidate inspection; no project writes."""
from hashlib import sha256
from .core import ImportError, find_scene_bundle, decompress_lzs
from .pipeline import _disc_context, _bounded_scene_range, REFERENCE_COMMIT, import_scene
from .man_actor_structure import append_actor_candidate
from .man_container import encode_man_candidate
from .prot_layout import inspect_entry_footprint, locate_physical_span


def inspect_actor_candidate(disc, scene: str, donor_record_index: int, *, position: dict | None = None) -> dict:
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        bundle, raw = find_scene_bundle(archive, start, end)
        descriptors = [d for d in bundle.descriptors if d.type_byte == 3 and d.size]
        if len(descriptors) != 1:
            raise ImportError('Actor candidate requires one MAN descriptor')
        descriptor = descriptors[0]
        offset = bundle.table_offset+descriptor.data_offset
        limit = min([bundle.table_offset+d.data_offset for d in bundle.descriptors
                     if d.data_offset > descriptor.data_offset]+[len(raw)])
        if not 0 <= offset < limit <= len(raw):
            raise ImportError('Actor candidate MAN span exceeds source bounds')
        source, _ = decompress_lzs(raw[offset:limit], descriptor.size)
        candidate, actor_audit = append_actor_candidate(source, sha256(source).hexdigest(), donor_record_index,
                                                       position=position)
        document = import_scene(disc, scene)
        donor = next(a for a in document['actors'] if a['source_record']['record_index'] == donor_record_index)
        dependencies = dict(actor_semantic_id=donor['semantic_id'],
                            model=donor['model_reference'],
                            initial_animation_id=donor['placement_fields']['animation_id'],
                            animations=[], animation_status='unavailable')
        from .animation_catalog import load_animation_asset_catalog
        try:
            catalog = load_animation_asset_catalog(disc, scene)
            dependencies['animations'] = [dict(semantic_id=a['semantic_id'],
                                                frame_count=a['frame_count'], channel_count=a['channel_count'])
                                           for a in catalog['assets']
                                           if donor['semantic_id'] in a['actor_semantic_ids']]
            if dependencies['animations']:
                dependencies['animation_status'] = 'verified_initial_scene_binding'
        except ImportError as exc:
            dependencies['animation_reason'] = str(exc)
        try:
            absolute_table = archive.entry(bundle.entry_index).start_lba*archive.SECTOR+bundle.table_offset
            physical = locate_physical_span(archive, absolute_table)
            physical_bytes = archive.image.read_user(archive.node.extent_lba, physical['byte_offset'],
                                                      physical['byte_length'], archive.node.size)
            encoded, container_audit = encode_man_candidate(physical_bytes, sha256(physical_bytes).hexdigest(),
                                                      physical['offset_within_span'], sha256(source).hexdigest(),
                                                      candidate, allow_growth=True)
            container_audit['supported'] = True
            container_audit['physical_source'] = physical
            container_audit['sector_aligned_candidate_bytes'] = (len(encoded)+archive.SECTOR-1)//archive.SECTOR*archive.SECTOR
            container_audit['required_sector_growth'] = (len(encoded)+archive.SECTOR-1)//archive.SECTOR-physical['byte_length']//archive.SECTOR
        except ImportError as exc:
            container_audit = dict(supported=False, reason=str(exc), build_ready=False,
                                   growth_bytes=None)
        return dict(schema_version='legaia.actor-candidate-inspection.v1',
                    scene=scene, disc_sha256=digest, reference_commit=REFERENCE_COMMIT,
                    actor=actor_audit, container=container_audit,
                    donor_dependencies=dependencies,
                    archive=inspect_entry_footprint(archive, bundle.entry_index),
                    build_ready=False, read_only=True)
