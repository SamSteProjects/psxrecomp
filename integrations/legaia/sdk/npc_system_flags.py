"""Source-qualified normal system selectors in independently allocated NPCs.

This native stage does not expose a project component or runtime flag writes.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.script_inspection import inspect_record
from importer.system_flag_authoring import patch_system_flag_selector
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def context_for(project, owner):
    from importer.system_flag_authoring import SystemFlagAuthoringContext
    return SystemFlagAuthoringContext(project._dialogue_context(owner))


def validate(project, draft):
    if 'system_flags' not in draft:
        return
    value = draft['system_flags']
    if (not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'}
            or value['donor_entity_id'] != draft['donor_entity_id']):
        raise ProjectError('NPC system selectors belong to their script donor; clear them before changing donor')
    from .system_flags import validate as validate_component
    validate_component(project, draft['donor_entity_id'], {'entries': value['entries']})


def qualify(project, draft):
    validate(project, draft)
    return context_for(project, draft['donor_entity_id']).patch(draft.get('system_flags', {}).get('entries', {}))


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC system selectors require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft)
    key = source_key(project); context = context_for(project, draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('system_flags', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC system selectors are not source-qualified')
    qualify(project, draft)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if key != source_key(project):
        raise ProjectError('Project changed during NPC system selector inspection')
    return dict(schema_version='legaia.npc-system-flags-source.v1', entity_id=identifier,
        scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft), options=options,
        gameplay_verified=False, runtime_variable_identity='not_asserted', story_meaning='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC system selector Review requires identity and complete typed entries')
    report = source(project, request['entity_id']); draft = report['draft']; proposed = deepcopy(draft)
    if request['entries']:
        proposed['system_flags'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('system_flags', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC system selector entry is not qualified by its script donor')
    _, changes = qualify(project, proposed)
    if 'branches' in proposed:
        from .npc_branches import qualify as qualify_branches
        qualify_branches(project, proposed)
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC system selector Review')
    return dict(schema_version='legaia.npc-system-flags-review.v1', entity_id=request['entity_id'],
        project_source_key=report['project_source_key'], request=deepcopy(request), current=draft,
        proposed=proposed, changes=changes,
        review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-system-selectors.v1')),
        gameplay_verified=False, runtime_variable_identity='not_asserted', story_meaning='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC system selector Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC system selector inputs changed; Review again')
    if report['current'] == report['proposed']:
        return
    project.actor_drafts[command['entity_id']] = deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts', entity_id=command['entity_id'],
        before=deepcopy(report['current']), after=deepcopy(report['proposed'])))
    project.redo_stack.clear()


def patch_project(project, scene_id, context, candidate, allocations):
    requests = []
    for row in allocations['drafts']:
        draft = project.actor_drafts[row['draft_id']]
        if draft['scene_id'] != scene_id:
            raise ProjectError('NPC system selector allocation belongs to another scene')
        if 'system_flags' in draft:
            validate(project, draft)
            requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['system_flags'])))
    return patch_allocated_system_flags(context, candidate, allocations, requests) if requests else (candidate, None)


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
