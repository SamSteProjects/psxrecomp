"""Source-qualified signed model selector words in appended NPC scripts.

Uses the existing MENU_CTRL 0x50 serializer. Encoded selectors are not resolved
asset IDs; model restaging, pairing and story execution remain unknown.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.model_selector_authoring import patch_model_selector_target
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def validate(project, draft):
    if 'model_selectors' not in draft:
        return
    value = draft['model_selectors']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC model selectors belong to their script donor; clear model selectors before changing donor')
    project._validate_model_selectors(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC model selectors require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._model_selector_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('model_selectors', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC model selectors are not source-qualified')
    context.patch(entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC model_selector inspection')
    return dict(schema_version='legaia.npc-model-selectors-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_model_identity='not_asserted', model_restaging='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC model_selector review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['model_selectors'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('model_selectors', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC model_selector entry is not qualified by its script donor')
    _, changes = project._model_selector_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC model_selector review')
    return dict(schema_version='legaia.npc-model-selectors-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-model_selector-targets.v1')),
                gameplay_verified=False, runtime_model_identity='not_asserted', model_restaging='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC model_selector Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC model selectors changed; review again')
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
            raise ProjectError('NPC model_selector allocation belongs to another scene')
        if 'model_selectors' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['model_selectors'])))
    return patch_allocated_model_selectors(context, candidate, allocations, requests) if requests else (candidate, None)



def patch_allocated_model_selectors(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];source=item['source_record'];entry=item['entry'];start=item['start'];length=item['length']
        for identifier,values in sorted(item['entries'].items()):
            target=item['targets'][identifier];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset
            _,source_changes=patch_model_selector_target(source,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # A no-op must still prove the opcode, sub-op, extended dispatch and
            # original word. Existing unrelated script operands may differ.
            if clone[pc:relative+2]!=source[pc:relative+2]:
                raise ProjectError('NPC model selector dispatch or operand preimage differs from source')
            _,clone_changes=patch_model_selector_target(clone,entry,pc,values,base_offset=start)
            if len(source_changes)!=len(clone_changes):raise ProjectError('NPC model selector candidate instruction differs from source')
            for change,current in zip(source_changes,clone_changes):
                fields=('field','pc','mnemonic','target_context','record_relative_byte_offset','byte_length','before_hex','after_hex','before_selector','after_selector')
                if any(change[k]!=current[k] for k in fields):raise ProjectError('NPC model selector candidate operand differs from source')
                at=start+change['record_relative_byte_offset'];span=set(range(at,at+2))
                if span&occupied or not start<=at<=start+length-2:raise ProjectError('NPC model selector words overlap or escape their clone')
                occupied.update(span);output[at:at+2]=bytes.fromhex(change['after_hex'])
                audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,model_selector_id=identifier,record_index=item['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC model selectors changed MAN structure')
    return result,dict(schema_version='legaia.npc-model-selectors-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_signed_model_selector_words_only',gameplay_verified=False,runtime_model_identity='not_asserted',model_restaging='not_asserted',npc_placement_changed=False)
