"""Bounded minimum-byte encoder for the existing Legaia 4-KiB LZS grammar.

Eight states per decoded position include the control-byte cost every eight
tokens. All back-reference lengths 3..18 are considered, including initial
zero-window and overlapping copies. No offsets, text or container sizes change.
This slower encoder is intended only for a greedy encoder's capacity failure.
"""
from __future__ import annotations

from array import array
from collections import defaultdict, deque

from .core import ImportError, decompress_lzs

MAX_OPTIMAL_BYTES = 256 * 1024


def _matches(data: bytes) -> tuple[bytearray, array]:
    """Find the longest valid copy at each position; its shorter prefixes suffice."""
    size = len(data)
    lengths, offsets = bytearray(size), array("H", [0]) * size
    positions = defaultdict(deque)

    def key_at(position):
        return bytes(data[i] if i >= 0 else 0 for i in range(position, min(position + 3, size)))

    for earlier in range(-4096, 0):
        positions[key_at(earlier)].append(earlier)
    for cursor in range(size):
        maximum = min(18, size - cursor)
        best_length, best_position = 0, 0
        if maximum >= 3:
            for earlier in reversed(positions.get(data[cursor:cursor + 3], ())):
                # Exact prefix keys establish the first three bytes, including
                # overlap. Each later source byte is either initial zero or a
                # previously decoded byte of this same matching output prefix.
                length = 3
                while length < maximum:
                    source = earlier + length
                    if data[cursor + length] != (data[source] if source >= 0 else 0):
                        break
                    length += 1
                if length > best_length:
                    best_length, best_position = length, earlier
                if best_length == maximum:
                    break
        lengths[cursor] = best_length
        offsets[cursor] = (0xFEE + best_position) & 0xFFF
        expired = cursor - 4096
        old_key = key_at(expired)
        old = positions[old_key]
        old.popleft()
        if not old:
            del positions[old_key]
        positions[key_at(cursor)].append(cursor)
    return lengths, offsets


def compress_lzs_optimal(data: bytes) -> bytes:
    """Return a minimum-size exact-expansion stream, deterministically breaking ties.

    Bounded to 256 KiB decoded input. Packed DP/match arrays use 35 bytes per
    input byte (under 9 MiB at the cap); the candidate index retains at most
    4096 positions. Allocation failure becomes a normal importer rejection.
    References never expand past the declared decoded size. The Python decoder's
    clipped final-reference behavior is not assumed safe in the retail loader.
    """
    if not isinstance(data, bytes) or len(data) > MAX_OPTIMAL_BYTES:
        raise ImportError("optimal LZS requires immutable bytes of at most 256 KiB")
    if not data:
        return b""
    try:
        lengths, offsets = _matches(data)
        size = len(data)
        costs = array("I", [0]) * (8 * (size + 1))
        for cursor in range(size - 1, -1, -1):
            base = cursor * 8
            maximum = lengths[cursor]
            for phase in range(8):
                next_phase = (phase + 1) & 7
                best = 1 + costs[base + 8 + next_phase]
                for length in range(3, maximum + 1):
                    candidate = 2 + costs[base + length * 8 + next_phase]
                    if candidate < best:
                        best = candidate
                costs[base + phase] = best + (phase == 0)
        encoded = bytearray()
        cursor = phase = 0
        control_offset = 0
        while cursor < size:
            if phase == 0:
                control_offset = len(encoded)
                encoded.append(0)
            next_phase = (phase + 1) & 7
            remaining = costs[cursor * 8 + phase] - (phase == 0)
            chosen = 0
            # Deterministic tie choice: longest optimal copy, otherwise literal.
            for length in range(lengths[cursor], 2, -1):
                if 2 + costs[(cursor + length) * 8 + next_phase] == remaining:
                    chosen = length
                    break
            if chosen:
                offset = offsets[cursor]
                encoded.extend((offset & 255, ((offset >> 4) & 0xF0) | (chosen - 3)))
                cursor += chosen
            else:
                encoded[control_offset] |= 1 << phase
                encoded.append(data[cursor])
                cursor += 1
            phase = next_phase
        result = bytes(encoded)
        if len(result) != costs[0]:
            raise ImportError("optimal LZS reconstruction disagrees with minimum-byte cost")
        decoded, consumed = decompress_lzs(result, size)
        if decoded != data or consumed != len(result):
            raise ImportError("independent decoder rejected optimal LZS output")
        return result
    except MemoryError as exc:
        raise ImportError("insufficient memory for bounded optimal LZS fallback") from exc
