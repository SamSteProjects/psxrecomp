"""Bounded, independent Legaia TMD preview decoder.

Format evidence: pinned Andrew reference crates/tmd/{lib,descriptor,legaia_prims}.rs,
retail renderer FUN_8002735C/FUN_80029888 and descriptor table DAT_8007326C.
No dependency on the reference implementation. Geometry is private retail output;
unlike scene metadata, it must not be committed or published as a fixture.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

from .core import ImportError, TMD_MAGIC, decompress_lzs, parse_lzs_sections
from .pipeline import REFERENCE_COMMIT, _disc_context

MAX_MODEL_BYTES = 4 * 1024 * 1024
MAX_OBJECTS = 1024
MAX_VERTICES = 100_000
MAX_PRIMITIVES = 100_000


def _range(data: bytes, offset: int, length: int, label: str) -> None:
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ImportError(f"{label} span [{offset}, {offset + length}) exceeds model size {len(data)}")


def _layout(flags: int) -> tuple[int, int, bool, bool, int | None, bool]:
    """Topology, vertex offset, texture/color placement from retail mode rows."""
    if not 0x10 <= flags <= 0x27:
        raise ImportError(f"unsupported ETMD/primitive group flags 0x{flags:04X}")
    row = (flags - 0x10) // 4
    quad = bool(flags & 2)
    corners = 4 if quad else 3
    textured = row in (0, 1, 4, 5)
    gouraud = row in (1, 3, 5)
    vertex_offset = ((12, 12, 4, 16, 16, 28) if quad
                     else (14, 12, 4, 12, 14, 22))[row]
    # Lit rows carry normals, not baked colors; texture block begins at zero.
    texture_offset = (0 if row < 2 else (corners * 4 if gouraud else 4)) if textured else None
    baked_colors = row >= 2
    return corners, vertex_offset, textured, gouraud, texture_offset, baked_colors


def decode_tmd(data: bytes) -> dict[str, Any]:
    """Decode a bare relative-pointer Legaia TMD; reject unknown packet modes.

    Positions remain in object-local retail integer coordinates. The object
    table's final word is retained as opaque metadata; no skeletal assembly or
    pose is inferred from it. Every returned face has checked vertex indices.
    """
    if len(data) > MAX_MODEL_BYTES:
        raise ImportError(f"model exceeds {MAX_MODEL_BYTES}-byte preview limit")
    _range(data, 0, 12, "TMD header")
    magic, header_flags, object_count = struct.unpack_from("<III", data)
    if magic != TMD_MAGIC or header_flags != 0:
        raise ImportError(f"unsupported TMD/ETMD header magic=0x{magic:08X} flags=0x{header_flags:08X}")
    if not 1 <= object_count <= MAX_OBJECTS:
        raise ImportError(f"unsupported TMD object count {object_count}")
    table_end = 12 + object_count * 28
    _range(data, 12, object_count * 28, "TMD object table")
    result: dict[str, Any] = {
        "schema_version": "legaia.model-preview.v1",
        "coordinate_system": "retail_tmd_object_local", "posed": False,
        "vertices": [], "triangles": [], "triangle_colors": [],
        "triangle_uvs": [], "triangle_materials": [], "objects": [],
        "materials": [], "diagnostics": [],
        "reference_commit": REFERENCE_COMMIT,
    }
    material_ids: dict[tuple, int] = {}
    primitive_total = 0
    for index in range(object_count):
        vert, vertex_count, normal, normal_count, prim, claimed, opaque = struct.unpack_from(
            "<7I", data, 12 + index * 28)
        vert += 12
        normal += 12
        prim += 12
        if len(result["vertices"]) + vertex_count > MAX_VERTICES:
            raise ImportError(f"model exceeds {MAX_VERTICES}-vertex preview limit")
        for offset, count, label in [(vert, vertex_count, "vertices"), (normal, normal_count, "normals")]:
            _range(data, offset, count * 8, f"object {index} {label}")
            if count and offset < table_end:
                raise ImportError(f"object {index} {label} overlap the object table")
        if prim < table_end:
            raise ImportError(f"object {index} primitives overlap the object table")
        end = min([start for start, count in [(vert, vertex_count), (normal, normal_count)] if count] or [len(data)])
        _range(data, prim, end - prim, f"object {index} primitives")
        first_vertex = len(result["vertices"])
        first_triangle = len(result["triangles"])
        result["vertices"].extend([list(struct.unpack_from("<hhh", data, vert + n * 8))
                                  for n in range(vertex_count)])
        position = prim
        object_primitives = 0
        while position + 4 <= end:
            count, flags = struct.unpack_from("<HH", data, position)
            if count == flags == 0:
                break
            _range(data, position, 8, f"object {index} group header")
            if position + 8 > end:
                raise ImportError(f"object {index} has a truncated primitive group")
            _olen, ilen, _flag, mode = struct.unpack_from("<4B", data, position + 4)
            stride = ilen * 4
            if not count or not stride:
                raise ImportError(f"object {index} has an empty non-terminator primitive group")
            if primitive_total + count > MAX_PRIMITIVES:
                raise ImportError(f"model exceeds {MAX_PRIMITIVES}-primitive preview limit")
            next_group = position + 8 + (count + 1) * stride
            if next_group > end:
                raise ImportError(f"object {index} primitive group exceeds its section")
            corners, vi_offset, textured, gouraud, uv_offset, baked = _layout(flags)
            if vi_offset + corners * 2 > stride:
                raise ImportError(f"object {index} vertex indices exceed primitive stride")
            if uv_offset is not None and uv_offset + (12 if corners == 4 else 10) > stride:
                raise ImportError(f"object {index} texture fields exceed primitive stride")
            color_words = corners if gouraud else 1
            if baked and color_words * 4 > stride:
                raise ImportError(f"object {index} color fields exceed primitive stride")
            for primitive in range(count):
                base = position + 8 + primitive * stride
                raw_indices = struct.unpack_from(f"<{corners}H", data, base + vi_offset)
                if any(raw % 8 or raw // 8 >= vertex_count for raw in raw_indices):
                    raise ImportError(f"object {index} primitive {primitive} has invalid vertex offsets")
                indices = [first_vertex + raw // 8 for raw in raw_indices]
                colors = ([list(data[base + n * 4:base + n * 4 + 3]) for n in range(color_words)]
                          if baked else [[128, 128, 128]] * color_words)
                if not gouraud:
                    colors *= corners
                uvs = None
                clut = tpage = None
                if uv_offset is not None:
                    uv_base = base + uv_offset
                    uvs = [list(data[uv_base + delta:uv_base + delta + 2])
                           for delta in (0, 4, 8, 10)[:corners]]
                    clut = struct.unpack_from("<H", data, uv_base + 2)[0]
                    tpage = struct.unpack_from("<H", data, uv_base + 6)[0]
                material_key = (textured, clut, tpage, bool(mode & 2))
                if material_key not in material_ids:
                    material_ids[material_key] = len(result["materials"])
                    result["materials"].append(dict(zip(
                        ("textured", "clut", "tpage", "semi_transparent"), material_key)))
                # PSX quad order uses the v1-v2 diagonal.
                for corners_used in ((0, 1, 2), (1, 3, 2)) if corners == 4 else ((0, 1, 2),):
                    result["triangles"].append([indices[n] for n in corners_used])
                    result["triangle_colors"].append([colors[n] for n in corners_used])
                    result["triangle_uvs"].append([uvs[n] for n in corners_used] if uvs else None)
                    result["triangle_materials"].append(material_ids[material_key])
            primitive_total += count
            object_primitives += count
            position = next_group
        if object_primitives != claimed:
            result["diagnostics"].append({"kind": "primitive_count_mismatch", "object_index": index,
                                          "declared": claimed, "decoded": object_primitives})
        result["objects"].append({
            "object_index": index, "vertex_start": first_vertex, "vertex_count": vertex_count,
            "triangle_start": first_triangle,
            "triangle_count": len(result["triangles"]) - first_triangle,
            "raw_object_word6": opaque, "transform": None,
        })
    if not result["vertices"] or not result["triangles"]:
        raise ImportError("TMD contains no supported bounded triangle geometry")
    result["bounds"] = {
        "min": [min(vertex[axis] for vertex in result["vertices"]) for axis in range(3)],
        "max": [max(vertex[axis] for vertex in result["vertices"]) for axis in range(3)],
    }
    return result


def load_model_source(disc: Path | str, asset: dict[str, Any]) -> bytes:
    """Read the imported model span with the same disc and container guards as preview."""
    if not isinstance(asset, dict) or asset.get("asset_kind") != "tmd_model":
        raise ImportError("preview requires an imported TMD model asset")
    source = asset.get("source_record", {})
    if not isinstance(source, dict) or not isinstance(asset.get("semantic_id"), str):
        raise ImportError("preview requires a structural asset identity and source locator")
    required = ("prot_entry_index", "byte_offset", "byte_length", "containing_size")
    if any(type(source.get(key)) is not int or source[key] < 0 for key in required):
        raise ImportError("model source locator contains invalid integer bounds")
    if source.get("iso_file") != "PROT.DAT":
        raise ImportError("unsupported model source ISO file")
    if not 0 < source["byte_length"] <= MAX_MODEL_BYTES:
        raise ImportError("model source span exceeds preview bounds")
    if not isinstance(source.get("disc"), dict):
        raise ImportError("model source disc identity is missing")
    with _disc_context(disc) as (_image, digest, _mapping, archive):
        if source.get("disc", {}).get("sha256") != digest:
            raise ImportError("model source identity does not match the verified disc")
        body = archive.read_entry(archive.entry(source["prot_entry_index"]))
        kind = source.get("record_kind")
        if kind in ("decoded_lzs_section", "decoded_tmd_pack_slot"):
            sections = parse_lzs_sections(body)
            section_index = source.get("container_section")
            if type(section_index) is not int or not 0 <= section_index < len(sections):
                raise ImportError("model source has an invalid LZS section")
            section = sections[section_index]
            if source.get("compressed_stream_offset") != section.stream_offset:
                raise ImportError("model compressed-stream locator no longer matches")
            end = sections[section_index + 1].stream_offset if section_index + 1 < len(sections) else len(body)
            body, _consumed = decompress_lzs(body[section.stream_offset:end], section.decoded_size)
        elif kind != "raw_prot_entry":
            raise ImportError(f"unsupported model source record kind: {kind!r}")
        if len(body) != source["containing_size"]:
            raise ImportError("model containing source size no longer matches")
        offset, length = source["byte_offset"], source["byte_length"]
        _range(body, offset, length, "model source")
        return body[offset:offset + length]


def load_model_preview(disc: Path | str, asset: dict[str, Any]) -> dict[str, Any]:
    """Decode a source-verified model privately in object-local coordinates."""
    preview = decode_tmd(load_model_source(disc, asset))
    preview["semantic_id"] = asset["semantic_id"]
    preview["source_record"] = asset["source_record"]
    return preview
