"""Bounded source object-init binds; neither live activation nor clip identity.

Pinned field_env.rs supplies anchor lookup and P0 header evidence. Native
FUN_8003C8F0(id,0) uses flat MAN indices (see field_map.py). Resolve that index
first; never reinterpret another partition as a P0 header or skip a malformed
primary hit in favour of a convenient fallback.
"""
from base64 import b64encode
from collections import Counter
from hashlib import sha256

from .core import ImportError
from .man_layout import read_man_layout


def resolve_object_bind(catalog, man, col, row):
    if (type(col) is not int or type(row) is not int or
            not 0 <= col < 128 or not 0 <= row < 128):
        raise ImportError('Object bind anchor must be a native kingdom tile')
    if not isinstance(man, bytes) or not 0x2b <= len(man) <= 4*1024*1024:
        raise ImportError('Object bind requires a bounded immutable MAN')
    layout = read_man_layout(man)
    if len(layout['records']) > 8192:
        raise ImportError('Object bind MAN exceeds its record budget')
    hits = [a for a in catalog['assets'] if a.get('table_kind') == 1 and
            a['encoded']['tile_x'] == col and a['encoded']['tile_z'] == row]
    # Explicit ordering, independent of the catalog caller's iteration order.
    hits.sort(key=lambda a: ({'primary': 0, 'fallback': 1}[a['table_source']], a['record_index']))
    result = dict(anchor=dict(col=col, row=row), status='no_source_bind',
                  trigger=None, shadowed_trigger_ids=[], man_record=None,
                  encoded_animation_selector=None, animation_clip='not_resolved',
                  interaction_script='not_resolved', runtime_activation='not_evaluated')
    if not hits:
        return result
    hit = hits[0]
    result['trigger'] = hit
    result['shadowed_trigger_ids'] = [a['semantic_id'] for a in hits[1:]]
    index = hit['encoded']['record_index']
    if type(index) is not int or not 0 <= index < len(layout['records']):
        raise ImportError('Primary source object bind has an invalid flat MAN index')
    record = layout['records'][index]
    at, length = record['byte_offset'], record['byte_length']
    if Counter(r['byte_offset'] for r in layout['records'])[at] != 1:
        raise ImportError('Object bind MAN record has aliased ownership')
    if not 0 < length <= 65536 or any(
            at < s['byte_offset']+s['byte_length'] and s['byte_offset'] < at+length
            for s in layout['sections']):
        raise ImportError('Object bind MAN record overlaps a section or exceeds its budget')
    result['man_record'] = dict(record, flat_record_index=index,
                               sha256=sha256(man[at:at+length]).hexdigest())
    if record['partition'] != 0:
        result['status'] = 'unsupported_header_partition'
        return result
    count = man[at]
    header_length = 2+2*count
    if header_length > length:
        raise ImportError('Object bind P0 header crosses its record boundary')
    header = man[at:at+header_length]
    result['man_record']['header'] = dict(local_count=count, byte_length=header_length,
        sha256=sha256(header).hexdigest(), bytes_base64=b64encode(header).decode('ascii'))
    result['encoded_animation_selector'] = header[-1]
    result['status'] = 'resolved_source_header'
    return result
