"""Source-qualified WAIT_FRAMES target authoring, pinned step.rs opcode0x4A.

The target is u16 but the reference accumulator is signed16 and saturating.
No seconds, actual scheduling, frame rate or execution outcome is inferred.
"""
from copy import deepcopy
import hashlib
import re
import struct
from .core import ImportError
from .dialogue_authoring import load_dialogue_authoring_context
from .script_inspection import inspect_record

LIMITATIONS = [
    "Only reached WAIT_FRAMES operands in records without decoder stops are editable.",
    "Targets above32767 exceed the pinned signed16 accumulator and remain unsupported.",
    "Ticks use host frame_delta; seconds, frame rate and actual execution remain unresolved.",
    "Opcode, extended context, record lengths, branch bytes and other operands remain unchanged.",
    "Project history, persistence, editor Apply and output are supported; gameplay timing remains unverified."
]


def validate_wait_values(values):
    if (not isinstance(values, dict) or set(values) != {'duration_ticks'} or
            type(values['duration_ticks']) is not int or not 0 <= values['duration_ticks'] <= 32767):
        raise ImportError('Wait requires only an integer duration_ticks0..32767')
    return values['duration_ticks']


def _target(record, entry, pc, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError('Wait PC must be a nonnegative source-record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('Wait authoring requires no unknown/conflicting source-path stops')
    node = next((n for n in report['instructions'] if n['pc'] == pc), None)
    if node is None or node['mnemonic'] != 'WAIT_FRAMES':
        raise ImportError('Wait PC must identify a reached WAIT_FRAMES instruction')
    if node['operands']['duration_ticks'] > 32767:
        raise ImportError('Retail wait target exceeds the pinned signed16 accumulator')
    return node, pc + (2 if node['target_context'] is not None else 1), report


def patch_wait_target(record, entry, pc, values, *, base_offset=0):
    duration = validate_wait_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('Wait base offset must be nonnegative')
    node, offset, report = _target(record, entry, pc)
    after = struct.pack('<H', duration)
    before = record[offset:offset+2]
    if before == after:
        return record, []
    result = record[:offset] + after + record[offset+2:]
    check = inspect_record(result, entry)
    shape = lambda r: [(n['pc'], n['mnemonic'], n['length'], n['target_context'], n['successors']) for n in r['instructions']]
    if check['stops'] != report['stops'] or shape(check) != shape(report):
        raise ImportError('Wait edit changed instruction layout or continuations')
    audit = [dict(field='duration_ticks', pc=pc, mnemonic=node['mnemonic'], target_context=node['target_context'],
                  record_relative_byte_offset=offset, decoded_byte_offset=base_offset+offset, byte_length=2,
                  before_hex=before.hex(), after_hex=after.hex(), before_ticks=node['operands']['duration_ticks'],
                  after_ticks=duration, source_record_sha256=hashlib.sha256(record).hexdigest())]
    return result, audit


class WaitAuthoringContext:
    def __init__(self, source):
        self._source, self._man = source, source._man

    def provenance(self):
        return dict(self._source.provenance(), limitations=list(LIMITATIONS))

    def options(self, owner):
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        targets, unavailable = [], []
        if not report['stops']:
            for node in report['instructions']:
                if node['mnemonic'] != 'WAIT_FRAMES':
                    continue
                try:
                    _, relative, _ = _target(record, entry, node['pc'], report)
                except ImportError as exc:
                    unavailable.append(dict(pc=node['pc'], reason=str(exc)))
                    continue
                targets.append(dict(semantic_id='script://'+owner.removeprefix('scene://')+f"/wait/{node['pc']:04x}",
                                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], target_context=node['target_context'],
                                    decoded_byte_offset=offset+relative, values={'duration_ticks':node['operands']['duration_ticks']},
                                    source_record_sha256=hashlib.sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, unavailable=unavailable,
                    reason='Wait authoring requires no decoder stops' if report['stops'] else None,
                    source=self.provenance(), limitations=list(LIMITATIONS))

    def patch_appended(self, candidate, edits):
        from .man_layout import read_man_layout
        _, changes = self.patch(edits)
        layout = read_man_layout(candidate)
        records = {(r['partition'],r['record_index']):r for r in layout['records']}
        result, audit = bytearray(candidate), []
        for change in changes:
            owner = change['owner_id']
            _, record, entry = self._source.verified_record(owner)
            partition = 2 if '/scripts/man-p2/' in owner else 1
            target = records.get((partition,int(owner.rsplit('/',1)[1])))
            if target is None or target['byte_length'] != len(record):
                raise ImportError('Appended wait owner differs from verified source extent')
            start = target['byte_offset']
            if sum(r['byte_offset']==start for r in layout['records']) != 1:
                raise ImportError('Appended wait owner is aliased')
            node, relative, _ = _target(candidate[start:start+len(record)], entry, change['pc'])
            at = start+relative
            if relative != change['record_relative_byte_offset'] or candidate[at:at+2].hex() != change['before_hex']:
                raise ImportError('Appended wait instruction or preimage differs from source')
            result[at:at+2] = bytes.fromhex(change['after_hex'])
            audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,
                              appended_man_sha256=hashlib.sha256(candidate).hexdigest(),appended_target_context=node['target_context']))
        result = bytes(result)
        if read_man_layout(result) != layout:
            raise ImportError('Wait authoring changed appended MAN layout')
        return result,audit

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('Wait MAN differs from verified source')
        if not isinstance(edits, dict) or len(edits) > 1024:
            raise ImportError('Wait edit set exceeds bounds')
        audit, occupied = [], set()
        for key, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/wait/([0-9a-f]{4})', key) if isinstance(key,str) else None
            if match is None:
                raise ImportError('Wait identity requires source owner and hexadecimal PC')
            owner = 'scene://' + match[1]
            offset, record, entry = self._source.verified_record(owner)
            _, changes = patch_wait_target(record, entry, int(match[2],16), values, base_offset=offset)
            for change in changes:
                span = set(range(change['decoded_byte_offset'],change['decoded_byte_offset']+2))
                if span & occupied:
                    raise ImportError('Wait edits overlap another authored span')
                occupied.update(span)
                audit.append(dict(change, wait_id=key, owner_id=owner, source_decoded_man_sha256=hashlib.sha256(self._man).hexdigest()))
        result = bytearray(self._man)
        audit.sort(key=lambda c:c['decoded_byte_offset'])
        for change in audit:
            at=change['decoded_byte_offset'];result[at:at+2]=bytes.fromhex(change['after_hex'])
        return bytes(result),deepcopy(audit)


def load_wait_authoring_context(disc, scene):
    return WaitAuthoringContext(load_dialogue_authoring_context(disc,scene))
