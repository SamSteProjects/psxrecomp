"""Source-qualified whole walk-kingdom ground, not menu or overview placement.

PIN d6e64c68: kingdom_bundle.rs; field_objects.rs::build_walk_heightfield;
web-viewer/lib.rs::resolve_walk_map_and_lut. Raw retail Y-down coordinates
stay unchanged here; the central renderer owns the display Y flip.
"""
from copy import deepcopy
from hashlib import sha256
import struct

from .core import ImportError, decompress_lzs, parse_scene_assets
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context
from .terrain import decode_terrain
from .textures import (MAX_CATALOG_BYTES, MAX_TEXTURES, TextureCatalog,
                       _pack_members, associate_material, parse_tim)

KINGDOM_BASES = {'map01': 85, 'map02': 244, 'map03': 391}
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_SLOT_BYTES = 4 * 1024 * 1024
MAX_CELLS = 16384
MAX_MATERIALS = 256
MAX_TEXTURE_OUTPUT_BYTES = 16 * 1024 * 1024
LIMITATIONS = [
    'Whole source walk-visible ground; overview MAPDSIP geometry is a separate render mode.',
    'The floor-nibble surface is derived from MAP cells and the kingdom MAN floor LUT, not a captured retail primitive pool or complete collision surface.',
    'No menu coordinate placement, unplaced mesh layout, script-resting-position inference, fog, sky, ocean-plane or sparse landmark geometry is synthesized.',
    'Textures require unique static kingdom TIM address coverage; missing, conflicting or unsupported selectors remain explicit.',
    'Runtime upload order, CLUT animation, deformation, story visibility and gameplay parity remain unverified.',
]


def _scene(scene):
    if not isinstance(scene, str) or scene not in KINGDOM_BASES:
        raise ImportError('World-map geometry supports only map01, map02 and map03 walk kingdoms')


def decode_worldmap_geometry(map_data, man_data, texture_catalog, *, scene, source_record):
    """Pure derived preview; all source locators are qualified by the loader."""
    _scene(scene)
    if not isinstance(man_data, bytes) or not 0x22 <= len(man_data) <= MAX_SLOT_BYTES:
        raise ImportError('World-map MAN floor LUT source is truncated or exceeds its budget')
    if not isinstance(source_record, dict) or not isinstance(texture_catalog, TextureCatalog):
        raise ImportError('World-map geometry requires source metadata and a qualified texture catalog')
    if texture_catalog.scene != scene:
        raise ImportError('World-map texture catalog belongs to another kingdom')
    if source_record.get('disc_sha256', texture_catalog.disc_sha256) != texture_catalog.disc_sha256:
        raise ImportError('World-map texture catalog disc identity differs from its source')
    if isinstance(map_data, bytes) and source_record.get('map_sha256', sha256(map_data).hexdigest()) != sha256(map_data).hexdigest():
        raise ImportError('World-map MAP source hash differs from the preview input')
    man_source = source_record.get('man_slot', {})
    if not isinstance(man_source, dict) or man_source.get('decoded_sha256', sha256(man_data).hexdigest()) != sha256(man_data).hexdigest():
        raise ImportError('World-map MAN source hash differs from the preview input')
    floor_lut = list(struct.unpack_from('<16h', man_data, 2))
    preview = decode_terrain(map_data, floor_lut)
    if not preview['cells'] or len(preview['cells']) > MAX_CELLS or len(preview['materials']) > MAX_MATERIALS:
        raise ImportError('World-map ground is empty or exceeds cell/material budgets')
    uv_bounds = {}
    for material, points in zip(preview['triangle_materials'], preview['triangle_uvs']):
        if points is None:
            continue
        bounds = uv_bounds.setdefault(material, [255, 255, 0, 0])
        for u, v in points:
            bounds[:] = [min(bounds[0], u), min(bounds[1], v), max(bounds[2], u), max(bounds[3], v)]
    textures, texture_bytes = [], 0
    for index, material in enumerate(preview['materials']):
        if material['source_selector_supported']:
            item = associate_material(texture_catalog, material, tuple(uv_bounds[index]))
        else:
            item = dict(status='unsupported', reason='Source tile or page selector is unsupported; no fallback atlas is invented')
        texture_bytes += len(item.get('rgba', b'')) + len(item.get('stp', b''))
        if texture_bytes > MAX_TEXTURE_OUTPUT_BYTES:
            raise ImportError('World-map decoded texture output exceeds its byte budget')
        textures.append(dict(item, material_index=index))
    preview['textures'] = textures
    preview['objects'] = [dict(object_index=0, vertex_start=0, vertex_count=len(preview['vertices']),
                               triangle_start=0, triangle_count=len(preview['triangles']))]
    preview['bounds'] = {key: [fn(vertex[axis] for vertex in preview['vertices']) for axis in range(3)]
                         for key, fn in (('min', min), ('max', max))}
    preview['posed'] = False
    preview['source_record'] = deepcopy(source_record)
    preview['limitations'] = list(LIMITATIONS)
    preview['texture_catalog'] = texture_catalog.metadata()
    matched = sum(item['status'] == 'address_match' for item in textures)
    return dict(schema_version='legaia.worldmap-geometry.v1',
                semantic_id=f'asset://{scene}/worldmap/walk-ground', scene=scene,
                reference_commit=REFERENCE_COMMIT, preview=preview,
                source_record=deepcopy(source_record), floor_height_lut=floor_lut,
                metrics=dict(cell_count=len(preview['cells']), vertex_count=len(preview['vertices']),
                             triangle_count=len(preview['triangles']), material_count=len(textures),
                             matched_texture_count=matched, unsupported_texture_count=len(textures)-matched,
                             texture_output_bytes=texture_bytes),
                source_xyz='[col*128, -MAN.floor_lut[MAP.floor_nibble], row*128]',
                display_conversion='[x,-y,z] only at renderer boundary',
                gameplay_verified=False, limitations=list(LIMITATIONS))


