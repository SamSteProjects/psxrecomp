"""Construct a new TIM from bounded PNG samples and explicit native choices."""
from array import array
from collections import Counter
from hashlib import sha256
import math
import struct

from .core import ImportError
from .texture_png import decode_png, RGB5, _representatives, _assign_indices
from .texture_slot_allocation import validate_added_tim
from .textures import decode_tim


OPTION_KEYS = {'bpp', 'image_x', 'image_y', 'clut_x', 'clut_y', 'stp_mode'}
LIMITATIONS = [
    'PNG samples are numeric RGB8 values; no color-space conversion is inferred.',
    'Alpha must be zero or 255. STP is a separate explicit policy or black/white plane.',
    'Opaque rounded black requires STP1; transparent pixels require word zero and STP0.',
    'Indexed output contains one deterministic RGB5 median-cut palette, without dithering.',
    'Image and CLUT placement are explicit native word coordinates; no scaling or padding is inferred.',
    'Runtime residency, upload order, semi-transparent blending and gameplay appearance remain unverified.',
]


def convert_png(png_content, options, stp_content=None):
    if (not isinstance(options, dict) or set(options) != OPTION_KEYS or
            any(type(options[k]) is not int for k in OPTION_KEYS - {'stp_mode'}) or
            options['bpp'] not in (4, 8, 16, 24) or options['stp_mode'] not in ('opaque', 'semi')):
        raise ImportError('PNG conversion requires exact native mode, placement and STP choices')
    bpp = options['bpp']
    x, y, cx, cy = (options[k] for k in ('image_x', 'image_y', 'clut_x', 'clut_y'))
    if not 0 <= x < 1024 or not 0 <= y < 512:
        raise ImportError('Image origin must be inside VRAM')
    if bpp <= 8:
        if not 0 <= cx <= 1024-(1 << bpp) or cx % 16 or not 0 <= cy < 512:
            raise ImportError('Indexed palette needs a 16-word-aligned origin and room for its complete CLUT')
    elif (cx, cy) != (0, 0):
        raise ImportError('Direct-color conversion requires zero unused CLUT coordinates')
    if bpp == 24 and options['stp_mode'] != 'opaque':
        raise ImportError('RGB24 requires opaque samples and STP0')
    png = decode_png(png_content)
    width, height, rgba = png['width'], png['height'], png['rgba']
    if width*bpp % 16:
        raise ImportError('PNG width must encode whole TIM words; change the source image explicitly')
    words = width*bpp//16
    if not words or x+words > 1024 or y+height > 512:
        raise ImportError('Converted image rectangle exceeds VRAM')
    capacity = 1 << bpp if bpp <= 8 else 0
    if 20+words*height*2+(12+capacity*2 if capacity else 0) > 1024*1024:
        raise ImportError('Converted TIM exceeds the one MiB authored content budget')
    plane = None
    if stp_content is not None:
        stp = decode_png(stp_content)
        if (stp['width'], stp['height']) != (width, height):
            raise ImportError('Explicit STP plane must match the source PNG dimensions')
        plane = bytearray()
        for at in range(0, len(stp['rgba']), 4):
            pixel = stp['rgba'][at:at+4]
            if pixel not in (b'\0\0\0\xff', b'\xff\xff\xff\xff'):
                raise ImportError('STP plane must contain only opaque black or white pixels')
            plane.append(pixel[0]//255)
    desired, classes = array('H'), bytearray()
    forced_black = forced_transparent = transparent = 0
    for index in range(width*height):
        r, g, b, alpha = rgba[index*4:index*4+4]
        if alpha not in (0, 255):
            raise ImportError('Partial PNG alpha cannot encode native transparent-zero or STP')
        bit = plane[index] if plane is not None else int(options['stp_mode'] == 'semi')
        if bpp == 24:
            if alpha != 255 or bit:
                raise ImportError('RGB24 requires opaque alpha and STP0')
            continue
        word = RGB5[r] | RGB5[g] << 5 | RGB5[b] << 10
        if alpha == 0:
            if plane is not None and bit:
                raise ImportError('Transparent source pixel conflicts with explicit STP1')
            forced_transparent += int(bit != 0)
            transparent += 1
            word, bit = 0, 0
        elif word == 0:
            if plane is not None and not bit:
                raise ImportError('Opaque rounded black conflicts with explicit STP0')
            forced_black += int(bit == 0)
            bit = 1
        desired.append(word | bit << 15)
        classes.append(0 if alpha == 0 else 2 if bit else 1)
    palette = []
    indices = None
    if bpp <= 8:
        palette = _representatives(Counter(desired), capacity)
        representative_count = len(palette)
        palette += [0]*(capacity-len(palette))
        indices = _assign_indices(rgba, desired, classes, palette, bytes(width*height))
        image = bytearray(words*height*2)
        for index, value in enumerate(indices):
            image[index*bpp//8] |= value << (index*bpp % 8)
        image = bytes(image)
    elif bpp == 16:
        image = struct.pack(f'<{len(desired)}H', *desired)
        representative_count = 0
    else:
        image = bytes(c for at in range(0, len(rgba), 4) for c in rgba[at:at+3])
        representative_count = 0
    result = struct.pack('<II', 0x10, (4, 8, 16, 24).index(bpp) | (8 if capacity else 0))
    if capacity:
        result += struct.pack('<I4H', 12+capacity*2, cx, cy, capacity, 1)
        result += struct.pack(f'<{capacity}H', *palette)
    result += struct.pack('<I4H', 12+len(image), x, y, words, height)+image
    tim = validate_added_tim(result)
    decoded = decode_tim(tim)
    if (tim.width, tim.image.height) != (width, height) or tim.byte_length != len(result):
        raise ImportError('Converted TIM readback differs from the source dimensions')
    maximum = squared = visible = changed = 0
    for index in range(width*height):
        at = index*4
        if decoded['rgba'][at+3] != rgba[at+3] or bpp != 24 and decoded['stp'][index] != (desired[index] >> 15):
            raise ImportError('Converted TIM readback changed alpha or the qualified STP class')
        if rgba[at+3] == 0:
            continue
        visible += 1
        errors = [abs(rgba[at+k]-decoded['rgba'][at+k]) for k in range(3)]
        maximum = max(maximum, *errors)
        squared += sum(e*e for e in errors)
        changed += int(any(errors))
    report = dict(schema_version='legaia.texture-image-conversion.v1',
        png_sha256=sha256(png_content).hexdigest(),png_byte_length=len(png_content),
        stp_png_sha256=sha256(stp_content).hexdigest() if stp_content is not None else None,
        options=dict(options),width=width,height=height,proposed_sha256=sha256(result).hexdigest(),
        byte_length=len(result),palette_count=int(bool(capacity)),
        quantization=dict(color_max_error=maximum,color_rms_error=math.sqrt(squared/(visible*3)) if visible else 0.,
            quantized_pixel_count=changed,visible_pixel_count=visible,transparent_pixel_count=transparent,
            distinct_requested_words=len(set(desired)) if bpp != 24 else len({rgba[at:at+3] for at in range(0,len(rgba),4)}),
            palette_representative_count=representative_count,used_palette_entries=len(set(indices)) if indices is not None else 0,
            forced_black_stp_pixels=forced_black,forced_transparent_stp_pixels=forced_transparent),
        native_readback_verified=True,alpha_stp_classes_verified=True,project_changed=False,
        gameplay_verified=False,limitations=list(LIMITATIONS))
    return result, report
