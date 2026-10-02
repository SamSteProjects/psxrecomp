"""Source-bound existing-layout vertex/normal interchange in source units."""
from hashlib import sha256
import json
import struct

from .assets import decode_tmd
from .core import ImportError
from .model_authoring import replace_model_shape, replace_model_content

MAX_JSON_BYTES = 16 * 1024 * 1024


def rotate_shape_object(original: bytes, effective: bytes, expected_sha256: str,
                        object_index: int, axis: str, quarter_turns: int) -> bytes:
    """Exact signed permutations around an object's source-local origin."""
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since object inspection; reopen the vector editor')
    if axis not in ('x','y','z') or type(quarter_turns) is not int or quarter_turns not in (-1,1,2):
        raise ImportError('Choose a source XYZ axis and −90, +90 or 180 degree turn')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original,source_hash,effective)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj = document['objects'][object_index]
    if not obj['vertices']:
        raise ImportError('The selected object has no vertices')
    def rotate(vector):
        x,y,z = vector
        for _ in range(quarter_turns % 4):
            x,y,z = (x,-z,y) if axis == 'x' else (z,y,-x) if axis == 'y' else (-y,x,z)
        if any(not -32768 <= value <= 32767 for value in (x,y,z)):
            raise ImportError('Object rotation exceeds signed16 vector values; nothing was applied')
        return [x,y,z]
    for kind in ('vertices','normals'):
        obj[kind] = [rotate(vector) for vector in obj[kind]]
    replacement = import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0]
    return replace_model_content(original,source_hash,replacement)[0]


def translate_shape_object(original: bytes, effective: bytes, expected_sha256: str,
                           object_index: int, offset: list[int]) -> bytes:
    """Translate a source-bound object without changing other model spans."""
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since object inspection; reopen the vector editor')
    if not isinstance(offset, list) or len(offset) != 3 or any(type(v) is not int or not -65535 <= v <= 65535 for v in offset):
        raise ImportError('Object offset requires three integer source-unit values within ±65535')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original, source_hash, effective)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    vertices = document['objects'][object_index]['vertices']
    if not vertices:
        raise ImportError('The selected object has no vertices')
    translated = [[v + offset[a] for a, v in enumerate(vertex)] for vertex in vertices]
    if any(not -32768 <= v <= 32767 for vertex in translated for v in vertex):
        raise ImportError('Object translation exceeds signed16 vertex coordinates; nothing was applied')
    document['objects'][object_index]['vertices'] = translated
    replacement = import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0]
    return replace_model_content(original,source_hash,replacement)[0]


def scale_shape_object(original: bytes, effective: bytes, expected_sha256: str,
                       object_index: int, percent: int) -> bytes:
    """Positive uniform vertex scaling; nearest integer, half away from zero."""
    if sha256(effective).hexdigest() != expected_sha256:
        raise ImportError('Model changed since object inspection; reopen the vector editor')
    if type(percent) is not int or not 1 <= percent <= 1000:
        raise ImportError('Object scale requires an integer percent1..1000')
    source_hash = sha256(original).hexdigest()
    replace_model_content(original,source_hash,effective)
    document = json.loads(export_shape_json(effective))
    if type(object_index) is not int or not 0 <= object_index < len(document['objects']):
        raise ImportError('Choose an existing model object')
    obj = document['objects'][object_index]
    if not obj['vertices']:
        raise ImportError('The selected object has no vertices')
    def scale(value):
        result = ((abs(value)*percent+50)//100) * (-1 if value < 0 else 1)
        if not -32768 <= result <= 32767:
            raise ImportError('Object scale exceeds signed16 vertex values; nothing was applied')
        return result
    obj['vertices'] = [[scale(v) for v in vector] for vector in obj['vertices']]
    replacement = import_shape_json(effective,expected_sha256,json.dumps(document).encode())[0]
    return replace_model_content(original,source_hash,replacement)[0]


def export_shape_json(source: bytes) -> bytes:
    digest = sha256(source).hexdigest()
    replace_model_shape(source, digest, source)
    objects = []
    for obj in decode_tmd(source)['objects']:
        index = obj['object_index']
        vert, count, normal, normals = struct.unpack_from('<4I', source, 12 + index * 28)
        objects.append({'object_index': index,
                        'vertices': [list(struct.unpack_from('<3h', source, 12 + vert + n * 8)) for n in range(count)],
                        'normals': [list(struct.unpack_from('<3h', source, 12 + normal + n * 8)) for n in range(normals)]})
    content = (json.dumps({'schema_version': 'legaia.model-shape.v1', 'source_sha256': digest,
                           'coordinate_system': 'retail_psx_object_local_y_down', 'objects': objects},
                          indent=2, sort_keys=True) + '\n').encode('utf-8')
    if len(content) > MAX_JSON_BYTES:
        raise ImportError('Model shape JSON exceeds 16 MiB')
    return content


def import_shape_json(source: bytes, source_sha256: str, content: bytes):
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_JSON_BYTES:
        raise ImportError('Model shape JSON requires at most 16 MiB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    try:
        document = json.loads(content.decode('utf-8-sig'), object_pairs_hook=unique)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ImportError('Model shape requires unambiguous JSON') from exc
    if (not isinstance(document, dict) or set(document) != {'schema_version','source_sha256','coordinate_system','objects'} or
            document['schema_version'] != 'legaia.model-shape.v1' or
            document['coordinate_system'] != 'retail_psx_object_local_y_down' or
            document['source_sha256'] != source_sha256):
        raise ImportError('Model shape JSON schema, coordinates or source binding differ')
    replace_model_shape(source, source_sha256, source)
    objects = decode_tmd(source)['objects']
    if not isinstance(document['objects'], list) or len(document['objects']) != len(objects):
        raise ImportError('Model shape JSON must preserve every source object')
    changed = bytearray(source)
    for original, item in zip(objects, document['objects']):
        index = original['object_index']
        if (not isinstance(item, dict) or set(item) != {'object_index','vertices','normals'} or
                type(item['object_index']) is not int or item['object_index'] != index):
            raise ImportError('Model shape JSON must retain ordered object identities')
        vert, count, normal, normals = struct.unpack_from('<4I', source, 12 + index * 28)
        for field, offset, size in (('vertices', vert, count), ('normals', normal, normals)):
            vectors = item[field]
            if not isinstance(vectors, list) or len(vectors) != size:
                raise ImportError('Model shape JSON vector count differs from source')
            for n, vector in enumerate(vectors):
                if (not isinstance(vector, list) or len(vector) != 3 or
                        any(type(v) is not int or not -32768 <= v <= 32767 for v in vector)):
                    raise ImportError('Model shape vectors require three signed 16-bit integers')
                struct.pack_into('<3h', changed, 12 + offset + n * 8, *vector)
    return replace_model_shape(source, source_sha256, bytes(changed))
