"""Imported field environment placements, separate from MAN actors.

Pinned evidence: asset/field_objects.rs::parse_placements and
engine-core/scene/scene_ty.rs::field_floor_height_lut. This enumerates both
placed-object sweeps; it does not claim runtime window visibility or bindings.
Ground/decorations are different consumers and are not included here.
"""
from hashlib import sha256
import struct

from .core import ImportError, decompress_lzs, find_scene_bundle, parse_man
from .field_map import _validate_scene
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context


def decode_environment_placements(data: bytes, man: bytes, scene: str) -> dict:
    _validate_scene(scene)
    if not isinstance(data, bytes) or len(data) != 0x12000:
        raise ImportError("environment requires the complete 0x12000-byte field MAP")
    parse_man(man, scene)
    floor_lut = struct.unpack_from("<16h", man, 2)
    placements, excluded = [], []
    for cell_index in range(128 * 128):
        col, row = cell_index % 128, cell_index // 128
        grid_offset = 0x8000 + cell_index * 2
        cell = struct.unpack_from("<H", data, grid_offset)[0]
        record_index = cell & 0x1FF
        offset = record_index * 32
        flags = struct.unpack_from("<H", data, offset + 0x12)[0]
        if not flags & 4:
            continue
        x, y, z, dx, dz = struct.unpack_from("<hhhbb", data, offset)
        anchor_x, anchor_z = col + dx, row + dz
        identifier = f"environment://{scene}/field-map/cells/{cell_index:05d}"
        if not 0 <= anchor_x < 128 or not 0 <= anchor_z < 128:
            excluded.append({"semantic_id": identifier, "reason": "footprint_anchor_outside_grid"})
            continue
        anchor_cell = struct.unpack_from("<H", data, 0x8000 + (anchor_z * 128 + anchor_x) * 2)[0]
        # Reference implementation reads the placement cell, despite its
        # floor_nibble field comment saying anchor. Preserve that distinction.
        tier = data[0x4000 + cell_index] & 15
        rotations = struct.unpack_from("<3H", data, offset + 8)
        placements.append({
            "semantic_id": identifier, "asset_kind": "environment_placement",
            "name": f"MAP object {record_index} at {col},{row}",
            "tile": {"x": col, "z": row}, "object_record_index": record_index,
            "source_record": {"grid_byte_offset": grid_offset, "grid_byte_length": 2,
                              "object_byte_offset": offset, "object_byte_length": 32,
                              "object_sha256": sha256(data[offset:offset + 32]).hexdigest()},
            "imported_transform": {"position": {"x": col * 128 + x + 64,
                                                   "y": -floor_lut[tier] + y,
                                                   "z": row * 128 - z + 64},
                                   "rotation_psx": dict(zip("xyz", rotations)),
                                   "coordinate_system": "retail_field_y_down"},
            "floor": {"tier": tier, "lut_value": floor_lut[tier], "record_y_offset": y,
                      "sample": "placement_cell_not_footprint_anchor"},
            "footprint_anchor": {"x": anchor_x, "z": anchor_z, "cell_word": anchor_cell,
                                 "bind_owned": bool(anchor_cell & 0x400)},
            "flags": flags, "mesh_drawn_flag": bool(flags & 2),
            "pack_index": None if record_index in (1, 2, 3) else struct.unpack_from("<H", data, offset + 16)[0],
            "model_resolution": "not_resolved", "animation_binding": "not_resolved",
        })
    return {"schema_version": "legaia.environment-placements.v1", "scene": scene,
            "reference_commit": REFERENCE_COMMIT, "placements": placements,
            "excluded": excluded, "floor_height_lut": list(floor_lut),
            "limitations": ["Placed-object source baseline only; ground and decorations are separate layers.",
                            "Mesh pack and MAN partition-0 animation bindings are not resolved here.",
                            "Source placements do not imply current runtime visibility or spawn state."]}


def load_environment_placements(disc, scene: str) -> dict:
    """Read source-controlled locations; never accept client-provided offsets."""
    _validate_scene(scene)
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        entry = archive.entry(start)
        if entry.size_sectors * archive.SECTOR != 0x12000:
            raise ImportError("scene does not have the supported full field MAP footprint")
        data = archive.read_entry(entry, extended=True)
        bundle, raw = find_scene_bundle(archive, start, end)
        candidates = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(candidates) != 1:
            raise ImportError("environment requires one unambiguous scene MAN descriptor")
        descriptor = candidates[0]
        if descriptor.size > 4 * 1024 * 1024:
            raise ImportError("environment MAN exceeds decoded byte bound")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
            raise ImportError("environment MAN descriptor aliases another resource")
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not bundle.table_offset + 8 + len(bundle.descriptors) * 8 <= offset < ceiling <= len(raw):
            raise ImportError("environment MAN stream exceeds descriptor boundaries")
        man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
        result = decode_environment_placements(data, man, scene)
        result["source_record"] = {"disc_sha256": digest, "iso_file": "PROT.DAT",
                                   "map_entry_index": entry.index, "map_sha256": sha256(data).hexdigest(),
                                   "map_byte_length": len(data), "man_entry_index": bundle.entry_index,
                                   "man_descriptor_index": descriptor.index,
                                   "man_stream_offset": offset, "man_stream_bytes_consumed": consumed,
                                   "man_sha256": sha256(man).hexdigest()}
        return result