def _kingdom_table(archive, base):
    candidates = []
    for index in (base, base + 1):
        entry = archive.entry(index)
        if entry.size_sectors * archive.SECTOR > MAX_SOURCE_BYTES:
            raise ImportError('World-map kingdom carrier exceeds its source byte budget')
        raw = archive.read_entry(entry, extended=True)
        indexed = archive.read_entry(entry, extended=False)
        if len(raw) > MAX_SOURCE_BYTES:
            raise ImportError('World-map kingdom carrier exceeds its source byte budget')
        for offset in range(0, len(indexed) - 63, 0x800):
            bundle = parse_scene_assets(indexed, index, offset)
            if bundle is None or len(bundle.descriptors) != 7:
                continue
            if tuple(item.type_byte for item in bundle.descriptors) != tuple(range(1, 8)):
                continue
            if any(item.size <= 0 or item.size > MAX_SLOT_BYTES for item in bundle.descriptors):
                raise ImportError('World-map kingdom slot has an unsupported decoded size')
            offsets = [item.data_offset for item in bundle.descriptors]
            if offsets[0] != 0x40 or any(a >= b for a, b in zip(offsets, offsets[1:])):
                raise ImportError('World-map kingdom slot pointers overlap or are unordered')
            if offset + offsets[-1] >= len(raw):
                raise ImportError('World-map kingdom slot pointer exceeds its carrier')
            physical = entry.start_lba * archive.SECTOR + offset
            candidates.append((physical, index, offset, bundle, raw))
    if not candidates or len({item[0] for item in candidates}) != 1:
        raise ImportError('World-map kingdom requires one uniquely qualified physical seven-slot table')
    # Overlapping indexed PROT entries can expose the same physical table.
    # Prefer its bare entry-head view, retaining the exact chosen locator.
    candidates.sort(key=lambda item: (item[2] != 0, item[1]))
    return candidates[0]


