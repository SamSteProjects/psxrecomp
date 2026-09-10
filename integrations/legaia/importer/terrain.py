"""Source heightfield preview from MAP walk-visible cells.

Pinned field_objects.rs::build_walk_heightfield supplies the corner and UV
conventions. No guessed grass texture replaces missing source selectors.
This is a reference surface, not the full retail ground emitter/collision mesh.
"""
import struct
from .core import ImportError


def decode_terrain(data: bytes, floor_lut: list[int]) -> dict:
    if not isinstance(data, bytes) or len(data) != 0x12000:
        raise ImportError("terrain requires a complete field MAP")
    if (not isinstance(floor_lut, list) or len(floor_lut) != 16 or
            any(type(v) is not int or not -32768 <= v <= 32767 for v in floor_lut)):
        raise ImportError("terrain requires sixteen signed MAN floor heights")
    result = {"vertices": [], "triangles": [], "triangle_uvs": [],
              "triangle_colors": [], "triangle_materials": [], "materials": [], "cells": [],
              "coordinate_system": "retail_field_y_down", "objects": [],
              "limitations": ["Source walk-visible cell surface; no script visibility or terrain deformation.",
                              "Corner heights use the MAN floor LUT; collision ramp overrides are not a visual mesh prescription.",
                              "Missing texture selectors remain unsupported; no fallback atlas is invented."]}
    materials = {}
    for index in range(16384):
        word = struct.unpack_from("<H", data, 0x8000 + index * 2)[0]
        if not word & 0x1000:
            continue
        col, row, record = index % 128, index // 128, word & 511
        offset = record * 32
        tile, page = data[offset + 20:offset + 22]
        clut = struct.unpack_from("<H", data, offset + 22)[0]
        supported = page != 0 and tile < 64
        key = (page, clut, supported)
        if key not in materials:
            materials[key] = len(result["materials"])
            result["materials"].append({"textured": supported, "tpage": page, "clut": clut,
                                        "semi_transparent": False, "source_selector_supported": supported})
        base = len(result["vertices"])
        for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
            tier = data[0x4000 + min(row + dz, 127) * 128 + min(col + dx, 127)] & 15
            result["vertices"].append([(col + dx) * 128, -floor_lut[tier], (row + dz) * 128])
        u, v = (tile % 8) * 32, (tile // 8) * 32
        uvs = [[u, v + 31], [u + 31, v + 31], [u, v], [u + 31, v]]
        for corners in ((0, 1, 2), (1, 3, 2)):
            result["triangles"].append([base + i for i in corners])
            result["triangle_uvs"].append([uvs[i] for i in corners] if supported else None)
            result["triangle_colors"].append([[128, 128, 128] for _ in corners])
            result["triangle_materials"].append(materials[key])
        result["cells"].append({"cell_index": index, "object_record_index": record,
                                "vertex_start": base, "atlas_tile": tile,
                                "source_selector_supported": supported})
    return result


def load_terrain(disc, scene: str) -> dict:
    from .environment import load_environment_placements
    from .pipeline import _disc_context
    from hashlib import sha256
    with _disc_context(disc) as (_, digest, _, archive):
        environment = load_environment_placements(disc, scene)
        source = environment["source_record"]
        data = archive.read_entry(archive.entry(source["map_entry_index"]), extended=True)
        if digest != source["disc_sha256"] or sha256(data).hexdigest() != source["map_sha256"]:
            raise ImportError("terrain source changed during resolution")
        result = decode_terrain(data, environment["floor_height_lut"])
        result["source_record"] = source
        return result
