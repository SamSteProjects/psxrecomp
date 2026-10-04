"""Source-bound TMD shape and existing-layout content replacement.

Object-local vertex and normal XYZ words are writable. Legacy shape bindings
keep primitives source-owned. Versioned content bindings
also permit proven face references, UV bytes and baked RGB without reallocating
packets. V2 adds masked CLUT/page selectors and group ABE, preserving source ABR,
reserved bits, all packet layout and vector padding. V3 explicitly permits
qualified existing lit normal references within the source object normal table.
"""
from hashlib import sha256
from itertools import chain
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
    topology_changed = binding.get('format') in ('tmd-face-removal-v1', 'tmd-face-addition-v1')
    vector_growth=None
    if binding.get('format')=='tmd-face-addition-v1' and binding.get('ledger',{}).get('schema_version') in ('legaia.model-face-addition-ledger.v5','legaia.model-face-addition-ledger.v6'):
        from .model_face_ledger import _operations,MAX_LEDGER_VECTORS
        from .model_primitives import _qualified_model
        _qualified_model(replacement)
        if binding.get('asset_sha256')!=sha256(replacement).hexdigest() or binding.get('byte_length')!=len(replacement):
            raise ImportError('Allocated vector preview differs from its qualified binding')
        vector_growth=[0]*len(shape['objects']);total=0
        for operation in _operations(binding['ledger']):
            if not isinstance(operation,dict):raise ImportError('Allocated vector preview requires typed operations')
            if operation.get('kind')!='allocate_vectors':continue
            if set(operation)!={'kind','input_sha256','proposed_sha256','requests'} or not isinstance(operation['requests'],list):
                raise ImportError('Allocated vector preview operation schema changed')
            seen=set()
            for request in operation['requests']:
                if (not isinstance(request,dict) or set(request)!={'object_index','kind','vectors'}
                        or type(request['object_index']) is not int or not 0<=request['object_index']<len(vector_growth)
                        or request['kind'] not in ('vertices','normals') or not isinstance(request['vectors'],list)
                        or not request['vectors'] or any(not isinstance(row,list) or len(row)!=3 or any(
                            type(value) is not int or not -32768<=value<=32767 for value in row) for row in request['vectors'])):
                    raise ImportError('Allocated vector preview ownership changed')
                identity=(request['object_index'],request['kind'])
                if identity in seen:raise ImportError('Allocated vector preview repeats table ownership')
                seen.add(identity);total+=len(request['vectors'])
                if total>MAX_LEDGER_VECTORS:raise ImportError('Allocated vector preview exceeds its row budget')
                if request['kind']=='vertices':vector_growth[request['object_index']]+=len(request['vectors'])
        preceding=result.get('authored_shape',{})
        if preceding.get('format')=='tmd-face-addition-v1' and 'ledger' in preceding:
            old=preceding['ledger'];new=binding['ledger'];old_operations=_operations(old);new_operations=_operations(new)
            if (any(old[key]!=new[key] for key in ('source_sha256','source_byte_length'))
                    or old_operations!=new_operations[:len(old_operations)]
                    or preceding.get('asset_sha256')!=(old_operations[-1]['proposed_sha256'] if old_operations else old['source_sha256'])):
                raise ImportError('Allocated vector preview is not a continuation of its Current ledger')
            # Current scene geometry already contains these allocations.
            for operation in old_operations:
                if operation['kind']=='allocate_vectors':
                    for request in operation['requests']:
                        if request['kind']=='vertices':vector_growth[request['object_index']]-=len(request['vectors'])
    # Party poses omit trailing equipment objects. Qualified V5 append counts
    # may enlarge the same prefix; never infer a new object/channel association.
    if vector_growth is not None:
        old_count=0
        if len(objects)>len(shape['objects']):raise ImportError('Allocated vectors cannot infer new pose channels')
        for i,obj in enumerate(objects):
            if (obj.get('object_index')!=i or obj.get('vertex_start')!=old_count
                    or type(obj.get('vertex_count')) is not int or obj['vertex_count']<0
                    or shape['objects'][i]['vertex_count']!=obj['vertex_count']+vector_growth[i]):
                raise ImportError('Allocated vectors do not match their existing object channel')
            old_count+=obj['vertex_count']
        if old_count!=len(result['vertices']):raise ImportError('Allocated vector source preview has incomplete ownership')
        for i,obj in enumerate(objects):
            obj.update(vertex_start=shape['objects'][i]['vertex_start'],vertex_count=shape['objects'][i]['vertex_count'])
    elif len(objects) > len(shape['objects']) or any(
            any(obj[k] != shape['objects'][i][k] for k in
                (('object_index','vertex_start','vertex_count') if topology_changed else
                 ('object_index','vertex_start','vertex_count','triangle_start','triangle_count')))
            for i,obj in enumerate(objects)):
        raise ImportError('Shape objects do not match the existing pose layout')
    count = sum(obj['vertex_count'] for obj in objects)
    vertices = shape['vertices'][:count]
    if vector_growth is None and len(vertices) != len(result['vertices']):
        raise ImportError('Shape vertex count differs from preview geometry')
    if topology_changed:
        for i, obj in enumerate(objects):
            obj.update(triangle_start=shape['objects'][i]['triangle_start'], triangle_count=shape['objects'][i]['triangle_count'])
    triangle_count = sum(obj['triangle_count'] for obj in objects)
    if not topology_changed and triangle_count != len(result['triangles']):
        raise ImportError('Model face count differs from preview geometry')
    # V2 is explicit: material IDs may split, merge or reorder. Rebuild the
    # entire table and discard associations indexed by old IDs before the
    # server freshly qualifies the candidate texture catalog/crops.
    material_fields = ('textured', 'clut', 'tpage', 'semi_transparent')
    material_changed = (len(result['materials']) != len(shape['materials']) or
            any(any(old.get(key) != new.get(key) for key in material_fields)
                for old, new in zip(result['materials'], shape['materials'])))
    material_v2 = binding.get('format') in ('tmd-content-v2', 'tmd-content-v3', 'tmd-face-removal-v1', 'tmd-face-addition-v1')
    if material_changed and not material_v2:
        raise ImportError('Model content changed source material bindings')
    if material_v2:
        result['materials'] = deepcopy(shape['materials'])
        result['textures'] = []
        result.pop('texture_catalog', None)
        result.pop('texture_scope', None)
    for key in ('triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials', 'triangle_normals'):
        result[key] = deepcopy(shape[key][:triangle_count])
    result['normal_preview'] = deepcopy(shape['normal_preview'])
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


