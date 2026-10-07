"""Bounded, same-layout rigid animation import from embedded glTF 2.0 GLB.

Normative TRS, accessor, STEP and shortest-arc rotation interpolation evidence:
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
Source signed12 / byte-angle packing and Rz*Ry*Rx evidence is pinned at
d6e64c68ede25813d35db20980da82a1a025549b in
crates/asset/src/player_anm.rs and crates/tmd/src/mesh/vram_posed.rs:
https://github.com/AndrewAltimit/legend-of-legaia-re/tree/d6e64c68ede25813d35db20980da82a1a025549b

Rigid node hierarchies are sampled into independent scene-space native poses.
This does not import meshes, skinning, timing evidence or new records.
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
# Room for all 64 rigid TRS triplets plus bounded neutral ancestor tracks.
MAX_ANIMATION_TRACKS = 256
MAX_ANIMATION_COMPONENTS = 1_000_000
MAX_HIERARCHY_SAMPLES = 65536
ANGLE_EQUIVALENCE_RADIANS = 1e-5
MAX_ANGULAR_ERROR_DEGREES = 2.2
_TICK = math.tau / 256
RIGID_MATRIX_TOLERANCE = 1e-5


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


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        # JSON integers need not fit a float; reject before numeric conversion.
        return False


def sampling_config(value):
    if (not isinstance(value,dict) or not {'start_seconds','rate'}<=set(value)
            or set(value)-{'start_seconds','rate','mode'}):
        raise ImportError('External sampling requires start_seconds, rate and optional mode only')
    start,rate=value['start_seconds'],value['rate']
    if (not _finite_number(start) or not 0<=start<=3600 or
            not _finite_number(rate) or not -16<=rate<=16):
        raise ImportError('External sampling requires start 0..3600 seconds and rate -16..16')
    mode=value.get('mode','clamp')
    if mode not in ('clamp','repeat','ping_pong'):
        raise ImportError('External sampling mode must be clamp, repeat or ping_pong')
    result=dict(start_seconds=float(start),rate=float(rate))
    # Preserve canonical legacy bindings/review identities for endpoint hold.
    if mode!='clamp':result['mode']=mode
    return result


def _external_time(seconds,mode,interval):
    if mode=='clamp' or interval is None:return seconds
    start,end=interval['start_seconds'],interval['end_seconds']
    duration=end-start
    if duration==0:return start
    if mode=='repeat':return start+(seconds-start)%duration
    phase=(seconds-start)%(2*duration)
    return start+(phase if phase<=duration else 2*duration-phase)


def _vector(value, count, label):
    if (not isinstance(value, list) or len(value) != count or
            any(not _finite_number(v) for v in value)):
        raise ImportError(f"GLB {label} requires {count} finite components")
    return list(value)


def _unit_quaternion(value, label):
    q = _vector(value, 4, label)
    if any(abs(v) > 1.001 for v in q):
        raise ImportError(f"GLB {label} must be a unit quaternion")
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

    def _span(self, descriptor, count, width, fmt, size):
        vi = _integer(descriptor.get("bufferView"), 0, len(self.views) - 1, "buffer view index")
        view = _object(self.views[vi], "animation buffer view")
        if view.get("buffer") != 0 or type(view.get("buffer")) is not int:
            raise ImportError("Animation accessor must reference embedded buffer zero")
        # glTF 2.0 reserves byteStride/target for other buffer usages.
        if "byteStride" in view or "target" in view:
            raise ImportError("Animation accessor data must be tightly packed without a vertex stride")
        start = _integer(view.get("byteOffset", 0), 0, len(self.payload), "buffer view offset")
        length = _integer(view.get("byteLength"), 1, len(self.payload), "buffer view length")
        relative = _integer(descriptor.get("byteOffset", 0), 0, length, "accessor byte offset")
        byte_length = count * width * size
        if start % size or relative % size or start + length > len(self.payload) or relative + byte_length > length:
            raise ImportError("Animation accessor alignment or byte span is invalid")
        return [list(value) for value in struct.iter_unpack(f"<{width}{fmt}",
                self.payload[start + relative:start + relative + byte_length])]

    def read(self, index, shape):
        _integer(index, 0, len(self.rows) - 1, "accessor index")
        key = (index, shape)
        if key in self.cache:
            return self.cache[key]
        row = _object(self.rows[index], "animation accessor")
        if (type(row.get("componentType")) is not int or row.get("componentType") != 5126 or row.get("type") != shape or
                row.get("normalized", False) is not False):
            raise ImportError("Animation accessors require unnormalized FLOAT data of the expected shape")
        count = _integer(row.get("count"), 1, MAX_KEYS, "animation key count")
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4, "MAT4": 16}[shape]
        if self.component_count + count * width > MAX_ANIMATION_COMPONENTS:
            raise ImportError("Animation accessors exceed the one-million-component decoding bound")
        if "bufferView" in row:
            result = self._span(row, count, width, 'f', 4)
        else:
            if "byteOffset" in row:
                raise ImportError("Animation accessor without a base buffer view cannot define byteOffset")
            result = [[0.0] * width for _ in range(count)]
        if any(not math.isfinite(v) for values in result for v in values):
            raise ImportError("Animation accessor contains a nonfinite component")
        if "sparse" in row:
            sparse = _object(row['sparse'], "sparse animation accessor")
            sparse_count = _integer(sparse.get('count'), 1, count, "sparse animation count")
            indices = _object(sparse.get('indices'), "sparse animation indices")
            component = indices.get('componentType')
            if type(component) is not int or component not in (5121, 5123, 5125):
                raise ImportError("Sparse animation indices require unsigned byte, short or int components")
            fmt, size = {5121:('B', 1), 5123:('H', 2), 5125:('I', 4)}[component]
            positions = [value[0] for value in self._span(indices, sparse_count, 1, fmt, size)]
            if any(position >= count or (i and position <= positions[i-1]) for i, position in enumerate(positions)):
                raise ImportError("Sparse animation indices must be strictly increasing and within the accessor")
            values = self._span(_object(sparse.get('values'), "sparse animation values"), sparse_count, width, 'f', 4)
            if any(not math.isfinite(v) for value in values for v in value):
                raise ImportError("Sparse animation values contain a nonfinite component")
            for position, value in zip(positions, values):
                result[position] = value
        self.cache[key] = result
        self.component_count += count * width
        return result


def _rigid_matrix(value):
    """Decompose column-major affine rigid matrices, allowing float32 noise."""
    m = _vector(value, 16, "node matrix")
    if [m[i] for i in (3, 7, 11, 15)] != [0, 0, 0, 1]:
        raise ImportError("GLB rigid matrix must have an affine final row")
    columns = [[m[i+j] for j in range(3)] for i in (0, 4, 8)]
    tolerance = RIGID_MATRIX_TOLERANCE
    if any(abs(v) > 1+tolerance for column in columns for v in column):
        raise ImportError("GLB rigid matrix cannot contain scale or shear")
    for i, a in enumerate(columns):
        for j, b in enumerate(columns):
            if abs(sum(x*y for x,y in zip(a,b)) - int(i == j)) > tolerance:
                raise ImportError("GLB rigid matrix cannot contain scale or shear")
    a,b,c = columns
    determinant = a[0]*(b[1]*c[2]-b[2]*c[1]) - b[0]*(a[1]*c[2]-a[2]*c[1]) + c[0]*(a[1]*b[2]-a[2]*b[1])
    if abs(determinant-1) > tolerance:
        raise ImportError("GLB rigid matrix cannot contain a reflection")
    r00,r01,r02 = m[0],m[4],m[8]
    r10,r11,r12 = m[1],m[5],m[9]
    r20,r21,r22 = m[2],m[6],m[10]
    trace = r00+r11+r22
    if trace > 0:
        s = 2*math.sqrt(trace+1)
        q = [(r21-r12)/s,(r02-r20)/s,(r10-r01)/s,s/4]
    elif r00 >= r11 and r00 >= r22:
        s = 2*math.sqrt(1+r00-r11-r22)
        q = [s/4,(r01+r10)/s,(r02+r20)/s,(r21-r12)/s]
    elif r11 >= r22:
        s = 2*math.sqrt(1+r11-r00-r22)
        q = [(r01+r10)/s,s/4,(r12+r21)/s,(r02-r20)/s]
    else:
        s = 2*math.sqrt(1+r22-r00-r11)
        q = [(r02+r20)/s,(r12+r21)/s,s/4,(r10-r01)/s]
    return [m[12],m[13],m[14]], _unit_quaternion(q, "matrix rotation")


def _nodes(doc, object_count, object_node_indices=None, *, skin_index=None, accessors=None):
    if skin_index is not None and object_node_indices is None:raise ImportError('Joint rig extraction requires an explicit native-object node mapping')
    nodes = _array(doc.get("nodes"), "nodes", 4096)
    scenes = _array(doc.get("scenes"), "scenes", 4096)
    scene_index = _integer(doc.get("scene", 0), 0, len(scenes) - 1, "scene index")
    scene = _object(scenes[scene_index], "scene")
    roots = _array(scene.get("nodes", []), "scene roots", 4096)
    mapping, transforms, parents = {}, {}, {}
    explicit = {}
    if object_node_indices is not None:
        if not isinstance(object_node_indices,list) or len(object_node_indices)!=object_count:
            raise ImportError('Explicit rigid-object mapping requires one GLB node per native object')
        for obj,index in enumerate(object_node_indices):
            _integer(index,0,len(nodes)-1,'explicit object node index')
            if index in explicit:raise ImportError('Explicit rigid-object mapping contains duplicate nodes')
            explicit[index]=obj
        mapping={obj:index for index,obj in explicit.items()}
    for index, raw in enumerate(nodes):
        node = _object(raw, "node")
        if ("skin" in node and skin_index is None) or "weights" in node:
            raise ImportError("Rigid animation cannot import skinning or morph weights")
        name = node.get("name", "")
        if not isinstance(name, str):
            raise ImportError("GLB node display name must be a string")
        match = re.fullmatch(r"object-(0|[1-9][0-9]*)", name) if isinstance(name, str) else None
        extras = node.get("extras", {})
        source = extras.get("source_object") if isinstance(extras, dict) else None
        identity = int(match.group(1)) if match else None
        if isinstance(extras, dict) and "source_object" in extras:
            source = _object(source, "source object identity")
            source_index = _integer(source.get("object_index"), 0, object_count - 1, "source object identity")
            # Exported extras survive external object renaming. Canonical names
            # still cannot claim a different native object than those extras.
            if identity is not None and source_index != identity:
                raise ImportError("GLB object name and source object identity disagree")
            identity = source_index
        if identity is not None:
            _integer(identity, 0, object_count - 1, "source object index")
            if object_node_indices is not None:
                if explicit.get(index)!=identity:
                    raise ImportError('Explicit mapping conflicts with preserved source object identity')
            else:
                if identity in mapping:
                    raise ImportError("GLB has duplicate source object nodes")
                mapping[identity] = index
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
    rig = None
    if skin_index is not None:
        from .animation_glb_rig import qualify_joint_rig
        rig = qualify_joint_rig(doc,mapping,parents,seen,accessors,skin_index)
    relevant=set()
    for selected in mapping.values():
        current=selected
        while current is not None and current not in relevant:
            relevant.add(current);current=parents.get(current)
    for index,node in enumerate(nodes):
        if rig is not None and index not in relevant:
            from .model_mesh_transform import node_transform
            node_transform(node,allow_shear=True)
            continue
        translation = _vector(node.get("translation", [0, 0, 0]), 3, "node translation")
        rotation = _unit_quaternion(node.get("rotation", [0, 0, 0, 1]), "node rotation")
        scale = _vector(node.get("scale", [1, 1, 1]), 3, "node scale")
        if scale != [1, 1, 1]:
            raise ImportError("Rigid animation requires identity node scale")
        if "matrix" in node:
            if any(k in node for k in ("translation", "rotation", "scale")):
                raise ImportError("GLB node matrices cannot be combined with TRS properties")
            translation, rotation = _rigid_matrix(node["matrix"])
        transforms[index] = (translation, rotation)
    return mapping, transforms, parents, rig


def _hierarchy_order(mapping, parents, frame_count):
    """Only source objects and their ancestors, parent first without recursion."""
    order, included = [], set()
    for node in mapping.values():
        path = []
        current = node
        while current is not None and current not in included:
            path.append(current)
            current = parents.get(current)
        for current in reversed(path):
            included.add(current)
            order.append(current)
    if len(order) * frame_count > MAX_HIERARCHY_SAMPLES:
        raise ImportError("GLB hierarchy exceeds the 65536 sampled-node bound")
    return order



def _tracks(doc, accessors, mapping, duration, animation_index=None, *, hierarchy_nodes=None, ignored_joint_nodes=frozenset()):
    animations = _array(doc.get("animations", []), "animations", 64)
    if animation_index is None:
        if len(animations) > 1:
            raise ImportError("Choose an explicit GLB animation index for a multi-clip file")
        if not animations:
            return {}
        selected = 0
    else:
        selected = _integer(animation_index, 0, len(animations)-1, "selected animation index")
    animation = _object(animations[selected], "animation")
    samplers = _array(animation.get("samplers"), "animation samplers", MAX_ANIMATION_TRACKS)
    channels = _array(animation.get("channels"), "animation channels", MAX_ANIMATION_TRACKS)
    tracks, allowed, time_cache = {}, set(mapping.values()) if hierarchy_nodes is None else set(hierarchy_nodes), {}
    for channel in channels:
        channel = _object(channel, "animation channel")
        target = _object(channel.get("target"), "animation target")
        node, path = target.get("node"), target.get("path")
        if (type(node) is not int or not 0 <= node < len(doc['nodes']) or
                path not in ("translation", "rotation", "scale") or
                (path != "scale" and node not in allowed and node not in ignored_joint_nodes)):
            raise ImportError("Animation targets require source-object/ancestor translation/rotation or exact identity scale")
        if "matrix" in doc['nodes'][node]:
            raise ImportError("Animated GLB nodes cannot contain matrices")
        if (node, path) in tracks:
            raise ImportError("GLB contains duplicate animation target channels")
        si = _integer(channel.get("sampler"), 0, len(samplers) - 1, "animation sampler index")
        sampler = _object(samplers[si], "animation sampler")
        mode = sampler.get("interpolation", "LINEAR")
        if mode not in ("STEP", "LINEAR", "CUBICSPLINE"):
            raise ImportError("Animation interpolation must be STEP, LINEAR or CUBICSPLINE")
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
            raise ImportError("Animation key times exceed the qualified duration; choose bounded external sampling for a longer clip")
        values = accessors.read(sampler.get("output"), "VEC4" if path == "rotation" else "VEC3")
        cubic = mode == "CUBICSPLINE"
        if cubic and len(times) < 2:
            raise ImportError("CUBICSPLINE animation requires at least two keyframes")
        if len(values) != len(times) * (3 if cubic else 1):
            raise ImportError("Animation input and output key counts disagree")
        if path == "rotation":
            if cubic:
                # Tangents are derivatives, not unit quaternions. Retain all raw
                # components/signs for Hermite interpolation; normalize its result.
                for row in values[1::3]:
                    _unit_quaternion(row, "rotation key")
            else:
                values = [_unit_quaternion(row, "rotation key") for row in values]
        if path == "scale" and node not in ignored_joint_nodes:
            # Native rigid records have no scale channel. Prove a constant unit
            # curve over every interval, not just at the sampled PSX frames.
            # glTF Hermite tangents are derivatives: interior incoming and
            # outgoing tangents must be zero. The first incoming and final
            # outgoing tangents never participate in an interval.
            keys = values[1::3] if cubic else values
            tangents = values[2:-3:3] + values[3::3] if cubic else []
            if any(row != [1, 1, 1] for row in keys) or any(row != [0, 0, 0] for row in tangents):
                raise ImportError("Native rigid animation supports only provably constant identity scale tracks")
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
    if mode == "CUBICSPLINE":
        key = max(0, min(index, len(times) - 1))
        if index < 0 or index >= len(times) - 1 or time == times[index]:
            result = list(values[key * 3 + 1])
        else:
            duration = times[index + 1] - times[index]
            t = (time - times[index]) / duration
            # glTF 2.0 Appendix C.5: derivatives scale by segment seconds.
            h0, h1 = 2*t**3 - 3*t**2 + 1, duration*(t**3 - 2*t**2 + t)
            h2, h3 = -2*t**3 + 3*t**2, duration*(t**3 - t**2)
            result = [h0*a + h1*b + h2*c + h3*d for a, b, c, d in zip(
                values[index*3 + 1], values[index*3 + 2],
                values[(index + 1)*3 + 1], values[(index + 1)*3])]
        if any(not math.isfinite(v) for v in result):
            raise ImportError("CUBICSPLINE animation produced a nonfinite sample")
        if rotation:
            norm = math.hypot(*result)
            if norm == 0 or not math.isfinite(norm):
                raise ImportError("CUBICSPLINE rotation produced an invalid zero quaternion")
            result = [v / norm for v in result]
        return result
    if index < 0:
        return list(values[0])
    if index >= len(times) - 1 or mode == "STEP":
        return list(values[index])
    ratio = (time - times[index]) / (times[index + 1] - times[index])
    if rotation:
        return _slerp(values[index], values[index + 1], ratio)
    return [(1 - ratio) * a + ratio * b for a, b in zip(values[index], values[index + 1])]



def _multiply_quaternions(a, b):
    x, y, z, w = a; bx, by, bz, bw = b
    q = [w*bx + x*bw + y*bz - z*by,
         w*by - x*bz + y*bw + z*bx,
         w*bz + x*by - y*bx + z*bw,
         w*bw - x*bx - y*by - z*bz]
    norm = math.hypot(*q)
    if not math.isfinite(norm) or norm == 0:
        raise ImportError("GLB hierarchy produced an invalid orientation")
    return [v / norm for v in q]


def _rotate_vector(q, v):
    # Unit quaternion rotation: v + 2w(q.xyz cross v) +
    # 2(q.xyz cross (q.xyz cross v)). Parent scale is proven unit.
    x, y, z, w = q; vx, vy, vz = v
    cx, cy, cz = y*vz-z*vy, z*vx-x*vz, x*vy-y*vx
    result = [vx+2*(w*cx+y*cz-z*cy),
              vy+2*(w*cy+z*cx-x*cz),
              vz+2*(w*cz+x*cy-y*cx)]
    if any(not _finite_number(v) for v in result):
        raise ImportError("GLB hierarchy produced a nonfinite translation")
    return result


def _sample_hierarchy(order, parents, static, tracks, time):
    poses = {}
    for node in order:
        translation, quaternion = static[node]
        if (node, "translation") in tracks:
            translation = _sample(tracks[(node, "translation")], time)
        if (node, "rotation") in tracks:
            quaternion = _sample(tracks[(node, "rotation")], time, True)
        parent = parents.get(node)
        if parent is not None:
            parent_t, parent_q = poses[parent]
            rotated = _rotate_vector(parent_q, translation)
            translation = [a+b for a,b in zip(parent_t, rotated)]
            if any(not _finite_number(v) for v in translation):
                raise ImportError("GLB hierarchy produced a nonfinite translation")
            quaternion = _multiply_quaternions(parent_q, quaternion)
        poses[node] = (translation, quaternion)
    return poses


def pose_blend_config(value):
    if (not isinstance(value, dict) or set(value) != {'translation_weight','rotation_weight'}
            or any(not _finite_number(v) or not 0 <= v <= 1 for v in value.values())):
        raise ImportError('Pose influence requires explicit finite translation/rotation weights within 0..1')
    return {key:float(value[key]) for key in ('translation_weight','rotation_weight')}


def pose_alignment_config(value, frame_count=4096):
    _integer(frame_count, 1, 4096, "pose alignment output frame count")
    if (not isinstance(value, dict) or set(value) != {'mode','source_frame_index','reference_seconds'}
            or value.get('mode') != 'native_reference_local'):
        raise ImportError('Pose alignment requires native_reference_local mode and explicit frame/time references')
    frame = _integer(value['source_frame_index'], 0, frame_count-1, 'native reference frame')
    seconds = value['reference_seconds']
    if not _finite_number(seconds) or not 0 <= seconds <= 3600:
        raise ImportError('External reference seconds must be finite and within 0..3600')
    return dict(mode='native_reference_local', source_frame_index=frame, reference_seconds=float(seconds))


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


def import_animation_glb(baseline: bytes, content: bytes, *, fps: float, animation_index: int | None = None, object_node_indices: list[int] | None = None, external_sampling: dict | None = None, external_skin_index: int | None = None, external_pose_alignment: dict | None = None, external_pose_blend: dict | None = None) -> tuple[bytes, dict]:
    """Sample external poses at explicit 1..120 fps with fixed native frame count.

    At i/fps, the float32 representation matches glTF key storage and the SDK
    exporter. Default sampling holds endpoints; explicit cyclic sampling maps
    the shared clip extent. No appended source frame is allocated. Y reflection
    is inverted before signed12 and source-biased 8-bit Euler quantization.
    Equivalent source angles survive.
    """
    if not isinstance(baseline, bytes):
        raise ImportError("Animation GLB baseline must be immutable record bytes")
    if type(fps) not in (int, float) or not 1 <= fps <= 120 or not math.isfinite(fps):
        raise ImportError("Animation GLB requires an explicit rate from 1 to 120 fps")
    sampling=sampling_config(external_sampling) if external_sampling is not None else None
    blend=pose_blend_config(external_pose_blend) if external_pose_blend is not None else None
    source = decode_animation_record(baseline)
    alignment = pose_alignment_config(external_pose_alignment, source['frame_count']) if external_pose_alignment is not None else None
    if alignment is not None and object_node_indices is None:
        raise ImportError('Native reference pose alignment requires explicit rigid object mapping')
    if source['bone_count'] > 64:
        raise ImportError('Animation GLB source exceeds the 64 rigid-object bound')
    total = source["frame_count"] * source["bone_count"]
    if total > MAX_CHANNEL_EDITS:
        raise ImportError("Animation GLB source exceeds the 4096-channel bound")
    doc, payload = _read_glb(content)
    accessors=_Accessors(doc,payload)
    mapping, static, parents, rig = _nodes(doc, source["bone_count"], object_node_indices,skin_index=external_skin_index,accessors=accessors)
    order = _hierarchy_order(mapping, parents, source["frame_count"] + (1 if alignment is not None else 0))
    tracks = _tracks(doc, accessors, mapping, (3600 if sampling is not None else source["frame_count"] / fps), animation_index, hierarchy_nodes=order,ignored_joint_nodes=set(rig['joint_nodes'])-set(order) if rig else frozenset())
    mode=sampling.get('mode','clamp') if sampling is not None else 'clamp'
    interval=(dict(start_seconds=min(track[0][0] for track in tracks.values()),
                   end_seconds=max(track[0][-1] for track in tracks.values())) if tracks else None)
    aligned_objects = {}
    if alignment is not None:
        reference_time = struct.unpack('<f', struct.pack('<f', alignment['reference_seconds']))[0]
        external_reference = _sample_hierarchy(order, parents, static, tracks, reference_time)
        for channel in source['frames'][alignment['source_frame_index']]['object_transforms']:
            obj = channel['object_index']
            external_t, external_q = external_reference[mapping[obj]]
            q = _source_quaternion([value//16 for value in channel['rotation_psx']])
            native_q = [-q[0], q[1], -q[2], q[3]]
            correction = _multiply_quaternions(native_q, [-external_q[0], -external_q[1], -external_q[2], external_q[3]])
            native_t = channel['translation'];native_t = [native_t[0], -native_t[1], native_t[2]]
            aligned_objects[obj] = (native_t, external_t, correction)
    edits, maximum_translation, maximum_angle, preserved = [], 0.0, 0.0, 0
    for frame in source["frames"]:
        seconds=(frame['frame_index']/fps if mode!='clamp' else
                 struct.unpack('<f',struct.pack('<f',frame['frame_index']/fps))[0])
        if sampling is not None:seconds=sampling['start_seconds']+seconds*sampling['rate']
        time = struct.unpack("<f", struct.pack("<f", seconds))[0]
        time=_external_time(time,mode,interval)
        poses = _sample_hierarchy(order, parents, static, tracks, time)
        for channel in frame["object_transforms"]:
            obj, before_t, before_r = channel["object_index"], channel["translation"], channel["rotation_psx"]
            node = mapping[obj]
            translation, quaternion = poses[node]
            if alignment is not None:
                native_t, external_t, correction = aligned_objects[obj]
                delta = _rotate_vector(correction, [a-b for a,b in zip(translation, external_t)])
                translation = [a+b for a,b in zip(native_t, delta)]
                quaternion = _multiply_quaternions(correction, quaternion)
            if blend is not None:
                weight = blend['translation_weight']
                native_t = [before_t[0], -before_t[1], before_t[2]]
                if weight == 0:
                    translation = native_t
                elif weight != 1:
                    translation = [(1-weight)*a+weight*b for a,b in zip(native_t,translation)]
                weight = blend['rotation_weight']
                if weight != 1:
                    q = _source_quaternion([value//16 for value in before_r])
                    native_q = [-q[0], q[1], -q[2], q[3]]
                    quaternion = native_q if weight == 0 else _slerp(native_q, quaternion, weight)
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
    report = {
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
                         "timeline": ("float32(start_seconds+float32(i/fps)*rate), fixed source frame count, endpoint hold" if sampling is not None else
                                      "float32(i/fps), fixed source frame count, endpoint hold"),
                         "coordinate_conversion": "translation [x,-y,z]; quaternion [-x,y,-z,w]"},
        "scope": "existing-rigid-animation-channels-only", "gameplay_verified": False,
    }
    if sampling is not None:report['external_sampling']=sampling
    if blend is not None:
        report['external_pose_blend'] = blend
        report['quantization']['timeline'] += '; pose influence blends each sampled/aligned frame with its current native frame before quantization; translation linear, rotation shortest-arc slerp'
    if alignment is not None:
        report['external_pose_alignment'] = alignment
        report['quantization']['timeline'] += '; pose = native_reference * inverse(external_reference) * sampled_external; reference time float32 with endpoint hold'
    if mode!='clamp':
        report['external_time_range']=interval
        report['quantization']['timeline']=report['quantization']['timeline'].replace(
            'float32(i/fps)','i/fps').replace('endpoint hold',
            'shared '+mode+' time mapping; individual track endpoints hold')
        report['quantization']['timeline']+=('; '+mode+' over the selected GLB animation key extent '+str(interval)+
            '; repeat excludes the final endpoint; ping_pong includes both endpoints; zero extent/static poses hold')
    if rig is not None:
        rig['ignored_channels']=[dict(node_index=node,path=path) for node,path in sorted(tracks) if node not in order]
        report['external_rig']=rig
        report['external_skin_index']=external_skin_index
    if object_node_indices is not None:
        report['external_object_nodes'] = list(object_node_indices)
    if animation_index is not None:
        report['file_animation_index'] = animation_index
    return candidate, report
