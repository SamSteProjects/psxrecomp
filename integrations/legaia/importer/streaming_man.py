"""Bounded DATA_FIELD streaming MAN discovery, separate from bundle compression.

Reference: LegaiaRE d6e64c68ede25813d35db20980da82a1a025549b,
asset::parse_streaming and engine_core::scene_bundle::streaming_man_payloads.
"""
from hashlib import sha256
import struct
from .core import ImportError, KNOWN_ASSET_TYPES, parse_man


def streaming_chunks(data: bytes, max_chunks: int = 4096):
    if not isinstance(data,bytes) or len(data)>16*1024*1024:
        raise ImportError('Streaming carrier exceeds the 16 MiB bound')
    if type(max_chunks) is not int or not 1<=max_chunks<=4096:
        raise ImportError('Invalid streaming chunk limit')
    position=0
    chunks=[]
    while position+4<=len(data) and len(chunks)<max_chunks:
        header=struct.unpack_from('<I',data,position)[0]
        kind,size=header>>24,header&0xffffff
        if size==0:
            return chunks,True
        if kind not in KNOWN_ASSET_TYPES or position+4+size>len(data):
            return chunks,False
        chunks.append(dict(header_offset=position,type_byte=kind,size=size))
        # Retail advances by truncated word count, not rounded-up byte size.
        position+=4+(size&~3)
    return chunks,False


def find_streaming_man_candidates(archive,start,end,scene):
    following=[entry.start_lba*archive.SECTOR for entry in archive.entries if entry.index>=end]
    limit=min(following) if following else archive.node.size
    found=[];seen=set()
    for entry in archive.entries:
        if not start<=entry.index<end:
            continue
        base=entry.start_lba*archive.SECTOR
        raw=archive.read_entry(entry,extended=False)[:max(0,limit-base)]
        chunks,terminated=streaming_chunks(raw)
        for chunk in chunks:
            offset=chunk['header_offset']+4;size=chunk['size']
            if chunk['type_byte']!=3 or size>4*1024*1024 or (base+offset,size) in seen:
                continue
            payload=raw[offset:offset+size]
            try:
                man=parse_man(payload,scene)
            except ImportError:
                continue
            if not any(man.partition_counts):
                continue
            seen.add((base+offset,size))
            found.append(dict(entry_index=entry.index,chunk_header_offset=chunk['header_offset'],
                              payload_offset=offset,byte_length=size,payload=payload,
                              payload_sha256=sha256(payload).hexdigest(),
                              partition_counts=list(man.partition_counts),stream_terminated=terminated,
                              source_kind='raw_streaming_man',compression='none',
                              exportable=False))
    return found


def replace_streaming_payload(source: bytes, expected_sha256: str, header_offset: int,
                              expected_payload_sha256: str, candidate: bytes):
    """Equal-span streaming edit; growing payloads require archive relocation work."""
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Streaming carrier source hash mismatch')
    if type(header_offset) is not int or header_offset < 0 or not isinstance(candidate, bytes):
        raise ImportError('Streaming replacement locator or payload is invalid')
    chunks, terminated = streaming_chunks(source)
    if not terminated:
        raise ImportError('Streaming replacement requires a complete terminated carrier')
    target = next((c for c in chunks if c['header_offset'] == header_offset), None)
    if target is None or target['type_byte'] not in (3, 5):
        raise ImportError('Streaming replacement requires a structural MAN or animation chunk')
    size = target['size']
    if size % 4 or len(candidate) != size:
        raise ImportError('Streaming replacement requires an unchanged word-aligned payload size')
    start, end = header_offset + 4, header_offset + 4 + size
    before = source[start:end]
    if sha256(before).hexdigest() != expected_payload_sha256:
        raise ImportError('Streaming payload preimage mismatch')
    result = source[:start] + candidate + source[end:]
    if streaming_chunks(result) != (chunks, terminated):
        raise ImportError('Streaming edit changed structural chunk boundaries')
    return result, dict(header_offset=header_offset, payload_offset=start, byte_length=size,
                        type_byte=target['type_byte'], source_sha256=expected_sha256,
                        result_sha256=sha256(result).hexdigest(),
                        payload_before_sha256=expected_payload_sha256,
                        payload_after_sha256=sha256(candidate).hexdigest())


def grow_streaming_man(source: bytes, expected_sha256: str, header_offset: int,
                       expected_payload_sha256: str, candidate: bytes):
    """Grow one MAN chunk and rebase following chunks without altering their bytes.

    The caller must provide a word-aligned MAN and relocate the enclosing
    physical archive allocation. This function does not update archive TOCs.
    """
    if not isinstance(source, bytes) or sha256(source).hexdigest() != expected_sha256:
        raise ImportError('Streaming growth source hash mismatch')
    if type(header_offset) is not int or header_offset < 0 or not isinstance(candidate, bytes):
        raise ImportError('Streaming growth locator or candidate is invalid')
    chunks, terminated = streaming_chunks(source)
    if not terminated:
        raise ImportError('Streaming growth requires a complete terminated carrier')
    target = next((c for c in chunks if c['header_offset'] == header_offset), None)
    if target is None or target['type_byte'] != 3:
        raise ImportError('Streaming growth requires a structural MAN chunk')
    old_size, new_size = target['size'], len(candidate)
    if old_size % 4 or new_size % 4 or not old_size <= new_size <= 4 * 1024 * 1024:
        raise ImportError('Streaming MAN growth requires bounded word-aligned sizes without shrinkage')
    start, end = header_offset + 4, header_offset + 4 + old_size
    original = source[start:end]
    if sha256(original).hexdigest() != expected_payload_sha256:
        raise ImportError('Streaming growth payload preimage mismatch')
    parse_man(original)
    parse_man(candidate)
    delta = new_size - old_size
    if len(source) + delta > 16 * 1024 * 1024:
        raise ImportError('Streaming grown carrier exceeds the byte bound')
    result = source[:header_offset] + struct.pack('<I', (3 << 24) | new_size) + candidate + source[end:]
    expected = [dict(c, size=new_size) if c['header_offset'] == header_offset else
                dict(c, header_offset=c['header_offset'] + delta) if c['header_offset'] > header_offset else dict(c)
                for c in chunks]
    if streaming_chunks(result) != (expected, True):
        raise ImportError('Streaming MAN growth changed the expected chunk chain')
    return result, dict(header_offset=header_offset, payload_offset=start,
                        original_payload_size=old_size, payload_size=new_size, growth_bytes=delta,
                        source_sha256=expected_sha256, result_sha256=sha256(result).hexdigest(),
                        payload_sha256=sha256(candidate).hexdigest(),
                        relocated_chunks=[dict(before=c['header_offset'], after=c['header_offset'] + delta,
                                               type_byte=c['type_byte'], byte_length=c['size'])
                                          for c in chunks if c['header_offset'] > header_offset],
                        archive_relocation_verified=False)
