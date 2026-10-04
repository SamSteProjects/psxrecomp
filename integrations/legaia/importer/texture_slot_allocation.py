"""Append explicit TIM uploads while retaining existing pack slot identities."""
from hashlib import sha256
import struct

from .core import ImportError
from .textures import _pack_members, parse_tim, MAX_ENTRY_BYTES, MAX_TEXTURES
from .texture_layout_allocation import _tim
from .texture_pack_allocation import allocate_texture_pack


def validate_added_tim(content):
    tim = _tim(content)
    if tim.image.x + tim.image.width_words > 1024 or tim.image.y + tim.image.height > 512:
        raise ImportError('Added TIM image exceeds VRAM bounds')
    if tim.bpp == 24 and tim.image.width_words * 2 % 3:
        raise ImportError('Added RGB24 TIM must contain whole pixels')
    if tim.clut and (tim.clut.x + tim.clut.width_words * tim.clut.height > 1024 or tim.clut.y >= 512):
        raise ImportError('Added TIM flattened CLUT upload exceeds VRAM bounds')
    return tim


def append_texture_pack(source, expected_sha256, additions, *, edits=None, standalone=False):
    if (not isinstance(source, bytes) or not 0 < len(source) <= MAX_ENTRY_BYTES or
            sha256(source).hexdigest() != expected_sha256 or type(standalone) is not bool):
        raise ImportError('Texture slot allocation requires bounded hash-qualified source bytes')
    if not isinstance(additions, list) or not 1 <= len(additions) <= 128:
        raise ImportError('Texture slot allocation requires one to 128 complete TIM additions')
    if edits is not None and (not isinstance(edits, list) or len(edits) > 128):
        raise ImportError('Texture slot allocation member edits are malformed')
    original_members = _pack_members(source, standalone)
    if len(original_members) + len(additions) > MAX_TEXTURES:
        raise ImportError('Texture slot allocation exceeds the native slot budget')
    # Validate the entire input before allocating output or accepting old edits.
    for content in additions:
        validate_added_tim(content)
    effective, edit_audit = (allocate_texture_pack(source, expected_sha256, edits, standalone=standalone)
                             if edits else (source, None))
    members = _pack_members(effective, standalone)
    base = 4 if standalone else 0
    old_table_end = base + 4 + len(members) * 4
    gap = effective[old_table_end:members[0][0]]
    count = len(members) + len(additions)
    result = bytearray(effective[:base] + struct.pack('<I', count) + bytes(count * 4) + gap)
    payloads = []
    rows = []
    for slot in range(count):
        added = slot >= len(members)
        if added:
            payload = additions[slot - len(members)]
            tail = b''
        else:
            start, end = members[slot]
            tim = parse_tim(effective[start:end])
            payload, tail = effective[start:start + tim.byte_length], effective[start + tim.byte_length:end]
        start = len(result)
        if (start - base) % 4:
            raise ImportError('Texture slot allocation lost word alignment')
        struct.pack_into('<I', result, base + 4 + slot * 4, (start - base) // 4)
        result.extend(payload + tail)
        padding = -len(result) % 4 if slot < count - 1 else 0
        result.extend(bytes(padding))
        if len(result) > MAX_ENTRY_BYTES:
            raise ImportError('Texture slot allocation exceeds its decoded byte budget')
        payloads.append(payload + tail + bytes(padding))
        rows.append(dict(slot_index=slot, added=added, proposed_byte_offset=start,
                         tim_sha256=sha256(payload).hexdigest(), tim_byte_length=len(payload),
                         opaque_tail_sha256=sha256(tail).hexdigest(), opaque_tail_byte_length=len(tail),
                         alignment_padding_bytes=padding))
    candidate = bytes(result)
    reopened = _pack_members(candidate, standalone)
    if len(reopened) != count or candidate[base + 4 + count * 4:reopened[0][0]] != gap:
        raise ImportError('Texture slot allocation failed table/gap readback')
    for row, payload, (start, end) in zip(rows, payloads, reopened):
        if start != row['proposed_byte_offset'] or candidate[start:end] != payload:
            raise ImportError('Texture slot allocation failed exact member/tail readback')
        parse_tim(candidate[start:end])
    return candidate, dict(schema_version='legaia.texture-pack-slot-allocation.v1',
                           source_sha256=expected_sha256, proposed_sha256=sha256(candidate).hexdigest(),
                           source_byte_length=len(source), proposed_byte_length=len(candidate),
                           growth_bytes=len(candidate)-len(source), standalone=standalone,
                           source_slot_count=len(members), slot_count=count,
                           added_slot_indices=list(range(len(members), count)), members=rows,
                           existing_edit_audit=edit_audit, native_members_verified=True,
                           opaque_tails_preserved=True, gameplay_verified=False)
