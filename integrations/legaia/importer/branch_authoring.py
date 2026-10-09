"""Source-bound, same-length writes to existing field-script target words.

The source snapshot owns P1/P2 record identity and every original boundary.
Retail opcode evidence takes precedence over known false pinned camera/field
jump interpretations. Relative targets wrap in the retail sixteen-bit PC;
this module never executes a VM or infers story activation or termination.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import re

from .core import ImportError
from .man_layout import read_man_layout
from .script_inspection import _instruction, decode_inline_message, inspect_record
from .trigger_scripts import _p2_entry

MAX_MAN_BYTES = 4 * 1024 * 1024
MAX_BRANCH_EDITS = 1024
MAX_BRANCH_OWNERS = 128
LIMITATIONS = [
    'Only existing reached JMP, conditional, bounding-box, flag-word, field-68, actor-search, value-comparison and ordinary system-flag target words are editable.',
    'Targets are original decoded instruction or atomic MES starts from the source entry through 32767; interiors and opaque bytes are excluded.',
    'Opcode, dispatch context, conditions, flag indices, bounds, selectors, ticks, record lengths and MAN pointers remain unchanged.',
    'Changed edges may make original instructions unreachable; their source spans and other authored operands remain retained.',
    'Source qualification and independent readback do not establish story behavior, branch activation or runtime termination.',
]

_FAMILIES = {
    'JMP_REL': (0, 'unconditional', 'relative_u16_wrap16'),
    'COND_JMP': (2, 'test_passed', 'relative_u16_wrap16'),
    'BBOX_TEST': (4, 'outside_box', 'relative_u16_wrap16'),
    'SYSFLAG_TEST': (1, 'flag_set', 'relative_u16_wrap16'),
    'FLAG_WORD_BRANCH': (2, 'flag_bit_set', 'relative_i16_wrap16'),
    'FIELD_68_BRANCH': (1, 'field_68_zero', 'relative_i16_wrap16'),
    'ACTOR_SEARCH_BRANCH': (3, 'search_match', 'relative_i16_wrap16'),
    'VALUE_COMPARE_BRANCH': (4, 'comparison_true', 'relative_u16_wrap16'),
}


def _hash(data):
    return sha256(data).hexdigest()


def validate_branch_values(values):
    if (not isinstance(values, dict) or set(values) != {'target_pc'} or
            type(values['target_pc']) is not int or not 0 <= values['target_pc'] <= 32767):
        raise ImportError('Branch values require only an integer target_pc from 0 through 32767')
    return values['target_pc']


def _branch(record, node):
    family = _FAMILIES.get(node['mnemonic'])
    if family is None:
        return None
    if node['mnemonic'] == 'SYSFLAG_TEST' and node['target_context'] is not None:
        raise ImportError('Extended system-flag branch control flow is not qualified for authoring')
    relative, condition, encoding = family
    operand = node['pc'] + (2 if node['target_context'] is not None else 1) + relative
    if not 0 <= operand <= len(record) - 2:
        raise ImportError('Branch destination word escapes its source record')
    target = (operand + int.from_bytes(record[operand:operand + 2], 'little')) & 0xffff
    selected = [edge for edge in node['successors'] if edge['condition'] == condition]
    if len(selected) != 1 or selected[0]['pc'] != target:
        raise ImportError('Branch decoder and qualified retail target-word arithmetic disagree')
    return dict(operand_pc=operand, width=2, condition=condition,
                encoding=encoding, target_pc=target)


def _entry(record, partition):
    if partition == 2:
        return _p2_entry(record)[0]
    if not record:
        raise ImportError('Branch actor record has no placement header')
    entry = 1 + record[0] * 2 + 4
    if entry > len(record):
        raise ImportError('Branch actor header exceeds its source record')
    return entry


def _shape(node):
    return node['pc'], node['length'], node['mnemonic'], node['target_context']


def _graph_candidate(original, candidate, entry, source_graph, selector_baseline=None):
    """Re-decode original anchors before following intentionally changed edges.

    Other authored values are supplied by the caller's existing qualified
    serializers. Original headers, all branch conditions and every original
    atomic instruction/message boundary are retained, even if no longer reached.
    """
    if not isinstance(candidate, bytes) or len(candidate) != len(original):
        raise ImportError('Branch candidate must preserve its exact source record length')
    if source_graph['stops']:
        raise ImportError('Branch authoring requires no unknown or conflicting source-path stops')
    # This optional baseline is supplied only by the context's independent
    # SystemFlagAuthoringContext writer; unreviewed opcode changes still refuse.
    selector_baseline = original if selector_baseline is None else selector_baseline
    known = {node['pc']: node for node in source_graph['instructions']}
    messages = {row['pc']: row for row in source_graph['dialogues']}
    original_boundaries = set(known) | set(messages)
    qualified_instructions = []
    qualified_dialogues = []
    for node in known.values():
        decoded = _instruction(candidate, node['pc'])
        decoded['byte_offset'] = node['pc']
        qualified_instructions.append(decoded)
        header = 2 if node['target_context'] is not None else 1
        if (_shape(decoded) != _shape(node) or
                node['mnemonic'].startswith('SYSFLAG_') and candidate[node['pc']:node['pc'] + 2] != selector_baseline[node['pc']:node['pc'] + 2] or
                candidate[node['pc']:node['pc'] + header] != selector_baseline[node['pc']:node['pc'] + header]):
            raise ImportError('Branch candidate changed an original instruction or dispatch boundary')
        layout = _branch(original, node)
        if layout is not None:
            lo, hi = node['pc'], node['pc'] + node['length']
            operand = layout['operand_pc']
            if (candidate[lo:operand] != selector_baseline[lo:operand] or
                    candidate[operand + 2:hi] != original[operand + 2:hi]):
                raise ImportError('Branch candidate changed an immutable condition, selector or flag operand')
            current_layout = _branch(candidate, decoded)
            if current_layout['condition'] != layout['condition']:
                raise ImportError('Branch candidate changed its source branch condition')
            if (current_layout['target_pc'] != layout['target_pc'] and
                    current_layout['target_pc'] not in original_boundaries):
                raise ImportError('Branch candidate targets a new or opaque source boundary, including an unreachable branch')
    for row in messages.values():
        decoded = decode_inline_message(candidate, row['pc'])
        qualified_dialogues.append(decoded)
        if (decoded['length'] != row['length'] or decoded['terminator'] != row['terminator'] or
                [(t['pc'], t['length'], t['kind']) for t in decoded['tokens']] !=
                [(t['pc'], t['length'], t['kind']) for t in row['tokens']]):
            raise ImportError('Branch candidate changed an original message boundary')
    report = inspect_record(candidate, entry)
    if report['stops']:
        raise ImportError('Branch candidate has an unknown, out-of-bounds or conflicting path stop')
    for node in report['instructions']:
        if node['pc'] not in known or _shape(node) != _shape(known[node['pc']]):
            raise ImportError('Branch candidate reaches a new or changed source instruction boundary')
    for row in report['dialogues']:
        if row['pc'] not in messages or row['length'] != messages[row['pc']]['length']:
            raise ImportError('Branch candidate reaches an opaque or changed source message boundary')
    reached = {row['pc'] for row in report['instructions']} | {row['pc'] for row in report['dialogues']}
    report['unreachable_source_pcs'] = sorted((set(known) | set(messages)) - reached)
    # Keep independently redecoded original anchors available to read-only graph
    # diagnostics. The reached-path arrays retain their existing meaning.
    report['unvisited_instructions'] = sorted(
        (row for row in qualified_instructions if row['pc'] not in reached), key=lambda row: row['pc'])
    report['unvisited_dialogues'] = sorted(
        (row for row in qualified_dialogues if row['pc'] not in reached), key=lambda row: row['pc'])
    return report


class BranchAuthoringContext:
    """Request-scoped private MAN source snapshot with detached review products."""
    OWNER_PATTERN = r'[A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4}'

    def __init__(self, source, *, system_selectors=None):
        if not isinstance(source._man, bytes) or not 0 < len(source._man) <= MAX_MAN_BYTES:
            raise ImportError('Branch source requires a bounded immutable verified MAN')
        self._source, self._man = source, source._man
        self._layout = read_man_layout(self._man)
        if len(self._layout['records']) > 8192:
            raise ImportError('Branch MAN exceeds its bounded record table')
        self._owners = {}
        self._selector_man = self._man if not system_selectors else self._selector_context(source).patch(system_selectors)[0]

    @staticmethod
    def _selector_context(source):
        from .system_flag_authoring import SystemFlagAuthoringContext
        return SystemFlagAuthoringContext(source)

    def _selector_record(self, snapshot):
        at = snapshot['offset']
        return self._selector_man[at:at + len(snapshot['record'])]

    def provenance(self):
        return dict(deepcopy(self._source.provenance()), limitations=list(LIMITATIONS))

    def _owner(self, owner):
        if not isinstance(owner, str) or re.fullmatch('scene://'+self.OWNER_PATTERN,owner) is None:
            raise ImportError('Branch owner requires a verified source identity string')
        if owner not in self._owners:
            offset, record, entry = self._source.verified_record(owner)
            partition = 2 if '/scripts/man-p2/' in owner else 1
            index = int(owner.rsplit('/', 1)[1])
            span = self._span(self._layout, partition, index, len(record))
            if span['byte_offset'] != offset or _entry(record, partition) != entry:
                raise ImportError('Branch source owner does not match its verified MAN layout')
            report = inspect_record(record, entry)
            self._owners[owner] = dict(owner_id=owner, partition=partition, record_index=index,
                                      offset=offset, record=record, entry=entry, inspection=report)
        return self._owners[owner]

    @staticmethod
    def _span(layout, partition, index, length):
        span = next((row for row in layout['records'] if row['partition'] == partition and row['record_index'] == index), None)
        if span is None or span['byte_length'] != length:
            raise ImportError('Branch owner differs from its verified source record extent')
        start, end = span['byte_offset'], span['byte_offset'] + length
        if (Counter(row['byte_offset'] for row in layout['records'])[start] != 1 or
                start < layout['data_region_offset'] or
                any(start < row['byte_offset'] + row['byte_length'] and row['byte_offset'] < end
                    for row in layout['sections'])):
            raise ImportError('Branch owner is aliased or intersects a MAN section')
        return span

    def options(self, owner):
        snapshot = self._owner(owner)
        report, record, entry = snapshot['inspection'], snapshot['record'], snapshot['entry']
        targets, destinations, reason = [], [], None
        if report['stops']:
            reason = 'Branch authoring requires no unknown or conflicting source-path stops'
        else:
            destinations = [dict(pc=row['pc'], mnemonic=row['mnemonic'])
                            for row in report['instructions'] if entry <= row['pc'] <= 32767]
            destinations += [dict(pc=row['pc'], mnemonic='MES_SEGMENT') for row in report['dialogues']
                             if entry <= row['pc'] <= 32767]
            destinations.sort(key=lambda row: row['pc'])
            allowed_targets = {row['pc'] for row in destinations}
            try:
                for row in report['instructions']:
                    layout = _branch(record, row)
                    if (layout is None or not entry <= row['pc'] <= 32767 or
                            layout['target_pc'] not in allowed_targets):
                        continue
                    targets.append(dict(semantic_id='script://' + owner.removeprefix('scene://') + f"/branch/{row['pc']:04x}",
                                        owner_id=owner, pc=row['pc'], mnemonic=row['mnemonic'],
                                        target_context=row['target_context'], **layout,
                                        decoded_byte_offset=snapshot['offset'] + layout['operand_pc'],
                                        source_record_sha256=_hash(record), values={'target_pc': layout['target_pc']}))
            except ImportError as exc:
                targets, destinations, reason = [], [], str(exc)
            if not targets and reason is None:
                reason = 'No supported source branch target words occur on the inspected paths'
        return deepcopy(dict(supported=bool(targets), owner_id=owner, targets=targets,
                             destinations=destinations, reason=reason, inspection=report,
                             source=self.provenance(), limitations=list(LIMITATIONS)))

    def _edits(self, edits):
        if not isinstance(edits, dict) or len(edits) > MAX_BRANCH_EDITS:
            raise ImportError('Branch edits require a bounded source-identity mapping')
        staged, owners = [], set()
        pattern = r'script://('+self.OWNER_PATTERN+r')/branch/([0-9a-f]{4})'
        for identifier, values in edits.items():
            match = re.fullmatch(pattern, identifier) if isinstance(identifier, str) else None
            if match is None:
                raise ImportError('Branch identity requires a source owner and hexadecimal PC')
            owner = 'scene://' + match.group(1)
            owners.add(owner)
            if len(owners) > MAX_BRANCH_OWNERS:
                raise ImportError('Branch edit set exceeds 128 source owners')
            target = validate_branch_values(values)
            options = self.options(owner)
            row = next((item for item in options['targets'] if item['semantic_id'] == identifier), None)
            if row is None:
                raise ImportError(options['reason'] or 'Branch instruction is not a supported original source boundary')
            if target not in {item['pc'] for item in options['destinations']}:
                raise ImportError('Branch target must be an original reached instruction or MES boundary; interior and opaque targets are unsupported')
            staged.append((self._owner(owner), row, target))
        return sorted(staged, key=lambda item: (item[0]['offset'], item[1]['operand_pc']))

    def _candidate(self, candidate, *, appended):
        if not isinstance(candidate, bytes) or not 0 < len(candidate) <= MAX_MAN_BYTES:
            raise ImportError('Branch composition requires a bounded immutable MAN candidate')
        layout = read_man_layout(candidate)
        if not appended and (len(candidate) != len(self._man) or layout != self._layout):
            raise ImportError('Branch composition must preserve the complete source MAN layout and length')
        if len(layout['records']) > 8192:
            raise ImportError('Branch candidate exceeds the bounded record table')
        return layout

    def _patch(self, candidate, edits, *, appended=False):
        layout = self._candidate(candidate, appended=appended)
        staged = self._edits(edits)
        output, audit, current_reports, offsets, occupied = bytearray(candidate), [], {}, {}, set()
        for snapshot, row, target in staged:
            owner, record = snapshot['owner_id'], snapshot['record']
            span = self._span(layout, snapshot['partition'], snapshot['record_index'], len(record))
            start, operand = span['byte_offset'], row['operand_pc']
            current = candidate[start:start + len(record)]
            if _entry(current, snapshot['partition']) != snapshot['entry']:
                raise ImportError('Branch candidate changed its original script entry boundary')
            if owner not in current_reports:
                current_reports[owner] = _graph_candidate(record, current, snapshot['entry'], snapshot['inspection'], self._selector_record(snapshot))
                offsets[owner] = start
            before = record[operand:operand + 2]
            if current[operand:operand + 2] != before:
                raise ImportError('Branch destination overlaps an existing authored span or differs from its source preimage')
            at = start + operand
            if {at, at + 1} & occupied:
                raise ImportError('Branch edits overlap another destination word')
            occupied.update((at, at + 1))
            after = ((target - operand) & 0xffff).to_bytes(2, 'little')
            if before == after:
                continue
            output[at:at + 2] = after
            audit.append(dict(owner_id=owner, branch_id=row['semantic_id'], pc=row['pc'],
                              mnemonic=row['mnemonic'], target_context=row['target_context'],
                              condition=row['condition'], encoding=row['encoding'],
                              field='script.branch_target', before_value=row['target_pc'], after_value=target,
                              before_target_pc=row['target_pc'], after_target_pc=target,
                              record_relative_byte_offset=operand, decoded_byte_offset=at, byte_length=2,
                              before_hex=before.hex(), after_hex=after.hex(),
                              changed_bytes=[dict(decoded_byte_offset=at + i, before_byte=a, after_byte=b)
                                             for i, (a, b) in enumerate(zip(before, after)) if a != b],
                              source_record_sha256=_hash(record), effective_record_sha256=_hash(current),
                              source_decoded_man_sha256=_hash(self._man), scope='script-branch-target-only'))
            if appended:
                audit[-1].update(source_decoded_byte_offset=snapshot['offset'] + operand,
                                 appended_man_sha256=_hash(candidate))
        result = bytes(output)
        proposed_reports = {}
        for owner, start in offsets.items():
            snapshot = self._owner(owner)
            proposed_reports[owner] = _graph_candidate(snapshot['record'], result[start:start + len(snapshot['record'])],
                                                       snapshot['entry'], snapshot['inspection'], self._selector_record(snapshot))
        for row in audit:
            owner, pc = row['owner_id'], row['pc']
            snapshot, start = self._owner(owner), offsets[owner]
            current = _instruction(candidate[start:start + len(snapshot['record'])], pc)
            proposed = _instruction(result[start:start + len(snapshot['record'])], pc)
            row.update(current_successors=deepcopy(current['successors']), proposed_successors=deepcopy(proposed['successors']),
                       unreachable_source_pcs=list(proposed_reports[owner]['unreachable_source_pcs']),
                       candidate_record_sha256=_hash(result[start:start + len(snapshot['record'])]))
        allowed = {at for row in audit for at in range(row['decoded_byte_offset'], row['decoded_byte_offset'] + 2)}
        if (read_man_layout(result) != layout or any(a != b and at not in allowed
                for at, (a, b) in enumerate(zip(candidate, result)))):
            raise ImportError('Branch patch changed a layout or unaudited candidate byte')
        return result, deepcopy(audit)

    def patch(self, edits, *, original=None):
        if original is not None and (not isinstance(original, bytes) or original != self._man):
            raise ImportError('Branch MAN differs from its verified source baseline')
        if self._selector_man != self._man:
            return type(self)(self._source)._patch(self._man, edits)
        return self._patch(self._man, edits)

    def patch_composed(self, candidate, edits):
        """Preserve independently authored operands; target words need source preimages."""
        return self._patch(candidate, edits)

    def patch_appended(self, candidate, edits):
        """Rebind original partition/index owners without changing appended bytes."""
        return self._patch(candidate, edits, appended=True)

    def inspect_owner(self, owner, candidate=None):
        snapshot = self._owner(owner)
        data = self._man if candidate is None else candidate
        layout = self._candidate(data, appended=False)
        span = self._span(layout, snapshot['partition'], snapshot['record_index'], len(snapshot['record']))
        record = data[span['byte_offset']:span['byte_offset'] + span['byte_length']]
        if _entry(record, snapshot['partition']) != snapshot['entry']:
            raise ImportError('Branch inspection changed the source entry boundary')
        report = _graph_candidate(snapshot['record'], record, snapshot['entry'], snapshot['inspection'], self._selector_record(snapshot))
        return deepcopy(dict(report, owner_id=owner, source_record_sha256=_hash(snapshot['record']),
                             current_record_sha256=_hash(record)))


def load_branch_authoring_context(disc, scene, *, system_selectors=None):
    from .dialogue_authoring import load_dialogue_authoring_context
    return BranchAuthoringContext(load_dialogue_authoring_context(disc, scene), system_selectors=system_selectors)
