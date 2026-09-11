"""Ordered OBJ shape interchange, preserving source TMD topology and normals."""
import math
import struct

from .assets import decode_tmd
from .core import ImportError
from .model_authoring import replace_model_shape


def export_shape_obj(source: bytes) -> bytes:
    mesh = decode_tmd(source)
    lines = ['# Legaia object-local shape. Preserve vertex order and faces.',
             '# Source units and Y-down axes; normals/materials remain in the TMD.']
    lines.extend('v ' + ' '.join(str(axis) for axis in vertex) for vertex in mesh['vertices'])
    for obj in mesh['objects']:
        lines.append('g object_' + str(obj['object_index']))
        for tri in mesh['triangles'][obj['triangle_start']:obj['triangle_start']+obj['triangle_count']]:
            lines.append('f ' + ' '.join(str(index+1) for index in tri))
    return ('\n'.join(lines)+'\n').encode('ascii')


def import_shape_obj(source: bytes, source_sha256: str, content: bytes):
    """Import positions only; reject changed indexing/topology rather than guess."""
    if not isinstance(content, bytes) or not 1 <= len(content) <= 16*1024*1024:
        raise ImportError('OBJ shape must contain at most 16 MiB')
    mesh = decode_tmd(source)
    vertices, faces = [], []
    try:
        for line in content.decode('utf-8-sig').splitlines():
            fields = line.split('#',1)[0].split()
            if not fields:
                continue
            kind, values = fields[0], fields[1:]
            if kind == 'v':
                if len(values) != 3 or len(vertices) >= len(mesh['vertices']):
                    raise ImportError('OBJ vertex layout differs from source model')
                point = [float(value) for value in values]
                if any(not math.isfinite(v) or not -32768 <= v <= 32767 or abs(v-round(v)) > 1e-6 for v in point):
                    raise ImportError('OBJ positions must be signed 16-bit integer source coordinates')
                vertices.append([round(v) for v in point])
            elif kind == 'f':
                if len(values) != 3 or len(faces) >= len(mesh['triangles']):
                    raise ImportError('OBJ must preserve source triangulation')
                indices = [int(value.split('/')[0]) for value in values]
                if any(index <= 0 or index > len(mesh['vertices']) for index in indices):
                    raise ImportError('OBJ requires positive source vertex indices')
                faces.append([index-1 for index in indices])
            elif kind not in ('g','o','s','vn','vt','usemtl','mtllib'):
                raise ImportError('Unsupported OBJ directive: ' + kind)
    except (UnicodeError, ValueError) as exc:
        raise ImportError('OBJ contains invalid text or numeric fields') from exc
    if len(vertices) != len(mesh['vertices']) or faces != mesh['triangles']:
        raise ImportError('OBJ vertex count, face order or topology differs from source')
    changed = bytearray(source)
    for obj in mesh['objects']:
        start = 12 + struct.unpack_from('<I',source,12+obj['object_index']*28)[0]
        for index in range(obj['vertex_count']):
            struct.pack_into('<hhh',changed,start+index*8,*vertices[obj['vertex_start']+index])
    return replace_model_shape(source, source_sha256, bytes(changed))
