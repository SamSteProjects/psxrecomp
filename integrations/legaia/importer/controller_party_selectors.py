"""Source-qualified masked party selector serialization; runtime identity remains unresolved."""
from copy import deepcopy
from hashlib import sha256
import re
from .core import ImportError
from .controller_system_flags import ControllerRecordSource
from .script_inspection import inspect_record
from .man_layout import read_man_layout

LIMITATIONS = [
    'Only reached party-control selectors with no decoder stops are candidates.',
    'The runtime party identity and request effect remain unresolved.',
    'Dispatch context, operation nibble, bit3, continuation, dialogue and MAN pointers remain unchanged.',
    'Native serialization does not establish project/editor Build or gameplay support.',
]


def validate_party_selector_values(values):
    if (not isinstance(values, dict) or set(values) != {'party_selector'} or
            type(values['party_selector']) is not int or not 0 <= values['party_selector'] <= 7):
        raise ImportError('Party selector requires exactly one integer selector in0..7')
    return bytes([values['party_selector']])


def _values(raw):
    return dict(party_selector=raw[0] & 7)


def _target(record, entry, pc, mnemonic, sub_ops, label, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError(f'{label} request PC must be a nonnegative record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError(f'{label} authoring requires no unknown/conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] not in mnemonic:
        raise ImportError(f'{label} request PC must identify a reached source instruction')
    header = 1 if node['target_context'] is None else 2
    relative = pc + header
    byte_length = 1
    fields = ('party_selector',)
    # Verify the fixed-width preimage independently of decoded operand names.
    if (record[pc] != (0x4c if header == 1 else 0xcc) or
            record[pc+header] not in sub_ops or record[pc+header] != node['operands']['sub_op'] or header == 2 and record[pc+1] != node['target_context'] or node['length'] != header+byte_length or
            node['successors'] != [{'pc': pc+header+byte_length, 'condition': 'encoded_continuation'}]):
        raise ImportError(f'{label} request dispatch or continuation changed')
    values = {key: node['operands'][key] for key in fields}
    if bytes([record[relative] & 7]) != validate_party_selector_values(values):
        raise ImportError(f'{label} request operands differ from their source bytes')
    return node, relative, report


class ControllerPartySelectorAuthoringContext:
    MNEMONIC = ('PARTY_LEADER_REQUEST', 'PARTY_VIEW_SWAP_REQUEST')
    SUB_OPS = tuple(range(0x10)) + tuple(range(0x20, 0x30))
    IDENTITY_SEGMENT = 'party-selector'
    AUDIT_ID = 'party_selector_id'
    LABEL = 'Party selector'
    LIMITATIONS = LIMITATIONS
    def __init__(self, source):
        if not isinstance(source, ControllerRecordSource):
            raise ImportError(f'{self.LABEL} authoring requires a dedicated controller source')
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(self._source.provenance(), limitations=list(self.LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets = []
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] not in self.MNEMONIC:
                    continue
                _, relative, _ = _target(record, entry, node['pc'], self.MNEMONIC, self.SUB_OPS, self.LABEL, report)
                targets.append(dict(semantic_id=owner.replace('scene://', 'script://', 1)+f"/{self.IDENTITY_SEGMENT}/{node['pc']:04x}",
                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], sub_op=node['operands']['sub_op'],
                    target_context=node['target_context'], decoded_byte_offset=offset+relative,
                    selector_mask=7, preserved_bits=record[relative] & 0xF8,
                    values=deepcopy({key: node['operands'][key] for key in ('party_selector',)}),
                    source_record_sha256=sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, source=self.provenance(), inspection=deepcopy(report),
                    limitations=list(self.LIMITATIONS), reason=f'{self.LABEL} authoring requires no decoder stops' if report['stops'] else None)

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError(f'{self.LABEL} MAN differs from verified Retail source')
        if not isinstance(edits, dict) or len(edits) > 1024:
            raise ImportError(f'{self.LABEL} edit set exceeds bounds')
        result, audit, occupied, records = bytearray(self._man), [], set(), {}
        for identity, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/controllers/man-p1/0000)/'+re.escape(self.IDENTITY_SEGMENT)+r'/([a-f0-9]{4})', identity) if isinstance(identity, str) else None
            if match is None:
                raise ImportError(f'{self.LABEL} identity requires its controller owner and source PC')
            after = validate_party_selector_values(values)
            byte_length = len(after)
            owner = 'scene://'+match[1]
            offset, record, entry = self._source.verified_record(owner)
            node, relative, report = _target(record, entry, int(match[2], 16), self.MNEMONIC, self.SUB_OPS, self.LABEL)
            at = offset+relative; span = set(range(at, at+byte_length))
            if occupied & span:
                raise ImportError(f'{self.LABEL} edits overlap another source span')
            occupied.update(span); records[owner] = (offset, record, entry, report)
            before = record[relative:relative+byte_length]
            after = bytes([(before[0] & 0xF8) | after[0]])
            if before == after:
                continue
            result[at:at+byte_length] = after
            audit.append(dict(**{self.AUDIT_ID: identity}, owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'],
                sub_op=node['operands']['sub_op'], target_context=node['target_context'],
                selector_mask=7, preserved_bits=before[0] & 0xF8,
                record_relative_byte_offset=relative, decoded_byte_offset=at, byte_length=byte_length,
                before_hex=before.hex(), after_hex=after.hex(),
                before_values=_values(before),
                after_values=deepcopy(values), source_record_sha256=sha256(record).hexdigest(),
                source_decoded_man_sha256=sha256(self._man).hexdigest()))
        result = bytes(result)
        shape = lambda r: [(n['pc'], n['mnemonic'], n['length'], n['target_context'], n['successors']) for n in r['instructions']]
        for offset, record, entry, report in records.values():
            check = inspect_record(result[offset:offset+len(record)], entry)
            if check['stops'] or shape(check) != shape(report) or check['dialogues'] != report['dialogues']:
                raise ImportError(f'{self.LABEL} edit changed source layout or continuation')
        if read_man_layout(result) != read_man_layout(self._man):
            raise ImportError(f'{self.LABEL} edit changed MAN layout')
        return result, deepcopy(sorted(audit, key=lambda row: row['decoded_byte_offset']))


def load_controller_party_selector_context(disc, scene):
    from .controller_system_flags import load_controller_record_source
    return ControllerPartySelectorAuthoringContext(load_controller_record_source(disc, scene))