def replace_model_content(original: bytes, expected_sha256: str, replacement: bytes, *, allow_materials=True, allow_normal_references=False):
    """Validate typed fields; normal-reference writes require explicit v3 opt-in."""
    from .model_primitives import _qualified_model, _primitive_field_locations
    from .model_materials import _material_field_locations
    from .model_normal_references import _normal_field_locations
    if type(allow_materials) is not bool or type(allow_normal_references) is not bool:
        raise ImportError('Material and normal reference qualification flags must be boolean')
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
                allowed[at:at + 2] = b'\xff\xff'
                before = struct.unpack_from('<h', original, at)[0]
                after = struct.unpack_from('<h', replacement, at)[0]
                if before != after:
                    audit.append(dict(object_index=index, kind=kind, vector_index=vector,
                                      axis='xyz'[axis], byte_offset=at,
                                      before_value=before, after_value=after))
    primitive_fields = _primitive_field_locations(inspection)
    if allow_normal_references:
        primitive_fields = chain(primitive_fields, _normal_field_locations(original, inspection))
        # Qualify every candidate reference, even words unchanged in this edit.
        for _field in _normal_field_locations(replacement, inspection):
            pass
    for identity, width in primitive_fields:
        at = identity['byte_offset']
        allowed[at:at + width] = b'\xff' * width
        before, after = original[at], replacement[at]
        if width == 2:
            before = struct.unpack_from('<H', original, at)[0] // 8
            raw_after = struct.unpack_from('<H', replacement, at)[0]
            if raw_after % 8:
                raise ImportError('Face reference must be an aligned SVECTOR byte offset')
            after = raw_after // 8
        if before != after:
            audit.append({**identity, 'before_value': before, 'after_value': after})
    if allow_materials:
        for identity, width, mask in _material_field_locations(original, inspection):
            at = identity['byte_offset']
            for delta in range(width):
                allowed[at + delta] |= (mask >> (delta * 8)) & 255
            before = int.from_bytes(original[at:at + width], 'little')
            after = int.from_bytes(replacement[at:at + width], 'little')
            if before == after:
                continue
            if (before ^ after) & (0xffff ^ mask if width == 2 else 255 ^ mask):
                raise ImportError('Model material edit changed source ABR, reserved bits or unrelated GPU command bits')
            if identity['field'] == 'tpage' and (after >> 7) & 3 == 3:
                raise ImportError('Material edit cannot target reserved texture depth3')
            if identity['field'] == 'clut':
                page = struct.unpack_from('<H', replacement, at + 4)[0]
                if (page >> 7) & 3 not in (0, 1):
                    raise ImportError('CLUT edits require a supported indexed target texture depth')
            audit.append({**identity, 'before_value': before, 'after_value': after})
    if len(audit) > 600000:
        raise ImportError('Model content exceeds the bounded 600000-field audit')
    if any((a ^ b) & (255 ^ allowed[i]) for i, (a, b) in enumerate(zip(original, replacement))):
        raise ImportError('Model content changed layout, protected material, normal reference or opaque bits')
    _qualified_model(replacement)
    audited = bytearray(len(original))
    for change in audit:
        at = change['byte_offset']
        primitive = change['kind'] == 'primitive'
        if primitive and change['field'] in ('vertex_index', 'normal_index'):
            before = struct.pack('<H', change['before_value'] * 8)
            after = struct.pack('<H', change['after_value'] * 8)
        elif primitive and change['field'] in ('clut', 'tpage'):
            before, after = (struct.pack('<H', change[key]) for key in ('before_value', 'after_value'))
        elif primitive or change['kind'] == 'primitive_group':
            before, after = bytes([change['before_value']]), bytes([change['after_value']])
        else:
            before = struct.pack('<h', change['before_value'])
            after = struct.pack('<h', change['after_value'])
        for delta, (a, b) in enumerate(zip(before, after)):
            if a != b:
                if audited[at + delta]:
                    raise ImportError('Model content audit fields overlap')
                if original[at + delta] != a or replacement[at + delta] != b:
                    raise ImportError('Model content audit bytes differ from the source or candidate')
                audited[at + delta] = 1
    if any((a != b) != bool(audited[i]) for i, (a, b) in enumerate(zip(original, replacement))):
        raise ImportError('Model content changed an unaudited byte')
    return replacement, audit


