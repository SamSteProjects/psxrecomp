"""Qualified existing lit TMD normal references; no allocation or packet edits.

Retail/pinned descriptor layouts: FT3 n0 at12 before vertices14; FT4 n0
at20 after vertices12; GT3/GT4 normal operands at18/20 after vertices.
Each operand is an aligned 8-byte SVECTOR offset into its object's table.
"""
import struct

from .core import ImportError


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
