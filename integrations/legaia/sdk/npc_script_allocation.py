"""Common final-record ownership guard for fixed-width NPC script operands."""
from copy import deepcopy
from importer.man_layout import read_man_layout
from .project import ProjectError


def allocated_scripts(context,candidate,allocations,requests,*,target_key="targets"):
    """Verify exact donor/clone ownership without applying any authored bytes."""
    if target_key not in ('targets','transitions'):raise ProjectError('NPC script target collection is unsupported')
    if not isinstance(candidate, bytes) or not 0 < len(candidate) <= 4*1024*1024:
        raise ProjectError('NPC scripts require a bounded immutable MAN candidate')
    if not isinstance(allocations, dict) or not isinstance(allocations.get('drafts'), list) or len(allocations['drafts'])>128:
        raise ProjectError('NPC scripts require the actor allocation audit')
    if not isinstance(requests, list) or not 1 <= len(requests) <= 128:
        raise ProjectError('NPC scripts require 1 through 128 unique draft requests')
    original, _ = context.patch({})
    source_layout = read_man_layout(original)
    layout = read_man_layout(candidate)
    records = {(r['partition'], r['record_index']): r for r in layout['records']}
    source_indices = {r['record_index'] for r in source_layout['records'] if r['partition'] == 1}
    rows = {}
    for row in allocations['drafts']:
        if not isinstance(row, dict) or not isinstance(row.get('draft_id'), str) or row['draft_id'] in rows:
            raise ProjectError('NPC script allocation identities are ambiguous')
        rows[row['draft_id']] = row
    prepared = []
    seen, indices = set(), set()
    target_count = 0
    for request in requests:
        if not isinstance(request, dict) or set(request) != {'draft_id', 'donor_entity_id', 'entries'}:
            raise ProjectError('NPC scripts accept draft identity, script donor and typed entries only')
        identifier, owner, entries = (request[k] for k in ('draft_id', 'donor_entity_id', 'entries'))
        if not isinstance(identifier, str) or identifier in seen or identifier not in rows:
            raise ProjectError('NPC script draft is unavailable or duplicated')
        if not isinstance(owner, str) or '/actors/man-p1/' not in owner:
            raise ProjectError('NPC scripts require an imported actor script donor')
        if not isinstance(entries, dict) or not 1 <= len(entries) <= 1024:
            raise ProjectError('NPC scripts require a bounded nonempty entry collection')
        target_count += len(entries)
        if target_count > 1024:
            raise ProjectError('NPC scripts exceed the candidate-wide 1024-target budget')
        seen.add(identifier)
        row = rows[identifier]
        if not isinstance(row.get('donor'), dict):
            raise ProjectError('NPC script allocation script donor is unavailable')
        index, donor_index = row.get('record_index'), row.get('donor', {}).get('record_index')
        if type(index) is not int or index in source_indices or index in indices or type(donor_index) is not int:
            raise ProjectError('NPC scripts must target unique appended actor records')
        options = context.options(owner)
        targets = {r['semantic_id']: r for r in options[target_key]}
        if set(entries) - set(targets):
            raise ProjectError('NPC script entry is not supported by its recorded script donor')
        # verified_record qualifies scene identity, record/hash/alias ownership.
        source_offset, source_record, entry = context._source.verified_record(owner)
        if owner.rsplit('/', 1)[-1] != f'{donor_index:04d}' or donor_index not in source_indices:
            raise ProjectError('NPC script allocation belongs to another script donor')
        record = records.get((1, index))
        if record is None or record['byte_length'] != len(source_record) or row.get('byte_length') != len(source_record):
            raise ProjectError('NPC script allocation extent differs from its source')
        start, length = record['byte_offset'], record['byte_length']
        if sum(r['byte_offset'] == start for r in layout['records']) != 1:
            raise ProjectError('NPC scripts cannot edit an aliased clone')
        indices.add(index)
        local_header = 1 + source_record[0]*2
        if candidate[start:start+local_header] != source_record[:local_header]:
            raise ProjectError('NPC script clone local/script entry ownership differs from its donor')
        prepared.append(dict(draft_id=identifier,donor_entity_id=owner,entries=deepcopy(entries),targets=targets,source_offset=source_offset,source_record=source_record,entry=entry,start=start,length=length,record_index=index))
    return original,layout,prepared
