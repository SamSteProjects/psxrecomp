"""Normal SYSFLAG selector authoring; no story meaning or runtime writes.

The selector spans opcode low4 and the following byte. Native helper evidence
is in test_script_system_flags.py; extended raw addressing stays unresolved.
"""
from copy import deepcopy
import hashlib
import re
from .core import ImportError
from .script_inspection import inspect_record
from .dialogue_authoring import load_dialogue_authoring_context

MAX_SYSTEM_FLAG_EDITS = 1024
LIMITATIONS = [
    'Only reached normal SYSFLAG SET/CLEAR/TEST selectors in fully decoded source paths are candidates.',
    'The operation/high opcode nibble, TEST delta, dispatch context and record lengths remain unchanged.',
    'Encoded selector range0..4095 does not establish native bank capacity, story meaning or execution.',
    'Typed SDK Review/Apply and native Build serialize selectors; editor authoring controls remain pending.',
]


def validate_system_flag_values(values):
    if (not isinstance(values, dict) or set(values) != {'index'}
            or type(values['index']) is not int or not 0 <= values['index'] <= 4095):
        raise ImportError('System flag selector requires only an integer index0..4095')
    return values['index']


def _target(record, entry, pc, *, report=None):
    if type(pc) is not int or not 0 <= pc <= 65535:
        raise ImportError('System flag PC must be a bounded source-record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('System selector authoring requires no unknown or conflicting source-path stops')
    node = next((n for n in report['instructions'] if n['pc'] == pc), None)
    if (node is None or node['mnemonic'] not in ('SYSFLAG_SET', 'SYSFLAG_CLEAR', 'SYSFLAG_TEST')
            or node['target_context'] is not None):
        raise ImportError('System selector PC must identify a normal decoded SYSFLAG instruction')
    return node, report


def patch_system_flag_selector(record, entry, pc, values, *, base_offset=0):
    index = validate_system_flag_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('System selector base offset must be nonnegative')
    node, report = _target(record, entry, pc)
    before = record[pc:pc + 2]
    after = bytes(((before[0] & 0xF0) | (index >> 8), index & 255))
    if after == before:
        return record, []
    changed = record[:pc] + after + record[pc + 2:]
    check = inspect_record(changed, entry)
    def shape(result):
        return [(n['pc'], n['mnemonic'], n['length'], n['target_context'], n['successors'])
                for n in result['instructions']]
    if check['stops'] != report['stops'] or shape(check) != shape(report):
        raise ImportError('System selector edit changed instruction shape or continuations')
    return changed, [dict(field='system_flag_index', pc=pc, mnemonic=node['mnemonic'],
        target_context=None, record_relative_byte_offset=pc,
        decoded_byte_offset=base_offset + pc, byte_length=2,
        before_hex=before.hex(), after_hex=after.hex(),
        before_index=node['operands']['index'], after_index=index,
        source_record_sha256=hashlib.sha256(record).hexdigest())]


class SystemFlagAuthoringContext:
    def __init__(self, source):
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(self._source.provenance(), limitations=list(LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets = []
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] not in ('SYSFLAG_SET', 'SYSFLAG_CLEAR', 'SYSFLAG_TEST'):
                    continue
                _target(record, entry, node['pc'], report=report)
                targets.append(dict(semantic_id='script://' + owner.removeprefix('scene://')
                    + f"/system-flag/{node['pc']:04x}", owner_id=owner, pc=node['pc'],
                    mnemonic=node['mnemonic'], target_context=None,
                    decoded_byte_offset=offset + node['pc'], byte_length=2,
                    values={'index': node['operands']['index']}, maximum=4095,
                    source_record_sha256=hashlib.sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, source=self.provenance(),
                    reason='System selector authoring requires no unknown/conflicting path stops'
                    if report['stops'] else None, limitations=list(LIMITATIONS))

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('System selector MAN differs from verified source')
        if not isinstance(edits, dict) or len(edits) > MAX_SYSTEM_FLAG_EDITS:
            raise ImportError('System selector edit collection exceeds bounds')
        audit, occupied = [], set()
        for key, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/system-flag/([0-9a-f]{4})', key) if isinstance(key, str) else None
            if match is None:
                raise ImportError('System selector identity requires source owner and hexadecimal PC')
            owner = 'scene://' + match[1]
            offset, record, entry = self._source.verified_record(owner)
            _, changes = patch_system_flag_selector(record, entry, int(match[2], 16), values, base_offset=offset)
            # Reserve full two-byte ownership even if the requested edit is a no-op.
            span = set(range(offset + int(match[2], 16), offset + int(match[2], 16) + 2))
            if occupied & span:
                raise ImportError('System selector edits overlap another source span')
            occupied.update(span)
            audit.extend(dict(change, system_flag_id=key, owner_id=owner,
                         source_decoded_man_sha256=hashlib.sha256(self._man).hexdigest()) for change in changes)
        result = bytearray(self._man)
        audit.sort(key=lambda row: row['decoded_byte_offset'])
        for change in audit:
            at = change['decoded_byte_offset']
            result[at:at + 2] = bytes.fromhex(change['after_hex'])
        return bytes(result), deepcopy(audit)

    def patch_appended(self, candidate, edits):
        from .man_layout import read_man_layout
        # Qualify no-op edits too; they may not conceal invalid source ownership.
        _, changes = self.patch(edits)
        layout = read_man_layout(candidate)
        records = {(r['partition'], r['record_index']): r for r in layout['records']}
        output, audit = bytearray(candidate), []
        changes_by_id = {c['system_flag_id']: c for c in changes}
        for identity, values in sorted(edits.items()):
            owner_text, pc_text = identity.rsplit('/system-flag/', 1)
            owner = owner_text.replace('script://', 'scene://', 1)
            relative = int(pc_text, 16)
            _, original, entry = self._source.verified_record(owner)
            partition = 2 if '/scripts/man-p2/' in owner else 1
            target = records.get((partition, int(owner.rsplit('/', 1)[1])))
            if target is None or target['byte_length'] != len(original):
                raise ImportError('Appended system selector owner differs from verified source extent')
            start = target['byte_offset']
            if sum(r['byte_offset'] == start for r in layout['records']) != 1:
                raise ImportError('Appended system selector owner is aliased')
            node, _ = _target(candidate[start:start + len(original)], entry, relative)
            source_node, _ = _target(original, entry, relative)
            if node['mnemonic'] != source_node['mnemonic'] or node['successors'] != source_node['successors'] or candidate[start + relative:start + relative + 2] != original[relative:relative + 2]:
                raise ImportError('Appended system selector instruction or preimage differs from verified source')
            change = changes_by_id.get(identity)
            if change is None:
                continue
            at = start + relative
            output[at:at + 2] = bytes.fromhex(change['after_hex'])
            audit.append(dict(change, source_decoded_byte_offset=change['decoded_byte_offset'],
                decoded_byte_offset=at, appended_man_sha256=hashlib.sha256(candidate).hexdigest()))
        result = bytes(output)
        if read_man_layout(result) != layout:
            raise ImportError('System selector authoring changed appended MAN layout')
        return result, audit


def load_system_flag_authoring_context(disc, scene):
    return SystemFlagAuthoringContext(load_dialogue_authoring_context(disc, scene))
