"""Source-facing nibble edits; no initial-heading or runtime-state inference.

Retail SCUS compass data and PROT[897]'s actual dispatch/write instructions
prove the simple CAM_CFG and NPC_RUN scalar operands. See
docs/legaia-script-facing.md for exact source hashes and guest callsites.
"""
from copy import deepcopy
from hashlib import sha256
import re

from .core import ImportError
from .dialogue_authoring import MAX_MAN_BYTES, load_dialogue_authoring_context
from .script_inspection import inspect_record

MAX_FACING_EDITS = 1024
PRESERVATION_MASK = 0xF0
LIMITATIONS = [
    'Only reached simple CAM_CFG and nonparked NPC_RUN facing operands with no unknown or conflicting source-path stops are editable.',
    'Sectors 0..7 select the verified retail eight-direction LUT; its upper eight addressable slots are not direction values.',
    'Only the low operand nibble changes; upper flags, coordinates, move selectors, dispatch contexts, instructions and branches remain unchanged.',
    'Source instruction ownership and extended targets do not establish runtime actor binding or which story branch executes.',
    'These source operands are not a general initial or live Transform heading; later script writes can replace facing.',
    'Build composition and compressed capacity require separate validation; gameplay and experimental NPC append acceptance remain unverified.',
]
_ID = re.compile(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/facing/([0-9a-f]{4})')


def validate_facing_values(values):
    if (not isinstance(values, dict) or set(values) != {'sector'} or
            type(values['sector']) is not int or not 0 <= values['sector'] <= 7):
        raise ImportError('Facing requires exactly one integer sector from 0 through 7')
    return values['sector']


def _target(record, entry, pc, *, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError('Facing PC must be a nonnegative source-record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('Facing authoring requires no unknown or conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] not in ('CAM_CFG', 'NPC_RUN'):
        raise ImportError('Facing PC must identify a reached CAM_CFG or NPC_RUN source instruction')
    operand = pc + (2 if node['target_context'] is not None else 1)
    if node['mnemonic'] == 'CAM_CFG':
        if record[operand + 1] & 0x7F:
            raise ImportError('CAM_CFG halt-acquire mode has no scalar facing operand')
        offset = operand
    else:
        if node['operands']['parked_target']:
            raise ImportError('NPC_RUN parked sentinel has no supported visible facing candidate')
        offset = operand + 3
    if record[offset] & 0x0F > 7:
        raise ImportError('Source facing selects a nondirection LUT slot; authoring is unsupported')
    return node, offset, report


def _shape(report):
    return [(row['pc'], row['mnemonic'], row['length'], row['target_context'], row['successors'])
            for row in report['instructions']]


def patch_facing_sector(record, entry, pc, values, *, base_offset=0):
    """Return an equal-length record and exact nibble audit from verified bytes."""
    sector = validate_facing_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('Facing base offset must be a nonnegative integer')
    node, offset, report = _target(record, entry, pc)
    before = record[offset]
    after = (before & PRESERVATION_MASK) | sector
    if before == after:
        return record, []
    changed = bytearray(record)
    changed[offset] = after
    changed = bytes(changed)
    check = inspect_record(changed, entry)
    if check['stops'] != report['stops'] or _shape(check) != _shape(report):
        raise ImportError('Facing edit changed decoded instruction layout or continuations')
    return changed, [dict(field='sector', pc=pc, mnemonic=node['mnemonic'],
                          target_context=node['target_context'], record_relative_byte_offset=offset,
                          decoded_byte_offset=base_offset + offset, before_byte=before, after_byte=after,
                          before_sector=before & 0x0F, after_sector=sector,
                          source_record_sha256=sha256(record).hexdigest())]


class FacingAuthoringContext:
    """Immutable MAN snapshot with the existing uniquely owned script spans."""
    def __init__(self, source):
        if not isinstance(source._man, bytes):
            raise ImportError('Facing source requires an immutable verified MAN payload')
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(deepcopy(self._source.provenance()), limitations=list(LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets, unavailable = [], []
        for node in report['instructions']:
            if node['mnemonic'] not in ('CAM_CFG', 'NPC_RUN'):
                continue
            try:
                _, relative, _ = _target(record, entry, node['pc'], report=report)
            except ImportError as error:
                unavailable.append(dict(pc=node['pc'], mnemonic=node['mnemonic'], reason=str(error)))
                continue
            before = record[relative]
            targets.append(dict(semantic_id='script://' + owner.removeprefix('scene://') +
                                f"/facing/{node['pc']:04x}", owner_id=owner, pc=node['pc'],
                                mnemonic=node['mnemonic'], target_context=node['target_context'],
                                decoded_byte_offset=offset + relative,
                                source_record_sha256=sha256(record).hexdigest(), values={'sector': before & 0x0F},
                                before_raw=before, preservation_mask=PRESERVATION_MASK))
        reason = ('Facing authoring requires no unknown or conflicting source-path stops' if report['stops'] else
                  'No supported source facing operands occur on the inspected paths' if not targets else None)
        return dict(supported=bool(targets), targets=deepcopy(targets), unavailable=deepcopy(unavailable),
                    reason=reason, source=self.provenance(), limitations=list(LIMITATIONS))

    def patch_appended(self, candidate, edits):
        """Rebase original owners after append, retaining donor and unrelated bytes."""
        from .man_layout import read_man_layout
        from .trigger_scripts import _p2_entry
        if not isinstance(candidate, bytes) or not 0x2B <= len(candidate) <= MAX_MAN_BYTES:
            raise ImportError('Appended facing MAN requires bounded immutable bytes')
        _, changes = self.patch(edits)
        layout = read_man_layout(candidate)
        if sum(layout['partition_counts']) > 8192:
            raise ImportError('Appended facing MAN exceeds the record budget')
        records = {}
        for row in layout['records']:
            key = row['partition'], row['record_index']
            if key in records:
                raise ImportError('Appended facing record identity is duplicated')
            records[key] = row
        resolved = {}
        # Include no-op requests in qualification; they must not conceal a
        # changed source entry, target instruction, or operand preimage.
        for identifier in edits:
            match = _ID.fullmatch(identifier)
            owner, pc = 'scene://' + match.group(1), int(match.group(2), 16)
            _, original, entry = self._source.verified_record(owner)
            partition = 2 if '/scripts/man-p2/' in owner else 1
            record = records.get((partition, int(owner.rsplit('/', 1)[1])))
            if record is None or record['byte_length'] != len(original):
                raise ImportError('Appended facing record differs from verified source extent')
            start = record['byte_offset']
            if sum(row['byte_offset'] == start for row in layout['records']) != 1:
                raise ImportError('Appended facing record is aliased')
            if any(start < section['byte_offset'] + section['byte_length'] and
                   section['byte_offset'] < start + len(original) for section in layout['sections']):
                raise ImportError('Appended facing record overlaps a MAN section')
            current = candidate[start:start + len(original)]
            current_entry = _p2_entry(current)[0] if partition == 2 else 1 + current[0] * 2 + 4
            # P1's final two entry-header bytes are independently authored
            # placement coordinates; they do not select script entry or context.
            prefix_end = entry if partition == 2 else entry - 2
            if current_entry != entry or current[:prefix_end] != original[:prefix_end]:
                raise ImportError('Appended facing source entry differs from verified source')
            source_node, relative, source_report = _target(original, entry, pc)
            node, offset, report = _target(current, entry, pc)
            if (offset != relative or _shape(report) != _shape(source_report) or
                    current[pc] != original[pc] or node['mnemonic'] != source_node['mnemonic'] or
                    node['target_context'] != source_node['target_context']):
                raise ImportError('Appended facing instruction differs from source layout')
            if current[offset] != original[relative]:
                raise ImportError('Appended facing operand preimage differs from source')
            resolved[identifier] = (start + offset, node['target_context'])
        output, audit = bytearray(candidate), []
        digest = sha256(candidate).hexdigest()
        for change in changes:
            offset, context = resolved[change['facing_id']]
            if (candidate[offset] != change['before_byte'] or
                    change['before_byte'] & PRESERVATION_MASK != change['after_byte'] & PRESERVATION_MASK):
                raise ImportError('Appended facing operand preimage or preserved flags differ')
            output[offset] = change['after_byte']
            audit.append(dict(change, source_decoded_byte_offset=change['decoded_byte_offset'],
                              decoded_byte_offset=offset, appended_man_sha256=digest,
                              appended_target_context=context))
        result = bytes(output)
        if read_man_layout(result) != layout:
            raise ImportError('Appended facing edit changed MAN layout')
        return result, deepcopy(audit)

    def patch(self, edits, *, original=None):
        if original is not None and (not isinstance(original, bytes) or original != self._man):
            raise ImportError('Facing MAN differs from the verified source')
        if not isinstance(edits, dict) or len(edits) > MAX_FACING_EDITS:
            raise ImportError('Facing edit collection exceeds its source-bound limit')
        audit, occupied = [], set()
        for identifier, values in sorted(edits.items(), key=lambda item: str(item[0])):
            match = _ID.fullmatch(identifier) if isinstance(identifier, str) else None
            if match is None:
                raise ImportError('Facing identity requires a source owner and four-digit hexadecimal PC')
            owner = 'scene://' + match.group(1)
            offset, record, entry = self._source.verified_record(owner)
            _, changes = patch_facing_sector(record, entry, int(match.group(2), 16), values, base_offset=offset)
            for change in changes:
                if change['decoded_byte_offset'] in occupied:
                    raise ImportError('Facing edits overlap another source operand')
                occupied.add(change['decoded_byte_offset'])
                audit.append(dict(change, facing_id=identifier, owner_id=owner,
                                  source_decoded_man_sha256=sha256(self._man).hexdigest()))
        audit.sort(key=lambda row: row['decoded_byte_offset'])
        result = bytearray(self._man)
        for change in audit:
            if result[change['decoded_byte_offset']] != change['before_byte']:
                raise ImportError('Facing source operand preimage differs from the verified MAN')
            result[change['decoded_byte_offset']] = change['after_byte']
        return bytes(result), deepcopy(audit)


def load_facing_authoring_context(disc, scene):
    return FacingAuthoringContext(load_dialogue_authoring_context(disc, scene))
