"""Independent bounded field-party animation and rigid-object pose previews.

Evidence at pipeline.REFERENCE_COMMIT: crates/asset/src/{player_anm,
character_pack}.rs, crates/engine-core/src/field_anim.rs and
crates/tmd/src/mesh/{mod,vram_posed}.rs. Retail decoder FUN_8001BE80 packs
signed twelve-bit translations and eight-bit Euler angles. These records are
frame-major rigid-object transforms, not the unrelated ANM keyframe VM.

Only pinned global-party idle/walk associations are enabled. No anatomical
joint names, parent hierarchy, equipment state, or scene-actor binding is
inferred. All decoded animation/geometry output remains private disc data.
"""
from __future__ import annotations

from copy import deepcopy
import math
import struct
from typing import Any

from .assets import load_model_preview
from .core import ImportError, decompress_lzs, global_special_tmd_pool, parse_lzs_sections
from .pipeline import REFERENCE_COMMIT, _disc_context, _model_source_locator

MAX_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 4096
MAX_BONES = 64
MAX_FRAMES = 512
MAX_POSED_VERTICES = 1_000_000
_PARTY_IDS = tuple(f"asset://legaia/models/global-special/{0xF0 + slot:04x}"
                   for slot in range(3))


def animation_capabilities(asset: dict[str, Any]) -> dict[str, Any]:
    """Cheap structural advertisement; load re-verifies source against disc."""
    identity = asset.get("semantic_id") if isinstance(asset, dict) else None
    source = asset.get("source_record", {}) if isinstance(asset, dict) else {}
    supported = (identity in _PARTY_IDS and isinstance(source, dict)
                 and asset.get("asset_kind") == "tmd_model"
                 and source.get("prot_entry_index") == 874
                 and source.get("container_section") == 0
                 and source.get("pack_slot") == _PARTY_IDS.index(identity))
    return {
        "supported": supported,
        "clips": [{"id": "idle", "label": "Field idle"},
                  {"id": "walk", "label": "Field walk"}] if supported else [],
        "reason": None if supported else "Only the three pinned global field-party model banks support animation preview.",
    }


def animation_record_ranges(data: bytes) -> tuple[tuple[int, int], ...]:
    if not 4 <= len(data) <= MAX_BUNDLE_BYTES:
        raise ImportError("animation bundle size exceeds bounds or has a truncated header")
    count = struct.unpack_from("<I", data)[0]
    if not 1 <= count <= MAX_RECORDS or 4 + count * 4 > len(data):
        raise ImportError("animation record count or offset table exceeds bounds")
    offsets = list(struct.unpack_from(f"<{count}I", data, 4))
    if offsets[0] < 4 + count * 4 or offsets[-1] >= len(data):
        raise ImportError("animation record offset points into table or past payload")
    if any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise ImportError("animation record offsets must be strictly increasing")
    return tuple(zip(offsets, offsets[1:] + [len(data)]))


def decode_bone_transform(data: bytes) -> dict[str, Any]:
    if len(data) != 8:
        raise ImportError("rigid animation channel requires exactly eight bytes")

    def signed12(low: int, high: int) -> int:
        raw = low | ((high & 15) << 8)
        return raw - 4096 if raw & 2048 else raw

    return {
        "translation": [signed12(data[0], data[2]), signed12(data[1], data[2] >> 4),
                        signed12(data[3], data[4])],
        "rotation_psx": [v * 16 for v in data[5:8]],
        "opaque_nibble": data[4] >> 4,
    }


