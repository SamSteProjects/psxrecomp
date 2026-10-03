"""Small independent PNG/TIM fixtures for bounded pixel interchange."""
from copy import deepcopy
import math
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer import texture_png
from importer.texture_png import decode_png, export_texture_png, import_texture_png
from importer.textures import decode_tim, parse_tim


SIG = b'\x89PNG\r\n\x1a\n'


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def png(width, height, rows, *, color=6, depth=8, filters=None, metadata=(), compressed=None, after=()):
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    distance = max(1, (channels * depth + 7) // 8)
    previous = bytes(len(rows[0]))
    raw = bytearray()
    for y, row in enumerate(rows):
        filter_type = (filters or [0] * height)[y]
        raw.append(filter_type)
        for i, value in enumerate(row):
            left = row[i - distance] if i >= distance else 0
            above = previous[i]
            diagonal = previous[i - distance] if i >= distance else 0
            estimate = left + above - diagonal
            candidates = (left, above, diagonal)
            errors = [abs(estimate - candidate) for candidate in candidates]
            paeth = candidates[errors.index(min(errors))]
            predictor = [0, left, above, (left + above) // 2, paeth][filter_type] if filter_type <= 4 else 0
            raw.append((value - predictor) & 255)
        previous = row
    header = struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, 0)
    return (SIG + chunk(b'IHDR', header) + b''.join(chunk(*item) for item in metadata) +
            chunk(b'IDAT', zlib.compress(raw) if compressed is None else compressed) +
            b''.join(chunk(*item) for item in after) + chunk(b'IEND', b''))


def rgba_png(width, height, pixels):
    return png(width, height, [pixels[y * width * 4:(y + 1) * width * 4] for y in range(height)])


def tim(bpp, *, width=8, height=1, indices=None, words=None, palettes=None):
    flags = {4: 8, 8: 9, 16: 2, 24: 3}[bpp]
    content = bytearray(struct.pack('<II', 16, flags))
    if bpp in (4, 8):
        capacity = 1 << bpp
        default = [0, 0x8000, 0x001f, 0x001f, 0x03e0, 0x801f] + [0] * (capacity - 6)
        palettes = palettes or [default, list(default)]
        payload = b''.join(struct.pack(f'<{capacity}H', *row) for row in palettes)
        content.extend(struct.pack('<I4H', len(payload) + 12, 0, 240, capacity, len(palettes)))
        content.extend(payload)
        indices = indices if indices is not None else [2, 3, 4, 5, 2, 3, 0, 1] * (width * height // 8)
        image = bytearray(width * height * bpp // 8)
        for i, value in enumerate(indices):
            image[i * bpp // 8] |= value << (i * bpp % 8)
    elif bpp == 16:
        words = words or ([0, 0x8000, 31, 0x801f, 0x03e0, 0x83e0, 0x7c00, 0xffff] * (width * height // 8))
        image = struct.pack(f'<{len(words)}H', *words)
    else:
        image = bytes((i * 37 + 17) % 256 for i in range(width * height * 3))
    width_words = width * bpp // 16
    content.extend(struct.pack('<I4H', len(image) + 12, 4, 8, width_words, height))
    content.extend(image)
    return bytes(content)


def replace_pixel(content, pixel, rgba):
    decoded = decode_png(content)
    pixels = bytearray(decoded['rgba'])
    pixels[pixel * 4:pixel * 4 + 4] = rgba
    return rgba_png(decoded['width'], decoded['height'], bytes(pixels))


def plane(width, height, values):
    return rgba_png(width, height, bytes(channel for value in values
                                       for channel in (value * 255, value * 255, value * 255, 255)))


class TexturePngTests(unittest.TestCase):
    def test_all_tim_modes_exact_noop_duplicate_indices_and_stp(self):
        for bpp in (4, 8, 16, 24):
            source = tim(bpp)
            for palette_index in ([0, 1] if bpp < 16 else [0]):
                exported, stp, profile = export_texture_png(source, palette_index)
                self.assertEqual(set(profile), texture_png.PROFILE_KEYS)
                self.assertEqual(decode_png(exported)['rgba'], decode_tim(source, palette_index)['rgba'])
                for mode in (['existing', 'rebuild'] if bpp < 16 else ['existing']):
                    for mask in (None, stp):
                        with self.subTest(bpp=bpp, palette=palette_index, mode=mode, mask=mask is not None):
                            candidate, analysis = import_texture_png(source, exported, profile, mode, mask)
                            self.assertEqual(candidate, source)
                            q = analysis['quantization']
                            self.assertEqual(q['quantized_pixel_count'], 0)
                            self.assertEqual(q['color_max_error'], 0)
                            self.assertEqual(q['color_rms_error'], 0)
                            self.assertEqual(q['stp_changed_pixels'], 0)
                            self.assertEqual(q['forced_black_stp_pixels'], 0)
                            self.assertEqual(q['forced_transparent_stp_pixels'], 0)
                            self.assertEqual(analysis['changes']['total_change_count'], 0)

    def test_existing_pixel_ties_and_selected_row_rebuild_exact_byte_mask(self):
        source = tim(4)
        exported, _, profile = export_texture_png(source, 1)
        image_at = len(source) - len(parse_tim(source).image.data)
        edited = replace_pixel(exported, 0, bytes([0, 255, 0, 255]))
        candidate, analysis = import_texture_png(source, edited, profile)
        expected = bytearray(source)
        expected[image_at] = (expected[image_at] & 0xf0) | 4
        self.assertEqual(candidate, bytes(expected))
        self.assertEqual(analysis['changes']['palette_words_changed'], 0)
        self.assertEqual(analysis['changes']['pixel_indices_changed'], 1)
        # Unedited red duplicate index3 is retained, rather than canonicalized2.
        self.assertEqual(candidate[image_at] >> 4, 3)
        blue = replace_pixel(exported, 0, bytes([0, 0, 255, 255]))
        candidate, analysis = import_texture_png(source, blue, profile, 'rebuild')
        expected = bytearray(source)
        expected[image_at] = (expected[image_at] & 0xf0) | 15
        struct.pack_into('<H', expected, 20 + 32 + 15 * 2, 0x7c00)
        self.assertEqual(candidate, bytes(expected))
        self.assertEqual(candidate[20:52], source[20:52])
        self.assertEqual(analysis['changes']['palette_words_changed'], 1)
        self.assertEqual(analysis['changes']['pixel_indices_changed'], 1)
        self.assertEqual(analysis['quantization']['quantized_pixel_count'], 0)
        self.assertEqual(import_texture_png(source, blue, profile, 'rebuild')[0], candidate)

    def test_existing_raw_rgb_distance_original_index_ties_and_nearblack_class(self):
        palette = [0, 0x8000, 1, 2, 2, 3] + [0] * 10
        source = tim(4, indices=[3, 4, 5, 2, 3, 4, 0, 1], palettes=[palette])
        exported, _, profile = export_texture_png(source)
        # RGB12 is equally distant from expanded8 and16; original index4 wins.
        edited = replace_pixel(exported, 1, bytes([12, 0, 0, 255]))
        candidate, analysis = import_texture_png(source, edited, profile)
        self.assertEqual(candidate, source)
        self.assertEqual(analysis['quantization']['quantized_pixel_count'], 1)
        self.assertEqual(analysis['quantization']['color_max_error'], 4)
        # RGB5 rounds to8, but raw-distance16 tie behavior must retain index4.
        # A different original index5 must choose lowest tied index2 at RGB12.
        edited = replace_pixel(exported, 2, bytes([12, 0, 0, 255]))
        candidate, _ = import_texture_png(source, edited, profile)
        self.assertEqual((candidate[-3] & 15), 2)
        nearblack = replace_pixel(exported, 3, bytes([1, 0, 0, 255]))
        candidate, analysis = import_texture_png(source, nearblack, profile)
        self.assertEqual(decode_tim(candidate)['rgba'][12:16], bytes([8, 0, 0, 255]))
        self.assertEqual(analysis['quantization']['forced_black_stp_pixels'], 0)
        self.assertEqual(analysis['quantization']['stp_changed_pixels'], 0)

    def test_direct_quantization_alpha_and_explicit_stp_rules(self):
        source = tim(16)
        exported, _, profile = export_texture_png(source)
        changed = replace_pixel(exported, 0, bytes([0, 0, 0, 255]))
        candidate, analysis = import_texture_png(source, changed, profile)
        self.assertEqual(struct.unpack_from('<H', candidate, 20)[0], 0x8000)
        self.assertEqual(analysis['quantization']['forced_black_stp_pixels'], 1)
        self.assertEqual(analysis['quantization']['stp_changed_pixels'], 1)
        mask = plane(8, 1, list(decode_tim(source)['stp']))
        with self.assertRaisesRegex(ImportError, 'black.*STP0'):
            import_texture_png(source, changed, profile, stp_content=mask)
        transparent = replace_pixel(exported, 1, bytes([123, 99, 44, 0]))
        candidate, analysis = import_texture_png(source, transparent, profile)
        self.assertEqual(struct.unpack_from('<H', candidate, 22)[0], 0)
        self.assertEqual(analysis['quantization']['forced_transparent_stp_pixels'], 1)
        self.assertEqual(analysis['quantization']['color_max_error'], 0)
        with self.assertRaisesRegex(ImportError, 'Transparent.*STP1'):
            import_texture_png(source, transparent, profile, stp_content=mask)
        gray = replace_pixel(exported, 2, bytes([12, 12, 12, 255]))
        candidate, analysis = import_texture_png(source, gray, profile)
        self.assertEqual(struct.unpack_from('<H', candidate, 24)[0], 1 | 1 << 5 | 1 << 10)
        self.assertEqual(analysis['quantization']['color_max_error'], 4)
        self.assertAlmostEqual(analysis['quantization']['color_rms_error'], math.sqrt(48 / (3 * 7)))
        partial = replace_pixel(exported, 0, bytes([0, 0, 0, 128]))
        with self.assertRaisesRegex(ImportError, 'partial opacity'):
            import_texture_png(source, partial, profile)
        invalid = replace_pixel(mask, 0, bytes([1, 1, 1, 255]))
        with self.assertRaisesRegex(ImportError, 'black and white'):
            import_texture_png(source, exported, profile, stp_content=invalid)
        source24 = tim(24)
        image24, _, profile24 = export_texture_png(source24)
        for edit, mode, stp in [(replace_pixel(image24, 0, bytes([1, 2, 3, 0])), 'existing', None),
                                (image24, 'rebuild', None), (image24, 'existing', plane(8, 1, [1] * 8))]:
            with self.assertRaises(ImportError):
                import_texture_png(source24, edit, profile24, mode, stp)

    def test_weighted_rebuild_capacity_determinism_alpha_stp_classes(self):
        for bpp, width in ((4, 40), (8, 304)):
            source = tim(bpp, width=width, indices=[0] * width)
            _, _, profile = export_texture_png(source)
            pixels, requested_words, bits = bytearray(), {0}, [0]
            pixels.extend((99, 77, 55, 0))
            for i in range(1, width):
                r, g, b = i % 32, (i // 32) % 32, (i // 1024) % 32
                stp = i % 2
                bits.append(stp)
                pixels.extend(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2), 255))
                requested_words.add(r | g << 5 | b << 10 | stp << 15)
            edited = rgba_png(width, 1, bytes(pixels))
            mask = plane(width, 1, bits)
            candidate, analysis = import_texture_png(source, edited, profile, 'rebuild', mask)
            self.assertEqual(import_texture_png(source, edited, profile, 'rebuild', mask)[0], candidate)
            self.assertEqual(parse_tim(candidate).clut.data[(1 << bpp) * 2:], parse_tim(source).clut.data[(1 << bpp) * 2:])
            decoded = decode_tim(candidate)
            self.assertEqual(decoded['stp'], bytes(bits))
            self.assertEqual(decoded['rgba'][3], 0)
            self.assertTrue(all(decoded['rgba'][i * 4 + 3] == 255 for i in range(1, width)))
            selected = set(struct.unpack_from(f'<{1 << bpp}H', parse_tim(candidate).clut.data))
            self.assertTrue(selected <= requested_words)
            self.assertEqual(len(selected), 1 << bpp)
            self.assertGreater(analysis['quantization']['quantized_pixel_count'], 0)
            self.assertEqual(analysis['quantization']['distinct_requested_words'], len(requested_words))
            self.assertLessEqual(analysis['quantization']['color_max_error'], 255)
            self.assertEqual(analysis['quantization']['stp_changed_pixels'], sum(bits))

    def test_png_filters_rgb_gray_alpha_indexed_depths_and_metadata(self):
        rows = [bytes((i * 23 + y * 17) % 256 for i in range(12)) for y in range(5)]
        encoded = png(3, 5, rows, filters=[0, 1, 2, 3, 4], metadata=[
            (b'sRGB', b'\0'), (b'gAMA', struct.pack('>I', 45455)),
            (b'cHRM', struct.pack('>8I', *texture_png.SRGB_CHROMATICITIES)),
            (b'zTXt', b'Ignored\0\0not-a-zlib-stream')])
        self.assertEqual(decode_png(encoded), dict(width=3, height=5, rgba=b''.join(rows)))
        rgb = png(2, 1, [bytes([1, 2, 3, 4, 5, 6])], color=2,
                  metadata=[(b'tRNS', struct.pack('>3H', 1, 2, 3))])
        self.assertEqual(decode_png(rgb)['rgba'], bytes([1, 2, 3, 0, 4, 5, 6, 255]))
        gray = png(2, 1, [bytes([4, 8])], color=0, metadata=[(b'tRNS', struct.pack('>H', 4))])
        self.assertEqual(decode_png(gray)['rgba'], bytes([4, 4, 4, 0, 8, 8, 8, 255]))
        self.assertEqual(decode_png(png(2, 1, [bytes([9, 0, 7, 255])], color=4))['rgba'],
                         bytes([9, 9, 9, 0, 7, 7, 7, 255]))
        for depth in (1, 2, 4, 8):
            capacity, width = 1 << depth, 5
            samples = [i % capacity for i in range(width)]
            packed = bytearray((width * depth + 7) // 8)
            for i, value in enumerate(samples):
                packed[i * depth // 8] |= value << (8 - depth - i * depth % 8)
            palette = bytes(channel for i in range(capacity) for channel in (i, 255 - i, (i * 3) % 256))
            indexed = png(width, 1, [packed], color=3, depth=depth,
                          metadata=[(b'PLTE', palette), (b'tRNS', bytes([0, 128]))])
            expected = bytes(channel for i in samples for channel in
                             (i, 255 - i, (i * 3) % 256, 0 if i == 0 else 128 if i == 1 else 255))
            self.assertEqual(decode_png(indexed)['rgba'], expected)

    def test_png_malformed_order_crc_zlib_color_and_budget_rejection(self):
        valid = png(1, 1, [bytes([1, 2, 3, 255])])
        bad_crc = bytearray(valid)
        bad_crc[-1] ^= 1
        malformed = [bytes(bad_crc), valid[:-1], valid + b'extra',
            SIG + chunk(b'IHDR', b'bad') + chunk(b'IEND', b''),
            png(1, 1, [bytes([1, 2, 3, 255])], after=[(b'IDAT', zlib.compress(b'extra'))]),
            png(1, 1, [bytes([1, 2, 3, 255])], compressed=zlib.compress(b'\0\1\2\3\xffextra')),
            png(1, 1, [bytes([1, 2, 3, 255])], compressed=zlib.compress(b'\0\1\2\3\xff') + zlib.compress(b'extra')),
            png(1, 1, [bytes([1, 2, 3, 255])], compressed=zlib.compress(b'\0\1\2\3\xff')[:-2]),
            png(1, 1, [bytes([1, 2, 3, 255])], filters=[5]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))]),
            png(1, 1, [b'\0'], color=3),
            png(1, 1, [b'\1'], color=3, metadata=[(b'PLTE', b'\0\0\0')]),
            png(1, 1, [b'\0'], color=3, metadata=[(b'PLTE', b'\0\0\0'), (b'tRNS', b'')]),
            png(1, 1, [b'\0'], color=0, metadata=[(b'tRNS', struct.pack('>H', 256))]),
            png(1, 1, [b'\0\0\0'], color=2, metadata=[(b'tRNS', struct.pack('>3H', 256, 0, 0))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'gAMA', struct.pack('>I', 100000))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'cHRM', bytes(32))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'iCCP', b'profile')]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'cICP', bytes(4))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'acTL', bytes(8))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'tIME', b'bad')]),
            png(1, 1, [bytes([1, 2, 3])], color=2,
                metadata=[(b'bKGD', bytes(6)), (b'PLTE', bytes(3))]),
            png(1, 1, [bytes([1, 2, 3, 255])], metadata=[(b'ABCD', b'')])]
        header = struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)
        stream = zlib.compress(b'\0\1\2\3\xff')
        malformed.append(SIG + chunk(b'IHDR', header) + chunk(b'IDAT', stream[:3]) +
                         chunk(b'tEXt', b'key\0value') + chunk(b'IDAT', stream[3:]) + chunk(b'IEND', b''))
        for i, content in enumerate(malformed):
            with self.subTest(case=i), self.assertRaises(ImportError):
                decode_png(content)
        for depth, interlace in ((16, 0), (8, 1)):
            content = SIG + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, depth, 6, 0, 0, interlace))
            content += chunk(b'IDAT', stream) + chunk(b'IEND', b'')
            with self.assertRaises(ImportError):
                decode_png(content)
        for constant in ('MAX_PNG_BYTES', 'MAX_PIXELS'):
            with patch.object(texture_png, constant, 0), self.assertRaises(ImportError):
                decode_png(valid)
        for content in (None, bytearray(valid), 'png'):
            with self.assertRaises(ImportError):
                decode_png(content)

    def test_profile_modes_source_masks_and_missing_palette_class_reject(self):
        source = tim(4)
        image, mask, profile = export_texture_png(source)
        for value in ({**profile, 'extra': 0}, {**profile, 'width': 4}, {**profile, 'bpp': True}, {}):
            with self.subTest(profile=value), self.assertRaises(ImportError):
                import_texture_png(source, image, value)
        for palette in (True, -1, 2, '0'):
            with self.subTest(palette=palette), self.assertRaises(ImportError):
                export_texture_png(source, palette)
        for invalid in (source + b'extra', bytearray(source), source[:-1]):
            with self.assertRaises(ImportError):
                export_texture_png(invalid)
        for constant in ('MAX_TIM_BYTES', 'MAX_PIXELS'):
            with patch.object(texture_png, constant, 0), self.assertRaises(ImportError):
                export_texture_png(source)
        for mode in ('unknown', None, True):
            with self.assertRaises(ImportError):
                import_texture_png(source, image, profile, mode)
        with self.assertRaisesRegex(ImportError, 'dimensions'):
            import_texture_png(source, rgba_png(1, 1, bytes([0, 0, 0, 255])), profile)
        with self.assertRaisesRegex(ImportError, 'dimensions'):
            import_texture_png(source, image, profile, stp_content=plane(1, 1, [0]))
        no_stp = tim(4, indices=[2] * 8, palettes=[[0, 0, 31] + [0] * 13])
        no_stp_png, _, no_stp_profile = export_texture_png(no_stp)
        opaque_black = replace_pixel(no_stp_png, 0, bytes([0, 0, 0, 255]))
        with self.assertRaisesRegex(ImportError, 'compatible'):
            import_texture_png(no_stp, opaque_black, no_stp_profile)
        rebuilt, _ = import_texture_png(no_stp, opaque_black, no_stp_profile, 'rebuild')
        self.assertEqual(decode_tim(rebuilt)['rgba'][:4], bytes([0, 0, 0, 255]))
        self.assertEqual(decode_tim(rebuilt)['stp'][0], 1)


if __name__ == '__main__':
    unittest.main()
