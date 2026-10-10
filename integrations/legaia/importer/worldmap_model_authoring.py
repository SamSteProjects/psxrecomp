"""Native kingdom TMD source ownership for the shared model authoring codecs.

Uses the pinned seven-slot table and pack pointers already used by the World
viewport. No authored storage, compression path or runtime visibility is added.
"""
import re
from hashlib import sha256
from .core import ImportError
from .pipeline import _disc_context, _bounded_scene_range
from .worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from .worldmap_placements import _pack_spans
from .model_json import export_shape_json


def model_identity(identifier):
    match = re.fullmatch(r'asset://(map0[123])/worldmap/models/([0-9]{4})', identifier) if isinstance(identifier, str) else None
    return (match[1], int(match[2])) if match else None


def read_worldmap_model(disc, identifier):
    identity = model_identity(identifier)
    if not identity:
        raise ImportError('World TMD source requires a canonical native model identity')
    scene, slot = identity
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        base = KINGDOM_BASES[scene]
        if start != base-2 or not start <= base < base+1 < end:
            raise ImportError('World model source differs from the pinned kingdom range')
        _, index, offset, bundle, raw = _kingdom_table(archive, base)
        if offset != 0 or bundle.table_offset != 0:
            raise ImportError('World TMD source requires the entry-head kingdom table')
        pack, source = _slot(bundle, raw, 1)
        spans = _pack_spans(pack)
        if not 0 <= slot < len(spans):
            raise ImportError('World TMD member is outside its native pack')
        at, stop = spans[slot]
        content = pack[at:stop]
        shape = export_shape_json(content)
        source.update(disc_sha256=digest, prot_entry_index=index, bundle_table_offset=offset,
                      pack_slot=slot, decoded_member_offset=at, decoded_member_span_end=stop,
                      decoded_member_sha256=sha256(content).hexdigest())
        return content, shape, source
