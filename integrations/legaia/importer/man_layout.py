"""Bounded MAN partition and trailing-section layout for structural editing.

Reference: pinned crates/asset/src/man_section.rs and man_edit.rs. Offsets in
the record table and header0x28 are relative to the derived data-region base.
This reader does not assert that opaque script pointers can be relocated.
"""
import struct
from .core import ImportError


def resolve_spawn_record(layout: dict, global_index: int) -> dict:
    """Resolve opcode44's byte operand without asserting runtime reachability."""
    if type(global_index) is not int or not 0 <= global_index <= 255:
        raise ImportError('Spawn record operand must be a byte integer')
    first = sum(layout['partition_counts'][:2])
    index = global_index-first
    if not 0 <= index < layout['partition_counts'][2]:
        return dict(global_record_index=global_index, status='outside_partition2',
                    partition=2, record_index=None)
    target = next(record for record in layout['records']
                  if record['partition'] == 2 and record['record_index'] == index)
    return dict(global_record_index=global_index, status='resolved_encoded_reference',
                partition=2, record_index=index, byte_offset=target['byte_offset'],
                byte_length=target['byte_length'])


def read_man_layout(data: bytes) -> dict:
    if not isinstance(data, bytes) or len(data) < 0x2b:
        raise ImportError('MAN layout requires a complete immutable header')
    counts = struct.unpack_from('<hhh', data, 0x22)
    if any(n < 0 for n in counts):
        raise ImportError('MAN partition counts must be nonnegative')
    base = 0x2b + sum(counts)*3
    if base > len(data):
        raise ImportError('MAN offset table exceeds source bounds')
    def u24(at):
        if at < 0 or at+3 > len(data):
            raise ImportError('MAN u24 exceeds source bounds')
        return int.from_bytes(data[at:at+3], 'little')
    records, table_index = [], 0
    for partition, count in enumerate(counts):
        for index in range(count):
            table_offset = 0x2b + table_index*3
            start = base + u24(table_offset)
            if start >= len(data):
                raise ImportError('MAN record offset exceeds source bounds')
            records.append(dict(partition=partition, record_index=index, table_offset=table_offset,
                                byte_offset=start, relative_offset=start-base))
            table_index += 1
    sections, cursor = [], base + u24(0x28)
    for index in range(6):
        length = u24(cursor)
        end = cursor+3+length
        if end > len(data):
            raise ImportError('MAN section exceeds source bounds')
        sections.append(dict(section_index=index, byte_offset=cursor, byte_length=3+length))
        cursor = end
    boundaries = sorted({len(data), *(r['byte_offset'] for r in records), *(s['byte_offset'] for s in sections)})
    for record in records:
        record['byte_length'] = next(end for end in boundaries if end > record['byte_offset'])-record['byte_offset']
    return dict(partition_counts=list(counts), data_region_offset=base, records=records,
                sections=sections, trailing_byte_offset=cursor, trailing_byte_length=len(data)-cursor)
