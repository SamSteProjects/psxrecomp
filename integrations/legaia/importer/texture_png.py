"""Bounded PNG/TIM pixel interchange with source-owned layout and STP.

PNG structure, filters and transparency follow https://www.w3.org/TR/png-3/.
Numeric RGB samples are used directly, without claiming a retail color space.
TIM words and upload layout use the existing verified textures decoder.

Palette rebuild uses weighted median-cut in RGB5, separating transparent zero
and opaque STP classes. Each representative is an actual requested word nearest
its box's weighted centroid. Existing matching slots remain; surplus duplicates
are reclaimed from the highest index only when capacity requires it. New words
are allocated in ascending word order to the lowest free slots. Other slots and
CLUT rows stay exact. Pixel assignment uses original PNG RGB8 distance, with
the original index preferred on ties. Exact no-ops bypass palette rebuilding.
"""
from __future__ import annotations

from array import array
from collections import Counter
import math
import struct
import zlib

from .core import ImportError
from .texture_authoring import _payload_ranges, _validate, texture_payload_changes
from .textures import decode_tim, parse_tim


MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 2_097_152
MAX_TIM_BYTES = 1024 * 1024
MAX_CHOICES = 65536
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
PROFILE_KEYS = {'schema_version', 'bpp', 'width', 'height', 'palette_index',
                'palette_count', 'entry_count'}
SRGB_CHROMATICITIES = (31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000)
EXPANDED = tuple((value << 3) | (value >> 2) for value in range(32))
RGB5 = tuple(min(range(32), key=lambda sample: abs(EXPANDED[sample] - value))
             for value in range(256))
LIMITATIONS = [
    'Existing TIM dimensions, headers, VRAM rectangles and source allocation remain unchanged.',
    'PNG samples are numeric RGB values; alpha must be 0 or 255 and PSX STP is a separate bit.',
    'Existing-palette near-black samples retain their STP class; direct/rebuilt rounded black requires STP1.',
    'Indexed image indices are shared by every source palette; other CLUT rows remain unchanged.',
    'Palette rebuild separates transparent/STP classes and uses deterministic weighted median-cut in RGB5.',
    'Runtime texture residency, palette animation, blending and gameplay appearance remain unverified.',
]


def _dimensions(width: int, height: int) -> None:
    if (type(width) is not int or type(height) is not int or min(width, height) < 1 or
            max(width, height) > 0x7fffffff or width * height > MAX_PIXELS):
        raise ImportError('PNG dimensions exceed the bounded pixel count')


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    da, db, dc = abs(p - a), abs(p - b), abs(p - c)
    return a if da <= db and da <= dc else b if db <= dc else c


