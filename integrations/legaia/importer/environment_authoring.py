"""Exact transform writes to shared field MAP descriptors.

Descriptor layout follows environment.py. These are shared-record edits,
not allocation or per-instance overrides; collision/anchor fields are retained.
"""
from hashlib import sha256
import struct

from .core import ImportError


def patch_environment_transforms(original: bytes, expected_sha256: str,
                                 edits: list[dict]) -> tuple[bytes, list[dict]]:
    if not isinstance(original, bytes) or len(original) != 0x12000:
        raise ImportError("Environment authoring requires a complete field MAP")
    if sha256(original).hexdigest() != expected_sha256:
        raise ImportError("Environment source hash does not match")
    if not isinstance(edits, list) or len(edits) > 512:
        raise ImportError("Environment edits must be a bounded record list")
    normalized, seen = [], set()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) - {'record_index', 'offset', 'rotation_psx'}:
            raise ImportError("Unknown environment transform field")
        record = edit.get('record_index')
        if type(record) is not int or not 0 <= record < 512 or record in seen:
            raise ImportError("Environment record index is invalid or duplicated")
        seen.add(record)
        if not ({'offset', 'rotation_psx'} & set(edit)):
            raise ImportError("Environment edit requires transform axes")
        for field in ('offset', 'rotation_psx'):
            if field not in edit:
                continue
            axes = edit[field]
            if not isinstance(axes, dict) or not axes or set(axes) - set('xyz'):
                raise ImportError("Environment transform requires nonempty X/Y/Z axes")
            for axis, value in axes.items():
                low, high = (-32768, 32767) if field == 'offset' else (0, 4095)
                if type(value) is not int or not low <= value <= high:
                    raise ImportError("Environment transform axis exceeds exact encoded range")
                normalized.append((record, field, axis, value))
    references = {}
    for index, (word,) in enumerate(struct.iter_unpack('<H', original[0x8000:0x10000])):
        references.setdefault(word & 511, []).append(index)
    result, audit = bytearray(original), []
    for record, field, axis, value in sorted(normalized):
        if record not in references:
            raise ImportError("Environment record has no source grid references")
        offset = record * 32 + (0 if field == 'offset' else 8) + 'xyz'.index(axis) * 2
        fmt = '<h' if field == 'offset' else '<H'
        before = struct.unpack_from(fmt, original, offset)[0]
        if before == value:
            continue
        struct.pack_into(fmt, result, offset, value)
        audit.append({'record_index': record, 'field': f'{field}.{axis}',
                      'byte_offset': offset, 'byte_length': 2,
                      'before_value': before, 'after_value': value,
                      'affected_grid_cells': references[record].copy()})
    return bytes(result), audit
