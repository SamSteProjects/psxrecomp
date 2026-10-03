"""Fixed-layout mesh interchange with explicit source vertex/corner identities.

glTF 2.0 GLB/accessor semantics follow the Khronos specification. Source TMD
packet offsets are owned by model_primitives, pinned to Andrew's d6e64c68.
Positions, existing face references, UV bytes and source-bound baked RGB are
imported. Normals, material words, allocation and opaque source bytes survive.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import math
import re
import struct

from .animation_glb import _read_glb
from .assets import decode_tmd
from .core import ImportError
from .export import encode_model_glb
from .model_authoring import replace_model_content
from .model_primitives import _qualified_model, _primitive_field_locations

MAX_GLB_BYTES = 32 * 1024 * 1024
MAX_ITEMS = 16384
MAX_CORNERS = 300000
MAX_COMPONENTS = 4000000
VERTEX_ID = '_LEGAIA_SOURCE_VERTEX'
CORNER_ID = '_LEGAIA_SOURCE_CORNER'
COLOR_ID = '_LEGAIA_SOURCE_RGB'
LEGACY_PROFILE_SCHEMA = 'legaia.model-glb-profile.v1'
RGB_PROFILE_SCHEMA = 'legaia.model-glb-profile.v2'
PROFILE_SCHEMA = 'legaia.model-glb-profile.v3'
LIMITATIONS = [
    'Positions, stored UVs, baked RGB and existing vertex references within the source object and packet layout.',
    'Normals, material, image, command and opaque source bytes are retained.',
    'Edit raw byte-domain baked RGB through _LEGAIA_SOURCE_RGB; display COLOR_0 is not imported.',
    'No added or removed faces, skinning, animation, hierarchy or unapplied object transforms are imported.',
    'Keep all source identity attributes; import in Blender with Merge Vertices disabled and export custom attributes enabled.',
    'Duplicate seam and quad corners must agree after source-domain quantization.',
]


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ImportError(f'Model GLB {label} is outside its integer bounds')
    return value


def _array(value, label, maximum=MAX_ITEMS):
    if not isinstance(value, list) or len(value) > maximum:
        raise ImportError(f'Model GLB {label} must be a bounded array')
    return value


def _object(value, label):
    if not isinstance(value, dict) or 'extensions' in value:
        raise ImportError(f'Model GLB {label} must be an object without extensions')
    return value


def _write_glb(doc, binary):
    doc['buffers'] = [{'byteLength': len(binary)}]
    metadata = json.dumps(doc, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':')).encode('utf-8')
    metadata += b' ' * (-len(metadata) % 4)
    binary += b'\0' * (-len(binary) % 4)
    size = 28 + len(metadata) + len(binary)
    if size > MAX_GLB_BYTES:
        raise ImportError('Model authoring GLB exceeds the 32 MiB budget')
    return (struct.pack('<3I', 0x46546c67, 2, size) +
            struct.pack('<2I', len(metadata), 0x4e4f534a) + metadata +
            struct.pack('<2I', len(binary), 0x004e4942) + binary)


def _source(data):
    inspection, vectors = _qualified_model(data)
    geometry = decode_tmd(data)
    triangles = {}
    for obj, decoded in zip(inspection['objects'], geometry['objects']):
        rows = []
        at = decoded['triangle_start']
        for primitive in obj['primitives']:
            patterns = [(0, 1, 2)] if primitive['corner_count'] == 3 else [(0, 1, 2), (1, 3, 2)]
            for corners in patterns:
                ids = tuple(primitive['primitive_index'] * 4 + c for c in corners)
                vertices = tuple(primitive['vertices'][c] for c in corners)
                if geometry['triangles'][at] != [decoded['vertex_start'] + v for v in vertices]:
                    raise ImportError('Source primitive triangulation differs from the qualified decoder')
                rows.append({'triangle_index': at, 'corners': ids, 'vertices': vertices,
                             'material': geometry['triangle_materials'][at], 'primitive': primitive})
                at += 1
        if at != decoded['triangle_start'] + decoded['triangle_count']:
            raise ImportError('Source triangle count differs from its primitive layout')
        triangles[obj['object_index']] = rows
    return inspection, vectors, geometry, triangles


def export_model_glb(effective_tmd: bytes, preview: dict) -> tuple[bytes, dict]:
    """Export fresh unposed geometry with stable, per-corner source identifiers."""
    inspection, _vectors, geometry, triangles = _source(effective_tmd)
    if preview.get('posed') or preview.get('coordinate_system') != 'retail_tmd_object_local':
        raise ImportError('Model GLB authoring requires unposed object-local geometry')
    for field in ('vertices', 'triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials'):
        if preview.get(field) != geometry[field]:
            raise ImportError(f'Model authoring preview {field} differs from effective source bytes')
    object_fields = ('object_index', 'vertex_start', 'vertex_count', 'triangle_start', 'triangle_count')
    if ([{key: obj.get(key) for key in object_fields} for obj in preview.get('objects', [])] !=
            [{key: obj[key] for key in object_fields} for obj in geometry['objects']]):
        raise ImportError('Model authoring preview object ranges differ from source')
    glb, _audit = encode_model_glb(preview)
    doc, raw = _read_glb(glb)
    binary = bytearray(raw)

    def accessor(values, width):
        binary.extend(b'\0' * (-len(binary) % 4))
        offset = len(binary)
        flat = [float(v) for row in values for v in row]
        binary.extend(struct.pack(f'<{len(flat)}f', *flat))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset,
                                  'byteLength': len(flat) * 4, 'target': 34962})
        index = len(doc['accessors'])
        doc['accessors'].append({'bufferView': view, 'componentType': 5126,
                                'count': len(values), 'type': 'SCALAR' if width == 1 else f'VEC{width}'})
        return index

    textures = {item['material_index']: item for item in preview.get('textures', [])}
    crops = []
    for index, material in enumerate(geometry['materials']):
        item = textures.get(index, {})
        matched = material['textured'] and item.get('status') == 'address_match'
        crops.append({'material_index': index, 'textured': material['textured'],
                      'uv_origin': deepcopy(item['uv_origin']) if matched else [0, 0],
                      'width': item['width'] if matched else 256,
                      'height': item['height'] if matched else 256})
    for node in doc['nodes']:
        object_index = node['extras']['source_object']['object_index']
        if 'mesh' not in node:
            continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            material = primitive['material']
            crop = crops[material]
            ids, corners, uv, colors = [], [], [], []
            for row in triangles[object_index]:
                if row['material'] != material:
                    continue
                for c in (0, 2, 1):
                    ids.append([row['vertices'][c]])
                    corners.append([row['corners'][c]])
                    source_row = row['primitive']
                    source_corner = row['corners'][c] % 4
                    colors.append(source_row['colors'][source_corner if source_row['gouraud'] else 0]
                                  if source_row['colors'] is not None else [-1, -1, -1])
                    if crop['textured']:
                        point = geometry['triangle_uvs'][row['triangle_index']][c]
                        uv.append([(point[i] - crop['uv_origin'][i] + .5) / crop[axis]
                                   for i, axis in enumerate(('width', 'height'))])
            attrs = primitive['attributes']
            if doc['accessors'][attrs['POSITION']]['count'] != len(ids):
                raise ImportError('Model exporter changed its source corner ordering')
            attrs[VERTEX_ID] = accessor(ids, 1)
            attrs[CORNER_ID] = accessor(corners, 1)
            attrs[COLOR_ID] = accessor(colors, 3)
            # Also carry UVs when texture association is unresolved. Ownership
            # follows source corner IDs, never external material assignments.
            if uv:
                attrs['TEXCOORD_0'] = accessor(uv, 2)
    profile = {'schema_version': PROFILE_SCHEMA, 'effective_sha256': sha256(effective_tmd).hexdigest(),
               'coordinate_conversion': '[x,-y,z]; reverse triangle winding',
               'attributes': {'vertex': VERTEX_ID, 'corner': CORNER_ID, 'color': COLOR_ID},
               'objects': [{'object_index': obj['object_index'], 'vertex_count': obj['vertex_count'],
                            'primitive_count': len(obj['primitives']),
                            'triangle_count': len(triangles[obj['object_index']])} for obj in inspection['objects']],
               'uv_crops': crops, 'imported_fields': ['vertex_xyz', 'primitive_uv', 'primitive_rgb', 'primitive_vertex_indices']}
    return _write_glb(doc, bytes(binary)), profile


class _Accessors:
    """Bounded mesh accessors, including indexed and interleaved Blender output."""
    def __init__(self, doc, binary):
        self.accessors = _array(doc.get('accessors'), 'accessors')
        self.views = _array(doc.get('bufferViews'), 'buffer views')
        self.binary = binary
        self.cache = {}
        self.components = 0

    def read(self, index, width, label, indices=False):
        index = _integer(index, 0, len(self.accessors) - 1, f'{label} accessor')
        key = (index, width, indices)
        if key in self.cache:
            return self.cache[key]
        a = _object(self.accessors[index], f'{label} accessor')
        if a.get('type') != ('SCALAR' if width == 1 else f'VEC{width}') or a.get('normalized', False) is not False or 'sparse' in a:
            raise ImportError(f'Model GLB {label} accessor type, normalization or sparse storage is unsupported')
        component = a.get('componentType')
        formats = {5121: ('B', 1), 5123: ('H', 2), 5125: ('I', 4)} if indices else {5126: ('f', 4)}
        if component not in formats:
            raise ImportError(f'Model GLB {label} accessor component type is unsupported')
        fmt, size = formats[component]
        count = _integer(a.get('count'), 1, MAX_CORNERS, f'{label} count')
        self.components += count * width
        if self.components > MAX_COMPONENTS:
            raise ImportError('Model GLB decoded component budget exceeded')
        view_index = _integer(a.get('bufferView'), 0, len(self.views) - 1, f'{label} buffer view')
        view = _object(self.views[view_index], f'{label} buffer view')
        if view.get('buffer') != 0 or view.get('target') not in (None, 34962, 34963):
            raise ImportError('Model GLB accessor must use its embedded buffer')
        origin = _integer(view.get('byteOffset', 0), 0, len(self.binary), 'view offset')
        length = _integer(view.get('byteLength'), 1, len(self.binary), 'view length')
        relative = _integer(a.get('byteOffset', 0), 0, length, 'accessor offset')
        stride = view.get('byteStride', width * size)
        _integer(stride, width * size, 252, 'accessor stride')
        if ('byteStride' in view and (indices or stride % 4)) or (origin + relative) % size:
            raise ImportError('Model GLB accessor alignment or stride is unsupported')
        if origin + length > len(self.binary) or relative + (count - 1) * stride + width * size > length:
            raise ImportError('Model GLB accessor exceeds its buffer view')
        result = [struct.unpack_from(f'<{width}{fmt}', self.binary, origin + relative + n * stride) for n in range(count)]
        if any(not math.isfinite(v) for row in result for v in row):
            raise ImportError(f'Model GLB {label} contains nonfinite components')
        self.cache[key] = result
        return result


def _canonical_triangle(ids):
    return min(ids, ids[1:] + ids[:1], ids[2:] + ids[:2])


def _profile(profile, data, inspection, geometry, triangles):
    if not isinstance(profile, dict) or set(profile) != {
        'schema_version', 'effective_sha256', 'coordinate_conversion', 'attributes',
        'objects', 'uv_crops', 'imported_fields'}:
        raise ImportError('Model GLB source profile is malformed')
    expected_objects = [{'object_index': obj['object_index'], 'vertex_count': obj['vertex_count'],
                         'primitive_count': len(obj['primitives']),
                         'triangle_count': len(triangles[obj['object_index']])} for obj in inspection['objects']]
    references_enabled = profile['schema_version'] == PROFILE_SCHEMA
    color_enabled = profile['schema_version'] in (PROFILE_SCHEMA, RGB_PROFILE_SCHEMA)
    expected_attributes = {'vertex': VERTEX_ID, 'corner': CORNER_ID}
    expected_fields = ['vertex_xyz', 'primitive_uv']
    if color_enabled:
        expected_attributes['color'] = COLOR_ID
        expected_fields.append('primitive_rgb')
    if references_enabled:
        expected_fields.append('primitive_vertex_indices')
    if (profile['schema_version'] not in (PROFILE_SCHEMA, RGB_PROFILE_SCHEMA, LEGACY_PROFILE_SCHEMA) or profile['effective_sha256'] != sha256(data).hexdigest() or
            profile['coordinate_conversion'] != '[x,-y,z]; reverse triangle winding' or
            profile['attributes'] != expected_attributes or
            profile['imported_fields'] != expected_fields or profile['objects'] != expected_objects):
        raise ImportError('Model GLB profile differs from the effective source layout')
    crops = _array(profile['uv_crops'], 'source UV crops', 256)
    if len(crops) != len(geometry['materials']):
        raise ImportError('Model GLB source material count differs')
    for index, (crop, material) in enumerate(zip(crops, geometry['materials'])):
        if (not isinstance(crop, dict) or set(crop) != {'material_index', 'textured', 'uv_origin', 'width', 'height'} or
                type(crop['material_index']) is not int or crop['material_index'] != index or
                type(crop['textured']) is not bool or crop['textured'] != material['textured']):
            raise ImportError('Model GLB source UV crop identity differs')
        origin = _array(crop['uv_origin'], 'UV origin', 2)
        if len(origin) != 2:
            raise ImportError('Model GLB source UV crop requires two components')
        for axis, dimension in enumerate(('width', 'height')):
            _integer(origin[axis], 0, 255, 'UV origin')
            _integer(crop[dimension], 1, 256 - origin[axis], 'UV dimension')
    return crops, color_enabled, references_enabled


def import_model_glb(effective_tmd: bytes, content: bytes, profile: dict) -> tuple[bytes, dict]:
    """Recover source positions/UVs/RGB/references from IDs; reject topology and alias conflicts."""
    inspection, vectors, geometry, triangles = _source(effective_tmd)
    crops, color_enabled, references_enabled = _profile(profile, effective_tmd, inspection, geometry, triangles)
    doc, binary = _read_glb(content)
    if doc.get('animations') or doc.get('skins') or doc.get('cameras'):
        raise ImportError('Model GLB authoring does not import animation, skinning or cameras')
    if any(not isinstance(image, dict) or 'uri' in image for image in _array(doc.get('images', []), 'images')):
        raise ImportError('Model GLB requires self-contained images; external image URIs are unsupported')
    nodes = _array(doc.get('nodes'), 'nodes', 1024)
    meshes = _array(doc.get('meshes'), 'meshes', 1024)
    scenes = _array(doc.get('scenes'), 'scenes', 1)
    if len(scenes) != 1 or doc.get('scene', 0) != 0:
        raise ImportError('Model GLB authoring requires one flat source scene')
    roots = _array(_object(scenes[0], 'scene').get('nodes'), 'root nodes', 1024)
    if any(type(i) is not int for i in roots) or sorted(roots) != list(range(len(nodes))):
        raise ImportError('Model GLB requires each source object exactly once as a root')
    if len(nodes) != len(inspection['objects']):
        raise ImportError('Model GLB object count differs from the source')
    reader = _Accessors(doc, binary)
    result = bytearray(effective_tmd)
    positions, uv_values, color_values, reference_values = {}, {}, {}, {}
    seen_objects, seen_meshes = set(), set()
    quantization = dict(vertex_max_error=0.0, uv_max_error=0.0,
                        color_max_error=0.0, quantized_component_count=0)
    quantized_keys = set()

    def quantize(value, low, high, kind, key):
        # Float32 UV arithmetic produces sub-ulp deviations at source endpoints.
        # A 1e-4 byte tolerance only stabilizes those endpoints, never an overflow
        # by a meaningful source fraction. Interior edits retain reviewed error.
        epsilon = 1e-4 if kind == 'uv' else 0
        if not math.isfinite(value) or value < low - epsilon or value > high + epsilon:
            raise ImportError(f'Model GLB {kind} is outside the source integer domain')
        raw_value = value
        value = min(high, max(low, value))
        rounded = round(value)
        error = abs(raw_value - rounded)
        quantization[kind + '_max_error'] = max(quantization[kind + '_max_error'], error)
        if error > 1e-5:
            quantized_keys.add(key)
        return rounded

    for node in nodes:
        node = _object(node, 'source object node')
        match = re.fullmatch(r'object-(0|[1-9][0-9]*)', node.get('name', '') if isinstance(node.get('name'), str) else '')
        if not match:
            raise ImportError('Model GLB nodes must retain their object-N source names')
        identity = int(match.group(1))
        if identity not in triangles or identity in seen_objects:
            raise ImportError('Model GLB source object identity is missing or duplicated')
        seen_objects.add(identity)
        source_object = node.get('extras', {}).get('source_object') if isinstance(node.get('extras', {}), dict) else None
        if source_object is not None and (not isinstance(source_object, dict) or type(source_object.get('object_index')) is not int or source_object['object_index'] != identity):
            raise ImportError('Model GLB source object metadata conflicts with its name')
        if node.get('children') or any(key in node for key in ('skin', 'camera', 'weights')):
            raise ImportError('Model GLB source hierarchy, skinning and morph weights are unsupported')
        for key, default in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]),
                             ('scale', [1, 1, 1]), ('matrix', [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])):
            if key in node and node[key] != default:
                raise ImportError('Apply object transforms to mesh coordinates before model GLB export')
        expected = Counter(_canonical_triangle(tuple(row['corners'][c] for c in (0, 2, 1))) for row in triangles[identity])
        actual = Counter()
        source_corners = {row['primitive_index'] * 4 + corner: (row, corner)
                          for row in inspection['objects'][identity]['primitives'] for corner in range(row['corner_count'])}
        source_materials = {row['primitive']['primitive_index']: row['material'] for row in triangles[identity]}
        if not expected:
            if 'mesh' in node:
                raise ImportError('Model GLB added geometry to an empty source object')
            continue
        mesh_index = _integer(node.get('mesh'), 0, len(meshes) - 1, 'mesh index')
        if mesh_index in seen_meshes:
            raise ImportError('Model GLB source mesh instancing is unsupported')
        seen_meshes.add(mesh_index)
        mesh = _object(meshes[mesh_index], 'mesh')
        if mesh.get('weights'):
            raise ImportError('Model GLB morph weights are unsupported')
        for primitive in _array(mesh.get('primitives'), 'mesh primitives'):
            primitive = _object(primitive, 'mesh primitive')
            if primitive.get('mode', 4) != 4 or primitive.get('targets'):
                raise ImportError('Model GLB accepts existing triangles without morph targets')
            attrs = _object(primitive.get('attributes'), 'vertex attributes')
            if any(key.startswith('JOINTS_') or key.startswith('WEIGHTS_') for key in attrs):
                raise ImportError('Model GLB skinned mesh attributes are unsupported')
            values = reader.read(attrs.get('POSITION'), 3, 'positions')
            vertex_ids = reader.read(attrs.get(VERTEX_ID), 1, 'source vertex IDs')
            corner_ids = reader.read(attrs.get(CORNER_ID), 1, 'source corner IDs')
            if len(vertex_ids) != len(values) or len(corner_ids) != len(values):
                raise ImportError('Model GLB identity attributes must match position count')
            uv = reader.read(attrs['TEXCOORD_0'], 2, 'UVs') if 'TEXCOORD_0' in attrs else None
            if uv is not None and len(uv) != len(values):
                raise ImportError('Model GLB UV count differs from its positions')
            colors = reader.read(attrs.get(COLOR_ID), 3, 'source RGB') if color_enabled else None
            if colors is not None and len(colors) != len(values):
                raise ImportError('Model GLB source RGB count differs from its positions')
            if color_enabled:
                # Validate every attribute row, including unused indexed seam
                # copies, so an ignored index cannot hide an RGB alias conflict.
                for rgb_value, corner_value, vertex_value, position_value in zip(colors, corner_ids, vertex_ids, values):
                    corner_id, vertex_id = corner_value[0], vertex_value[0]
                    if (corner_id != int(corner_id) or vertex_id != int(vertex_id) or
                            int(corner_id) not in source_corners):
                        raise ImportError('Model GLB source RGB identity values are invalid')
                    row, corner = source_corners[int(corner_id)]
                    if references_enabled:
                        _integer(int(vertex_id), 0, min(8191, inspection['objects'][identity]['vertex_count'] - 1),
                                 'source vertex reference')
                        reference_key = identity, row['primitive_index'], corner
                        if reference_key in reference_values and reference_values[reference_key] != int(vertex_id):
                            raise ImportError('Model GLB duplicate source corner vertex references disagree')
                        reference_values[reference_key] = int(vertex_id)
                        xyz = tuple(quantize(v * sign, -32768, 32767, 'vertex',
                                             ('vertex', identity, int(vertex_id), axis))
                                    for axis, (v, sign) in enumerate(zip(position_value, (1, -1, 1))))
                        position_key = identity, int(vertex_id)
                        if position_key in positions and positions[position_key] != xyz:
                            raise ImportError('Model GLB duplicate vertex seam copies disagree after quantization')
                        positions[position_key] = xyz
                    elif int(vertex_id) != row['vertices'][corner]:
                        raise ImportError('Model GLB source RGB vertex identity conflicts with its corner')
                    if row['colors'] is None:
                        if tuple(rgb_value) != (-1, -1, -1):
                            raise ImportError('Model GLB unbaked RGB sentinel must remain unchanged')
                    else:
                        slot = corner if row['gouraud'] else 0
                        rgb = tuple(quantize(v, 0, 255, 'color',
                                    ('color', identity, row['primitive_index'], slot, axis))
                                    for axis, v in enumerate(rgb_value))
                        color_key = identity, row['primitive_index'], slot
                        if color_key in color_values and color_values[color_key] != rgb:
                            raise ImportError('Model GLB duplicate source RGB copies disagree after quantization')
                        color_values[color_key] = rgb
            indices = [row[0] for row in reader.read(primitive['indices'], 1, 'indices', True)] if 'indices' in primitive else list(range(len(values)))
            if len(indices) % 3:
                raise ImportError('Model GLB triangle index count is incomplete')
            for first in range(0, len(indices), 3):
                signature = []
                for index in indices[first:first + 3]:
                    _integer(index, 0, len(values) - 1, 'triangle vertex index')
                    vertex_id, corner_id = vertex_ids[index][0], corner_ids[index][0]
                    if vertex_id != int(vertex_id) or corner_id != int(corner_id) or int(corner_id) not in source_corners:
                        raise ImportError('Model GLB source identity values are invalid')
                    vertex_id, corner_id = int(vertex_id), int(corner_id)
                    row, corner = source_corners[corner_id]
                    if not references_enabled and vertex_id != row['vertices'][corner]:
                        raise ImportError('Model GLB source vertex identity conflicts with its corner')
                    signature.append(corner_id)
                    xyz = tuple(quantize(v * sign, -32768, 32767, 'vertex', ('vertex', identity, vertex_id, axis))
                                for axis, (v, sign) in enumerate(zip(values[index], (1, -1, 1))))
                    key = identity, vertex_id
                    if key in positions and positions[key] != xyz:
                        raise ImportError('Model GLB duplicate vertex seam copies disagree after quantization')
                    positions[key] = xyz
                    if row['uvs'] is not None:
                        if uv is None:
                            raise ImportError('Model GLB lost UVs for a textured source corner')
                        material = source_materials[row['primitive_index']]
                        crop = crops[material]
                        point = tuple(quantize(uv[index][axis] * crop[dimension] + crop['uv_origin'][axis] - .5,
                                               0, 255, 'uv', ('uv', identity, corner_id, axis))
                                      for axis, dimension in enumerate(('width', 'height')))
                        key = identity, corner_id
                        if key in uv_values and uv_values[key] != point:
                            raise ImportError('Model GLB duplicate quad UV copies disagree after quantization')
                        uv_values[key] = point
                actual[_canonical_triangle(tuple(signature))] += 1
                if len(actual) > len(expected) or actual[_canonical_triangle(tuple(signature))] > expected[_canonical_triangle(tuple(signature))]:
                    raise ImportError('Model GLB triangle topology or winding differs from source corner identities')
        if actual != expected:
            raise ImportError('Model GLB omitted or changed source triangles')
    if seen_meshes != set(range(len(meshes))):
        raise ImportError('Model GLB contains unowned mesh data')
    for offset, _end, identity, kind, _count in vectors:
        if kind == 'vertex':
            for (object_id, vertex_id), xyz in positions.items():
                if object_id == identity:
                    struct.pack_into('<3h', result, offset + vertex_id * 8, *xyz)
    for field, _width in _primitive_field_locations(inspection):
        if references_enabled and field.get('field') == 'vertex_index':
            key = field['object_index'], field['primitive_index'], field['corner_index']
            struct.pack_into('<H', result, field['byte_offset'], reference_values[key] * 8)
        elif field.get('field') == 'uv':
            key = field['object_index'], field['primitive_index'] * 4 + field['corner_index']
            point = uv_values[key]
            result[field['byte_offset']] = point[0 if field['axis'] == 'u' else 1]
        elif color_enabled and field.get('field') == 'color':
            key = field['object_index'], field['primitive_index'], field['corner_index']
            result[field['byte_offset']] = color_values[key]['rgb'.index(field['axis'])]
    candidate, changes = replace_model_content(effective_tmd, sha256(effective_tmd).hexdigest(), bytes(result))
    if len(changes) > 65536:
        raise ImportError('Model GLB changes exceed the source audit budget')
    quantization['quantized_component_count'] = len(quantized_keys)
    return candidate, {'quantization': quantization, 'limitations': (list(LIMITATIONS) if references_enabled else [
                           'Legacy v2 imports positions, stored UVs and baked RGB; vertex references are retained.',
                           *LIMITATIONS[1:]]) if color_enabled else [
                           'Legacy v1 imports positions and stored UVs only; baked RGB is retained.',
                           *LIMITATIONS[3:]],
                       'changed_field_count': len(changes)}
