"""Source-preserving X/Z and move-selector edits for decoded field movement instructions.

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
    "Only reached MOVE_TO/NPC_RUN X/Z and NPC_RUN/EXEC_MOVE encoded move selectors are editable; unknown or conflicting path stops reject authoring.",
    "X/Z must be exactly representable on the source grid: multiples of 64 from 64 through 16384.",
    "Instruction widths, branch targets, extended actor contexts, NPC_RUN depth remain unchanged; move-selector meanings remain unresolved.",
    "Y and runtime actor identity are unresolved; decoded paths do not establish branch execution or current positions.",
    "Changing both low-seven-bit coordinates to 127 selects NPC_RUN's parked target convention.",
    "Playable packaging must separately validate the composed MAN, compressed capacity and runtime behavior.",
]


def validate_movement_values(values):
    if not isinstance(values, dict) or not values or set(values) - {'x', 'z', 'move_id'}:
        raise ImportError('Movement edits require X/Z or an encoded move selector')
    encoded = {}
    for axis, value in values.items():
        if axis == 'move_id':
            if type(value) is not int or not 0 <= value <= 255:
                raise ImportError('Move selector requires an integer byte from 0 to 255')
            encoded[axis] = value
        else:
            encoded[axis] = encode_placement_coordinate(value, f'movement.{axis}')
    return encoded


def _coordinate_offset(node):
    return node['pc'] + (2 if node['target_context'] is not None else 1) + (1 if node['mnemonic'] == 'NPC_RUN' else 0)


def movement_operand_offsets(node):
    if node['mnemonic'] == 'EXEC_MOVE':
        return {'move_id': 0}
    if node['mnemonic'] == 'NPC_RUN':
        return {'x': 0, 'z': 1, 'move_id': 3}
    return {'x': 0, 'z': 1}


def _target(record, entry, pc):
    if type(pc) is not int or pc < 0:
        raise ImportError('Movement PC must be a nonnegative integer record offset')
    report = inspect_record(record, entry)
    if report['stops']:
        raise ImportError('Movement edits require no unknown or conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] not in ('MOVE_TO', 'NPC_RUN', 'EXEC_MOVE'):
        raise ImportError('Movement PC must identify a decoded MOVE_TO, NPC_RUN or EXEC_MOVE instruction')
    return node, _coordinate_offset(node)


def patch_movement_target(record, script_offset, pc, values, *, base_offset=0):
    """Return an equal-length record and exact byte audit without mutating input."""
    encoded = validate_movement_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('Movement base offset must be a nonnegative integer')
    node, start = _target(record, script_offset, pc)
    changed, audit = bytearray(record), []
    digest = hashlib.sha256(record).hexdigest()
    offsets = movement_operand_offsets(node)
    if set(encoded) - set(offsets):
        raise ImportError('Requested operand is unsupported for this movement instruction')
    for axis, relative in offsets.items():
        offset = start + relative
        if axis not in encoded or encoded[axis] == record[offset]:
            continue
        changed[offset] = encoded[axis]
        audit.append({'field': axis, 'pc': pc, 'mnemonic': node['mnemonic'],
                      'target_context': node['target_context'],
                      'record_relative_byte_offset': offset,
                      'decoded_byte_offset': base_offset + offset,
                      'before_byte': record[offset], 'after_byte': encoded[axis],
                      'before_coordinate': node['operands']['move_id'] if axis == 'move_id' else node['operands']['target_position'][axis],
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
                if node['mnemonic'] not in ('MOVE_TO', 'NPC_RUN', 'EXEC_MOVE'):
                    continue
                pc = node['pc']
                start = _coordinate_offset(node)
                args = node['operands']
                targets.append({'semantic_id': f"script://{owner.removeprefix('scene://')}/movement/{pc:04x}",
                                'owner_id': owner, 'pc': pc, 'mnemonic': node['mnemonic'],
                                'target_context': node['target_context'],
                                'values': {axis: args['move_id'] if axis == 'move_id' else args['target_position'][axis] for axis in movement_operand_offsets(node)},
                                'operand_offsets': movement_operand_offsets(node),
                                'encoded_xz': list(record[start:start + 2]) if node['mnemonic'] != 'EXEC_MOVE' else [],
                                'parked_target': args.get('parked_target'),
                                'decoded_byte_offset': offset + start,
                                'source_record_sha256': digest})
            if not targets:
                reason = 'No supported movement targets occur on the inspected paths'
        return {'supported': bool(targets), 'reason': reason, 'targets': targets,
                'source': self.provenance(), 'limitations': list(LIMITATIONS)}

    def patch_appended(self, candidate, edits):
        """Locate original owners after append; preserve all unrelated candidate bytes."""
        from .man_layout import read_man_layout
        _, changes = self.patch(edits)
        layout = read_man_layout(candidate)
        records = {(row['partition'], row['record_index']): row for row in layout['records']}
        output, audit = bytearray(candidate), []
        digest = hashlib.sha256(candidate).hexdigest()
        for change in changes:
            owner = change['owner_id']
            _, original, entry = self._source.verified_record(owner)
            partition = 2 if '/scripts/man-p2/' in owner else 1
            record = records.get((partition, int(owner.rsplit('/', 1)[1])))
            if record is None or record['byte_length'] != len(original):
                raise ImportError('Appended movement record differs from verified source extent')
            start = record['byte_offset']
            if sum(row['byte_offset'] == start for row in layout['records']) != 1:
                raise ImportError('Appended movement record is aliased')
            node, coordinate_start = _target(candidate[start:start + len(original)], entry, change['pc'])
            relative = coordinate_start + movement_operand_offsets(node)[change['field']]
            if node['mnemonic'] != change['mnemonic'] or relative != change['record_relative_byte_offset']:
                raise ImportError('Appended movement instruction differs from source layout')
            offset = start + relative
            if candidate[offset] != change['before_byte']:
                raise ImportError('Appended movement preimage differs from source')
            output[offset] = change['after_byte']
            audit.append(dict(change, source_decoded_byte_offset=change['decoded_byte_offset'],
                              decoded_byte_offset=offset, appended_man_sha256=digest,
                              appended_target_context=node['target_context']))
        result = bytes(output)
        if read_man_layout(result) != layout:
            raise ImportError('Appended movement edit changed MAN layout')
        return result, audit

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
