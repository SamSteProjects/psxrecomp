"""Clone-owned arrival references bind fresh native donor bytes, never routes."""
from copy import deepcopy
from hashlib import sha256
from importer.script_inspection import _instruction
from importer.transition_authoring import ENTRY_FIELDS, reference_entry_interpretation
from .project import ProjectError


def targets(project, draft):
    from .npc_transitions import validate
    validate(project, draft)
    context = project._transition_context(draft['donor_entity_id'])
    return context, {row['semantic_id']: row for row in context.options(draft['donor_entity_id'])['transitions']}


def binding(draft, donor, asset, script, context, qualified):
    owner = draft['donor_entity_id']
    pc = asset['reference']['pc']
    operand = 'script://' + owner[8:] + f'/transition/{pc:04x}'
    row = qualified.get(operand)
    if row is None:
        return None
    at, raw, entry = context._source.verified_record(owner)
    node = _instruction(raw, pc)
    relative = pc + node['length'] - 3
    values = dict(zip(ENTRY_FIELDS, raw[relative:relative+3]))
    reference = asset['reference']
    if (asset['owner_id'] != owner or asset['script_id'] != script['id'] or
            asset['source_record'] != script['source_record'] or
            donor['source_record_sha256'] != sha256(raw).hexdigest() or
            donor['byte_offset'] != at or donor['byte_length'] != len(raw) or
            row['pc'] != pc or row['owner_id'] != owner or row['semantic_id'] != operand or
            row['source_record_sha256'] != donor['source_record_sha256'] or
            row['decoded_byte_offset'] != at+relative or row['values'] != values or
            node['mnemonic'] != 'SCENE_CHANGE' or node['target_context'] != reference['extended_target'] or
            node['operands']['scene_name_ascii'] != reference['target_scene_name'] or
            row['destination'] != reference['target_scene_name'] or
            any(reference[field] != value for field, value in values.items())):
        raise ProjectError('NPC arrival reference differs from native donor or transition source')
    authored = deepcopy(draft.get('transitions', {}).get('entries', {}).get(operand))
    context.patch({operand: authored} if authored is not None else {})
    effective = dict(values, **(authored or {}))
    reference_value=reference_entry_interpretation(effective)
    return dict(donor=deepcopy(donor), operand_id=operand, transition_id=asset['id'],
                destination_scene_id='scene://'+row['destination'], retail_values=values,
                authored_values=authored, effective_values=effective,
                native_instruction=dict(raw_hex=node['raw_hex'], length=node['length'],
                                        target_context=node['target_context'], relative_operand_offset=relative),
                arrival_reference=dict(x=reference_value['x'],z=reference_value['z'],facing_sector=reference_value['facing_angle_12bit']//512,runtime_verified=False), reachability='not_evaluated')
