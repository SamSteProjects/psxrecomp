"""Record-level World branch words over independently qualified fixed operands.

Source callers own the P0 record and entry provenance. Branch boundaries and
retained dormant instructions reuse the existing field branch qualification.
This module does not change project state or execute scripts.
"""
from hashlib import sha256

from .branch_authoring import _branch, _graph_candidate, validate_branch_values, MAX_BRANCH_EDITS
from .core import ImportError
from .script_inspection import inspect_record, MAX_RECORD_BYTES


def _source(record, entry):
    if not isinstance(record, bytes) or not 0 < len(record) <= MAX_RECORD_BYTES or type(entry) is not int or not 0 <= entry < len(record):
        raise ImportError('World branch source requires bounded immutable record bytes and an exact entry')
    return inspect_record(record, entry)


def branch_record_options(record, entry):
    graph = _source(record, entry)
    destinations = []; targets = []; reason = None
    if graph['stops']:
        reason = 'World branch authoring requires no unknown or conflicting source-path stops'
    else:
        destinations = sorted([
            dict(pc=row['pc'], mnemonic=row.get('mnemonic', 'MES_SEGMENT'))
            for family in ('instructions', 'dialogues') for row in graph[family]
            if entry <= row['pc'] <= 32767], key=lambda row: row['pc'])
        allowed = {row['pc'] for row in destinations}
        for node in graph['instructions']:
            try:
                layout = _branch(record, node)
            except ImportError:
                continue
            if layout is not None and entry <= node['pc'] <= 32767 and layout['target_pc'] in allowed:
                targets.append(dict(pc=node['pc'], mnemonic=node['mnemonic'], target_context=node['target_context'], **layout))
    return dict(targets=targets, destinations=destinations, reason=reason,
                source_record_sha256=sha256(record).hexdigest(), entry_pc=entry)


def _operand_baseline(original, candidate, entry, graph):
    """Retain independently authored operands without licensing branch words.

    The caller qualifies fixed operand ownership before this stage. Here we
    independently forbid header/opaque changes and preserve SYSFLAG operation
    nibbles while admitting the already-authored normal selector encoding.
    """
    if not isinstance(candidate, bytes) or len(candidate) != len(original) or candidate[:entry] != original[:entry]:
        raise ImportError('World branch operand candidate changed source extent or header')
    for row in graph['opaque_regions']:
        start = row['pc']; end = start + row['length']
        if candidate[start:end] != original[start:end]:
            raise ImportError('World branch operand candidate changed opaque source bytes')
    baseline = bytearray(original)
    for row in graph['instructions']:
        layout = _branch(original, row)
        if layout is not None:
            at = layout['operand_pc']
            if candidate[at:at + 2] != original[at:at + 2]:
                raise ImportError('World branch operand candidate changed an unaudited branch word')
        if not row['mnemonic'].startswith('SYSFLAG_'):
            continue
        at = row['pc']
        if row['target_context'] is None:
            if candidate[at] & 0xf0 != original[at] & 0xf0:
                raise ImportError('World branch operand candidate changed a system flag operation')
            baseline[at:at + 2] = candidate[at:at + 2]
    baseline = bytes(baseline)
    _graph_candidate(original, candidate, entry, graph, baseline)
    return baseline


def patch_branch_record(original, entry, edits, *, operand_record=None, base_offset=0):
    """Apply all branch words last, preserving complete source anchor ownership.

    ``operand_record`` must come from the caller's qualified fixed writers.
    Requests use integer source PCs and exact ``{'target_pc': int}`` values.
    All requests inspect one immutable source; dormant source anchors remain
    represented by the returned graph's unvisited arrays.
    """
    graph = _source(original, entry)
    if type(base_offset) is not int or base_offset < 0:
        raise ImportError('World branch base offset must be nonnegative')
    if not isinstance(edits, dict) or len(edits) > MAX_BRANCH_EDITS or any(type(pc) is not int for pc in edits):
        raise ImportError('World branch requests require at most 1024 integer source PCs')
    options = branch_record_options(original, entry)
    if options['reason']:
        raise ImportError(options['reason'])
    candidate = original if operand_record is None else operand_record
    baseline = _operand_baseline(original, candidate, entry, graph)
    targets = {row['pc']: row for row in options['targets']}
    destinations = {row['pc'] for row in options['destinations']}
    output = bytearray(candidate); occupied = set(); audit = []
    for pc, values in sorted(edits.items()):
        target = validate_branch_values(values); row = targets.get(pc)
        if row is None or target not in destinations:
            raise ImportError('World branch edits require original reached branch and destination boundaries')
        at = row['operand_pc']; span = {at, at + 1}
        if occupied & span or candidate[at:at + 2] != original[at:at + 2]:
            raise ImportError('World branch word overlaps another edit or differs from its source preimage')
        occupied.update(span)
        before = original[at:at + 2]; after = ((target - at) & 0xffff).to_bytes(2, 'little')
        if before == after:
            continue
        output[at:at + 2] = after
        audit.append(dict(pc=pc, mnemonic=row['mnemonic'], target_context=row['target_context'],
            condition=row['condition'], encoding=row['encoding'], field='script.branch_target',
            before_target_pc=row['target_pc'], after_target_pc=target,
            record_relative_byte_offset=at, decoded_byte_offset=base_offset + at, byte_length=2,
            before_hex=before.hex(), after_hex=after.hex(), source_record_sha256=options['source_record_sha256'],
            effective_record_sha256=sha256(candidate).hexdigest(), scope='world-script-branch-target-only'))
    result = bytes(output)
    report = _graph_candidate(original, result, entry, graph, baseline)
    return result, audit, report
