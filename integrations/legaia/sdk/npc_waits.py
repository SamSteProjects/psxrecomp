"""Source-qualified fixed-width wait operands owned by allocated NPC records.

This adapter does not publish project commands. It retains script ownership and
layout, and makes no claim about runtime scheduling or elapsed seconds.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.wait_authoring import patch_wait_target
from .project import ProjectError


def patch_allocated_waits(context, candidate, allocations, requests):
    """Resolve clone identities after all appends; never reuse allocation offsets."""
    if not isinstance(candidate, bytes) or not 0 < len(candidate) <= 4*1024*1024:
        raise ProjectError('NPC waits require a bounded immutable MAN candidate')
    if not isinstance(allocations, dict) or not isinstance(allocations.get('drafts'), list):
        raise ProjectError('NPC waits require the actor allocation audit')
    if not isinstance(requests, list) or not 1 <= len(requests) <= 128:
        raise ProjectError('NPC waits require 1 through 128 unique draft requests')
    original, _ = context.patch({})
    source_layout = read_man_layout(original)
    layout = read_man_layout(candidate)
    records = {(r['partition'], r['record_index']): r for r in layout['records']}
    source_indices = {r['record_index'] for r in source_layout['records'] if r['partition'] == 1}
    rows = {}
    for row in allocations['drafts']:
        if not isinstance(row, dict) or not isinstance(row.get('draft_id'), str) or row['draft_id'] in rows:
            raise ProjectError('NPC wait allocation identities are ambiguous')
        rows[row['draft_id']] = row
    output = bytearray(candidate)
    audit, seen, indices, occupied = [], set(), set(), set()
    target_count = 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {'draft_id', 'donor_entity_id', 'entries'}:
            raise ProjectError('NPC waits accept draft identity, script donor and typed entries only')
        identifier, owner, entries = (request[k] for k in ('draft_id', 'donor_entity_id', 'entries'))
        if not isinstance(identifier, str) or identifier in seen or identifier not in rows:
            raise ProjectError('NPC wait draft is unavailable or duplicated')
        if not isinstance(owner, str) or '/actors/man-p1/' not in owner:
            raise ProjectError('NPC waits require an imported actor script donor')
        if not isinstance(entries, dict) or not 1 <= len(entries) <= 1024:
            raise ProjectError('NPC waits require a bounded nonempty entry collection')
        target_count += len(entries)
        if target_count > 1024:
            raise ProjectError('NPC waits exceed the candidate-wide 1024-target budget')
        seen.add(identifier)
        row = rows[identifier]
        if not isinstance(row.get('donor'), dict):
            raise ProjectError('NPC wait allocation script donor is unavailable')
        index, donor_index = row.get('record_index'), row.get('donor', {}).get('record_index')
        if type(index) is not int or index in source_indices or index in indices or type(donor_index) is not int:
            raise ProjectError('NPC waits must target unique appended actor records')
        options = context.options(owner)
        targets = {r['semantic_id']: r for r in options['targets']}
        if set(entries) - set(targets):
            raise ProjectError('NPC wait entry is not supported by its recorded script donor')
        # verified_record qualifies scene identity, record/hash/alias ownership.
        source_offset, source_record, entry = context._source.verified_record(owner)
        if owner.rsplit('/', 1)[-1] != f'{donor_index:04d}' or donor_index not in source_indices:
            raise ProjectError('NPC wait allocation belongs to another script donor')
        record = records.get((1, index))
        if record is None or record['byte_length'] != len(source_record) or row.get('byte_length') != len(source_record):
            raise ProjectError('NPC wait allocation extent differs from its source')
        start, length = record['byte_offset'], record['byte_length']
        if sum(r['byte_offset'] == start for r in layout['records']) != 1:
            raise ProjectError('NPC waits cannot edit an aliased clone')
        indices.add(index)
        local_header = 1 + source_record[0]*2
        if candidate[start:start+local_header] != source_record[:local_header]:
            raise ProjectError('NPC wait clone local/script entry ownership differs from its donor')
        for wait_id, values in sorted(entries.items()):
            target = targets[wait_id]
            _, changes = patch_wait_target(source_record, entry, target['pc'], values, base_offset=source_offset)
            # Qualify the current clone even for a source-identical no-op request.
            clone = bytes(output[start:start+length])
            _, clone_changes = patch_wait_target(clone, entry, target['pc'], values, base_offset=start)
            relative = target['decoded_byte_offset'] - source_offset
            if clone[target['pc']:relative+2] != source_record[target['pc']:relative+2]:
                raise ProjectError('NPC wait operand preimage differs from its retail donor')
            if len(changes) != len(clone_changes):
                raise ProjectError('NPC wait candidate instruction differs from its source')
            for change, clone_change in zip(changes, clone_changes):
                if any(change[k] != clone_change[k] for k in ('pc','mnemonic','target_context','record_relative_byte_offset','before_hex','after_hex')):
                    raise ProjectError('NPC wait candidate instruction differs from its source')
                at = start + change['record_relative_byte_offset']
                span = set(range(at, at+2))
                if span & occupied or not start <= at <= start+length-2:
                    raise ProjectError('NPC wait spans overlap or escape the clone')
                occupied.update(span)
                output[at:at+2] = bytes.fromhex(change['after_hex'])
                audit.append(dict(change, draft_id=identifier, donor_entity_id=owner,
                                  wait_id=wait_id, record_index=index,
                                  source_decoded_byte_offset=change['decoded_byte_offset'],
                                  decoded_byte_offset=at))
    result = bytes(output)
    if read_man_layout(result) != layout:
        raise ProjectError('NPC waits changed the MAN structure')
    return result, dict(schema_version='legaia.npc-waits-native.v1',
        source_man_sha256=sha256(original).hexdigest(), candidate_man_sha256=sha256(candidate).hexdigest(),
        result_man_sha256=sha256(result).hexdigest(), changes=deepcopy(audit),
        scope='appended_wait_frames_u16_operands_only', gameplay_verified=False,
        runtime_scheduling='not_asserted', elapsed_seconds='not_asserted')
