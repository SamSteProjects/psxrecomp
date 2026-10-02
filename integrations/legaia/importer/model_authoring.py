"""Source-bound TMD shape and existing-layout content replacement.

Object-local vertex and normal XYZ words are writable. Legacy shape bindings
keep primitives source-owned. Versioned content bindings
also permit proven face references, UV bytes and baked RGB without reallocating
packets or changing material bindings and vector padding.
"""
from hashlib import sha256
import struct

from .assets import decode_tmd
from .core import ImportError


def preview_model_shape(preview: dict, replacement: bytes, binding: dict):
    """Compose candidate content through already-verified rigid pose channels."""
    from copy import deepcopy
    from .animation import pose_vertices, _bounds
    result = deepcopy(preview)
    shape = decode_tmd(replacement)
    objects = result['objects']
    # Party poses intentionally omit trailing equipment objects; only accept the
    # same prefix/ranges, never infer a new object-to-channel association.
    if len(objects) > len(shape['objects']) or any(
            any(obj[k] != shape['objects'][i][k] for k in
                ('object_index','vertex_start','vertex_count','triangle_start','triangle_count'))
            for i,obj in enumerate(objects)):
        raise ImportError('Shape objects do not match the existing pose layout')
    count = sum(obj['vertex_count'] for obj in objects)
    vertices = shape['vertices'][:count]
    if len(vertices) != len(result['vertices']):
        raise ImportError('Shape vertex count differs from preview geometry')
    triangle_count = sum(obj['triangle_count'] for obj in objects)
    if triangle_count != len(result['triangles']):
        raise ImportError('Model face count differs from preview geometry')
    # Material identities use only unchanged flags/mode/CLUT/page words. Keep
    # any already-associated metadata (e.g. blend evidence), but reject changed
    # keys instead of assigning a candidate face to an unrelated texture.
    material_fields = ('textured', 'clut', 'tpage', 'semi_transparent')
    if (len(result['materials']) != len(shape['materials']) or
            any(any(old.get(key) != new.get(key) for key in material_fields)
                for old, new in zip(result['materials'], shape['materials']))):
        raise ImportError('Model content changed source material bindings')
    for key in ('triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials'):
        result[key] = deepcopy(shape[key][:triangle_count])
    transforms = result.get('pose', {}).get('object_transforms')
    if result.get('posed') and transforms is None and not result.get('frames'):
        raise ImportError('Shape preview requires explicit pose transforms')
    result['vertices'] = pose_vertices(vertices, objects, transforms) if transforms is not None else vertices
    result['bounds'] = _bounds(result['vertices'])
    for frame in result.get('frames', []):
        frame['vertices'] = pose_vertices(vertices, objects, frame['object_transforms'])
        frame['bounds'] = _bounds(frame['vertices'])
    result['representation'] = 'authored-shape'
    result['authored_shape'] = deepcopy(binding)
    return result


def replace_model_shape(original: bytes, expected_sha256: str, replacement: bytes):
    """Validate a same-layout TMD and return its audited coordinate changes."""
    if not isinstance(original, bytes) or sha256(original).hexdigest() != expected_sha256:
        raise ImportError("Model source hash differs from the authored binding")
    source = decode_tmd(original)
    if not isinstance(replacement, bytes) or len(replacement) != len(original):
        raise ImportError("Shape replacement must preserve the source TMD byte length")
    table_end = 12 + len(source['objects']) * 28
    spans = []
    for obj in source['objects']:
        index = obj['object_index']
        vert, count, normal, normal_count = struct.unpack_from('<4I', original, 12 + index * 28)
        for kind, start, size in (('vertex', vert + 12, count), ('normal', normal + 12, normal_count)):
            if size:
                spans.append((start, start + size * 8, index, kind, size))
    spans.sort()
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        raise ImportError("Shape replacement does not support aliased vector tables")
    # Primitive decoding bounds a packet stream by its own first vector table.
    # Protect every object's complete primitive interval, including opaque tail.
    for obj in source['objects']:
        vert, count, normal, normals, prim = struct.unpack_from('<5I', original, 12 + obj['object_index'] * 28)
        end = min([offset + 12 for offset, n in ((vert, count), (normal, normals)) if n] or [len(original)])
        if any(start < end and stop > prim + 12 for start, stop, *_ in spans):
            raise ImportError("Shape replacement vector table overlaps primitive data")
    allowed = bytearray(len(original))
    audit = []
    for start, stop, index, kind, count in spans:
        for vector in range(count):
            offset = start + vector * 8
            for axis in range(3):
                at = offset + axis * 2
                allowed[at:at+2] = b'\x01\x01'
                before = struct.unpack_from('<h', original, at)[0]
                after = struct.unpack_from('<h', replacement, at)[0]
                if before != after:
                    audit.append(dict(object_index=index, kind=kind, vector_index=vector,
                                      axis='xyz'[axis], byte_offset=at, before_value=before, after_value=after))
    if original[:table_end] != replacement[:table_end] or any(a != b and not allowed[i] for i, (a,b) in enumerate(zip(original,replacement))):
        raise ImportError("Shape replacement changed topology, material, descriptor or padding bytes")
    decode_tmd(replacement)
    return replacement, audit


