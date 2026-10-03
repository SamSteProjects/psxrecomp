"""Qualified existing lit TMD normal references; no allocation or packet edits.

Retail/pinned descriptor layouts: FT3 n0 at12 before vertices14; FT4 n0
at20 after vertices12; GT3/GT4 normal operands at18/20 after vertices.
Each operand is an aligned 8-byte SVECTOR offset into its object's table.
"""
import struct

from .core import ImportError


def normal_users(data, object_index, normal_index):
    """Existing stored reference operands in one qualified object's normal table."""
    from .model_primitives import _qualified_model
    inspection, _ = _qualified_model(data)
    if type(object_index) is not int or not 0 <= object_index < len(inspection['objects']):
        raise ImportError('Choose an existing model object')
    count = struct.unpack_from('<I', data, 24 + object_index * 28)[0]
    if type(normal_index) is not int or not 0 <= normal_index < count:
        raise ImportError('Choose an existing stored normal vector')
    primitives = {row['primitive_index']: row for row in inspection['objects'][object_index]['primitives']}
    users = []
    for field, _ in _normal_field_locations(data, inspection):
        if field['object_index'] != object_index or struct.unpack_from('<H', data, field['byte_offset'])[0] != normal_index * 8:
            continue
        primitive = primitives[field['primitive_index']]
        users.append(dict(field, normal_index=normal_index,
                          corner_count=primitive['corner_count'],
                          sharing='gouraud_corner' if primitive['gouraud'] else 'flat_all_corners',
                          affected_corners=[field['corner_index']] if primitive['gouraud'] else list(range(primitive['corner_count']))))
        if len(users) > 4096:
            raise ImportError('Normal reference usage exceeds 4096 qualified operands')
    return users


def _normal_field_locations(data, inspection):
    """Yield the distinct stored normal reference words, including flat owners."""
    for obj in inspection['objects']:
        normal_count = struct.unpack_from('<I', data, 12 + obj['object_index'] * 28 + 12)[0]
        groups = {}
        for row in obj['primitives']:
            group = row['group_index']
            if group not in groups:
                groups[group] = data[row['byte_offset'] - 3] * 4
            if row['baked_colors']:
                continue
            corners = row['corner_count']
            count = corners if row['gouraud'] else 1
            relative = (18 if corners == 3 else 20) if row['gouraud'] else (12 if corners == 3 else 20)
            if relative + count * 2 > groups[group]:
                raise ImportError('Model lit normal references exceed their source packet')
            for corner in range(count):
                at = row['byte_offset'] + relative + corner * 2
                raw = struct.unpack_from('<H', data, at)[0]
                if raw % 8 or raw // 8 >= normal_count:
                    raise ImportError('Model lit normal reference exceeds its source normal table or is misaligned')
                yield dict(kind='primitive', field='normal_index', object_index=obj['object_index'],
                           primitive_index=row['primitive_index'], group_index=group,
                           corner_index=corner, byte_offset=at), 2
