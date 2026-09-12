"""Source-preserving X/Z edits for decoded MOVE_TO and NPC_RUN instructions.

Evidence: pinned engine-vm/field/step.rs, helpers.rs::grid_to_world and
step/menu_ctrl/nibble_5_6_7.rs. This serializer does not execute the script,
resolve its dispatch actor, change Y, or establish gameplay acceptance.
"""
from copy import deepcopy
import hashlib
import re

from .core import ImportError
from .dialogue_authoring import load_dialogue_authoring_context
from .script_inspection import inspect_record
from .serialization import encode_placement_coordinate

MAX_MOVEMENT_EDITS = 1024
LIMITATIONS = [
    "Only reached MOVE_TO and NPC_RUN X/Z operands are editable; unknown or conflicting path stops reject authoring.",
    "X/Z must be exactly representable on the source grid: multiples of 64 from 64 through 16384.",
    "Instruction widths, branch targets, extended actor contexts, NPC_RUN depth and move IDs remain unchanged.",
    "Y and runtime actor identity are unresolved; decoded paths do not establish branch execution or current positions.",
    "Changing both low-seven-bit coordinates to 127 selects NPC_RUN's parked target convention.",
    "Playable packaging must separately validate the composed MAN, compressed capacity and runtime behavior.",
]


def validate_movement_values(values):
    if not isinstance(values, dict) or not values or set(values) - {'x', 'z'}:
        raise ImportError('Movement edits require X and/or Z; other operands are unsupported')
    return {axis: encode_placement_coordinate(value, f'movement.{axis}') for axis, value in values.items()}


def _coordinate_offset(node):
    return node['pc'] + (2 if node['target_context'] is not None else 1) + (1 if node['mnemonic'] == 'NPC_RUN' else 0)


def _target(record, entry, pc):
    if type(pc) is not int or pc < 0:
        raise ImportError('Movement PC must be a nonnegative integer record offset')
    report = inspect_record(record, entry)
    if report['stops']:
        raise ImportError('Movement edits require no unknown or conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] not in ('MOVE_TO', 'NPC_RUN'):
        raise ImportError('Movement PC must identify a decoded MOVE_TO or NPC_RUN instruction')
    return node, _coordinate_offset(node)


def patch_movement_target(record, script_offset, pc, values, *, base_offset=0):
    """Return an equal-length record and exact byte audit without mutating input."""
    encoded = validate_movement_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('Movement base offset must be a nonnegative integer')
    node, start = _target(record, script_offset, pc)
    changed, audit = bytearray(record), []
    digest = hashlib.sha256(record).hexdigest()
    for index, axis in enumerate(('x', 'z')):
        offset = start + index
        if axis not in encoded or encoded[axis] == record[offset]:
            continue
        changed[offset] = encoded[axis]
        audit.append({'field': axis, 'pc': pc, 'mnemonic': node['mnemonic'],
                      'target_context': node['target_context'],
                      'record_relative_byte_offset': offset,
                      'decoded_byte_offset': base_offset + offset,
                      'before_byte': record[offset], 'after_byte': encoded[axis],
                      'before_coordinate': node['operands']['target_position'][axis],
                      'after_coordinate': values[axis], 'source_record_sha256': digest})
    return bytes(changed), audit


class MovementAuthoringContext:
    """Verified immutable MAN source; source owner IDs never denote live actors."""

    def __init__(self, source):
        self._source = source
        self._man = source._man

    def provenance(self):
        result = self._source.provenance()
        result['limitations'] = list(LIMITATIONS)
        return result

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        digest = hashlib.sha256(record).hexdigest()
        targets = []
        reason = 'Movement edits require no unknown or conflicting source-path stops' if report['stops'] else None
        if reason is None:
            for node in report['instructions']:
                if node['mnemonic'] not in ('MOVE_TO', 'NPC_RUN'):
                    continue
                pc = node['pc']
                start = _coordinate_offset(node)
                args = node['operands']
                targets.append({'semantic_id': f"script://{owner.removeprefix('scene://')}/movement/{pc:04x}",
                                'owner_id': owner, 'pc': pc, 'mnemonic': node['mnemonic'],
                                'target_context': node['target_context'],
                                'values': {axis: args['target_position'][axis] for axis in ('x', 'z')},
                                'encoded_xz': list(record[start:start + 2]),
                                'parked_target': args.get('parked_target'),
                                'decoded_byte_offset': offset + start,
                                'source_record_sha256': digest})
            if not targets:
                reason = 'No supported movement targets occur on the inspected paths'
        return {'supported': bool(targets), 'reason': reason, 'targets': targets,
                'source': self.provenance(), 'limitations': list(LIMITATIONS)}

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('Movement MAN source differs from the verified baseline')
        if not isinstance(edits, dict) or len(edits) > MAX_MOVEMENT_EDITS:
            raise ImportError('Movement edit set exceeds the bounded edit count')
        changes, occupied = [], set()
        digest = hashlib.sha256(self._man).hexdigest()
        for identifier, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/movement/([0-9a-f]{4})', identifier) if isinstance(identifier, str) else None
            if match is None:
                raise ImportError('Movement identity requires a source owner and fixed hexadecimal PC')
            owner, pc = 'scene://' + match[1], int(match[2], 16)
            offset, record, entry = self._source.verified_record(owner)
            _, audit = patch_movement_target(record, entry, pc, values, base_offset=offset)
            for change in audit:
                if change['decoded_byte_offset'] in occupied:
                    raise ImportError('Movement edits overlap another authored span')
                occupied.add(change['decoded_byte_offset'])
                changes.append(dict(change, movement_id=identifier, owner_id=owner,
                                    source_decoded_man_sha256=digest))
        changes.sort(key=lambda item: item['decoded_byte_offset'])
        result = bytearray(self._man)
        for change in changes:
            result[change['decoded_byte_offset']] = change['after_byte']
        return bytes(result), deepcopy(changes)


def load_movement_authoring_context(disc, scene):
    return MovementAuthoringContext(load_dialogue_authoring_context(disc, scene))
