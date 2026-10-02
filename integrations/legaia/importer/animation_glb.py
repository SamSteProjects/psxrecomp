"""Bounded, same-layout rigid animation import from embedded glTF 2.0 GLB.

Normative TRS, accessor, STEP and shortest-arc rotation interpolation evidence:
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
Source signed12 / byte-angle packing and Rz*Ry*Rx evidence is pinned at
d6e64c68ede25813d35db20980da82a1a025549b in
crates/asset/src/player_anm.rs and crates/tmd/src/mesh/vram_posed.rs:
https://github.com/AndrewAltimit/legend-of-legaia-re/tree/d6e64c68ede25813d35db20980da82a1a025549b

This imports independent object-local translation and rotation channels only.
It does not import meshes, skinning, hierarchy, timing evidence or new records.
The caller must qualify the record and sidecar against its current project.
"""
from __future__ import annotations

from bisect import bisect_right
import hashlib
import json
import math
import re
import struct

from .animation import decode_animation_record
from .animation_authoring import MAX_CHANNEL_EDITS, patch_animation_channels
from .core import ImportError

MAX_GLB_BYTES = 32 * 1024 * 1024
MAX_GLTF_ITEMS = 16384
MAX_KEYS = 65536
MAX_ANIMATION_COMPONENTS = 1_000_000
ANGLE_EQUIVALENCE_RADIANS = 1e-5
MAX_ANGULAR_ERROR_DEGREES = 2.2
_TICK = math.tau / 256
_IDENTITY_MATRIX = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ImportError(f"GLB {label} is outside its integer bounds")
    return value


def _array(value, label, maximum=MAX_GLTF_ITEMS):
    if not isinstance(value, list) or len(value) > maximum:
        raise ImportError(f"GLB {label} must be a bounded array")
    return value


def _object(value, label):
    if not isinstance(value, dict):
        raise ImportError(f"GLB {label} must be an object")
    if "extensions" in value:
        raise ImportError(f"GLB {label} extensions are unsupported")
    return value


def _vector(value, count, label):
    if (not isinstance(value, list) or len(value) != count or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in value)):
        raise ImportError(f"GLB {label} requires {count} finite components")
    return list(value)


def _unit_quaternion(value, label):
    q = _vector(value, 4, label)
    norm = math.sqrt(sum(v * v for v in q))
    if not math.isfinite(norm) or abs(norm - 1) > 1e-3:
        raise ImportError(f"GLB {label} must be a unit quaternion")
    return [v / norm for v in q]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ImportError("GLB JSON contains duplicate properties")
        result[key] = value
    return result


def _finite_json_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ImportError("GLB JSON contains a nonfinite number")
    return result


