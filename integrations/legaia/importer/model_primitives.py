"""Source-bound Legaia primitive fields; packet layout and materials stay owned.

Evidence is pinned to d6e64c68 crates/tmd/{descriptor,legaia_prims}.rs and
docs/formats/tmd.md. Vertex references are SVECTOR byte offsets, UV3 occupies
texture bytes 10/11, and RGB excludes each word's GPU command/padding byte.
"""
from hashlib import sha256
import struct

from .assets import _layout, decode_tmd
from .core import ImportError


MAX_PRIMITIVE_EDITS = 4096


def _qualified_model(data: bytes):
    """Qualify global ownership, explicit terminators and declared group counts."""
    if not isinstance(data, bytes):
        raise ImportError('Model primitive inspection requires source bytes')
    shape = decode_tmd(data)
    table_end = 12 + len(shape['objects']) * 28
    spans = [(0, table_end)]
    vectors, objects = [], []
    for obj in shape['objects']:
        index = obj['object_index']
        vert, nv, normal, nn, prim, claimed, _opaque = struct.unpack_from('<7I', data, 12 + index * 28)
        for kind, offset, count in (('vertex', vert + 12, nv), ('normal', normal + 12, nn)):
            if count:
                spans.append((offset, offset + count * 8))
                vectors.append((offset, offset + count * 8, index, kind, count))
        start = prim + 12
        end = min([offset + 12 for offset, count in ((vert, nv), (normal, nn)) if count] or [len(data)])
        spans.append((start, end))
        position, group_index, primitive_index = start, 0, 0
        primitives = []
        terminated = False
        while position + 4 <= end:
            count, flags = struct.unpack_from('<HH', data, position)
            if count == flags == 0:
                terminated = True
                break
            # decode_tmd already bounds the complete header, rows and footer.
            stride = data[position + 5] * 4
            mode = data[position + 7]
            corners, vi, textured, gouraud, uv, baked = _layout(flags)
            for row_index in range(count):
                base = position + 8 + row_index * stride
                refs = list(struct.unpack_from(f'<{corners}H', data, base + vi))
                colors = ([list(data[base + n * 4:base + n * 4 + 3])
                           for n in range(corners if gouraud else 1)] if baked else None)
                uvs = ([list(data[base + uv + delta:base + uv + delta + 2])
                        for delta in (0, 4, 8, 10)[:corners]] if textured else None)
                material = {'clut': None, 'tpage': None, 'semi_transparent': bool(mode & 2)}
                if textured:
                    material.update(clut=struct.unpack_from('<H', data, base + uv + 2)[0],
                                    tpage=struct.unpack_from('<H', data, base + uv + 6)[0])
                primitives.append({'primitive_index': primitive_index, 'group_index': group_index,
                    'flags': flags, 'byte_offset': base, 'vertices': [ref // 8 for ref in refs],
                    'uvs': uvs, 'colors': colors, 'material': material, 'corner_count': corners,
                    'gouraud': gouraud, 'baked_colors': baked})
                primitive_index += 1
            group_index += 1
            position += 8 + (count + 1) * stride
        if not terminated:
            raise ImportError(f'Model object {index} requires an explicit primitive terminator')
        if primitive_index != claimed:
            raise ImportError(f'Model object {index} declared primitive count differs from its groups')
        objects.append({'object_index': index, 'vertex_count': nv, 'primitives': primitives})
    spans.sort()
    if any(start < previous_end for (_, previous_end), (start, _) in zip(spans, spans[1:])):
        raise ImportError('Model authoring does not support aliased table, vector or primitive spans')
    return {'schema_version': 'legaia.model-primitives.v1', 'source_sha256': sha256(data).hexdigest(),
            'objects': objects}, sorted(vectors)


def inspect_model_primitives(data: bytes, *, include_normal_references=False) -> dict:
    """Return detached packet identities and stored values without source payload."""
    inspection = _qualified_model(data)[0]
    if include_normal_references:
        from .model_normal_references import _normal_field_locations
        inspection['schema_version'] = 'legaia.model-primitives.v2'
        for obj in inspection['objects']:
            obj['normal_count'] = struct.unpack_from('<I', data, 24 + obj['object_index'] * 28)[0]
            for row in obj['primitives']:
                row['normal_indices'] = None if row['baked_colors'] else []
        for field, _ in _normal_field_locations(data, inspection):
            inspection['objects'][field['object_index']]['primitives'][field['primitive_index']]['normal_indices'].append(struct.unpack_from('<H', data, field['byte_offset'])[0] // 8)
    return inspection


def _primitive_field_locations(inspection: dict):
    """Yield only proven field locations; all omitted packet bytes are immutable."""
    for obj in inspection['objects']:
        for row in obj['primitives']:
            corners, vi, _textured, _gouraud, uv, _baked = _layout(row['flags'])
            identity = {'kind': 'primitive', 'object_index': obj['object_index'],
                        'primitive_index': row['primitive_index'], 'group_index': row['group_index']}
            for corner in range(corners):
                yield {**identity, 'field': 'vertex_index', 'corner_index': corner,
                       'byte_offset': row['byte_offset'] + vi + corner * 2}, 2
            if row['uvs'] is not None:
                for corner, delta in enumerate((0, 4, 8, 10)[:corners]):
                    for axis, name in enumerate('uv'):
                        yield {**identity, 'field': 'uv', 'corner_index': corner, 'axis': name,
                               'byte_offset': row['byte_offset'] + uv + delta + axis}, 1
            if row['colors'] is not None:
                for corner in range(len(row['colors'])):
                    for axis, name in enumerate('rgb'):
                        yield {**identity, 'field': 'color', 'corner_index': corner, 'axis': name,
                               'byte_offset': row['byte_offset'] + corner * 4 + axis}, 1


def _write_primitive_edit(result, edit, rows, seen, *, offset_origin=0):
    """Write proven operands into model or packet bytes from a qualified source.

    Callers own source qualification and final candidate validation. The internal
    offset origin permits packet allocation to reuse the same typed field checks.
    """
    if (not isinstance(edit, dict) or
            not {'object_index', 'primitive_index'} < set(edit) or
            not set(edit) <= {'object_index', 'primitive_index', 'vertices', 'uvs', 'colors', 'normal_indices'}):
        raise ImportError('Primitive edits require existing identities and vertices, UVs, colors or normal references only')
    if any(type(edit[key]) is not int for key in ('object_index', 'primitive_index')):
        raise ImportError('Primitive identities must be integer source indices')
    identity = edit['object_index'], edit['primitive_index']
    if identity not in rows or identity in seen:
        raise ImportError('Primitive identity is missing or duplicated in this model')
    seen.add(identity)
    obj, row = rows[identity]
    corners, vi, _textured, _gouraud, uv, _baked = _layout(row['flags'])
    base = row['byte_offset'] - offset_origin
    if 'vertices' in edit:
        vertices = edit['vertices']
        if (not isinstance(vertices, list) or len(vertices) != corners or
                any(type(value) is not int or not 0 <= value < min(obj['vertex_count'], 8192)
                    for value in vertices)):
            raise ImportError('Face references must fit the existing object and u16 SVECTOR offsets')
        struct.pack_into(f'<{corners}H', result, base + vi, *(value * 8 for value in vertices))
    if 'normal_indices' in edit:
        values, source = edit['normal_indices'], row['normal_indices']
        if (source is None or not isinstance(values, list) or len(values) != len(source) or
                any(type(v) is not int or not 0 <= v < min(obj['normal_count'], 8192) for v in values)):
            raise ImportError('Normal references must fit the existing lit packet and object normal table')
        relative = (18 if corners == 3 else 20) if row['gouraud'] else (12 if corners == 3 else 20)
        struct.pack_into(f'<{len(values)}H', result, base + relative, *(v * 8 for v in values))
    for field, width in (('uvs', 2), ('colors', 3)):

        if field not in edit:
            continue
        values, source = edit[field], row[field]
        if (source is None or not isinstance(values, list) or len(values) != len(source) or
                any(not isinstance(value, list) or len(value) != width or
                    any(type(v) is not int or not 0 <= v <= 255 for v in value) for value in values)):
            raise ImportError(f'Primitive {field} must match the stored byte-valued layout')
        for corner, value in enumerate(values):
            at = base + ((uv + (0, 4, 8, 10)[corner]) if field == 'uvs' else corner * 4)
            result[at:at + width] = bytes(value)


def patch_model_primitives(data: bytes, expected_sha256: str, edits: list[dict]):
    """Patch existing face/UV/RGB/normal-reference fields while preserving every other byte."""
    inspection = inspect_model_primitives(data, include_normal_references=True)
    if not isinstance(expected_sha256, str) or expected_sha256 != inspection['source_sha256']:
        raise ImportError('Model changed since primitive inspection; reopen the face editor')
    if not isinstance(edits, list) or len(edits) > MAX_PRIMITIVE_EDITS:
        raise ImportError(f'Model authoring accepts at most {MAX_PRIMITIVE_EDITS} primitive edits')
    rows = {(obj['object_index'], row['primitive_index']): (obj, row)
            for obj in inspection['objects'] for row in obj['primitives']}
    result = bytearray(data)
    seen = set()
    for edit in edits:
        _write_primitive_edit(result, edit, rows, seen)
    from .model_authoring import replace_model_content
    return replace_model_content(data, expected_sha256, bytes(result), allow_normal_references=True)
