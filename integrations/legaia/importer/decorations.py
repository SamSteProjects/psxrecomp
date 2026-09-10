"""Source field decoration sweep, distinct from placed actors and walk ground.

Pinned field_render.rs::resolve_field_terrain_draws selects 0x2000 cells
and excludes placed records. This is not the world-map 0x1000 sweep.
"""
from hashlib import sha256
import struct

from .core import ImportError
from .field_map import _validate_scene
from .pipeline import REFERENCE_COMMIT


def decode_field_decorations(data: bytes, floor_lut: list[int], scene: str) -> dict:
    _validate_scene(scene)
    if not isinstance(data, bytes) or len(data) != 0x12000:
        raise ImportError("decorations require the complete field MAP")
    if len(floor_lut) != 16 or any(type(v) is not int or not -32768 <= v <= 32767 for v in floor_lut):
        raise ImportError("decorations require sixteen signed floor heights")
    placements = []
    for index in range(128 * 128):
        cell = struct.unpack_from("<H", data, 0x8000 + index * 2)[0]
        record = cell & 511
        offset = record * 32
        flags = struct.unpack_from("<H", data, offset + 18)[0]
        if not cell & 0x2000 or flags & 4:
            continue
        x, y, z = struct.unpack_from("<3h", data, offset)
        col, row = index % 128, index // 128
        tier = data[0x4000 + index] & 15
        placements.append({
            "semantic_id": f"environment://{scene}/field-map/decorations/{index:05d}",
            "name": f"MAP decoration {record} at {col},{row}",
            "object_record_index": record, "flags": flags,
            "pack_index": None if record in (1, 2, 3) else struct.unpack_from("<H", data, offset + 16)[0],
            "tile": {"x": col, "z": row},
            "imported_transform": {
                "position": {"x": col * 128 + x + 64, "y": -floor_lut[tier] + y,
                             "z": row * 128 - z + 64},
                "rotation_psx": dict(zip("xyz", struct.unpack_from("<3H", data, offset + 8))),
                "coordinate_system": "retail_field_y_down"},
            "source_record": {"grid_byte_offset": 0x8000 + index * 2,
                              "object_byte_offset": offset,
                              "object_sha256": sha256(data[offset:offset + 32]).hexdigest()},
        })
    return {"schema_version": "legaia.field-decorations.v1", "scene": scene,
            "reference_commit": REFERENCE_COMMIT, "map_sha256": sha256(data).hexdigest(),
            "placements": placements,
            "limitations": ["Source field sweep only; runtime window and script visibility are not evaluated.",
                            "Mesh resolution and rendering are separate steps."]}
