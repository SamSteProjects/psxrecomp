"""Lossless MAN placement edits and capacity-guarded Legaia LZS serialization."""
from __future__ import annotations

from collections import defaultdict, deque
import math
from typing import Any

from .core import ImportError, decompress_lzs, parse_man


def encode_placement_coordinate(value: int | float, field: str = "position") -> int:
    """Invert retail `tile*128 + (bit7 ? 128 : 64)` without quantization."""
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            (isinstance(value, float) and not math.isfinite(value)) or
            not 64 <= value <= 16384 or value != int(value) or int(value) % 64):
        raise ImportError(f"{field} must be an exact multiple of 64 on the retail placement grid, from 64 through 16384")
    value = int(value)
    if value % 128 == 64:
        return (value - 64) // 128
    return 0x80 | (value // 128 - 1)


def patch_man_positions(
    original: bytes, scene: str, edits: dict[int, dict[str, int | float]]
) -> tuple[bytes, list[dict[str, Any]]]:
    """Change only requested X/Z placement bytes; retain every opaque byte."""
    parsed = parse_man(original, scene)
    actors = {actor.record_index: actor for actor in parsed.actors}
    result = bytearray(original)
    audit: list[dict[str, Any]] = []
    for record, position in sorted(edits.items()):
        if type(record) is not int or record not in actors:
            raise ImportError(f"{scene} actor placement record {record!r} is unsupported")
        if not isinstance(position, dict) or not position or set(position) - {"x", "z"}:
            raise ImportError(f"{scene} record {record}: only X/Z placement fields are serializable; height, facing, and model edits are unsupported")
        actor = actors[record]
        # Prefix: local-count byte, 2 bytes per local, model, animation, X, Z.
        x_offset = actor.byte_offset + 1 + actor.local_count * 2 + 2
        for axis in sorted(position):
            offset = x_offset + (axis == "z")
            encoded = encode_placement_coordinate(position[axis], f"{scene} record {record} position.{axis}")
            if encoded == original[offset]:
                continue
            result[offset] = encoded
            audit.append({
                "record_index": record, "field": f"position.{axis}",
                "decoded_byte_offset": offset,
                "before_byte": original[offset], "after_byte": encoded,
                "before_value": actor.world_x if axis == "x" else actor.world_z,
                "after_value": int(position[axis]),
            })
    changed = bytes(result)
    reparsed = {actor.record_index: actor for actor in parse_man(changed, scene).actors}
    for record, position in edits.items():
        for axis, value in position.items():
            actual = reparsed[record].world_x if axis == "x" else reparsed[record].world_z
            if actual != value:
                raise ImportError("MAN placement round-trip validation failed")
    return changed, audit


def compress_lzs(data: bytes) -> bytes:
    """Deterministic greedy encoder for the existing 4 KiB/3..18-byte decoder.

    Candidate positions are bounded to the ring window. Negative positions
    model its initial zero fill, and overlapping references are permitted.
    """
    if len(data) > 4 * 1024 * 1024:
        raise ImportError("LZS input exceeds the 4 MiB decoded limit")
    positions: dict[bytes, deque[int]] = defaultdict(deque)

    def key_at(position: int) -> bytes:
        return bytes(data[n] if n >= 0 else 0 for n in range(position, position + 3)
                     if n < len(data))

    for position in range(-4096, 0):
        positions[key_at(position)].append(position)
    out = bytearray()
    cursor = 0
    while cursor < len(data):
        control_offset = len(out)
        out.append(0)
        control = 0
        for bit in range(8):
            if cursor >= len(data):
                break
            best_length, best_position = 0, 0
            maximum = min(18, len(data) - cursor)
            if maximum >= 3:
                candidates = positions.get(data[cursor:cursor + 3], ())
                for earlier in reversed(candidates):
                    if earlier < cursor - 4096:
                        break
                    length = 0
                    while length < maximum:
                        source = earlier + length
                        if data[cursor + length] != (data[source] if source >= 0 else 0):
                            break
                        length += 1
                    if length > best_length:
                        best_length, best_position = length, earlier
                    if best_length == maximum:
                        break
            if best_length >= 3:
                ring_offset = (0xFEE + best_position) & 0xFFF
                out.extend((ring_offset & 0xFF, ((ring_offset >> 4) & 0xF0) | (best_length - 3)))
                consumed = best_length
            else:
                control |= 1 << bit
                out.append(data[cursor])
                consumed = 1
            for position in range(cursor, cursor + consumed):
                expired = position - 4096
                old_key = key_at(expired)
                old = positions.get(old_key)
                if old and old[0] == expired:
                    old.popleft()
                    if not old:
                        del positions[old_key]
                positions[key_at(position)].append(position)
            cursor += consumed
        out[control_offset] = control
    return bytes(out)


def serialize_man_stream(
    original_stream: bytes, decoded_size: int, scene: str,
    edits: dict[int, dict[str, int | float]],
) -> tuple[bytes, list[dict[str, Any]], dict[str, int | str]]:
    """Return an equal-length patch for exactly the original consumed stream.

    No subsequent descriptor, padding or opaque container bytes are touched.
    Unchanged edits return original encoded bytes, even if the encoder would
    otherwise choose a different equivalent token sequence.
    """
    original, consumed = decompress_lzs(original_stream, decoded_size)
    changed, audit = patch_man_positions(original, scene, edits)
    replacement, sizes = _serialize_man_decoded(original_stream, original, consumed, changed, scene)
    return replacement, audit, sizes


def serialize_man_decoded(original_stream: bytes, decoded_size: int, changed: bytes,
                          scene: str) -> tuple[bytes, dict[str, int | str]]:
    """Serialize a final composed decoded MAN within its original stream span.

    Callers own field-level provenance/audit validation. No file or input buffer
    is modified; this guard verifies exact decoded length and final LZS bytes.
    """
    original, consumed = decompress_lzs(original_stream, decoded_size)
    return _serialize_man_decoded(original_stream, original, consumed, changed, scene)


def _serialize_man_decoded(original_stream, original, consumed, changed, scene):
    if not isinstance(changed, bytes) or len(changed) != len(original):
        raise ImportError("composed MAN must preserve its exact decoded byte length")
    decoded_size = len(original)
    original_span = original_stream[:consumed]
    if changed == original:
        return original_span, {"original_encoded_size": consumed, "new_encoded_size": consumed,
                               "decoded_size": decoded_size}
    encoded = compress_lzs(changed)
    compression_info = {}
    if len(encoded) > consumed:
        from .lzs_optimal import MAX_OPTIMAL_BYTES, compress_lzs_optimal
        if decoded_size <= MAX_OPTIMAL_BYTES:
            compression_info = {"compression_strategy": "bounded_optimal_lzs", "greedy_encoded_size": len(encoded)}
            encoded = compress_lzs_optimal(changed)
    decoded, encoded_consumed = decompress_lzs(encoded, decoded_size)
    if decoded != changed or encoded_consumed != len(encoded):
        raise ImportError("independent LZS decode did not verify encoded MAN bytes")
    if len(encoded) > consumed:
        raise ImportError(f"{scene} edited MAN requires {len(encoded)} compressed bytes but its original span holds {consumed}; relocation is unsupported")
    replacement = encoded + original_span[len(encoded):]
    if decompress_lzs(replacement, decoded_size)[0] != changed:
        raise ImportError("padded MAN replacement failed decode validation")
    return replacement, {"original_encoded_size": consumed,
                         "new_encoded_size": len(encoded), "decoded_size": decoded_size, **compression_info}
