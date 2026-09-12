"""Encode a MAN candidate with optional descriptor relocation; not archive-ready."""
from hashlib import sha256
import struct
from .core import ImportError, parse_scene_table, decompress_lzs
from .serialization import compress_lzs


def encode_man_candidate(container: bytes, expected_sha256: str, table_offset: int,
                         source_man_sha256: str, candidate: bytes, *, allow_growth: bool = False):
    if not isinstance(container, bytes) or sha256(container).hexdigest() != expected_sha256:
        raise ImportError('MAN container source hash mismatch')
    if type(table_offset) is not int or table_offset < 0:
        raise ImportError('MAN scene table offset must be nonnegative')
    if not isinstance(candidate, bytes) or not 0 < len(candidate) <= 4*1024*1024:
        raise ImportError('MAN candidate exceeds decoded size limit')
    table = parse_scene_table(container, 0, table_offset)
    matches = [] if table is None else [d for d in table.descriptors if d.type_byte == 3 and d.size]
    if len(matches) != 1:
        raise ImportError('MAN container requires exactly one MAN descriptor')
    descriptor = matches[0]
    table_end = table_offset+8+8*len(table.descriptors)
    if any(not table_end <= table_offset+d.data_offset <= len(container)
           for d in table.descriptors):
        raise ImportError('MAN container descriptor overlaps table or exceeds source bounds')
    start = table_offset+descriptor.data_offset
    end = min([table_offset+d.data_offset for d in table.descriptors
               if d.data_offset > descriptor.data_offset]+[len(container)])
    if not table_offset+8+8*len(table.descriptors) <= start < end <= len(container):
        raise ImportError('MAN container payload bounds invalid')
    if sum(d.data_offset == descriptor.data_offset for d in table.descriptors) != 1:
        raise ImportError('MAN container payload is aliased')
    original, original_consumed = decompress_lzs(container[start:end], descriptor.size)
    if sha256(original).hexdigest() != source_man_sha256:
        raise ImportError('MAN decoded source hash mismatch')
    stream = container[start:start+original_consumed] if candidate == original else compress_lzs(candidate)
    if type(allow_growth) is not bool:
        raise ImportError('MAN container growth option must be boolean')
    growth = max(0, len(stream)-(end-start))
    # Preserve the alignment class of every following descriptor.
    growth = (growth+3)&~3
    if growth and not allow_growth:
        raise ImportError('MAN candidate exceeds existing compressed slot capacity')
    decoded, consumed = decompress_lzs(stream, len(candidate))
    if decoded != candidate or consumed != len(stream):
        raise ImportError('MAN candidate compression roundtrip failed')
    if any(not 0 <= table_offset+d.data_offset <= len(container) for d in table.descriptors):
        raise ImportError('MAN container descriptor offset exceeds source bounds')
    result = bytearray(container[:end]+b'\0'*growth+container[end:])
    result[start:start+len(stream)] = stream
    word_offset = table_offset+8+descriptor.index*8
    struct.pack_into('<I', result, word_offset, (3<<24)|len(candidate))
    moved = []
    for d in table.descriptors:
        if growth and table_offset+d.data_offset >= end:
            struct.pack_into('<I', result, table_offset+12+d.index*8, d.data_offset+growth)
            moved.append(dict(descriptor_index=d.index, before=d.data_offset,
                              after=d.data_offset+growth))
    if result[end+growth:] != container[end:]:
        raise ImportError('MAN container growth altered following payload bytes')
    emitted = bytes(result)
    reparsed = parse_scene_table(emitted, 0, table_offset)
    if reparsed is None:
        raise ImportError('MAN candidate descriptor table did not reparse')
    for before, after in zip(table.descriptors, reparsed.descriptors):
        expected_offset = before.data_offset+(growth if table_offset+before.data_offset >= end else 0)
        expected_size = len(candidate) if before.index == descriptor.index else before.size
        if (after.type_byte, after.size, after.data_offset) != (before.type_byte, expected_size, expected_offset):
            raise ImportError('MAN candidate descriptor did not roundtrip')
    verified, _ = decompress_lzs(emitted[start:start+len(stream)], len(candidate))
    if verified != candidate:
        raise ImportError('MAN emitted payload did not roundtrip')
    return emitted, dict(descriptor_index=descriptor.index,
                              decoded_size_before=descriptor.size, decoded_size_after=len(candidate),
                              stream_offset=start, compressed_size=len(stream), capacity=end-start,
                              container_sha256=sha256(result).hexdigest(), growth_bytes=growth,
                              moved_descriptors=moved, external_container_size_update_required=bool(growth),
                              build_ready=False)
