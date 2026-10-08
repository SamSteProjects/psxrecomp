"""Source-qualified animation arguments in independently allocated NPC scripts.

Project Review/Apply and Build retain donor provenance and independent clone
ownership. Animation playback remains unverified.
"""
from copy import deepcopy
from hashlib import sha256
from importer.animation_operand_authoring import patch_animation_operands_target
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key
from .script_animation_operands import context


def qualify(project,draft):
    validate(project,draft)
    return context(project,draft['donor_entity_id']).patch(draft['animation_operands']['entries'])


def validate(project, draft):
    if 'animation_operands' not in draft:
        return
    value = draft['animation_operands']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC animation arguments belong to their script donor; clear animation arguments before changing donor')
    project._validate_script_animation_operands(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC animation arguments require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    adapter = context(project,draft['donor_entity_id'])
    options = adapter.options(draft['donor_entity_id'])
    entries = draft.get('animation_operands', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC animation arguments are not source-qualified')
    adapter.patch(entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC animation_operand inspection')
    return dict(schema_version='legaia.npc-animation-operands-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, animation_playback='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC animation_operand review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['animation_operands'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('animation_operands', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC animation_operand entry is not qualified by its script donor')
    _, changes = context(project,draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC animation_operand review')
    from .npc_current_script import proposed_inspection
    current_inspection=proposed_inspection(project,request['entity_id'],draft)
    proposed=deepcopy(proposed)
    proposed_record=proposed_inspection(project,request['entity_id'],proposed)
    if source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during NPC animation record preview')
    return dict(current_inspection=current_inspection,proposed_inspection=proposed_record,schema_version='legaia.npc-animation-operands-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-animation_operand-targets.v1')),
                gameplay_verified=False, animation_playback='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC animation_operand Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC animation arguments changed; review again')
    if report['current'] == report['proposed']:
        return
    project.actor_drafts[command['entity_id']] = deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts', entity_id=command['entity_id'], before=report['current'], after=deepcopy(report['proposed'])))
    project.redo_stack.clear()


def patch_project(project, scene_id, context, candidate, allocations):
    requests = []
    for row in allocations['drafts']:
        draft = project.actor_drafts[row['draft_id']]
        if draft['scene_id'] != scene_id:
            raise ProjectError('NPC animation_operand allocation belongs to another scene')
        if 'animation_operands' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['animation_operands'])))
    return patch_allocated_animation_operands(context, candidate, allocations, requests) if requests else (candidate, None)




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
