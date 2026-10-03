"""Qualified existing-layout material fields and shared group ABE edits.

Pinned d6e64c68 legaia_prims.rs proves CLUT at texture+2, TPage at
texture+6, and ABE in group mode bit1. Retail consumers 80027480/80027E60
and 80029A84/8002A4EC propagate that group mode to emitted GPU commands.
Those consumers replace encoded ABR with caller state: ABR stays read-only.
No flags, row commands, packet allocation, normals or opaque bytes are authored.
"""
from hashlib import sha256
import json
import struct

from .assets import _layout
from .core import ImportError
from .model_primitives import _qualified_model


MAX_MATERIAL_EDITS = 256
MAX_CATALOG_BYTES = 16 * 1024 * 1024
CLUT_MASK = 0x7fff
TPAGE_MASK = 0x019f
ABE_MASK = 0x02
_PRIMITIVE_VALUES = {'page_column', 'page_row', 'texture_bpp', 'clut_column', 'clut_row'}


def _catalog(data: bytes, inspection: dict) -> dict:
    objects = []
    for obj in inspection['objects']:
        groups = []
        by_group = {}
        for row in obj['primitives']:
            by_group.setdefault(row['group_index'], []).append(row)
        for group_index, rows in by_group.items():
            header = rows[0]['byte_offset'] - 8
            count, flags = struct.unpack_from('<HH', data, header)
            stride, mode = data[header + 5] * 4, data[header + 7]
            if (count != len(rows) or flags != rows[0]['flags'] or
                    any(row['flags'] != flags or row['byte_offset'] != header + 8 + i * stride
                        for i, row in enumerate(rows))):
                raise ImportError('Material group differs from its qualified source row layout')
            primitives = []
            for row in rows:
                clut, tpage = row['material']['clut'], row['material']['tpage']
                textured = row['uvs'] is not None
                primitive = dict(primitive_index=row['primitive_index'], byte_offset=row['byte_offset'],
                    textured=textured, clut=clut, tpage=tpage,
                    page_column=(tpage & 15) if textured else None,
                    page_row=((tpage >> 4) & 1) if textured else None,
                    texture_bpp=((4, 8, 16, None)[(tpage >> 7) & 3]) if textured else None,
                    clut_column=(clut & 63) if textured else None,
                    clut_row=((clut >> 6) & 511) if textured else None,
                    source_blend_mode=((tpage >> 5) & 3) if textured else None)
                primitives.append(primitive)
            groups.append(dict(group_index=group_index, byte_offset=header, flags=flags,
                               mode=mode, semi_transparent=bool(mode & ABE_MASK), primitives=primitives))
        objects.append(dict(object_index=obj['object_index'], groups=groups))
    return dict(schema_version='legaia.model-materials.v1',
                source_sha256=sha256(data).hexdigest(), objects=objects)


def inspect_model_materials(data: bytes) -> dict:
    """Return detached source scalar metadata; reserved depth remains unknown."""
    inspection, _vectors = _qualified_model(data)
    result = _catalog(data, inspection)
    if len(json.dumps(result, separators=(',', ':'), allow_nan=False).encode('utf-8')) > MAX_CATALOG_BYTES:
        raise ImportError('Model material catalog exceeds its 16 MiB metadata budget')
    return result


def _material_field_locations(data: bytes, inspection: dict):
    """Yield unique typed source locations and writable bit masks."""
    catalog = _catalog(data, inspection)
    for obj in catalog['objects']:
        for group in obj['groups']:
            yield dict(kind='primitive_group', object_index=obj['object_index'],
                       group_index=group['group_index'], field='gpu_mode',
                       byte_offset=group['byte_offset'] + 7,
                       primitive_indices=[row['primitive_index'] for row in group['primitives']]), 1, ABE_MASK
            _, _, textured, _, uv, _ = _layout(group['flags'])
            if not textured:
                continue
            for row in group['primitives']:
                identity = dict(kind='primitive', object_index=obj['object_index'],
                                primitive_index=row['primitive_index'], group_index=group['group_index'])
                yield {**identity, 'field': 'clut', 'byte_offset': row['byte_offset'] + uv + 2}, 2, CLUT_MASK
                yield {**identity, 'field': 'tpage', 'byte_offset': row['byte_offset'] + uv + 6}, 2, TPAGE_MASK


