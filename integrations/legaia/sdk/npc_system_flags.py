"""Source-qualified normal system selectors in independently allocated NPCs.

This native stage does not expose a project component or runtime flag writes.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.script_inspection import inspect_record
from importer.system_flag_authoring import patch_system_flag_selector
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_system_flags(context, candidate, allocations, requests):
    original, layout, prepared = allocated_scripts(context, candidate, allocations, requests)
    output, audit, occupied = bytearray(candidate), [], set()
    for item in prepared:
        source = item['source_record']
        entry, start, length = item['entry'], item['start'], item['length']
        for identity, values in sorted(item['entries'].items()):
            target = item['targets'][identity]
            pc = target['pc']
            # Qualify the source even for a no-op. The independent writer binds
            # normal dispatch, full decoded paths and exact operation/edges.
            _, changes = patch_system_flag_selector(source, entry, pc, values,
                                                     base_offset=item['source_offset'])
            clone = bytes(output[start:start + length])
            source_node = next(n for n in inspect_record(source, entry)['instructions'] if n['pc'] == pc)
            current_node = next((n for n in inspect_record(clone, entry)['instructions'] if n['pc'] == pc), None)
            if (clone[pc:pc + 2] != source[pc:pc + 2] or current_node is None
                    or current_node['mnemonic'] != source_node['mnemonic']
                    or current_node['successors'] != source_node['successors']
                    or current_node['target_context'] is not None):
                raise ProjectError('NPC system selector preimage, dispatch or continuations differ from its donor')
            _, current_changes = patch_system_flag_selector(clone, entry, pc, values, base_offset=start)
            span = set(range(start + pc, start + pc + 2))
            if occupied & span or not start <= start + pc < start + pc + 2 <= start + length:
                raise ProjectError('NPC system selector spans overlap or escape their allocated clone')
            occupied.update(span)
            if len(changes) != len(current_changes):
                raise ProjectError('NPC system selector candidate differs from its qualified source')
            for change, current in zip(changes, current_changes):
                if any(change[k] != current[k] for k in ('field', 'pc', 'mnemonic', 'target_context',
                        'record_relative_byte_offset', 'byte_length', 'before_hex', 'after_hex',
                        'before_index', 'after_index')):
                    raise ProjectError('NPC system selector receipt differs from its source')
                at = start + pc
                output[at:at + 2] = bytes.fromhex(change['after_hex'])
                audit.append(dict(change, draft_id=item['draft_id'],
                    donor_entity_id=item['donor_entity_id'], system_flag_id=identity,
                    record_index=item['record_index'], decoded_byte_offset=at,
                    source_decoded_byte_offset=change['decoded_byte_offset']))
    result = bytes(output)
    if read_man_layout(result) != layout:
        raise ProjectError('NPC system selectors changed MAN structure')
    return result, dict(schema_version='legaia.npc-system-flags-native.v1',
        source_man_sha256=sha256(original).hexdigest(), candidate_man_sha256=sha256(candidate).hexdigest(),
        result_man_sha256=sha256(result).hexdigest(), changes=deepcopy(audit),
        scope='appended_normal_system_selector_indices_only', gameplay_verified=False,
        runtime_variable_identity='not_asserted', story_meaning='not_asserted', npc_placement_changed=False)