def model_shape_overlays(archive, assets: dict, replacements: dict, *, removal_bindings=None):
    """Compose model members sharing one compressed stream before encoding."""
    if any(binding.get('format') == 'tmd-face-addition-v1' for binding in (removal_bindings or {}).values()):
        raise ImportError('Face addition Build requires the relocated model-pack path; existing-layout overlays cannot export it')
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
            binding = (removal_bindings or {}).get(identifier, {})
            if binding.get('format') == 'tmd-face-removal-v1':
                from .model_face_removal import qualify_face_removal
                payload = replacements[identifier]
                _, changes = qualify_face_removal(original, binding['source_sha256'], payload, binding['removed_faces'])
                changes += [dict(kind='primitive_removal', **row) for row in binding['removed_faces']]
            else:
                payload, changes = replace_model_content(original, sha256(original).hexdigest(), replacements[identifier],
                                                        allow_normal_references=True)
            if not changes:
                continue
            if any(start < b and start+length > a for a,b in intervals):
                raise ImportError('Model replacement source members overlap')
            intervals.append((start,start+length))
            changed[start:start+length] = payload
            material_changes = any(c['kind'] == 'primitive_group' or
                                   c['kind'] == 'primitive' and c['field'] in ('clut', 'tpage') for c in changes)
            scope = ('TMD-source-allocation-face-removal' if binding.get('format') == 'tmd-face-removal-v1' else
                     'TMD-existing-layout-material-content' if material_changes else
                     'TMD-existing-layout-content' if any(c['kind'] == 'primitive' for c in changes) else
                     'TMD-vertex-normal-XYZ-only')
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
