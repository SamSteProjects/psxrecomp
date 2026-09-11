"""Source-bound metadata-only actor candidate inspection; no project writes."""
from hashlib import sha256
from .core import ImportError, find_scene_bundle, decompress_lzs
from .pipeline import _disc_context, _bounded_scene_range, REFERENCE_COMMIT
from .man_actor_structure import append_actor_candidate
from .man_container import encode_man_candidate
from .prot_layout import inspect_entry_footprint


def inspect_actor_candidate(disc, scene: str, donor_record_index: int) -> dict:
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
        candidate, actor_audit = append_actor_candidate(source, sha256(source).hexdigest(), donor_record_index)
        _, container_audit = encode_man_candidate(raw, sha256(raw).hexdigest(),
                                                  bundle.table_offset, sha256(source).hexdigest(),
                                                  candidate, allow_growth=True)
        return dict(schema_version='legaia.actor-candidate-inspection.v1',
                    scene=scene, disc_sha256=digest, reference_commit=REFERENCE_COMMIT,
                    actor=actor_audit, container=container_audit,
                    archive=inspect_entry_footprint(archive, bundle.entry_index),
                    build_ready=False, read_only=True)