def patch_model_materials(data: bytes, expected_sha256: str, edits: list):
    """Author semantic material fields on existing qualified rows/groups only."""
    catalog = inspect_model_materials(data)
    if not isinstance(expected_sha256, str) or expected_sha256 != catalog['source_sha256']:
        raise ImportError('Model changed since material inspection; reopen the material editor')
    if not isinstance(edits, list) or len(edits) > MAX_MATERIAL_EDITS:
        raise ImportError('Model material authoring accepts at most 256 edits')
    groups = {(obj['object_index'], group['group_index']): group
              for obj in catalog['objects'] for group in obj['groups']}
    rows = {(obj['object_index'], row['primitive_index']): (group, row)
            for obj in catalog['objects'] for group in obj['groups'] for row in group['primitives']}
    result, seen = bytearray(data), set()
    for edit in edits:
        if not isinstance(edit, dict) or edit.get('kind') not in ('primitive', 'group'):
            raise ImportError('Choose an existing primitive material or group ABE identity')
        primitive = edit['kind'] == 'primitive'
        index_key = 'primitive_index' if primitive else 'group_index'
        if (set(edit) != {'kind', 'object_index', index_key, 'values'} or
                any(type(edit[key]) is not int for key in ('object_index', index_key))):
            raise ImportError('Material edits require exact integer source identities and values')
        identity = edit['object_index'], edit[index_key]
        unique = edit['kind'], *identity
        if unique in seen:
            raise ImportError('Material edit repeats a source identity')
        seen.add(unique)
        values = edit['values']
        if not isinstance(values, dict) or not values:
            raise ImportError('Material edit values must be a nonempty semantic field object')
        if not primitive:
            if identity not in groups or set(values) != {'semi_transparent'} or type(values['semi_transparent']) is not bool:
                raise ImportError('Group edits require one source-qualified boolean ABE value')
            group = groups[identity]
            at = group['byte_offset'] + 7
            result[at] = (data[at] & (255 ^ ABE_MASK)) | (ABE_MASK if values['semi_transparent'] else 0)
            continue
        if identity not in rows or not set(values) <= _PRIMITIVE_VALUES:
            raise ImportError('Primitive edits require existing rows and page/depth/CLUT fields only; ABR is read-only')
        group, row = rows[identity]
        if not row['textured']:
            raise ImportError('Untextured primitives have no editable CLUT or texture page')
        if any(type(value) is not int for value in values.values()):
            raise ImportError('Material coordinate and depth values must be integers, not booleans')
        for key, maximum in (('page_column', 15), ('page_row', 1), ('clut_column', 63), ('clut_row', 511)):
            if key in values and not 0 <= values[key] <= maximum:
                raise ImportError('Material coordinates must fit their existing VRAM bit fields')
        if 'texture_bpp' in values and values['texture_bpp'] not in (4, 8, 16):
            raise ImportError('Choose a supported texture depth of 4, 8 or 16 bits')
        tpage, clut = row['tpage'], row['clut']
        for key, mask, shift in (('page_column', 0x0f, 0), ('page_row', 0x10, 4)):
            if key in values:
                tpage = (tpage & (0xffff ^ mask)) | (values[key] << shift)
        if 'texture_bpp' in values:
            tpage = (tpage & (0xffff ^ 0x180)) | ((4, 8, 16).index(values['texture_bpp']) << 7)
        target_depth = (tpage >> 7) & 3
        if target_depth == 3 and tpage != row['tpage']:
            raise ImportError('Reserved source depth requires an explicit supported texture_bpp target')
        if any(key in values for key in ('clut_column', 'clut_row')):
            if target_depth not in (0, 1):
                raise ImportError('Direct16 or reserved target retains its source CLUT; CLUT edits require indexed target depth')
            if 'clut_column' in values:
                clut = (clut & (0xffff ^ 63)) | values['clut_column']
            if 'clut_row' in values:
                clut = (clut & (0xffff ^ 0x7fc0)) | (values['clut_row'] << 6)
        _, _, _, _, uv, _ = _layout(group['flags'])
        struct.pack_into('<H', result, row['byte_offset'] + uv + 2, clut)
        struct.pack_into('<H', result, row['byte_offset'] + uv + 6, tpage)
    from .model_authoring import replace_model_content
    return replace_model_content(data, expected_sha256, bytes(result))