def _slot(bundle, raw, index):
    descriptor = bundle.descriptors[index]
    at = bundle.table_offset + descriptor.data_offset
    end = min([bundle.table_offset + item.data_offset for item in bundle.descriptors
               if item.data_offset > descriptor.data_offset] + [len(raw)])
    if not bundle.table_offset + 0x40 <= at < end <= len(raw):
        raise ImportError('World-map kingdom slot exceeds its bounded carrier span')
    decoded, consumed = decompress_lzs(raw[at:end], descriptor.size)
    if len(decoded) != descriptor.size or not 0 < consumed <= end-at:
        raise ImportError('World-map kingdom slot does not match its declared span')
    return decoded, dict(slot_index=index, descriptor_type=descriptor.type_byte,
                         decoded_byte_length=len(decoded), decoded_sha256=sha256(decoded).hexdigest(),
                         compressed_stream_offset=at, compressed_span_end=end,
                         compressed_bytes_consumed=consumed,
                         compressed_sha256=sha256(raw[at:at+consumed]).hexdigest())


def load_worldmap_geometry(disc, scene='map01'):
    """Load the proven MAP, kingdom MAN LUT and kingdom atlas; no disc export."""
    _scene(scene)
    base = KINGDOM_BASES[scene]
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        map_index = base - 2
        if start != map_index or not start <= base < base + 1 < end:
            raise ImportError('World-map scene range differs from the pinned kingdom carrier mapping')
        map_entry = archive.entry(map_index)
        if map_entry.size_sectors * archive.SECTOR != 0x12000:
            raise ImportError('World-map walk MAP lacks the exact full source footprint')
        map_data = archive.read_entry(map_entry, extended=True)
        if len(map_data) != 0x12000:
            raise ImportError('World-map walk MAP is truncated')
        physical, index, offset, bundle, raw = _kingdom_table(archive, base)
        man, man_source = _slot(bundle, raw, 2)
        tim_pack, tim_source = _slot(bundle, raw, 0)
        source = dict(disc_sha256=digest, iso_file='PROT.DAT', scene=scene,
                      map_entry_index=map_index, map_byte_length=len(map_data),
                      map_sha256=sha256(map_data).hexdigest(),
                      kingdom_base_entry_index=base, bundle_entry_index=index,
                      bundle_table_offset=offset, bundle_physical_byte_offset=physical,
                      bundle_byte_length=len(raw), bundle_sha256=sha256(raw).hexdigest(),
                      man_slot=man_source, texture_slot=tim_source,
                      floor_lut_byte_offset=2, floor_lut_byte_length=32,
                      floor_lut_sha256=sha256(man[2:34]).hexdigest())
        catalog = TextureCatalog(scene, digest)
        total = 0
        for slot, (at, stop) in enumerate(_pack_members(tim_pack, False)):
            if tim_pack[at:at+4] != b'\x10\0\0\0':
                catalog.diagnostics.append(f'Kingdom texture member {slot}: unsupported non-TIM payload')
                continue
            try:
                tim = parse_tim(tim_pack[at:stop])
            except ImportError as error:
                catalog.diagnostics.append(f'Kingdom texture member {slot}: {error}')
                continue
            total += tim.byte_length
            if total > MAX_CATALOG_BYTES or len(catalog.textures) >= MAX_TEXTURES:
                raise ImportError('World-map kingdom texture catalog exceeds its byte/count budget')
            catalog.textures.append((tim, dict(semantic_id=f'texture://{scene}/kingdom/{slot:04d}',
                                               prot_entry_index=index, descriptor_index=0,
                                               pack_slot=slot, byte_offset=at, byte_length=tim.byte_length,
                                               decoded_member_sha256=sha256(tim_pack[at:at+tim.byte_length]).hexdigest())))
        catalog.diagnostics.append('Only source kingdom atlas TIMs are associated; non-TIM CLUT strips and runtime palette walkers are not synthesized.')
        return decode_worldmap_geometry(map_data, man, catalog, scene=scene, source_record=source)
