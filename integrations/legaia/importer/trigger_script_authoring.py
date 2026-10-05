"""Existing primary gate-1 MAP rows: change only their P2 record-index byte."""
import re
from .core import ImportError
from .trigger_authoring import trigger_authoring_options, MAX_PRIMARY_TRIGGER_RECORDS


def patch_trigger_scripts(original, expected_sha256, scene, edits):
    options = trigger_authoring_options(original, scene)
    if expected_sha256 != options['source_sha256']:
        raise ImportError('Trigger script MAP source hash changed')
    if not isinstance(edits, list) or len(edits) > MAX_PRIMARY_TRIGGER_RECORDS:
        raise ImportError('Trigger script edits exceed the source table budget')
    records = {r['trigger_id']: r for r in options['records']}
    seen, qualified = set(), []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {'trigger_id', 'script_id', 'script_sha256'}:
            raise ImportError('Trigger script edits require stable trigger/script identities and target hash')
        identifier = edit['trigger_id']
        row = records.get(identifier) if isinstance(identifier, str) else None
        match = re.fullmatch(r'script://' + re.escape(scene) + r'/scripts/man-p2/([0-9]{4})', edit['script_id']) if isinstance(edit['script_id'], str) else None
        if (row is None or identifier in seen or row['table_kind'] != 1 or row['encoded']['gate'] != 1 or
                match is None or int(match[1]) > 255 or not isinstance(edit['script_sha256'], str) or
                re.fullmatch(r'[0-9a-f]{64}', edit['script_sha256']) is None):
            raise ImportError('Choose an existing primary gate-1 row and same-scene byte-addressable P2 script')
        seen.add(identifier)
        qualified.append((row, edit, int(match[1])))
    result, audit = bytearray(original), []
    for row, edit, index in sorted(qualified, key=lambda item: item[0]['record_index']):
        offset = row['byte_offset'] + 2
        if original[offset] == index:
            continue
        result[offset] = index
        audit.append(dict(trigger_id=row['trigger_id'], target_script_id=edit['script_id'],
                          target_script_sha256=edit['script_sha256'], table_kind=1,
                          record_index=row['record_index'], field='trigger.record_index',
                          byte_offset=offset, before_value=original[offset], after_value=index,
                          scope='source-MAP-trigger-P2-binding-only'))
    differences = {i: (a, b) for i, (a, b) in enumerate(zip(original, result)) if a != b}
    if len(result) != len(original) or differences != {r['byte_offset']: (r['before_value'], r['after_value']) for r in audit}:
        raise ImportError('Trigger script patch changed an unaudited byte')
    return bytes(result), audit
