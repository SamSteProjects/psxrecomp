"""Private, bounded GLB interchange from verified importer preview data.

This module does not load or alter a disc. Callers supply a freshly verified
preview and may choose one decoded pose. glTF 2.0 layout follows the Khronos
specification; no external exporter dependency or generated source is bundled.
"""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
from typing import Any
import uuid
import zlib

from .core import ImportError

MAX_TRIANGLES = 100_000
MAX_VERTICES = 100_000
MAX_TEXTURE_BYTES = 8 * 1024 * 1024
MAX_GLB_BYTES = 64 * 1024 * 1024


def _vector(value, size, label, low=None, high=None):
    if (not isinstance(value, (list, tuple)) or len(value) != size or
            any(type(v) not in (int, float) or not math.isfinite(v) or
                (low is not None and v < low) or (high is not None and v > high) for v in value)):
        raise ImportError(f"invalid export {label}")
    return value


def _png(width: int, height: int, rgba: bytes) -> bytes:
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    rows = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def encode_model_glb(preview: dict[str, Any], frame_index: int | None = None) -> tuple[bytes, dict]:
    """Encode source geometry or one posed frame, with embedded matched PNGs.

    Input is assets.load_model_preview decorated with textures[].rgba_base64
    (or rgba bytes), and optionally animation frames as used by the editor.
    Source arrays remain unchanged. Output applies [x,-y,z], reverses triangle
    winding, and retains source units (no evidenced physical meter scale).
    """
    if preview.get("schema_version") != "legaia.model-preview.v1":
        raise ImportError("export requires the supported decoded model preview schema")
    vertices = preview.get("vertices", [])
    source_space = preview.get("coordinate_system")
    pose = None
    if frame_index is not None:
        frames = preview.get("frames", [])
        if type(frame_index) is not int or not 0 <= frame_index < len(frames):
            raise ImportError("export frame index is outside the decoded clip")
        pose = frames[frame_index]
        vertices = pose.get("vertices", [])
        if len(vertices) != len(preview.get("vertices", [])) or not pose.get("posed"):
            raise ImportError("export frame does not provide a complete evidenced pose")
        source_space = pose.get("coordinate_system")
    if source_space not in ("retail_tmd_object_local", "retail_psx_actor_local_y_down"):
        raise ImportError("unsupported export coordinate system; refusing a guessed axis conversion")
    if not 0 < len(vertices) <= MAX_VERTICES:
        raise ImportError("export vertex count exceeds bounds")
    for vertex in vertices:
        _vector(vertex, 3, "vertex", -1e9, 1e9)
    triangles = preview.get("triangles", [])
    colors = preview.get("triangle_colors", [])
    uvs = preview.get("triangle_uvs", [])
    triangle_materials = preview.get("triangle_materials", [])
    objects = preview.get("objects", [])
    materials = preview.get("materials", [])
    if (not 0 < len(triangles) <= MAX_TRIANGLES or
            any(len(a) != len(triangles) for a in (colors, uvs, triangle_materials)) or
            not 0 < len(objects) <= 1024 or not 0 < len(materials) <= 256):
        raise ImportError("export geometry arrays or counts do not agree")
    for triangle, rgb, uv, material in zip(triangles, colors, uvs, triangle_materials):
        if (not isinstance(triangle, list) or len(triangle) != 3 or
                any(type(i) is not int or not 0 <= i < len(vertices) for i in triangle) or
                type(material) is not int or not 0 <= material < len(materials) or
                not isinstance(rgb, list) or len(rgb) != 3):
            raise ImportError("invalid export triangle, color or material indices")
        for color in rgb:
            _vector(color, 3, "vertex color", 0, 255)
        if uv is not None:
            if not isinstance(uv, list) or len(uv) != 3:
                raise ImportError("invalid export triangle UVs")
            for point in uv:
                _vector(point, 2, "UV", 0, 255)
    binary = bytearray()
    doc: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "Legaia SDK verified preview exporter"},
        "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
        "buffers": [], "bufferViews": [], "accessors": [], "materials": [],
        "extensionsUsed": ["KHR_materials_unlit"],
    }

    def view(data: bytes, target=None):
        binary.extend(bytes((-len(binary)) % 4))
        offset = len(binary)
        binary.extend(data)
        if len(binary) > MAX_GLB_BYTES:
            raise ImportError("GLB binary exceeds bounded export budget")
        entry = dict(buffer=0, byteOffset=offset, byteLength=len(data))
        if target:
            entry["target"] = target
        doc["bufferViews"].append(entry)
        return len(doc["bufferViews"]) - 1

    def accessor(values, components, position=False):
        flat = [float(v) for row in values for v in row]
        # Bounds must describe the stored float32 values, not Python doubles.
        packed = struct.pack(f"<{len(flat)}f", *flat)
        entry = dict(bufferView=view(packed, 34962), componentType=5126,
                     count=len(values), type=f"VEC{components}")
        if position:
            stored = list(struct.iter_unpack(f"<{components}f", packed))
            entry.update(min=[min(v[i] for v in stored) for i in range(components)],
                         max=[max(v[i] for v in stored) for i in range(components)])
        doc["accessors"].append(entry)
        return len(doc["accessors"]) - 1

    texture_inputs = {}
    for item in preview.get("textures", []):
        index = item.get("material_index")
        if type(index) is not int or not 0 <= index < len(materials) or index in texture_inputs:
            raise ImportError("invalid or duplicate export material texture binding")
        texture_inputs[index] = item
    matched = {}
    diagnostics = []
    texture_bytes = 0
    for index, source in enumerate(materials):
        material = {"name": f"material-{index}", "doubleSided": True,
                    "extensions": {"KHR_materials_unlit": {}},
                    "pbrMetallicRoughness": {"metallicFactor": 0, "roughnessFactor": 1},
                    "extras": {"retail_material": deepcopy(source)}}
        item = texture_inputs.get(index, {})
        if source.get("textured") and item.get("status") == "address_match":
            width, height = item.get("width"), item.get("height")
            if (type(width) is not int or type(height) is not int or
                    not 0 < width <= 256 or not 0 < height <= 256):
                raise ImportError("export texture dimensions exceed one bounded page crop")
            origin = _vector(item.get("uv_origin"), 2, "texture origin", 0, 255)
            if any(type(v) is not int for v in origin) or origin[0] + width > 256 or origin[1] + height > 256:
                raise ImportError("export texture crop is outside the UV page")
            rgba = item.get("rgba")
            if rgba is None:
                encoded = item.get("rgba_base64", "")
                if not isinstance(encoded, str) or len(encoded) > width * height * 4 * 2:
                    raise ImportError("export texture encoding exceeds bounds")
                try:
                    rgba = base64.b64decode(encoded, validate=True)
                except (ValueError, TypeError) as exc:
                    raise ImportError("invalid export texture base64") from exc
            if not isinstance(rgba, bytes) or len(rgba) != width * height * 4:
                raise ImportError("export texture byte length does not match dimensions")
            texture_bytes += len(rgba)
            if texture_bytes > MAX_TEXTURE_BYTES:
                raise ImportError("export texture byte budget exceeded")
            image_index = len(doc.setdefault("images", []))
            doc["images"].append(dict(bufferView=view(_png(width, height, rgba)), mimeType="image/png"))
            doc.setdefault("textures", []).append(dict(source=image_index, sampler=0))
            material["pbrMetallicRoughness"]["baseColorTexture"] = {"index": image_index}
            material["alphaMode"] = "MASK"
            material["alphaCutoff"] = 0.5
            material["extras"]["texture_source_ids"] = deepcopy(item.get("source_ids", []))
            matched[index] = (origin, width, height)
        elif source.get("textured"):
            diagnostics.append(f"material {index}: {item.get('status', 'missing')} texture; exported vertex-color fallback")
        if source.get("semi_transparent"):
            diagnostics.append(f"material {index}: PSX semitransparent blend is not reconstructed")
        doc["materials"].append(material)
    if matched:
        doc["samplers"] = [dict(magFilter=9728, minFilter=9728, wrapS=33071, wrapT=33071)]
    seen_triangles = set()
    seen_objects = set()
    clipped_modulation = False
    for obj in objects:
        identity, start, count = obj.get("object_index"), obj.get("triangle_start"), obj.get("triangle_count")
        first, vertex_count = obj.get("vertex_start"), obj.get("vertex_count")
        if (type(identity) is not int or identity < 0 or identity in seen_objects or
                any(type(v) is not int or v < 0 for v in (start, count, first, vertex_count)) or
                start + count > len(triangles) or first + vertex_count > len(vertices)):
            raise ImportError("export object ranges or identities are invalid")
        seen_objects.add(identity)
        groups = {}
        for tri in range(start, start + count):
            if tri in seen_triangles or any(not first <= i < first + vertex_count for i in triangles[tri]):
                raise ImportError("export object triangles overlap or reference another object")
            seen_triangles.add(tri)
            groups.setdefault(triangle_materials[tri], []).append(tri)
        primitives = []
        for material_index, group in sorted(groups.items()):
            positions, vertex_colors, texcoords = [], [], []
            binding = matched.get(material_index)
            for tri in group:
                for corner in (0, 2, 1):  # Y reflection changes winding.
                    x, y, z = vertices[triangles[tri][corner]]
                    positions.append([x, -y, z])
                    color = colors[tri][corner]
                    clipped_modulation |= bool(binding and any(v > 128 for v in color))
                    if binding:
                        vertex_colors.append([min(1.0, v / 128) for v in color])
                    else:
                        # Raw preview RGB values are display-referred. glTF
                        # COLOR_0 is linear, while PNG base color is sRGB.
                        rgb = [v / 255 for v in color]
                        vertex_colors.append([v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb])
                    if binding:
                        if uvs[tri] is None:
                            raise ImportError("matched textured triangle has no UV coordinates")
                        origin, width, height = binding
                        u, v = uvs[tri][corner]
                        if not origin[0] <= u < origin[0] + width or not origin[1] <= v < origin[1] + height:
                            raise ImportError("triangle UV is outside its exported texture crop")
                        # glTF and the decoded PNG both use a top-left origin.
                        texcoords.append([(u - origin[0] + 0.5) / width, (v - origin[1] + 0.5) / height])
            attributes = dict(POSITION=accessor(positions, 3, True), COLOR_0=accessor(vertex_colors, 3))
            if binding:
                attributes["TEXCOORD_0"] = accessor(texcoords, 2)
            primitives.append(dict(attributes=attributes, material=material_index, mode=4))
        node = dict(name=f"object-{identity}", extras={"source_object": deepcopy(obj)})
        if primitives:
            node["mesh"] = len(doc["meshes"])
            doc["meshes"].append(dict(name=f"object-{identity}", primitives=primitives))
        doc["scenes"][0]["nodes"].append(len(doc["nodes"]))
        doc["nodes"].append(node)
    if len(seen_triangles) != len(triangles):
        raise ImportError("export object ranges leave triangles unassigned")
    if clipped_modulation:
        diagnostics.append("PSX texture modulation above neutral 128 is clamped to glTF COLOR_0's supported range")
    audit = {
        "schema_version": "legaia.model-export.v1", "format": "glb", "asset_semantic_id": preview.get("semantic_id"),
        "source_record": deepcopy(preview.get("source_record")), "reference_commit": preview.get("reference_commit"),
        "representation": preview.get("representation", "imported"),
        **({"authored_shape": deepcopy(preview["authored_shape"])} if preview.get("authored_shape") else {}),
        "source_coordinate_system": source_space, "coordinate_conversion": "[x,-y,z]; reverse triangle winding",
        "units": "source units retained; physical meter scale is unknown", "frame_index": frame_index,
        "posed": pose is not None, "animation": deepcopy(preview.get("animation")) if pose else None,
        "object_transforms": deepcopy(pose.get("object_transforms")) if pose else None,
        "triangle_count": len(triangles), "object_count": len(objects), "texture_count": len(matched),
        "diagnostics": diagnostics, "limitations": ["Static geometry or a single baked pose; no animation channels or skin hierarchy.",
            "Unlit color preview; live lighting, equipment changes and texture animation are not reproduced.",
            "Untextured display RGB is linearized; textured PSX modulation is approximated in glTF linear color space."],
    }
    doc["extras"] = deepcopy(audit)
    doc["buffers"] = [{"byteLength": len(binary)}]
    try:
        metadata = json.dumps(doc, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise ImportError("export provenance metadata must be finite JSON") from exc
    metadata += b" " * (-len(metadata) % 4)
    binary.extend(bytes((-len(binary)) % 4))
    total = 12 + 8 + len(metadata) + 8 + len(binary)
    if total > MAX_GLB_BYTES:
        raise ImportError("GLB exceeds bounded export budget")
    result = (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(metadata), b"JSON") +
              metadata + struct.pack("<I4s", len(binary), b"BIN\0") + binary)
    audit.update(byte_length=len(result), sha256=hashlib.sha256(result).hexdigest())
    return result, audit


def write_model_export(preview: dict[str, Any], output_root: Path | str,
                       frame_index: int | None = None) -> dict[str, Any]:
    """Write a new unique GLB inside a caller-authorized private output root.

    Reject symlink/reparse ancestors and never overwrite an existing file.
    The SDK supplies project/Exports; no client-provided path is needed.
    """
    data, audit = encode_model_glb(preview, frame_index)
    root = Path(output_root).absolute()

    def guard():
        for part in (root, *root.parents):
            try:
                info = part.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ImportError(f"export output contains a symlink or reparse point: {part}")

    guard()
    root.mkdir(parents=True, exist_ok=True)
    guard()
    name = "model-" + uuid.uuid4().hex + ".glb"
    path = root / name
    with path.open("xb") as handle:
        handle.write(data)
    return {"path": str(path.resolve()), "filename": name, "audit": audit}