def replace_model_content(original: bytes, expected_sha256: str, replacement: bytes):
    """Validate the union of XYZ and proven primitive fields, with exact audit."""
    from .model_primitives import _qualified_model, _primitive_field_locations
    if not isinstance(original, bytes) or sha256(original).hexdigest() != expected_sha256:
        raise ImportError('Model source hash differs from the authored binding')
    inspection, vectors = _qualified_model(original)
    if not isinstance(replacement, bytes) or len(replacement) != len(original):
        raise ImportError('Model content must preserve the source TMD byte length')
    allowed = bytearray(len(original))
    audit = []
    for start, _stop, index, kind, count in vectors:
        for vector in range(count):
            for axis in range(3):
                at = start + vector * 8 + axis * 2
                allowed[at:at + 2] = b'\x01\x01'
                before = struct.unpack_from('<h', original, at)[0]
                after = struct.unpack_from('<h', replacement, at)[0]
                if before != after:
                    audit.append(dict(object_index=index, kind=kind, vector_index=vector,
                                      axis='xyz'[axis], byte_offset=at,
                                      before_value=before, after_value=after))
    for identity, width in _primitive_field_locations(inspection):
        at = identity['byte_offset']
        allowed[at:at + width] = b'\x01' * width
        before, after = original[at], replacement[at]
        if width == 2:
            before = struct.unpack_from('<H', original, at)[0] // 8
            raw_after = struct.unpack_from('<H', replacement, at)[0]
            if raw_after % 8:
                raise ImportError('Face reference must be an aligned SVECTOR byte offset')
            after = raw_after // 8
        if before != after:
            audit.append({**identity, 'before_value': before, 'after_value': after})
    differences = {i: (a, b) for i, (a, b) in enumerate(zip(original, replacement)) if a != b}
    if any(not allowed[at] for at in differences):
        raise ImportError('Model content changed layout, material, normal reference or opaque bytes')
    _qualified_model(replacement)
    audited = {}
    for change in audit:
        at = change['byte_offset']
        primitive = change['kind'] == 'primitive'
        if primitive and change['field'] == 'vertex_index':
            before = struct.pack('<H', change['before_value'] * 8)
            after = struct.pack('<H', change['after_value'] * 8)
        elif primitive:
            before, after = bytes([change['before_value']]), bytes([change['after_value']])
        else:
            before = struct.pack('<h', change['before_value'])
            after = struct.pack('<h', change['after_value'])
        for delta, (a, b) in enumerate(zip(before, after)):
            if a != b:
                if at + delta in audited:
                    raise ImportError('Model content audit fields overlap')
                audited[at + delta] = (a, b)
    if differences != audited:
        raise ImportError('Model content changed an unaudited byte')
    return replacement, audit


def model_shape_overlays(archive, assets: dict, replacements: dict):
    """Compose model members sharing one compressed stream before encoding."""
    from .core import parse_lzs_sections, decompress_lzs
    from .serialization import serialize_lzs_decoded
    groups = {}
    for identifier, payload in replacements.items():
        source = assets[identifier]['source_record']
        kind = source['record_kind']
        if kind not in ('raw_prot_entry', 'decoded_lzs_section', 'decoded_tmd_pack_slot'):
            raise ImportError('Unsupported model replacement container')
        key = (source['prot_entry_index'], source.get('container_section') if kind != 'raw_prot_entry' else None)
        groups.setdefault(key, []).append(identifier)
    overlays, audit = [], []
    for (entry_index, section_index), identifiers in sorted(groups.items(), key=lambda item: str(item[0])):
        entry = archive.entry(entry_index)
        body = archive.read_entry(entry)
        location = (archive.node.extent_lba + entry.start_lba) * 2048
        stream = None
        if section_index is not None:
            sections = parse_lzs_sections(body)
            section = sections[section_index]
            end = sections[section_index+1].stream_offset if section_index+1 < len(sections) else len(body)
            decoded, consumed = decompress_lzs(body[section.stream_offset:end], section.decoded_size)
            stream = body[section.stream_offset:section.stream_offset+consumed]
            location += section.stream_offset
        else:
            decoded = body
        changed = bytearray(decoded)
        intervals = []
        for identifier in sorted(identifiers):
            source = assets[identifier]['source_record']
            start, length = source['byte_offset'], source['byte_length']
            if len(decoded) != source['containing_size'] or start < 0 or start+length > len(decoded):
                raise ImportError('Model replacement source bounds changed')
            original = decoded[start:start+length]
            payload, changes = replace_model_content(original, sha256(original).hexdigest(), replacements[identifier])
            if not changes:
                continue
            if any(start < b and start+length > a for a,b in intervals):
                raise ImportError('Model replacement source members overlap')
            intervals.append((start,start+length))
            changed[start:start+length] = payload
            scope = ('TMD-existing-layout-content' if any(c['kind'] == 'primitive' for c in changes)
                     else 'TMD-vertex-normal-XYZ-only')
            audit.append(dict(semantic_id=identifier, field='model.shape', scope=scope,
                              before_sha256=sha256(original).hexdigest(), after_sha256=sha256(payload).hexdigest(),
                              coordinate_changes=changes))
            if stream is None:
                overlays.append(dict(offset=location+start, size=length, payload=payload,
                                     sha256=sha256(payload).hexdigest(), expected_sha256=sha256(original).hexdigest()))
        if stream is not None and intervals:
            payload, stats = serialize_lzs_decoded(stream, len(decoded), bytes(changed), 'model shapes')
            overlays.append(dict(offset=location, size=len(payload), payload=payload,
                                 sha256=sha256(payload).hexdigest(), expected_sha256=sha256(stream).hexdigest(),
                                 decoded_before_sha256=sha256(decoded).hexdigest(),
                                 decoded_after_sha256=sha256(changed).hexdigest(), **stats))
    return overlays, audit
