"""Native rigid-record allocation with explicit donor provenance.

Disc ANM evidence: pinned player_anm.rs d6e64c68ede25813d35db20980da82a1a025549b,
an absolute u32 offset table followed by 8-byte header, frame-major channels and
zero trailer. This edits disc bytes, never runtime pointers or inferred timing.
Project ledger, actor assignment and carrier relocation are separate consumers.
"""
from __future__ import annotations

from hashlib import sha256
import struct
from uuid import UUID

from .animation import (MAX_BUNDLE_BYTES, MAX_FRAMES, MAX_RECORDS,
                        animation_record_ranges, decode_animation_record)
from .animation_authoring import MAX_CHANNEL_EDITS, patch_animation_channels
from .core import ImportError

MAX_ALLOCATED_RECORDS = 64
MAX_ALLOCATED_CHANNELS = 4096


def _source(content, expected, label):
    if not isinstance(content, bytes) or sha256(content).hexdigest() != expected:
        raise ImportError(f'{label} source hash does not match immutable bytes')


def _record_id(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.version != 4 or str(parsed) != value:
        raise ImportError('Allocated animation requires a canonical UUIDv4 record identity')
    return value


def allocate_animation_record(donor: bytes, expected_sha256: str,
                              source_frame_indices: list[int], edits: list[dict]) -> tuple[bytes, dict]:
    """Allocate a frame sequence, preserving donor mode/object count/opaque data.

    Repetition, reordering, shortening and extension are explicit frame choices.
    Each new channel inherits its donor frame's opaque nibble before exact edits.
    No guessed neutral pose, object hierarchy, cadence or header mode is created.
    """
    _source(donor, expected_sha256, 'Animation donor')
    decoded = decode_animation_record(donor)
    if (not isinstance(source_frame_indices, list) or
            not 1 <= len(source_frame_indices) <= MAX_FRAMES or
            len(source_frame_indices) * decoded['bone_count'] > MAX_CHANNEL_EDITS):
        raise ImportError('Allocated animation frame/channel count exceeds bounds')
    if any(type(frame) is not int or not 0 <= frame < decoded['frame_count']
           for frame in source_frame_indices):
        raise ImportError('Allocated animation source frame index is outside the donor')
    header = bytearray(donor[:8])
    struct.pack_into('<H', header, 2, len(source_frame_indices))
    stride = decoded['bone_count'] * 8
    copied = bytes(header) + b''.join(donor[8+frame*stride:8+(frame+1)*stride]
                                    for frame in source_frame_indices) + donor[-8:]
    candidate, changes = patch_animation_channels(copied, sha256(copied).hexdigest(), edits)
    checked = decode_animation_record(candidate)
    if (candidate[:2] != donor[:2] or candidate[4:8] != donor[4:8] or
            candidate[-8:] != donor[-8:] or checked['bone_count'] != decoded['bone_count']):
        raise ImportError('Allocated animation changed its donor mode/object count/trailer')
    return candidate, dict(donor_record_sha256=expected_sha256,
        candidate_record_sha256=sha256(candidate).hexdigest(),
        donor_frame_count=decoded['frame_count'], frame_count=len(source_frame_indices),
        object_count=decoded['bone_count'], source_frame_indices=list(source_frame_indices),
        byte_length=len(candidate), changed_axes=changes)


def append_animation_records(original: bytes, expected_sha256: str,
                             requests: list[dict]) -> tuple[bytes, dict]:
    """Append stable named records and rebase the absolute table atomically.

    Existing record indices and every existing record byte remain unchanged.
    Table-to-record opaque padding is preserved exactly. Donors refer only to
    the supplied bank, so order cannot silently change donor provenance.
    """
    _source(original, expected_sha256, 'Animation bank')
    ranges = animation_record_ranges(original)
    if (not isinstance(requests, list) or not 1 <= len(requests) <= MAX_ALLOCATED_RECORDS or
            len(ranges) + len(requests) > MAX_RECORDS):
        raise ImportError('Animation allocation request/record count exceeds bounds')
    identities, allocated, channels = set(), [], 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {
                'record_id', 'donor_record_index', 'source_frame_indices', 'edits'}:
            raise ImportError('Animation allocation requires identity, donor, frame sequence and edits only')
        identity = _record_id(request['record_id'])
        if identity in identities:
            raise ImportError('Duplicate allocated animation record identity')
        identities.add(identity)
        index = request['donor_record_index']
        if type(index) is not int or not 0 <= index < len(ranges):
            raise ImportError('Animation allocation donor record index is outside the source bank')
        start, end = ranges[index]
        donor = original[start:end]
        candidate, audit = allocate_animation_record(donor, sha256(donor).hexdigest(),
                                                     request['source_frame_indices'], request['edits'])
        channels += audit['frame_count'] * audit['object_count']
        if channels > MAX_ALLOCATED_CHANNELS:
            raise ImportError('Animation allocation exceeds the cumulative channel budget')
        allocated.append((candidate, dict(audit, record_id=identity, donor_record_index=index,
            donor_byte_offset=start, donor_byte_length=end-start,
            record_index=len(ranges)+len(allocated))))
    return _append_prepared(original, expected_sha256, ranges, allocated, channels)


def append_animation_record_payloads(original: bytes, expected_sha256: str,
                                     requests: list[dict]) -> tuple[bytes, dict]:
    """Append already reconstructed records without borrowing a changed donor.

    Project consumers verify frozen donor provenance before calling this. This
    function verifies every payload's supported wire layout and exact readback.
    """
    _source(original, expected_sha256, 'Animation bank')
    ranges = animation_record_ranges(original)
    if (not isinstance(requests, list) or len(requests) > MAX_ALLOCATED_RECORDS or
            len(ranges) + len(requests) > MAX_RECORDS):
        raise ImportError('Animation allocation request/record count exceeds bounds')
    identities, allocated, channels = set(), [], 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {'record_id', 'record'}:
            raise ImportError('Prepared animation requires record identity and immutable record bytes')
        identity = _record_id(request['record_id'])
        if identity in identities:
            raise ImportError('Duplicate allocated animation record identity')
        identities.add(identity)
        record = request['record']
        if not isinstance(record, bytes):
            raise ImportError('Prepared animation requires immutable record bytes')
        decoded = decode_animation_record(record)
        channels += decoded['frame_count'] * decoded['bone_count']
        if channels > MAX_ALLOCATED_CHANNELS:
            raise ImportError('Animation allocation exceeds the cumulative channel budget')
        allocated.append((record, dict(record_id=identity, record_index=len(ranges)+len(allocated),
            candidate_record_sha256=sha256(record).hexdigest(), frame_count=decoded['frame_count'],
            object_count=decoded['bone_count'], byte_length=len(record))))
    return _append_prepared(original, expected_sha256, ranges, allocated, channels)


def _append_prepared(original, expected_sha256, ranges, allocated, channels):
    shift = len(allocated) * 4
    proposed_size = len(original) + shift + sum(len(record) for record, _ in allocated)
    if proposed_size > MAX_BUNDLE_BYTES:
        raise ImportError('Allocated animation bank exceeds the native byte budget')
    offsets = [start+shift for start, _ in ranges]
    at = len(original) + shift
    for record, audit in allocated:
        offsets.append(at)
        audit['byte_offset'] = at
        at += len(record)
    table_end = 4 + len(ranges)*4
    result = (struct.pack('<I', len(offsets)) + struct.pack(f'<{len(offsets)}I', *offsets) +
              original[table_end:] + b''.join(record for record, _ in allocated))
    checked_ranges = animation_record_ranges(result)
    preserved = []
    for index, ((start, end), (new_start, new_end)) in enumerate(zip(ranges, checked_ranges)):
        if result[new_start:new_end] != original[start:end]:
            raise ImportError('Animation allocation changed an existing record')
        preserved.append(dict(record_index=index, source_byte_offset=start,
            byte_offset=new_start, byte_length=end-start,
            record_sha256=sha256(original[start:end]).hexdigest()))
    for record, audit in allocated:
        start, end = checked_ranges[audit['record_index']]
        if result[start:end] != record:
            raise ImportError('Animation allocation record readback failed')
    return result, dict(schema_version='legaia.animation-record-allocation.v1',
        source_bank_sha256=expected_sha256, candidate_bank_sha256=sha256(result).hexdigest(),
        source_byte_length=len(original), byte_length=len(result),
        source_record_count=len(ranges), record_count=len(offsets), table_growth_bytes=shift,
        preserved_records=preserved, allocated_records=[audit for _, audit in allocated],
        allocated_channel_count=channels, scope='native-disc-animation-record-allocation',
        gameplay_verified=False)
