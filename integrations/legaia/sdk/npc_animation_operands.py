"""Source-qualified animation arguments in independently allocated NPC scripts.

This allocation writer is infrastructure for the NPC authoring workflow. It
does not expose project commands or claim animation playback qualification.
"""
from copy import deepcopy
from hashlib import sha256
from importer.animation_operand_authoring import patch_animation_operands_target
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_animation_operands(context, candidate, allocations, requests):
    original, layout, prepared = allocated_scripts(context, candidate, allocations, requests)
    output = bytearray(candidate)
    audit = []
    occupied = set()
    for item in prepared:
        source = item['source_record']
        entry, start, length = item['entry'], item['start'], item['length']
        for identifier, values in sorted(item['entries'].items()):
            target = item['targets'][identifier]
            pc, size = target['pc'], target['instruction_length']
            span = set(range(start + pc, start + pc + size))
            if pc < entry or pc + size > length or occupied & span:
                raise ProjectError('NPC animation instruction ownership overlaps or escapes its clone')
            occupied.update(span)
            # Qualify every byte of the fixed instruction even for no-op values:
            # opcode, extended context, selector and all unedited arguments.
            if candidate[start + pc:start + pc + size] != source[pc:pc + size]:
                raise ProjectError('NPC animation dispatch or operand preimage differs from its donor')
            _, source_changes = patch_animation_operands_target(
                source, entry, pc, values, base_offset=item['source_offset'])
            clone = candidate[start:start + length]
            _, clone_changes = patch_animation_operands_target(clone, entry, pc, values, base_offset=start)
            if len(source_changes) != len(clone_changes):
                raise ProjectError('NPC animation candidate instruction differs from its donor')
            for change, current in zip(source_changes, clone_changes):
                fields = ('field', 'pc', 'mnemonic', 'target_context', 'record_relative_byte_offset',
                          'byte_length', 'before_hex', 'after_hex', 'before_value', 'after_value')
                if any(change[key] != current[key] for key in fields):
                    raise ProjectError('NPC animation candidate operand differs from its donor')
                at = start + change['record_relative_byte_offset']
                width = change['byte_length']
                if not start + pc <= at < at + width <= start + pc + size:
                    raise ProjectError('NPC animation field escapes its qualified instruction')
                output[at:at + width] = bytes.fromhex(change['after_hex'])
                audit.append(dict(change, draft_id=item['draft_id'], donor_entity_id=item['donor_entity_id'],
                                  animation_operand_id=identifier, record_index=item['record_index'],
                                  source_decoded_byte_offset=change['decoded_byte_offset'], decoded_byte_offset=at))
    result = bytes(output)
    if read_man_layout(result) != layout:
        raise ProjectError('NPC animation arguments changed MAN structure')
    return result, dict(schema_version='legaia.npc-animation-operands-native.v1',
                        source_man_sha256=sha256(original).hexdigest(),
                        candidate_man_sha256=sha256(candidate).hexdigest(),
                        result_man_sha256=sha256(result).hexdigest(), changes=deepcopy(audit),
                        scope='appended_source_qualified_fixed_animation_arguments_only',
                        gameplay_verified=False, animation_playback='not_asserted', npc_placement_changed=False)