def decode_png(content: bytes) -> dict:
    """Decode a strict noninterlaced bounded PNG into immutable RGBA8 bytes."""
    if (not isinstance(content, bytes) or not 8 <= len(content) <= MAX_PNG_BYTES or
            content[:8] != PNG_SIGNATURE):
        raise ImportError('Choose an immutable PNG no larger than 8 MiB')
    at, seen = 8, set()
    width = height = depth = color = None
    palette = transparency = None
    data = bytearray()
    data_started = data_ended = ended = False
    while at < len(content):
        if at + 12 > len(content):
            raise ImportError('Truncated PNG chunk')
        length = struct.unpack_from('>I', content, at)[0]
        kind = content[at + 4:at + 8]
        if (length > 0x7fffffff or at + 12 + length > len(content) or
                any(not (65 <= c <= 90 or 97 <= c <= 122) for c in kind) or kind[2] & 32):
            raise ImportError('Malformed PNG chunk type or length')
        body = content[at + 8:at + 8 + length]
        crc = struct.unpack_from('>I', content, at + 8 + length)[0]
        if zlib.crc32(body, zlib.crc32(kind)) & 0xffffffff != crc:
            raise ImportError('PNG chunk CRC differs')
        at += 12 + length
        if not seen and kind != b'IHDR':
            raise ImportError('PNG IHDR must be first')
        if kind in (b'acTL', b'fcTL', b'fdAT'):
            raise ImportError('Animated PNG is unsupported')
        if kind in (b'iCCP', b'cICP', b'mDCV', b'cLLI'):
            raise ImportError('ICC/HDR PNG color data is unsupported')
        if kind in (b'IHDR', b'PLTE', b'tRNS', b'gAMA', b'cHRM', b'sRGB', b'sBIT',
                    b'bKGD', b'hIST', b'pHYs', b'tIME', b'eXIf', b'IEND') and kind in seen:
            raise ImportError('Duplicate singleton PNG chunk')
        if data_started and kind != b'IDAT':
            data_ended = True
        if kind == b'IHDR':
            if length != 13:
                raise ImportError('PNG IHDR length must be 13')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            _dimensions(width, height)
            if (color not in (0, 2, 3, 4, 6) or
                    depth not in ((1, 2, 4, 8) if color == 3 else (8,)) or
                    compression != 0 or filtering != 0 or interlace != 0):
                raise ImportError('PNG requires supported 8-bit or indexed samples without interlace')
        elif kind == b'PLTE':
            if (data_started or b'tRNS' in seen or b'bKGD' in seen or color in (0, 4) or
                    length == 0 or length % 3 or length > 768):
                raise ImportError('PNG palette has invalid length, type or order')
            if color == 3 and length // 3 > 1 << depth:
                raise ImportError('PNG palette exceeds its indexed sample depth')
            palette = tuple(body[i:i + 3] for i in range(0, length, 3))
        elif kind == b'tRNS':
            if data_started or color in (4, 6):
                raise ImportError('PNG transparency has invalid type or order')
            if color == 3:
                if palette is None or not 1 <= length <= len(palette):
                    raise ImportError('Indexed PNG transparency requires its palette')
                transparency = body
            elif color == 0 and length == 2:
                transparency = struct.unpack('>H', body)
                if transparency[0] > 255:
                    raise ImportError('8-bit PNG transparency sample exceeds 255')
            elif color == 2 and length == 6:
                transparency = struct.unpack('>3H', body)
                if any(sample > 255 for sample in transparency):
                    raise ImportError('8-bit PNG transparency sample exceeds 255')
            else:
                raise ImportError('PNG transparency length differs from color type')
        elif kind in (b'sRGB', b'gAMA', b'cHRM', b'sBIT'):
            if data_started or b'PLTE' in seen:
                raise ImportError('PNG color metadata must precede palette and image data')
            if kind == b'sRGB' and (length != 1 or body[0] > 3):
                raise ImportError('Malformed PNG sRGB rendering intent')
            if kind == b'gAMA' and (length != 4 or struct.unpack('>I', body)[0] != 45455):
                raise ImportError('Only standard sRGB PNG gamma is supported')
            if kind == b'cHRM' and (length != 32 or struct.unpack('>8I', body) != SRGB_CHROMATICITIES):
                raise ImportError('Only standard sRGB PNG chromaticities are supported')
            channels = {0: 1, 2: 3, 3: 3, 4: 2, 6: 4}[color]
            if kind == b'sBIT' and (length != channels or any(not 1 <= v <= (8 if color == 3 else depth) for v in body)):
                raise ImportError('Malformed PNG significant sample depths')
        elif kind == b'IDAT':
            if data_ended or color == 3 and palette is None:
                raise ImportError('PNG IDAT must be consecutive and follow any indexed palette')
            data_started = True
            data.extend(body)
        elif kind == b'IEND':
            if length or not data_started or at != len(content):
                raise ImportError('PNG must end exactly at its empty IEND chunk')
            ended = True
            seen.add(kind)
            break
        elif kind in (b'bKGD', b'hIST', b'pHYs'):
            if data_started:
                raise ImportError('PNG physical/palette metadata must precede image data')
            if kind == b'bKGD' and (length != (1 if color == 3 else 2 if color in (0, 4) else 6) or
                                    color == 3 and (palette is None or body[0] >= len(palette))):
                raise ImportError('Malformed PNG background metadata')
            if kind == b'hIST' and (palette is None or length != 2 * len(palette)):
                raise ImportError('Malformed PNG histogram')
            if kind == b'pHYs' and (length != 9 or body[8] not in (0, 1)):
                raise ImportError('Malformed PNG physical dimensions')
        elif kind == b'tIME':
            if length != 7:
                raise ImportError('Malformed PNG modification time')
        elif not kind[0] & 32:
            raise ImportError('Unknown critical PNG chunk')
        # Unneeded ancillary text/physical metadata is never decompressed.
        seen.add(kind)
    if not ended or width is None:
        raise ImportError('PNG is incomplete')
    samples = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    stride = (width * samples * depth + 7) // 8
    expected = (stride + 1) * height
    try:
        inflater = zlib.decompressobj()
        scanlines = inflater.decompress(data, expected + 1)
    except zlib.error as exc:
        raise ImportError('Malformed PNG zlib stream') from exc
    if (len(scanlines) != expected or not inflater.eof or inflater.unconsumed_tail or inflater.unused_data):
        raise ImportError('PNG zlib stream has wrong size, is incomplete or contains trailing data')
    bpp = max(1, (samples * depth + 7) // 8)
    prior, rgba = bytes(stride), bytearray()
    for y in range(height):
        offset = y * (stride + 1)
        filtering = scanlines[offset]
        if filtering > 4:
            raise ImportError('Unknown PNG row filter')
        row = bytearray(scanlines[offset + 1:offset + 1 + stride])
        if filtering:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prior[i]
                c = prior[i - bpp] if i >= bpp else 0
                predictor = a if filtering == 1 else b if filtering == 2 else (a + b) // 2 if filtering == 3 else _paeth(a, b, c)
                row[i] = (row[i] + predictor) & 255
        if color == 6:
            rgba.extend(row)
        elif color == 2:
            for x in range(width):
                rgb = row[x * 3:x * 3 + 3]
                rgba.extend(rgb)
                rgba.append(0 if transparency is not None and tuple(rgb) == transparency else 255)
        elif color in (0, 4):
            for x in range(width):
                gray = row[x * samples]
                alpha = row[x * samples + 1] if color == 4 else 0 if transparency == (gray,) else 255
                rgba.extend((gray, gray, gray, alpha))
        else:
            mask = (1 << depth) - 1
            for x in range(width):
                bit = x * depth
                index = (row[bit // 8] >> (8 - depth - bit % 8)) & mask
                if index >= len(palette):
                    raise ImportError('PNG pixel references an absent palette entry')
                rgba.extend(palette[index])
                rgba.append(transparency[index] if transparency is not None and index < len(transparency) else 255)
        prior = row
    return dict(width=width, height=height, rgba=bytes(rgba))


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(data, zlib.crc32(kind)) & 0xffffffff)


def _encode_png(width: int, height: int, rgba: bytes) -> bytes:
    _dimensions(width, height)
    if not isinstance(rgba, bytes) or len(rgba) != width * height * 4:
        raise ImportError('PNG RGBA bytes differ from dimensions')
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        rows.extend(rgba[y * width * 4:(y + 1) * width * 4])
    result = PNG_SIGNATURE + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    result += _chunk(b'IDAT', zlib.compress(rows, 9)) + _chunk(b'IEND', b'')
    if len(result) > MAX_PNG_BYTES:
        raise ImportError('Exported PNG exceeds 8 MiB')
    return result


def _source(content: bytes, palette_index: int):
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_TIM_BYTES:
        raise ImportError('PNG interchange requires one TIM no larger than 1 MiB')
    tim = parse_tim(content)
    if tim.byte_length != len(content):
        raise ImportError('PNG interchange requires exactly one source TIM')
    if type(palette_index) is not int or palette_index < 0:
        raise ImportError('Choose an existing integer palette index')
    _dimensions(tim.width, tim.image.height)
    decoded = decode_tim(tim, palette_index)
    _validate(content, content)
    entries = (1 << tim.bpp) if tim.bpp in (4, 8) else 0
    profile = dict(schema_version='legaia.texture-png-profile.v1', bpp=tim.bpp,
                   width=tim.width, height=tim.image.height, palette_index=palette_index,
                   palette_count=len(tim.clut.data) // (entries * 2) if entries else 0,
                   entry_count=entries)
    return tim, decoded, profile


def export_texture_png(effective_tim: bytes, palette_index: int = 0) -> tuple[bytes, bytes, dict]:
    _, decoded, profile = _source(effective_tim, palette_index)
    stp = bytes(channel for bit in decoded['stp'] for channel in (bit * 255, bit * 255, bit * 255, 255))
    return (_encode_png(profile['width'], profile['height'], decoded['rgba']),
            _encode_png(profile['width'], profile['height'], stp), profile)


def _class(word: int) -> int:
    return 0 if word == 0 else 2 if word & 0x8000 else 1


def _rgb5(word: int) -> tuple[int, int, int]:
    return word & 31, (word >> 5) & 31, (word >> 10) & 31


def _representatives(counts: Counter, capacity: int) -> list[int]:
    if len(counts) <= capacity:
        return sorted(counts)
    boxes = [sorted(word for word in counts if _class(word) == category) for category in range(3)]
    boxes = [box for box in boxes if box]
    while len(boxes) < capacity:
        choices = []
        for index, box in enumerate(boxes):
            if len(box) <= 1:
                continue
            ranges = [max((word >> shift) & 31 for word in box) -
                      min((word >> shift) & 31 for word in box) for shift in (0, 5, 10)]
            weight = sum(counts[word] for word in box)
            choices.append(((max(ranges), weight, len(box), -min(box)), index, ranges))
        if not choices:
            break
        _, index, ranges = max(choices)
        axis = ranges.index(max(ranges))
        box = sorted(boxes[index], key=lambda word: ((word >> (axis * 5)) & 31, word))
        target, cumulative = (sum(counts[word] for word in box) + 1) // 2, 0
        cut = len(box) - 1
        for i, word in enumerate(box[:-1]):
            cumulative += counts[word]
            if cumulative >= target:
                cut = i + 1
                break
        boxes[index:index + 1] = [box[:cut], box[cut:]]
    representatives = []
    for box in boxes:
        weight = sum(counts[word] for word in box)
        sums = [sum(((word >> shift) & 31) * counts[word] for word in box) for shift in (0, 5, 10)]
        representatives.append(min(box, key=lambda word: (
            sum((((word >> shift) & 31) * weight - sums[axis]) ** 2 for axis, shift in enumerate((0, 5, 10))), word)))
    return sorted(representatives)


def _rebuild_palette(palette: tuple[int, ...], counts: Counter) -> list[int]:
    representatives = _representatives(counts, len(palette))
    wanted = set(representatives)
    reserved = {i for i, word in enumerate(palette) if word in wanted}
    present = {palette[i] for i in reserved}
    new = [word for word in representatives if word not in present]
    if len(new) > len(palette) - len(reserved):
        protected = {min(i for i, old in enumerate(palette) if old == word) for word in present}
        for i in sorted(reserved - protected, reverse=True):
            reserved.remove(i)
            if len(new) <= len(palette) - len(reserved):
                break
    free = [i for i in range(len(palette)) if i not in reserved]
    result = list(palette)
    for word, slot in zip(new, free):
        result[slot] = word
    if not wanted <= set(result):
        raise ImportError('Rebuilt palette cannot retain its qualified representatives')
    return result


def _assign_indices(rgba: bytes, desired: array, classes: bytes, palette: list[int], original: bytes) -> bytearray:
    # A bit mask retains all tied indices without allocating a tuple of up to
    # 256 duplicates for every requested color. Cache keys use the original
    # RGB8 sample and alpha/STP class, not a second quantized RGB distance.
    entries = {category: {} for category in range(3)}
    for index, word in enumerate(palette):
        entries[_class(word)][word] = entries[_class(word)].get(word, 0) | (1 << index)
    groups = {category: [(tuple(EXPANDED[v] for v in _rgb5(word)), mask)
                         for word, mask in sorted(values.items())]
              for category, values in entries.items()}
    cache, result = {}, bytearray(len(desired))
    for index, word in enumerate(desired):
        category = classes[index]
        if not groups[category]:
            raise ImportError('Existing palette has no entry compatible with requested alpha/STP; choose palette rebuild')
        at = index * 4
        r, g, b = rgba[at:at + 3]
        key = (category << 24) | (r << 16) | (g << 8) | b
        choice = cache.get(key)
        if choice is None:
            distance, mask = 1 << 30, 0
            for rgb, indices in groups[category]:
                error = (r - rgb[0]) ** 2 + (g - rgb[1]) ** 2 + (b - rgb[2]) ** 2 if category else 0
                if error < distance:
                    distance, mask = error, indices
                elif error == distance:
                    mask |= indices
            choice = mask
            if len(cache) >= MAX_CHOICES:
                cache.clear()
            cache[key] = choice
        before = original[index]
        result[index] = before if choice & (1 << before) else (choice & -choice).bit_length() - 1
    return result


def _analysis(original: bytes, candidate: bytes, requested: bytes, decoded: dict,
              desired: array | None, direct_colors: set | None, palette_index: int,
              palette_mode: str, forced_black: int, forced_transparent: int) -> dict:
    after = decode_tim(candidate, palette_index)
    maximum = squared = visible = pixels = 0
    for index in range(after['width'] * after['height']):
        at = index * 4
        if requested[at + 3] == 0:
            continue
        visible += 1
        errors = [abs(requested[at + axis] - after['rgba'][at + axis]) for axis in range(3)]
        maximum = max(maximum, *errors)
        squared += sum(error * error for error in errors)
        pixels += any(errors)
    tim = parse_tim(candidate)
    palette = (struct.unpack_from(f'<{1 << tim.bpp}H', tim.clut.data, palette_index * (1 << tim.bpp) * 2)
               if tim.bpp in (4, 8) else ())
    quantization = dict(color_max_error=maximum,
                        color_rms_error=math.sqrt(squared / (visible * 3)) if visible else 0.0,
                        quantized_pixel_count=pixels,
                        distinct_requested_words=len(set(desired)) if desired is not None else len(direct_colors),
                        output_palette_size=len(set(palette)),
                        stp_changed_pixels=sum(a != b for a, b in zip(decoded['stp'], after['stp'])),
                        forced_black_stp_pixels=forced_black,
                        forced_transparent_stp_pixels=forced_transparent)
    return dict(quantization=quantization, changes=texture_payload_changes(original, candidate),
                palette_index=palette_index, palette_mode=palette_mode, limitations=list(LIMITATIONS))


def import_texture_png(effective_tim: bytes, png_content: bytes, profile: dict,
                       palette_mode: str = 'existing', stp_content: bytes | None = None) -> tuple[bytes, dict]:
    if (not isinstance(profile, dict) or set(profile) != PROFILE_KEYS or
            profile.get('schema_version') != 'legaia.texture-png-profile.v1' or
            any(type(profile.get(key)) is not int for key in PROFILE_KEYS - {'schema_version'})):
        raise ImportError('Choose the exact source-qualified texture PNG profile')
    tim, decoded, expected = _source(effective_tim, profile['palette_index'])
    if profile != expected:
        raise ImportError('Texture PNG profile differs from the effective TIM layout')
    if palette_mode not in ('existing', 'rebuild') or tim.bpp > 8 and palette_mode != 'existing':
        raise ImportError('Choose an indexed palette mode; direct-color TIMs require existing')
    png = decode_png(png_content)
    if (png['width'], png['height']) != (profile['width'], profile['height']):
        raise ImportError('PNG dimensions must match the source texture exactly')
    plane = None
    if stp_content is not None:
        stp_png = decode_png(stp_content)
        if (stp_png['width'], stp_png['height']) != (profile['width'], profile['height']):
            raise ImportError('STP PNG dimensions must match the source texture exactly')
        plane = bytearray()
        for at in range(0, len(stp_png['rgba']), 4):
            pixel = stp_png['rgba'][at:at + 4]
            if pixel not in (b'\0\0\0\xff', b'\xff\xff\xff\xff'):
                raise ImportError('STP PNG requires only opaque black and white pixels')
            plane.append(pixel[0] // 255)
    rgba = png['rgba']
    desired = array('H') if tim.bpp != 24 else None
    classes = bytearray()
    direct_colors = set() if tim.bpp == 24 else None
    forced_black = forced_transparent = 0
    for index in range(profile['width'] * profile['height']):
        at = index * 4
        r, g, b, alpha = rgba[at:at + 4]
        if alpha not in (0, 255):
            raise ImportError('PNG alpha must be 0 or 255; partial opacity does not encode PSX STP')
        stp = plane[index] if plane is not None else decoded['stp'][index]
        if tim.bpp == 24:
            if alpha != 255 or stp:
                raise ImportError('24-bpp TIMs require opaque alpha and STP0')
            direct_colors.add((r << 16) | (g << 8) | b)
            continue
        word = RGB5[r] | (RGB5[g] << 5) | (RGB5[b] << 10)
        if alpha == 0:
            if plane is not None and stp:
                raise ImportError('Transparent PNG pixel conflicts with explicit STP1')
            if plane is None and stp:
                forced_transparent += 1
            word, stp = 0, 0
        elif ((r == g == b == 0) if tim.bpp in (4, 8) and palette_mode == 'existing' else word == 0):
            if plane is not None and not stp:
                raise ImportError('Opaque black pixel conflicts with explicit STP0')
            if plane is None and not stp:
                forced_black += 1
            stp = 1
        desired.append(word | (stp << 15))
        classes.append(0 if alpha == 0 else 2 if stp else 1)
    # Compare visible samples and STP before general indexed quantization. This
    # preserves duplicate source indices, unused palette words and opaque bits.
    unchanged = all(rgba[i + 3] == decoded['rgba'][i + 3] and
                    (rgba[i + 3] == 0 or rgba[i:i + 3] == decoded['rgba'][i:i + 3])
                    for i in range(0, len(rgba), 4))
    if unchanged and (plane is None or plane == decoded['stp']):
        return effective_tim, _analysis(effective_tim, effective_tim, rgba, decoded, desired,
                                        direct_colors, profile['palette_index'], palette_mode, 0, 0)
    candidate = bytearray(effective_tim)
    image_start = _payload_ranges(tim)[-1][0]
    if tim.bpp == 24:
        candidate[image_start:] = bytes(channel for at in range(0, len(rgba), 4) for channel in rgba[at:at + 3])
    elif tim.bpp == 16:
        for index, word in enumerate(desired):
            struct.pack_into('<H', candidate, image_start + index * 2, word)
    else:
        capacity = 1 << tim.bpp
        palette_at = profile['palette_index'] * capacity * 2
        old_palette = struct.unpack_from(f'<{capacity}H', tim.clut.data, palette_at)
        palette = (_rebuild_palette(old_palette, Counter(desired)) if palette_mode == 'rebuild' else list(old_palette))
        original_indices = bytes((value >> shift) & (capacity - 1)
                                 for value in tim.image.data for shift in range(0, 8, tim.bpp))
        indices = _assign_indices(rgba, desired, classes, palette, original_indices)
        if palette_mode == 'rebuild':
            struct.pack_into(f'<{capacity}H', candidate, 20 + palette_at, *palette)
        mask = capacity - 1
        for index, value in enumerate(indices):
            offset, shift = image_start + index * tim.bpp // 8, index * tim.bpp % 8
            candidate[offset] = (candidate[offset] & (255 ^ (mask << shift))) | (value << shift)
    result = bytes(candidate)
    _validate(effective_tim, result)
    decode_tim(result, profile['palette_index'])
    return result, _analysis(effective_tim, result, rgba, decoded, desired, direct_colors,
                             profile['palette_index'], palette_mode, forced_black, forced_transparent)