def _read_glb(content):
    if not isinstance(content, bytes) or not 28 <= len(content) <= MAX_GLB_BYTES:
        raise ImportError("Animation GLB must be immutable bytes of at most 32 MiB")
    magic, version, size = struct.unpack_from("<3I", content)
    if magic != 0x46546C67 or version != 2 or size != len(content):
        raise ImportError("Invalid GLB 2.0 header or declared byte length")
    chunks, offset = [], 12
    while offset < len(content):
        if offset + 8 > len(content):
            raise ImportError("GLB chunk header is truncated")
        length, kind = struct.unpack_from("<2I", content, offset)
        offset += 8
        if length % 4 or offset + length > len(content):
            raise ImportError("GLB chunk length or alignment is invalid")
        chunks.append((kind, content[offset:offset + length]))
        offset += length
        if len(chunks) > 2:
            raise ImportError("GLB requires one JSON and one embedded BIN chunk")
    if len(chunks) != 2 or [kind for kind, _ in chunks] != [0x4E4F534A, 0x004E4942]:
        raise ImportError("GLB requires one JSON followed by one embedded BIN chunk")
    try:
        doc = json.loads(chunks[0][1].decode("utf-8"), object_pairs_hook=_unique_object,
                         parse_float=_finite_json_float,
                         parse_constant=lambda value: (_ for _ in ()).throw(
                             ImportError("GLB JSON contains a nonfinite number")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ImportError("GLB JSON is malformed") from exc
    _object(doc, "root")
    asset = _object(doc.get("asset"), "asset")
    if asset.get("version") != "2.0" or asset.get("minVersion", "2.0") != "2.0":
        raise ImportError("GLB requires glTF version 2.0")
    required = _array(doc.get("extensionsRequired", []), "required extensions")
    used = _array(doc.get("extensionsUsed", []), "used extensions")
    if required or any(item != "KHR_materials_unlit" for item in used) or len(used) > 1:
        raise ImportError("GLB animation cannot require extensions")
    buffers = _array(doc.get("buffers"), "buffers")
    if len(buffers) != 1:
        raise ImportError("GLB requires exactly one embedded buffer")
    buffer = _object(buffers[0], "buffer")
    if "uri" in buffer:
        raise ImportError("GLB external or data-URI buffers are unsupported")
    length = _integer(buffer.get("byteLength"), 1, MAX_GLB_BYTES, "buffer byte length")
    payload = chunks[1][1]
    if not length <= len(payload) <= length + 3 or any(payload[length:]):
        raise ImportError("GLB BIN length or padding does not match the embedded buffer")
    return doc, payload[:length]


class _Accessors:
    def __init__(self, doc, payload):
        self.rows = _array(doc.get("accessors", []), "accessors")
        self.views = _array(doc.get("bufferViews", []), "buffer views")
        self.payload = payload
        self.cache = {}
        self.component_count = 0

    def read(self, index, shape):
        _integer(index, 0, len(self.rows) - 1, "accessor index")
        key = (index, shape)
        if key in self.cache:
            return self.cache[key]
        row = _object(self.rows[index], "animation accessor")
        if (type(row.get("componentType")) is not int or row.get("componentType") != 5126 or row.get("type") != shape or
                row.get("normalized", False) is not False or "sparse" in row):
            raise ImportError("Animation accessors require nonsparse FLOAT SCALAR/VEC3/VEC4 data")
        count = _integer(row.get("count"), 1, MAX_KEYS, "animation key count")
        vi = _integer(row.get("bufferView"), 0, len(self.views) - 1, "buffer view index")
        view = _object(self.views[vi], "animation buffer view")
        if view.get("buffer") != 0 or type(view.get("buffer")) is not int:
            raise ImportError("Animation accessor must reference embedded buffer zero")
        # glTF 2.0 section 3.6.2.1 reserves byteStride for vertex attributes.
        if "byteStride" in view or "target" in view:
            raise ImportError("Animation accessor data must be tightly packed without a vertex stride")
        start = _integer(view.get("byteOffset", 0), 0, len(self.payload), "buffer view offset")
        length = _integer(view.get("byteLength"), 1, len(self.payload), "buffer view length")
        relative = _integer(row.get("byteOffset", 0), 0, length, "accessor byte offset")
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[shape]
        if self.component_count + count * width > MAX_ANIMATION_COMPONENTS:
            raise ImportError("Animation accessors exceed the one-million-component decoding bound")
        if start % 4 or relative % 4 or start + length > len(self.payload) or relative + count * width * 4 > length:
            raise ImportError("Animation accessor alignment or byte span is invalid")
        values = list(struct.iter_unpack(f"<{width}f",
                      self.payload[start + relative:start + relative + count * width * 4]))
        if any(not math.isfinite(v) for row_values in values for v in row_values):
            raise ImportError("Animation accessor contains a nonfinite component")
        result = [list(value) for value in values]
        self.cache[key] = result
        self.component_count += count * width
        return result


def _nodes(doc, object_count):
    nodes = _array(doc.get("nodes"), "nodes", 4096)
    scenes = _array(doc.get("scenes"), "scenes", 4096)
    scene_index = _integer(doc.get("scene", 0), 0, len(scenes) - 1, "scene index")
    scene = _object(scenes[scene_index], "scene")
    roots = _array(scene.get("nodes", []), "scene roots", 4096)
    mapping, transforms, parents = {}, {}, {}
    for index, raw in enumerate(nodes):
        node = _object(raw, "node")
        if "skin" in node or "weights" in node:
            raise ImportError("Rigid animation cannot import skinning or morph weights")
        name = node.get("name", "")
        match = re.fullmatch(r"object-(0|[1-9][0-9]*)", name) if isinstance(name, str) else None
        extras = node.get("extras", {})
        source = extras.get("source_object") if isinstance(extras, dict) else None
        identity = int(match.group(1)) if match else None
        if source is not None:
            if not isinstance(source, dict) or type(source.get("object_index")) is not int or source["object_index"] != identity:
                raise ImportError("GLB object name and source object identity disagree")
        if identity is not None:
            _integer(identity, 0, object_count - 1, "source object index")
            if identity in mapping:
                raise ImportError("GLB has duplicate source object nodes")
            mapping[identity] = index
        translation = _vector(node.get("translation", [0, 0, 0]), 3, "node translation")
        rotation = _unit_quaternion(node.get("rotation", [0, 0, 0, 1]), "node rotation")
        scale = _vector(node.get("scale", [1, 1, 1]), 3, "node scale")
        if scale != [1, 1, 1]:
            raise ImportError("Rigid animation requires identity node scale")
        if "matrix" in node:
            matrix = _vector(node["matrix"], 16, "node matrix")
            if identity is not None or matrix != _IDENTITY_MATRIX or any(k in node for k in ("translation", "rotation", "scale")):
                raise ImportError("Rigid animation does not import node matrices")
        if identity is None and (translation != [0, 0, 0] or abs(rotation[3]) != 1):
            raise ImportError("Unmapped nodes and ancestors must have identity transforms")
        transforms[index] = (translation, rotation)
        children = _array(node.get("children", []), "node children", 4096)
        for child in children:
            _integer(child, 0, len(nodes) - 1, "child node index")
            if child in parents:
                raise ImportError("GLB node hierarchy is not a disjoint tree")
            parents[child] = index
    if set(mapping) != set(range(object_count)):
        raise ImportError("GLB must map every existing source object exactly once")
    seen = set()
    for root in roots:
        _integer(root, 0, len(nodes) - 1, "scene root node")
        if root in parents:
            raise ImportError("GLB scene root cannot have a parent")
        stack = [root]
        while stack:
            current = stack.pop()
            if current in seen:
                raise ImportError("GLB scene hierarchy contains duplicate nodes or a cycle")
            seen.add(current)
            stack.extend(nodes[current].get("children", []))
    if not set(mapping.values()) <= seen:
        raise ImportError("Source object nodes are not reachable in the selected GLB scene")
    # Check even detached nodes for cycles; no ambiguous parent interpretation.
    finished = set()
    mapped_nodes = set(mapping.values())
    for index in range(len(nodes)):
        path, current = set(), index
        while current not in finished:
            if current in path:
                raise ImportError("GLB node hierarchy contains a cycle")
            path.add(current)
            parent = parents.get(current)
            if parent is None:
                break
            current = parent
        finished.update(path)
    for index in mapped_nodes:
        current = parents.get(index)
        while current is not None:
            if current in mapped_nodes:
                raise ImportError("Source object nodes require independent rigid channels")
            current = parents.get(current)
    return mapping, transforms


def _tracks(doc, accessors, mapping, duration):
    animations = _array(doc.get("animations", []), "animations", 1)
    if not animations:
        return {}
    animation = _object(animations[0], "animation")
    samplers = _array(animation.get("samplers"), "animation samplers", 128)
    channels = _array(animation.get("channels"), "animation channels", 128)
    tracks, allowed, time_cache = {}, set(mapping.values()), {}
    for channel in channels:
        channel = _object(channel, "animation channel")
        target = _object(channel.get("target"), "animation target")
        node, path = target.get("node"), target.get("path")
        if type(node) is not int or node not in allowed or path not in ("translation", "rotation"):
            raise ImportError("Animation targets must be mapped object translation or rotation only")
        if (node, path) in tracks:
            raise ImportError("GLB contains duplicate animation target channels")
        si = _integer(channel.get("sampler"), 0, len(samplers) - 1, "animation sampler index")
        sampler = _object(samplers[si], "animation sampler")
        mode = sampler.get("interpolation", "LINEAR")
        if mode not in ("STEP", "LINEAR"):
            raise ImportError("Animation interpolation must be STEP or LINEAR")
        input_index = sampler.get("input")
        _integer(input_index, 0, len(accessors.rows) - 1, "animation input accessor index")
        if input_index not in time_cache:
            time_cache[input_index] = [row[0] for row in accessors.read(input_index, "SCALAR")]
        times = time_cache[input_index]
        if times[0] < 0 or any(a >= b for a, b in zip(times, times[1:])):
            raise ImportError("Animation key times must be nonnegative and strictly increasing")
        endpoint = struct.unpack("<f", struct.pack("<f", duration))[0]
        tolerance = max(1e-7, abs(endpoint) * 2 ** -23)
        if times[-1] > endpoint + tolerance:
            raise ImportError("Animation key times exceed the existing clip duration; retiming is unsupported")
        values = accessors.read(sampler.get("output"), "VEC3" if path == "translation" else "VEC4")
        if len(values) != len(times):
            raise ImportError("Animation input and output key counts disagree")
        if path == "rotation":
            values = [_unit_quaternion(row, "rotation key") for row in values]
        tracks[(node, path)] = (times, values, mode)
    return tracks


def _slerp(a, b, ratio):
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-v for v in b], -dot
    dot = max(-1.0, min(1.0, dot))
    if dot > 0.9995:
        q = [(1 - ratio) * x + ratio * y for x, y in zip(a, b)]
    else:
        angle = math.acos(dot)
        q = [(math.sin((1 - ratio) * angle) * x + math.sin(ratio * angle) * y) / math.sin(angle)
             for x, y in zip(a, b)]
    norm = math.sqrt(sum(v * v for v in q))
    return [v / norm for v in q]


def _sample(track, time, rotation=False):
    times, values, mode = track
    index = bisect_right(times, time) - 1
    if index < 0:
        return list(values[0])
    if index >= len(times) - 1 or mode == "STEP":
        return list(values[index])
    ratio = (time - times[index]) / (times[index + 1] - times[index])
    if rotation:
        return _slerp(values[index], values[index + 1], ratio)
    return [(1 - ratio) * a + ratio * b for a, b in zip(values[index], values[index + 1])]


def _source_quaternion(angles):
    x, y, z = [value * _TICK / 2 for value in angles]
    sx, cx, sy, cy, sz, cz = math.sin(x), math.cos(x), math.sin(y), math.cos(y), math.sin(z), math.cos(z)
    return [sx * cy * cz - cx * sy * sz, cx * sy * cz + sx * cy * sz,
            cx * cy * sz - sx * sy * cz, cx * cy * cz + sx * sy * sz]


def _orientation_error(a, b):
    # Chord distance avoids loss of precision near equivalent q / -q.
    chord = min(sum((x - y) ** 2 for x, y in zip(a, b)),
                sum((x + y) ** 2 for x, y in zip(a, b))) ** 0.5
    return 4 * math.asin(min(1.0, chord / 2))


def _wrap(angle):
    return (angle + math.pi) % math.tau - math.pi


def _nearest(value):
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def _quantize_rotation(glb_q, baseline_angles):
    q = [-glb_q[0], glb_q[1], -glb_q[2], glb_q[3]]
    baseline = [v // 16 for v in baseline_angles]
    baseline_q = _source_quaternion(baseline)
    if _orientation_error(q, baseline_q) <= ANGLE_EQUIVALENCE_RADIANS:
        return list(baseline_angles), math.degrees(_orientation_error(q, baseline_q))
    x, y, z, w = q
    r00, r10, r20 = 1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)
    r21, r22 = 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)
    r01, r11 = 2 * (x * y - w * z), 1 - 2 * (x * x + z * z)
    ey = math.asin(max(-1.0, min(1.0, -r20)))
    source = [v * _TICK for v in baseline]
    if abs(math.cos(ey)) <= 1e-6:
        sign = 1 if ey >= 0 else -1
        delta = math.atan2(sign * r01, r11)
        difference = _wrap(delta - (source[0] - sign * source[2]))
        chosen = [source[0] + difference / 2, sign * math.pi / 2,
                  source[2] - sign * difference / 2]
    else:
        ex, ez = math.atan2(r21, r22), math.atan2(r10, r00)
        branches = ([ex, ey, ez], [ex + math.pi, math.pi - ey, ez + math.pi])
        chosen = min(branches, key=lambda branch: (
            sum(_wrap(v - old) ** 2 for v, old in zip(branch, source)), tuple(branch)))
    rounded = [_nearest(v / _TICK) % 256 for v in chosen]
    candidates = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                ticks = [(v + d) % 256 for v, d in zip(rounded, (dx, dy, dz))]
                error = _orientation_error(q, _source_quaternion(ticks))
                distance = sum(min((v - old) % 256, (old - v) % 256) ** 2 for v, old in zip(ticks, baseline))
                candidates.append((error, distance, ticks))
    minimum_error = min(row[0] for row in candidates)
    # Equivalent numerical minima use source proximity, then byte order.
    error, _, ticks = min((row for row in candidates if row[0] <= minimum_error + 1e-12),
                          key=lambda row: (row[1], row[2]))
    degrees = math.degrees(error)
    if degrees > MAX_ANGULAR_ERROR_DEGREES:
        raise ImportError("Animation rotation exceeds the 2.2 degree quantization error bound")
    return [v * 16 for v in ticks], degrees


