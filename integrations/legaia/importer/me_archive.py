"""Bounded ME archive and packed channel-delta codec from pinned retail reader.

Source evidence: me_archive.rs / FUN_8002B28C and FUN_8002A9CC. Decoding
does not establish resident archive selection, playback cadence or allocation.
"""
import struct
from .core import ImportError


def decode_channel_delta(source):
    if not isinstance(source, bytes) or not 7 <= len(source) <= 0x7fff or source[0] & 0xc0 != 0x40:
        raise ImportError('ME channel codec requires a bounded supported source header')
    nibble_at, byte_at = (5 + v for v in struct.unpack_from('<2H', source, 1))
    if not 5 <= nibble_at <= byte_at <= len(source) - 2:
        raise ImportError('ME channel codec streams exceed their ordered source spans')
    parts, frames = source[byte_at:byte_at + 2]
    if not 1 <= parts <= 64 or not 1 <= frames <= 255:
        raise ImportError('ME channel codec has unsupported parts or frame counts')
    bit_index, nibble_index, byte_index = 0, 0, byte_at + 2

    def bit():
        nonlocal bit_index
        if 5 + bit_index // 8 >= nibble_at:
            raise ImportError('ME selector stream exhausted')
        value = (source[5 + bit_index // 8] >> (7 - bit_index % 8)) & 1
        bit_index += 1
        return value

    def nibble():
        nonlocal nibble_index
        if nibble_at + nibble_index // 2 >= byte_at:
            raise ImportError('ME nibble stream exhausted')
        value = (source[nibble_at + nibble_index // 2] >> (4 if nibble_index % 2 == 0 else 0)) & 15
        nibble_index += 1
        return value

    def low_byte():
        nonlocal byte_index
        if byte_index >= len(source):
            raise ImportError('ME literal byte stream exhausted')
        value = source[byte_index]
        byte_index += 1
        return value

    channels = parts * 6
    delta, accumulated = [0] * channels, [0] * channels
    output = bytearray([parts, frames])
    for frame in range(frames):
        for channel in range(channels):
            if bit():
                value = (nibble() << 8) | low_byte()
            else:
                previous = delta[channel - 6 if channel >= 6 else channel + channels - 6]
                if bit():
                    value = previous + nibble()
                elif bit():
                    value = previous + (nibble() | 0xff0)
                elif bit():
                    value = nibble()
                else:
                    value = nibble() | 0xff0
            delta[channel] = value & 0xffff
        for channel in range(channels):
            if frame == 0:
                accumulated[channel] = (delta[channel] + (accumulated[channel - 6] if channel >= 6 else 0)) & 0xffff
            else:
                accumulated[channel] = (accumulated[channel] + delta[channel]) & 0xffff
        for part in range(parts):
            for pair in range(3):
                a, b = accumulated[part * 6 + pair * 2:part * 6 + pair * 2 + 2]
                output.extend((a & 255, b & 255, ((a >> 8) & 15) | ((b >> 4) & 0xf0)))
    return bytes(output)


def entries(content):
    if not isinstance(content, bytes) or not 3 <= len(content) <= 0x10800 or content[:2] != b'ME' or not content[2]:
        raise ImportError('ME archive requires a nonempty bounded source header')
    count = content[2]
    end = 3 + count * 2
    if end > len(content):
        raise ImportError('ME size table exceeds its source archive')
    result = []
    for index, word in enumerate(struct.unpack_from(f'<{count}H', content, 3)):
        size = word & 0x7fff
        if not size or end + size > len(content):
            raise ImportError('ME entry body exceeds its source archive')
        body = content[end:end + size]
        decoded = decode_channel_delta(body) if word & 0x8000 else body
        if len(decoded) < 2 or not 1 <= decoded[0] <= 64 or not decoded[1] or len(decoded) != 2 + decoded[0] * decoded[1] * 9:
            raise ImportError('ME entry does not decode to a complete packed native channel stream')
        result.append(dict(entry_index=index, size_word=word, compressed=bool(word & 0x8000), byte_offset=end,
                           byte_length=size, decoded=decoded))
        end += size
    return result


def encode_channel_delta(decoded, flags=0x40):
    """Canonical bounded inverse; native part/frame counts are not allocated."""
    if (not isinstance(decoded, bytes) or len(decoded) < 2 or
            not 1 <= decoded[0] <= 64 or not 1 <= decoded[1] <= 255 or
            len(decoded) != 2 + decoded[0] * decoded[1] * 9 or
            type(flags) is not int or not 0x40 <= flags <= 0x7f):
        raise ImportError('ME encoding requires a complete bounded packed stream')
    parts, frames = decoded[:2]
    channels = parts * 6
    bits, nibbles, literals = [], [], []
    delta, accumulated = [0] * channels, [0] * channels
    for frame in range(frames):
        wanted = []
        for part in range(parts):
            at = 2 + (frame * parts + part) * 9
            for pair in range(3):
                a, b, high = decoded[at + pair * 3:at + pair * 3 + 3]
                wanted.extend((a | (high & 15) << 8, b | (high >> 4) << 8))
        for channel, target in enumerate(wanted):
            anchor = wanted[channel - 6] if frame == 0 and channel >= 6 else 0 if frame == 0 else accumulated[channel]
            value = (target - anchor) & 0xfff
            previous = delta[channel - 6 if channel >= 6 else channel + channels - 6]
            difference = (value - previous) & 0xfff
            # Every selector emits one nibble. Prefer the shortest selector
            # without a literal low byte; preserve the actual u16 shadow row.
            if difference <= 15:
                selector, operand, actual = (0, 1), difference, previous + difference
            elif difference >= 0xff0:
                selector, operand = (0, 0, 1), difference & 15
                actual = previous + (operand | 0xff0)
            elif value <= 15:
                selector, operand, actual = (0, 0, 0, 1), value, value
            elif value >= 0xff0:
                selector, operand, actual = (0, 0, 0, 0), value & 15, value
            else:
                selector, operand, actual = (1,), value >> 8, value
                literals.append(value & 255)
            bits.extend(selector); nibbles.append(operand)
            delta[channel] = actual & 0xffff
        for channel in range(channels):
            if frame == 0:
                accumulated[channel] = (delta[channel] + (accumulated[channel - 6] if channel >= 6 else 0)) & 0xffff
            else:
                accumulated[channel] = (accumulated[channel] + delta[channel]) & 0xffff
    selectors = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        selectors[i // 8] |= bit << (7 - i % 8)
    operands = bytearray((len(nibbles) + 1) // 2)
    for i, nibble in enumerate(nibbles):
        operands[i // 2] |= nibble << (4 if i % 2 == 0 else 0)
    if 7 + len(selectors) + len(operands) + len(literals) > 0x7fff:
        raise ImportError('ME encoded stream exceeds its bounded body size')
    result = bytes([flags]) + struct.pack('<2H', len(selectors), len(selectors) + len(operands)) + selectors + operands + bytes([parts, frames]) + bytes(literals)
    if decode_channel_delta(result) != decoded:
        raise ImportError('ME encoded stream exceeds its bounded format or replay differs')
    return bytes(result)


def replace_entry(content, index, decoded):
    """Replace one stream inside its original declared body; keep size chain."""
    original = entries(content)
    if type(index) is not int or not 0 <= index < len(original):
        raise ImportError('Choose an existing ME entry')
    record = original[index]
    if not isinstance(decoded, bytes) or decoded[:2] != record['decoded'][:2] or len(decoded) != len(record['decoded']):
        raise ImportError('ME replacement cannot change decoded part/frame capacity')
    if decoded == record['decoded']:
        return content
    start, size = record['byte_offset'], record['byte_length']
    replacement = encode_channel_delta(decoded, content[start]) if record['compressed'] else decoded
    if len(replacement) > size:
        raise ImportError('ME replacement exceeds the original declared entry body')
    candidate = content[:start] + replacement + content[start + len(replacement):]
    replay = entries(candidate)
    for i, (before, after) in enumerate(zip(original, replay)):
        if any(before[k] != after[k] for k in ('entry_index', 'size_word', 'compressed', 'byte_offset', 'byte_length')) or after['decoded'] != (decoded if i == index else before['decoded']):
            raise ImportError('ME replacement changed its size chain or neighboring stream')
    return candidate
