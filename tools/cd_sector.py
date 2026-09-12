"""Generic Mode 2/2352 Form 1 EDC and P/Q parity encoding.

Layout cross-checked against pinned LegaiaRE crates/iso/src/write.rs;
no game data or game-specific behavior is included.
"""
import struct

SYNC = b'\x00'+b'\xff'*10+b'\x00'


def _tables():
    crc, forward, backward = [], [0]*256, [0]*256
    for value in range(256):
        c = value
        for _ in range(8):
            c = (c >> 1) ^ (0xD8018001 if c & 1 else 0)
        crc.append(c)
        doubled = (value << 1) ^ (0x11D if value & 0x80 else 0)
        forward[value] = doubled
        backward[value ^ doubled] = value
    return crc, forward, backward


_CRC, _FORWARD, _BACKWARD = _tables()


def _parity(data, majors, minors, stride, increment):
    output = bytearray(majors*2)
    for major in range(majors):
        index = (major//2)*stride+(major & 1)
        a = b = 0
        for _ in range(minors):
            value = data[index]
            index = (index+increment) % (majors*minors)
            a = _FORWARD[a ^ value]
            b ^= value
        a = _BACKWARD[_FORWARD[a] ^ b]
        output[major], output[major+majors] = a, a ^ b
    return output


def encode_form1(sector: bytes) -> bytes:
    """Preserve framing/payload and regenerate Form 1 error protection."""
    if not isinstance(sector, bytes) or len(sector) != 2352:
        raise ValueError('Expected one immutable 2352-byte sector')
    if sector[:12] != SYNC or sector[15] != 2:
        raise ValueError('Expected Mode 2 sync and header')
    if sector[16:20] != sector[20:24] or sector[18] & 0x20:
        raise ValueError('Expected matching Form 1 subheaders')
    out = bytearray(sector)
    crc = 0
    for value in sector[16:2072]:
        crc = (crc >> 8) ^ _CRC[(crc ^ value) & 255]
    struct.pack_into('<I', out, 2072, crc)
    out[12:16] = bytes(4)
    out[2076:2248] = _parity(out[12:2076], 86, 24, 2, 86)
    out[2248:2352] = _parity(out[12:2248], 52, 43, 86, 88)
    out[12:16] = sector[12:16]
    return bytes(out)


def relocate_mode2(sector: bytes, lba: int) -> bytes:
    """Change only MSF address; Mode 2 protection does not include this header."""
    if not isinstance(sector, bytes) or len(sector) != 2352 or sector[:12] != SYNC or sector[15] != 2:
        raise ValueError('Expected Mode 2 sector')
    if type(lba) is not int or not 0 <= lba < 100*60*75-150:
        raise ValueError('LBA is outside two-digit BCD MSF range')
    frames = lba+150
    values = (frames//4500, frames//75 % 60, frames % 75)
    address = bytes((value//10)*16+value % 10 for value in values)
    return sector[:12]+address+sector[15:]
