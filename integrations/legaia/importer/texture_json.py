"""Source-bound indexed TIM interchange; no quantization or layout changes."""
from hashlib import sha256
import json
import struct
from .core import ImportError
from .textures import parse_tim
from .texture_authoring import _validate, inspect_tim_pixel_index

MAX_JSON_BYTES = 16 * 1024 * 1024
FIELDS = {'schema_version','source_sha256','bpp','width','height','palette_words','pixel_indices'}


def export_texture_json(source: bytes) -> bytes:
    _validate(source, source)
    inspect_tim_pixel_index(source, 0, 0)
    tim = parse_tim(source)
    mask = (1 << tim.bpp) - 1
    pixels = [(byte >> shift) & mask for byte in tim.image.data for shift in range(0, 8, tim.bpp)]
    document = {'schema_version':'legaia.indexed-texture.v1','source_sha256':sha256(source).hexdigest(),
                'bpp':tim.bpp,'width':tim.width,'height':tim.image.height,
                'palette_words':list(struct.unpack(f'<{len(tim.clut.data)//2}H',tim.clut.data)),
                'pixel_indices':[pixels[y*tim.width:(y+1)*tim.width] for y in range(tim.image.height)]}
    content = (json.dumps(document, separators=(',',':'), sort_keys=True)+'\n').encode()
    if len(content) > MAX_JSON_BYTES:
        raise ImportError('Texture JSON exceeds 16 MiB')
    return content


def import_texture_json(source: bytes, expected_sha256: str, content: bytes) -> bytes:
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_JSON_BYTES:
        raise ImportError('Texture JSON requires at most 16 MiB')
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    try:
        document = json.loads(content.decode('utf-8-sig'),object_pairs_hook=unique)
    except (UnicodeError,ValueError,RecursionError) as exc:
        raise ImportError('Texture requires unambiguous JSON') from exc
    if (not isinstance(document,dict) or set(document) != FIELDS or
            document['schema_version'] != 'legaia.indexed-texture.v1' or
            document['source_sha256'] != expected_sha256 or sha256(source).hexdigest() != expected_sha256):
        raise ImportError('Texture JSON schema or source binding differs')
    _validate(source, source)
    inspect_tim_pixel_index(source,0,0)
    tim = parse_tim(source)
    if any(type(document[key]) is not int or document[key] != value for key,value in
           (('bpp',tim.bpp),('width',tim.width),('height',tim.image.height))):
        raise ImportError('Texture JSON must preserve bit depth and dimensions')
    words = document['palette_words']
    if (not isinstance(words,list) or len(words)*2 != len(tim.clut.data) or
            any(type(word) is not int or not 0 <= word <= 65535 for word in words)):
        raise ImportError('Texture JSON must retain complete unsigned16 palette words')
    rows = document['pixel_indices']
    if (not isinstance(rows,list) or len(rows) != tim.image.height or
            any(not isinstance(row,list) or len(row) != tim.width or
                any(type(index) is not int or not 0 <= index < (1 << tim.bpp) for index in row) for row in rows)):
        raise ImportError('Texture JSON must retain complete ordered pixel-index rows')
    result = bytearray(source)
    struct.pack_into(f'<{len(words)}H',result,20,*words)
    pixels = [index for row in rows for index in row]
    image_start = 32 + len(tim.clut.data)
    per_byte = 8 // tim.bpp
    for offset in range(len(tim.image.data)):
        result[image_start+offset] = sum(pixels[offset*per_byte+i] << (i*tim.bpp) for i in range(per_byte))
    replacement = bytes(result)
    _validate(source,replacement)
    return replacement
