"""Controller table-copy operand authoring; parameter meanings and runtime effects unresolved."""
from copy import deepcopy
from hashlib import sha256
import re
import struct
from .core import ImportError
from .controller_system_flags import ControllerRecordSource, load_controller_record_source
from .script_inspection import inspect_record
from .man_layout import read_man_layout

LIMITATIONS = [
    'Only reached FIELD_TABLE_COPY operands in fully decoded controller paths are candidates.',
    'Signed word meanings and runtime table bindings, runtime ownership and visible table effects remain unresolved.',
    'Sub-op, dispatch context, instruction layout, successors, dialogue and MAN pointers remain unchanged.',
    'Native serialization does not establish gameplay execution or project/editor Build support.',
]


def validate_table_copy_values(values):
    if (not isinstance(values, dict) or set(values) != {'signed_words'} or
            not isinstance(values['signed_words'], list) or len(values['signed_words']) != 16 or
            any(type(word) is not int or not -32768 <= word <= 32767 for word in values['signed_words'])):
        raise ImportError('Table-copy request requires exactly sixteen signed words-32768..32767')
    return struct.pack('<16h', *values['signed_words'])


def _target(record, entry, pc, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError('Table-copy request PC must be a nonnegative record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('Table-copy authoring requires no unknown/conflicting source-path stops')
    node = next((row for row in report['instructions'] if row['pc'] == pc), None)
    if node is None or node['mnemonic'] != 'FIELD_TABLE_COPY':
        raise ImportError('Table-copy request PC must identify a reached source instruction')
    header = 1 if node['target_context'] is None else 2
    relative = pc + header + 1
    # Verify the 32-byte preimage independently of decoded operand names.
    if (record[pc] != (0x4c if header == 1 else 0xcc) or
            record[pc+header] != 0x9e or header == 2 and record[pc+1] != node['target_context'] or node['length'] != header+33 or
            node['successors'] != [{'pc': pc+header+33, 'condition': 'encoded_continuation'}]):
        raise ImportError('Table-copy request dispatch or continuation changed')
    values = {'signed_words': node['operands']['signed_words']}
    if record[relative:relative+32] != validate_table_copy_values(values):
        raise ImportError('Table-copy request operands differ from their source bytes')
    return node, relative, report


class ControllerTableCopyAuthoringContext:
    def __init__(self, source):
        if not isinstance(source, ControllerRecordSource):
            raise ImportError('Table-copy authoring requires a dedicated controller source')
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(self._source.provenance(), limitations=list(LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets = []
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] != 'FIELD_TABLE_COPY':
                    continue
                _, relative, _ = _target(record, entry, node['pc'], report)
                targets.append(dict(semantic_id=owner.replace('scene://', 'script://', 1)+f"/table-copy/{node['pc']:04x}",
                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], sub_op=node['operands']['sub_op'],
                    target_context=node['target_context'], decoded_byte_offset=offset+relative,
                    values=deepcopy({key: node['operands'][key] for key in ('signed_words',)}),
                    source_record_sha256=sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, source=self.provenance(), inspection=deepcopy(report),
                    limitations=list(LIMITATIONS), reason='Table-copy authoring requires no decoder stops' if report['stops'] else None)

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('Table-copy MAN differs from verified Retail source')
        if not isinstance(edits, dict) or len(edits) > 1024:
            raise ImportError('Table-copy edit set exceeds bounds')
        result, audit, occupied, records = bytearray(self._man), [], set(), {}
        for identity, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/controllers/man-p1/0000)/table-copy/([a-f0-9]{4})', identity) if isinstance(identity, str) else None
            if match is None:
                raise ImportError('Table-copy identity requires its controller owner and source PC')
            after = validate_table_copy_values(values)
            owner = 'scene://'+match[1]
            offset, record, entry = self._source.verified_record(owner)
            node, relative, report = _target(record, entry, int(match[2], 16))
            at = offset+relative; span = set(range(at, at+32))
            if occupied & span:
                raise ImportError('Table-copy edits overlap another source span')
            occupied.update(span); records[owner] = (offset, record, entry, report)
            before = record[relative:relative+32]
            if before == after:
                continue
            result[at:at+32] = after
            audit.append(dict(table_copy_id=identity, owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'],
                sub_op=node['operands']['sub_op'], target_context=node['target_context'],
                record_relative_byte_offset=relative, decoded_byte_offset=at, byte_length=32,
                before_hex=before.hex(), after_hex=after.hex(),
                before_values=dict(signed_words=list(struct.unpack('<16h', before))),
                after_values=deepcopy(values), source_record_sha256=sha256(record).hexdigest(),
                source_decoded_man_sha256=sha256(self._man).hexdigest()))
        result = bytes(result)
        shape = lambda r: [(n['pc'], n['mnemonic'], n['length'], n['target_context'], n['successors']) for n in r['instructions']]
        for offset, record, entry, report in records.values():
            check = inspect_record(result[offset:offset+len(record)], entry)
            if check['stops'] or shape(check) != shape(report) or check['dialogues'] != report['dialogues']:
                raise ImportError('Table-copy edit changed source layout or continuation')
        if read_man_layout(result) != read_man_layout(self._man):
            raise ImportError('Table-copy edit changed MAN layout')
        return result, deepcopy(sorted(audit, key=lambda row: row['decoded_byte_offset']))


def load_controller_table_copy_context(disc, scene):
    return ControllerTableCopyAuthoringContext(load_controller_record_source(disc, scene))
