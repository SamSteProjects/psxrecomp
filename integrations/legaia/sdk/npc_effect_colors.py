"""Source-qualified RGB bytes and signed intensity in appended NPC scripts.

Uses the existing EFFECT sub0 serializer; visual color space, rendering and
story execution remain unverified. Retail donor records stay unchanged.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.effect_color_authoring import patch_effect_color_target
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def qualify(project,draft):
    validate(project,draft)
    return project._effect_color_context(draft['donor_entity_id']).patch(draft['effect_colors']['entries'])


def validate(project, draft):
    if 'effect_colors' not in draft:
        return
    value = draft['effect_colors']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC effect colors belong to their script donor; clear effect colors before changing donor')
    project._validate_effect_colors(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC effect colors require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._effect_color_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('effect_colors', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC effect colors are not source-qualified')
    context.patch(entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC effect_color inspection')
    return dict(schema_version='legaia.npc-effect-colors-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_effect='not_asserted', visual_color_space='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC effect_color review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['effect_colors'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('effect_colors', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC effect_color entry is not qualified by its script donor')
    _, changes = project._effect_color_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC effect_color review')
    return dict(schema_version='legaia.npc-effect-colors-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-effect_color-targets.v1')),
                gameplay_verified=False, runtime_effect='not_asserted', visual_color_space='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC effect_color Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC effect colors changed; review again')
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
            raise ProjectError('NPC effect_color allocation belongs to another scene')
        if 'effect_colors' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['effect_colors'])))
    return patch_allocated_effect_colors(context, candidate, allocations, requests) if requests else (candidate, None)



def patch_allocated_effect_colors(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];source=item['source_record'];entry=item['entry'];start=item['start'];length=item['length']
        for identifier,values in sorted(item['entries'].items()):
            target=item['targets'][identifier];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset
            _,source_changes=patch_effect_color_target(source,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # A no-op must still prove the opcode, sub-op, extended dispatch and
            # complete original color span. Unrelated script operands may differ.
            if clone[pc:relative+5]!=source[pc:relative+5]:
                raise ProjectError('NPC effect color dispatch or operand preimage differs from source')
            _,clone_changes=patch_effect_color_target(clone,entry,pc,values,base_offset=start)
            if len(source_changes)!=len(clone_changes):raise ProjectError('NPC effect color candidate instruction differs from source')
            for change,current in zip(source_changes,clone_changes):
                fields=('field','pc','mnemonic','target_context','record_relative_byte_offset','byte_length','before_hex','after_hex','before_values','after_values')
                if any(change[k]!=current[k] for k in fields):raise ProjectError('NPC effect color candidate operand differs from source')
                at=start+change['record_relative_byte_offset'];span=set(range(at,at+5))
                if span&occupied or not start<=at<=start+length-5:raise ProjectError('NPC effect color spans overlap or escape their clone')
                occupied.update(span);output[at:at+5]=bytes.fromhex(change['after_hex'])
                audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,effect_color_id=identifier,record_index=item['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC effect colors changed MAN structure')
    return result,dict(schema_version='legaia.npc-effect-colors-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_rgb_intensity_spans_only',gameplay_verified=False,runtime_effect='not_asserted',visual_color_space='not_asserted',npc_placement_changed=False)
