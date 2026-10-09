"""Shared source-qualified fixed signed-word operands with optional selector."""
from copy import deepcopy
from hashlib import sha256
import re
import struct
from .core import ImportError
from .controller_system_flags import ControllerRecordSource
from .script_inspection import inspect_record
from .man_layout import read_man_layout

def validate_triplet_values(values, label, *, selector=True, word_count=3):
    if type(word_count) is not int or word_count not in (3, 5):
        raise ImportError('Word-operand serialization requires a qualified three- or five-word layout')
    fields = {'selector', 'signed_words'} if selector else {'signed_words'}
    if (not isinstance(values, dict) or set(values) != fields or
            selector and (type(values['selector']) is not int or not 0 <= values['selector'] <= 255) or
            not isinstance(values['signed_words'], list) or len(values['signed_words']) != word_count or
            any(type(word) is not int or not -32768 <= word <= 32767 for word in values['signed_words'])):
        prefix = 'one selector byte0..255 and ' if selector else ''
        count_name = 'three' if word_count == 3 else 'five'
        raise ImportError(f'{label} request requires {prefix}exactly {count_name} signed words-32768..32767')
    return (bytes([values['selector']]) if selector else b'') + struct.pack('<'+str(word_count)+'h', *values['signed_words'])


def _values(raw, selector, word_count=3):
    words = raw[1:] if selector else raw
    return dict(**({'selector': raw[0]} if selector else {}), signed_words=list(struct.unpack('<'+str(word_count)+'h', words)))


def _target(record, entry, pc, mnemonic, sub_ops, label, report=None, *, selector=True, word_count=3, opcode=0x4c):
    if type(pc) is not int or pc < 0:
        raise ImportError(f'{label} request PC must be a nonnegative record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError(f'{label} authoring requires no unknown/conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] != mnemonic:
        raise ImportError(f'{label} request PC must identify a reached source instruction')
    header = 1 if node['target_context'] is None else 2
    relative = pc + header + 1
    byte_length = 2*word_count + int(selector)
    fields = ('selector', 'signed_words') if selector else ('signed_words',)
    # Verify the fixed-width preimage independently of decoded operand names.
    if (record[pc] != (opcode if header == 1 else opcode | 0x80) or
            record[pc+header] not in sub_ops or header == 2 and record[pc+1] != node['target_context'] or node['length'] != header+1+byte_length or
            node['successors'] != [{'pc': pc+header+1+byte_length, 'condition': 'encoded_continuation'}]):
        raise ImportError(f'{label} request dispatch or continuation changed')
    values = {key: node['operands'][key] for key in fields}
    if record[relative:relative+byte_length] != validate_triplet_values(values, label, selector=selector, word_count=word_count):
        raise ImportError(f'{label} request operands differ from their source bytes')
    return node, relative, report


class ControllerWordOperandAuthoringContext:
    HAS_SELECTOR = True
    WORD_COUNT = 3
    OPCODE = 0x4c
    def __init__(self, source):
        if type(self) is ControllerWordOperandAuthoringContext:
            raise ImportError('Triplet authoring requires a dedicated source-qualified family')
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
                if node['mnemonic'] != self.MNEMONIC:
                    continue
                _, relative, _ = _target(record, entry, node['pc'], self.MNEMONIC, self.SUB_OPS, self.LABEL, report, selector=self.HAS_SELECTOR, word_count=self.WORD_COUNT, opcode=self.OPCODE)
                targets.append(dict(semantic_id=owner.replace('scene://', 'script://', 1)+f"/{self.IDENTITY_SEGMENT}/{node['pc']:04x}",
                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], sub_op=node['operands']['sub_op'],
                    target_context=node['target_context'], decoded_byte_offset=offset+relative,
                    values=deepcopy({key: node['operands'][key] for key in (('selector', 'signed_words') if self.HAS_SELECTOR else ('signed_words',))}),
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
            after = validate_triplet_values(values, self.LABEL, selector=self.HAS_SELECTOR, word_count=self.WORD_COUNT)
            byte_length = len(after)
            owner = 'scene://'+match[1]
            offset, record, entry = self._source.verified_record(owner)
            node, relative, report = _target(record, entry, int(match[2], 16), self.MNEMONIC, self.SUB_OPS, self.LABEL, selector=self.HAS_SELECTOR, word_count=self.WORD_COUNT, opcode=self.OPCODE)
            at = offset+relative; span = set(range(at, at+byte_length))
            if occupied & span:
                raise ImportError(f'{self.LABEL} edits overlap another source span')
            occupied.update(span); records[owner] = (offset, record, entry, report)
            before = record[relative:relative+byte_length]
            if before == after:
                continue
            result[at:at+byte_length] = after
            audit.append(dict(**{self.AUDIT_ID: identity}, owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'],
                sub_op=node['operands']['sub_op'], target_context=node['target_context'],
                record_relative_byte_offset=relative, decoded_byte_offset=at, byte_length=byte_length,
                before_hex=before.hex(), after_hex=after.hex(),
                before_values=_values(before, self.HAS_SELECTOR, self.WORD_COUNT),
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


# Preserve the existing family imports while sharing the fixed-word foundation.
ControllerTripletAuthoringContext = ControllerWordOperandAuthoringContext