def decode_animation_record(data: bytes) -> dict[str, Any]:
    """Decode supported eight-byte channels, preserving opaque header fields."""
    if len(data) < 16 or len(data) > MAX_BUNDLE_BYTES:
        raise ImportError("animation record is truncated or exceeds byte bound")
    a, frames, marker, flags = struct.unpack_from("<4H", data)
    bones = a & 255
    if marker != 0x080C or a >> 8 not in (0, 1) or flags not in (2, 4):
        raise ImportError(f"unsupported animation record mode a=0x{a:04x} flags=0x{flags:04x} marker=0x{marker:04x}")
    if not 1 <= bones <= MAX_BONES or not 1 <= frames <= MAX_FRAMES:
        raise ImportError("animation bone/frame count exceeds preview bounds")
    if len(data) != 16 + bones * frames * 8:
        raise ImportError("animation record byte length does not match bone/frame counts")
    if any(data[-8:]):
        raise ImportError("unsupported nonzero animation record trailer")
    decoded = []
    for frame in range(frames):
        transforms = []
        for bone in range(bones):
            pos = 8 + (frame * bones + bone) * 8
            transforms.append(dict(object_index=bone, **decode_bone_transform(data[pos:pos + 8])))
        decoded.append({"frame_index": frame, "object_transforms": transforms})
    return dict(bone_count=bones, frame_count=frames, header_a=a, header_flags=flags,
                frames=decoded)


def pose_vertices(vertices: list[list[float]], objects: list[dict[str, Any]],
                  transforms: list[dict[str, Any]]) -> list[list[float]]:
    """Apply Rz*Ry*Rx then actor-local translation, without a Y-axis flip.

    Uses analytic double-precision trig for viewing, not a bit-exact GTE fixed
    point/rounding emulation. Objects are independent rigid channels.
    """
    if len(objects) != len(transforms) or len(vertices) > MAX_POSED_VERTICES:
        raise ImportError("pose object/channel mapping or vertex count exceeds bounds")
    posed: list[list[float] | None] = [None] * len(vertices)
    for obj, transform in zip(objects, transforms):
        if obj.get("object_index") != transform.get("object_index"):
            raise ImportError("pose channel does not match its TMD object")
        start, count = obj.get("vertex_start"), obj.get("vertex_count")
        if type(start) is not int or type(count) is not int or start < 0 or count < 0 or start + count > len(vertices):
            raise ImportError("pose object vertex span is invalid")
        t, angles = transform.get("translation"), transform.get("rotation_psx")
        if not isinstance(t, list) or not isinstance(angles, list) or len(t) != 3 or len(angles) != 3:
            raise ImportError("pose requires three translation and rotation components")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in t + angles):
            raise ImportError("pose components must be finite numbers")
        rx, ry, rz = [v * math.tau / 4096 for v in angles]
        sx, cx, sy, cy, sz, cz = math.sin(rx), math.cos(rx), math.sin(ry), math.cos(ry), math.sin(rz), math.cos(rz)
        for i in range(start, start + count):
            if posed[i] is not None:
                raise ImportError("pose object vertex spans overlap")
            vertex = vertices[i]
            if len(vertex) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in vertex):
                raise ImportError("pose vertex must contain three finite components")
            x, y, z = vertex
            y, z = y * cx - z * sx, y * sx + z * cx
            x, z = x * cy + z * sy, -x * sy + z * cy
            x, y = x * cz - y * sz, x * sz + y * cz
            posed[i] = [x + t[0], y + t[1], z + t[2]]
    if any(v is None for v in posed):
        raise ImportError("pose leaves vertices without an evidenced object channel")
    return posed


def _source(disc: Any, asset: dict[str, Any], clip_id: str):
    capabilities = animation_capabilities(asset)
    if not capabilities["supported"]:
        raise ImportError(capabilities["reason"])
    if clip_id not in ("idle", "walk"):
        raise ImportError("unsupported field clip: choose idle or walk")
    slot = _PARTY_IDS.index(asset["semantic_id"])
    record_index = slot * 7 + (1 if clip_id == "idle" else 0)
    with _disc_context(disc) as (_, digest, _, archive):
        # A plausible caller-supplied source locator is insufficient: compare
        # to the exact current disc record before associating its animation.
        record = global_special_tmd_pool(archive)[slot]
        expected = _model_source_locator(digest, "", record)
        if asset.get("source_record") != expected:
            raise ImportError("animation model provenance does not match the verified global pack record")
        raw = archive.read_entry(archive.entry(874), extended=True)
        sections = parse_lzs_sections(raw)
        if len(sections) != 3:
            raise ImportError("unsupported global character container descriptor count")
        section = sections[1]
        body, consumed = decompress_lzs(raw[section.stream_offset:sections[2].stream_offset], section.decoded_size)
        ranges = animation_record_ranges(body)
        if len(ranges) != 23:
            raise ImportError("global locomotion bank does not match pinned 23-record layout")
        start, end = ranges[record_index]
        decoded = decode_animation_record(body[start:end])
        if decoded["bone_count"] != 10 or record.object_count != 12:
            raise ImportError("global party animation/model channel counts do not match pinned 10/12 layout")
        source = {
            "disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
            "prot_entry_index": 874, "container_section": 1,
            "compressed_stream_offset": section.stream_offset, "compressed_bytes_consumed": consumed,
            "record_index": record_index, "byte_offset": start, "byte_length": end - start,
            "byte_coordinate_space": "decoded_lzs_section", "containing_size": len(body),
        }
        return decoded, source, slot


