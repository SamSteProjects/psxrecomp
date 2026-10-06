"""Source-qualified fixed-width wait operands owned by allocated NPC records.

Reviewed project commands retain script ownership and layout, and make no claim
about runtime scheduling or elapsed seconds.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.wait_authoring import patch_wait_target
from .project import ProjectError, digest
from .project_copy import source_key


def validate(project, draft):
    if 'waits' not in draft:
        return
    value = draft['waits']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC waits belong to their script donor; clear waits before changing donor')
    project._validate_waits(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC waits require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._wait_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('waits', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC waits are not source-qualified')
    context.patch(entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC wait inspection')
    return dict(schema_version='legaia.npc-waits-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_scheduling='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC wait review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['waits'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('waits', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC wait entry is not qualified by its script donor')
    _, changes = project._wait_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC wait review')
    return dict(schema_version='legaia.npc-waits-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-wait-targets.v1')),
                gameplay_verified=False, runtime_scheduling='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC wait Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC waits changed; review again')
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
            raise ProjectError('NPC wait allocation belongs to another scene')
        if 'waits' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['waits'])))
    return patch_allocated_waits(context, candidate, allocations, requests) if requests else (candidate, None)


def patch_allocated_waits(context, candidate, allocations, requests):
    """Resolve clone identities after all appends; never reuse allocation offsets."""
    from .npc_script_allocation import allocated_scripts
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
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
