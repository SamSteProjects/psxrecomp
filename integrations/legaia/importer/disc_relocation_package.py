"""Source-bound logical relocation payload for future feature package activation.

Binary v1: 96-byte header, PROT user bytes, then 2120-byte metadata records.
Native manifest parsing/activation is not connected yet.
"""
from hashlib import sha256
import struct
from .core import ImportError

HEADER = struct.Struct('<8s6I32s32s')
RECORD = struct.Struct('<II32s32s')
MAGIC = b'PSXDRLOC'
MAX_BYTES = 1024*1024*1024
MAX_METADATA = 4096


def encode_relocation_package(view):
    audit = view.audit
    records = audit['metadata_sectors']
    if len(records) > MAX_METADATA or HEADER.size+len(view.replacement)+len(records)*(RECORD.size+2048) > MAX_BYTES:
        raise ImportError('Relocation package metadata budget exceeded')
    data = bytearray(HEADER.pack(MAGIC, 1, audit['source_sector_count'], audit['prot_lba'],
        audit['source_prot_bytes']//2048, len(view.replacement)//2048, len(records),
        bytes.fromhex(audit['source_prot_sha256']), bytes.fromhex(audit['proposed_prot_sha256'])))
    data.extend(view.replacement)
    for row in records:
        data.extend(RECORD.pack(row['source_lba'], row['proposed_lba'],
            bytes.fromhex(row['source_sha256']), bytes.fromhex(row['proposed_sha256'])))
        data.extend(view.metadata[row['proposed_lba']])
    result = bytes(data)
    decoded = decode_relocation_package(result, sha256(result).hexdigest())
    if decoded['replacement'] != view.replacement or decoded['metadata'] != view.metadata:
        raise ImportError('Relocation package readback differs from logical view')
    return result, dict(schema_version='legaia.disc-relocation-package.v1',
        sha256=sha256(result).hexdigest(), byte_length=len(result), metadata_count=len(records),
        readback_verified=True, runtime_connected=False, build_ready=False, gameplay_verified=False)


def decode_relocation_package(data, expected_sha256):
    if (not isinstance(data, bytes) or not HEADER.size <= len(data) <= MAX_BYTES
            or sha256(data).hexdigest() != expected_sha256):
        raise ImportError('Relocation package hash or byte budget changed')
    magic, version, count, start, old, new, number, source_hash, proposed_hash = HEADER.unpack_from(data)
    total = count+new-old
    if (magic != MAGIC or version != 1 or not count or not old or new < old
            or start+old > count or total > 449850 or number > MAX_METADATA
            or HEADER.size+new*2048+number*(RECORD.size+2048) != len(data)):
        raise ImportError('Relocation package header or extent is invalid')
    replacement = data[HEADER.size:HEADER.size+new*2048]
    if sha256(replacement).digest() != proposed_hash:
        raise ImportError('Relocation package PROT payload hash changed')
    metadata, preimages = {}, []
    position, previous = HEADER.size+new*2048, -1
    for _ in range(number):
        original, proposed, before_hash, after_hash = RECORD.unpack_from(data, position)
        position += RECORD.size
        payload = data[position:position+2048];position += 2048
        if (not previous < original < count or start <= original < start+old
                or proposed != original+(new-old if original >= start+old else 0)
                or proposed >= total or start <= proposed < start+new
                or sha256(payload).digest() != after_hash):
            raise ImportError('Relocation package metadata ownership or hash changed')
        previous = original;metadata[proposed] = payload
        preimages.append(dict(source_lba=original, proposed_lba=proposed, source_sha256=before_hash.hex()))
    return dict(source_sector_count=count, prot_lba=start, source_prot_sectors=old,
        proposed_sector_count=total, source_prot_sha256=source_hash.hex(),
        replacement=replacement, metadata=metadata, metadata_preimages=preimages)