def import_animation_glb(baseline: bytes, content: bytes, *, fps: float) -> tuple[bytes, dict]:
    """Sample an existing clip at explicit 1..120 fps without retiming/count growth.

    At i/fps, the float32 representation matches glTF key storage and the SDK
    exporter. Before/after key extents hold their endpoint value; no appended
    source frame is allocated. Y reflection is inverted before signed12 and
    source-biased 8-bit Euler quantization. Equivalent source angles survive.
    """
    if not isinstance(baseline, bytes):
        raise ImportError("Animation GLB baseline must be immutable record bytes")
    if type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120:
        raise ImportError("Animation GLB requires an explicit rate from 1 to 120 fps")
    source = decode_animation_record(baseline)
    if source['bone_count'] > 64:
        raise ImportError('Animation GLB source exceeds the 64 rigid-object bound')
    total = source["frame_count"] * source["bone_count"]
    if total > MAX_CHANNEL_EDITS:
        raise ImportError("Animation GLB source exceeds the 4096-channel bound")
    doc, payload = _read_glb(content)
    mapping, static = _nodes(doc, source["bone_count"])
    tracks = _tracks(doc, _Accessors(doc, payload), mapping, source["frame_count"] / fps)
    edits, maximum_translation, maximum_angle, preserved = [], 0.0, 0.0, 0
    for frame in source["frames"]:
        time = struct.unpack("<f", struct.pack("<f", frame["frame_index"] / fps))[0]
        for channel in frame["object_transforms"]:
            obj, before_t, before_r = channel["object_index"], channel["translation"], channel["rotation_psx"]
            node = mapping[obj]
            translation, quaternion = static[node]
            if (node, "translation") in tracks:
                translation = _sample(tracks[(node, "translation")], time)
            if (node, "rotation") in tracks:
                quaternion = _sample(tracks[(node, "rotation")], time, True)
            actual = [translation[0], -translation[1], translation[2]]
            if any(not -2048 <= value <= 2047 for value in actual):
                raise ImportError("GLB translation exceeds signed twelve-bit range before quantization")
            rounded = [_nearest(value) for value in actual]
            maximum_translation = max(maximum_translation, *(abs(a - b) for a, b in zip(actual, rounded)))
            angles, error = _quantize_rotation(quaternion, before_r)
            maximum_angle = max(maximum_angle, error)
            if angles == before_r:
                preserved += 1
            edit = {"frame_index": frame["frame_index"], "object_index": obj}
            for field, after, before in (("translation", rounded, before_t), ("rotation_psx", angles, before_r)):
                axes = {axis: value for axis, value, old in zip("xyz", after, before) if value != old}
                if axes:
                    edit[field] = axes
            if len(edit) > 2:
                edits.append(edit)
    candidate, audit = patch_animation_channels(baseline, _hash(baseline), edits)
    return candidate, {
        "schema_version": "legaia.animation-glb-import.v1",
        "source_record_sha256": _hash(baseline), "candidate_sha256": _hash(candidate),
        "glb_sha256": _hash(content), "frame_count": source["frame_count"],
        "object_count": source["bone_count"], "fps": float(fps),
        "sampled_channel_count": total, "changed_axes": len(audit), "changes": audit,
        "maximum_translation_error": maximum_translation,
        "maximum_angular_error_degrees": maximum_angle,
        "quantization": {"translation": "nearest integer; exact half ties away from zero; raw signed12 overflow rejected",
                         "rotation": "source-biased Rz*Ry*Rx Euler branches; nearest byte-angle neighborhood",
                         "rotation_step_degrees": 360 / 256,
                         "maximum_angular_error_degrees": MAX_ANGULAR_ERROR_DEGREES,
                         "baseline_equivalence_radians": ANGLE_EQUIVALENCE_RADIANS,
                         "preserved_rotation_channels": preserved,
                         "timeline": "float32(i/fps), fixed source frame count, endpoint hold",
                         "coordinate_conversion": "translation [x,-y,z]; quaternion [-x,y,-z,w]"},
        "scope": "existing-rigid-animation-channels-only", "gameplay_verified": False,
    }
