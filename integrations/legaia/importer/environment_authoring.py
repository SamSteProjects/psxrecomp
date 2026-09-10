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


def patch_environment_instances(original: bytes, expected_sha256: str,
                                edits: list[dict]) -> tuple[bytes, list[dict]]:
    """Split static decoration descriptors for cell-local transform edits.

    Allocation uses only zero-filled descriptors with no grid references.
    Spawnable objects and reserved descriptor identities are not supported:
    their script/runtime identity consumers need separate validation.
    """
    # Reuse source and transform validation before interpreting any locators.
    patch_environment_transforms(original, expected_sha256, [])
    if not isinstance(edits, list) or len(edits) > 512:
        raise ImportError("Instance edits must be a bounded cell list")
    normalized, seen = [], set()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) - {'cell_index', 'offset', 'rotation_psx'}:
            raise ImportError("Unknown environment instance field")
        cell = edit.get('cell_index')
        if type(cell) is not int or not 0 <= cell < 16384 or cell in seen:
            raise ImportError("Environment cell index is invalid or duplicated")
        seen.add(cell)
        word = struct.unpack_from('<H', original, 0x8000 + cell * 2)[0]
        record = word & 511
        flags = struct.unpack_from('<H', original, record * 32 + 0x12)[0]
        if record < 4 or not word & 0x2000 or flags & 4:
            raise ImportError("Instance authoring currently supports static decorations only")
        transform = {k: v for k, v in edit.items() if k != 'cell_index'}
        patched, changes = patch_environment_transforms(original, expected_sha256,
            [{'record_index': record, **transform}])
        if changes:
            normalized.append((cell, record, word, patched[record*32:(record+1)*32], changes))
    referenced = {word[0] & 511 for word in struct.iter_unpack('<H', original[0x8000:0x10000])}
    free = [record for record in range(4, 512)
            if record not in referenced and original[record*32:(record+1)*32] == bytes(32)]
    if len(normalized) > len(free):
        raise ImportError("No unused zero-filled MAP descriptors remain for instance edits")
    result, audit = bytearray(original), []
    for target, (cell, record, word, descriptor, changes) in zip(free, sorted(normalized)):
        result[target*32:(target+1)*32] = descriptor
        grid_offset = 0x8000 + cell * 2
        replacement = (word & ~511) | target
        struct.pack_into('<H', result, grid_offset, replacement)
        audit.append({'cell_index': cell, 'source_record_index': record,
                      'allocated_record_index': target,
                      'descriptor_byte_offset': target*32, 'descriptor_byte_length': 32,
                      'grid_byte_offset': grid_offset, 'grid_byte_length': 2,
                      'before_grid_word': word, 'after_grid_word': replacement,
                      'transform_changes': [{k:v for k,v in change.items()
                                             if k not in ('affected_grid_cells', 'byte_offset')}
                                            for change in changes]})
    return bytes(result), audit


def patch_environment_overrides(original: bytes, binding: dict) -> tuple[bytes, list[dict]]:
    """Apply shared edits first, then cell-local overrides against that baseline."""
    shared, audit = patch_environment_transforms(original, binding['source_sha256'], binding.get('edits', []))
    changed, instances = patch_environment_instances(shared, sha256(shared).hexdigest(), binding.get('instances', []))
    for instance in instances:
        for change in instance['transform_changes']:
            audit.append({**change, 'scope':'instance-MAP-transform-only',
                          'affected_grid_cells':[instance['cell_index']],
                          'allocation':{k:v for k,v in instance.items() if k != 'transform_changes'}})
    return changed, audit
