"""Source-qualified signed model selectors, pinned MENU_CTRL 0x50.

Evidence: nibble_5_6_7.rs and host.rs. The selector writes actor model_id,
resets move_id, clears draw flag0x1000 and dispatches signed >=0xF0 high pool.
No pool-to-asset resolution, restaging outcome or execution is inferred.
"""
from copy import deepcopy
import hashlib
import re
import struct
from .core import ImportError
from .dialogue_authoring import load_dialogue_authoring_context
from .script_inspection import inspect_record

LIMITATIONS = [
    "Only reached SET_ACTOR_MODEL signed16 operands in records without decoder stops are editable.",
    "Runtime model-pool bases and actual assets are unresolved; numeric selectors are not Asset Database IDs.",
    "Signed selectors >=240 request the high-pool dispatch flag; negative values retain their encoded meaning without an inferred binding.",
    "Opcode, MENU_CTRL sub-op, extended context, record lengths, branches and all other source bytes remain unchanged.",
    "The runtime primitive resets move_id and clears draw flag0x1000; world-map mode also mirrors the selector. Restaging and gameplay are unverified."
]


def validate_model_selector_values(values):
    if (not isinstance(values, dict) or set(values) != {'model_selector_signed'} or
            type(values['model_selector_signed']) is not int or not -32768 <= values['model_selector_signed'] <= 32767):
        raise ImportError('Model selector requires only an integer model_selector_signed from -32768 through 32767')
    return values['model_selector_signed']


def _target(record, entry, pc, report=None):
    if type(pc) is not int or pc < 0:
        raise ImportError('ModelSelector PC must be a nonnegative source-record offset')
    report = inspect_record(record, entry) if report is None else report
    if report['stops']:
        raise ImportError('ModelSelector authoring requires no unknown/conflicting source-path stops')
    node = next((n for n in report['instructions'] if n['pc'] == pc), None)
    if node is None or node['mnemonic'] != 'SET_ACTOR_MODEL':
        raise ImportError('ModelSelector PC must identify a reached SET_ACTOR_MODEL instruction')
    return node, pc + (3 if node['target_context'] is not None else 2), report


def patch_model_selector_target(record, entry, pc, values, *, base_offset=0):
    selector = validate_model_selector_values(values)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('ModelSelector base offset must be nonnegative')
    node, offset, report = _target(record, entry, pc)
    after = struct.pack('<h', selector)
    before = record[offset:offset+2]
    if before == after:
        return record, []
    result = record[:offset] + after + record[offset+2:]
    check = inspect_record(result, entry)
    shape = lambda r: [(n['pc'], n['mnemonic'], n['length'], n['target_context'], n['successors']) for n in r['instructions']]
    if check['stops'] != report['stops'] or shape(check) != shape(report):
        raise ImportError('ModelSelector edit changed instruction layout or continuations')
    audit = [dict(field='model_selector_signed', pc=pc, mnemonic=node['mnemonic'], target_context=node['target_context'],
                  record_relative_byte_offset=offset, decoded_byte_offset=base_offset+offset, byte_length=2,
                  before_hex=before.hex(), after_hex=after.hex(), before_selector=node['operands']['model_selector_signed'],
                  after_selector=selector, source_record_sha256=hashlib.sha256(record).hexdigest())]
    return result, audit


class ModelSelectorAuthoringContext:
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
                if node['mnemonic'] != 'SET_ACTOR_MODEL':
                    continue
                try:
                    _, relative, _ = _target(record, entry, node['pc'], report)
                except ImportError as exc:
                    unavailable.append(dict(pc=node['pc'], reason=str(exc)))
                    continue
                targets.append(dict(semantic_id='script://'+owner.removeprefix('scene://')+f"/model-selector/{node['pc']:04x}",
                                    owner_id=owner, pc=node['pc'], mnemonic=node['mnemonic'], target_context=node['target_context'],
                                    decoded_byte_offset=offset+relative, values={'model_selector_signed':node['operands']['model_selector_signed']},
                                    source_record_sha256=hashlib.sha256(record).hexdigest()))
        return dict(supported=bool(targets), targets=targets, unavailable=unavailable,
                    reason='ModelSelector authoring requires no decoder stops' if report['stops'] else None,
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
                raise ImportError('Appended model_selector owner differs from verified source extent')
            start = target['byte_offset']
            if sum(r['byte_offset']==start for r in layout['records']) != 1:
                raise ImportError('Appended model_selector owner is aliased')
            node, relative, _ = _target(candidate[start:start+len(record)], entry, change['pc'])
            at = start+relative
            if (relative != change['record_relative_byte_offset'] or
                    node['target_context'] != change['target_context'] or
                    candidate[at:at+2].hex() != change['before_hex']):
                raise ImportError('Appended model_selector instruction or preimage differs from source')
            result[at:at+2] = bytes.fromhex(change['after_hex'])
            audit.append(dict(change,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,
                              appended_man_sha256=hashlib.sha256(candidate).hexdigest(),appended_target_context=node['target_context']))
        result = bytes(result)
        if read_man_layout(result) != layout:
            raise ImportError('ModelSelector authoring changed appended MAN layout')
        return result,audit

    def patch(self, edits, *, original=None):
        if original is not None and original != self._man:
            raise ImportError('ModelSelector MAN differs from verified source')
        if not isinstance(edits, dict) or len(edits) > 1024:
            raise ImportError('ModelSelector edit set exceeds bounds')
        audit, occupied = [], set()
        for key, values in edits.items():
            match = re.fullmatch(r'script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/model-selector/([0-9a-f]{4})', key) if isinstance(key,str) else None
            if match is None:
                raise ImportError('ModelSelector identity requires source owner and hexadecimal PC')
            owner = 'scene://' + match[1]
            offset, record, entry = self._source.verified_record(owner)
            _, changes = patch_model_selector_target(record, entry, int(match[2],16), values, base_offset=offset)
            for change in changes:
                span = set(range(change['decoded_byte_offset'],change['decoded_byte_offset']+2))
                if span & occupied:
                    raise ImportError('ModelSelector edits overlap another authored span')
                occupied.update(span)
                audit.append(dict(change, model_selector_id=key, owner_id=owner, source_decoded_man_sha256=hashlib.sha256(self._man).hexdigest()))
        result = bytearray(self._man)
        audit.sort(key=lambda c:c['decoded_byte_offset'])
        for change in audit:
            at=change['decoded_byte_offset'];result[at:at+2]=bytes.fromhex(change['after_hex'])
        return bytes(result),deepcopy(audit)


def load_model_selector_authoring_context(disc, scene):
    return ModelSelectorAuthoringContext(load_dialogue_authoring_context(disc,scene))