def load_animation_preview(disc: Any, asset: dict[str, Any], clip_id: str = "idle") -> dict[str, Any]:
    """Decode the entire supported clip once for browser-side scrub/play."""
    decoded, source, slot = _source(disc, asset, clip_id)
    geometry = deepcopy(load_model_preview(disc, asset))
    objects = geometry["objects"][:10]
    vertex_count = sum(obj["vertex_count"] for obj in objects)
    triangle_count = sum(obj["triangle_count"] for obj in objects)
    if decoded["frame_count"] * vertex_count > MAX_POSED_VERTICES:
        raise ImportError("animation posed-vertex budget exceeded")
    geometry["vertices"] = geometry["vertices"][:vertex_count]
    for key in ("triangles", "triangle_colors", "triangle_uvs", "triangle_materials"):
        geometry[key] = geometry[key][:triangle_count]
    geometry["objects"] = objects
    geometry["diagnostics"].append({"kind": "equipment_templates_excluded", "object_indices": [10, 11]})
    geometry["bounds"] = _bounds(geometry["vertices"])
    frames = []
    for frame in decoded["frames"]:
        vertices = pose_vertices(geometry["vertices"], objects, frame["object_transforms"])
        frames.append(dict(frame, vertices=vertices, bounds=_bounds(vertices), posed=True,
                           coordinate_system="retail_psx_actor_local_y_down"))
    semantic_id = f"animation://legaia/field-locomotion/{source['record_index']:04d}"
    skeleton_id = f"skeleton://legaia/field-party/{slot:02d}"
    return {
        "schema_version": "legaia.animation-preview.v1", "semantic_id": semantic_id,
        "asset_semantic_id": asset["semantic_id"], "clip_id": clip_id,
        "label": ("Vahn", "Noa", "Gala")[slot] + " field " + clip_id,
        "reference_commit": REFERENCE_COMMIT, "source_record": source,
        "frame_count": decoded["frame_count"], "bone_count": 10,
        "header_a": decoded["header_a"], "header_flags": decoded["header_flags"],
        "coordinate_system": "retail_psx_actor_local_y_down", "geometry": geometry,
        "frames": frames, "looping": True,
        "timing": {"fps": 30, "wire_rate": None, "evidence": "reference_runtime_interpretation",
                   "source": "crates/engine-core/src/field_anim.rs:DEFAULT_TICKS_PER_FRAME",
                   "note": "Reference uses one clip frame per 30 Hz field tick; no rate byte is stored in these records."},
        "association": {"kind": "reference_pinned_global_party_bank", "pack_slot": slot,
                        "record_index": source["record_index"], "active_object_indices": list(range(10))},
        "skeleton": {"semantic_id": skeleton_id, "topology": "independent_rigid_objects", "hierarchy": None,
                     "channels": [{"semantic_id": f"{skeleton_id}/channels/{i:02d}",
                                   "object_index": i, "parent_index": None} for i in range(10)]},
        "limitations": ["Analytic rigid transforms approximate GTE fixed-point rounding.",
                        "Disc group descriptors are used; live equipment descriptor swaps are not reconstructed.",
                        "Scene actor animation IDs, scripted transitions and battle animation banks are unsupported.",
                        "Reference-derived clip identity and cadence have not been verified in a live runtime by this importer."],
    }


def _bounds(vertices: list[list[float]]) -> dict[str, list[float]]:
    return {"min": [min(v[i] for v in vertices) for i in range(3)],
            "max": [max(v[i] for v in vertices) for i in range(3)]}
