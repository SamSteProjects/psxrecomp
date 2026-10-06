"""Qualified fixed-width movement operands owned by appended NPC scripts.

Script targets remain distinct from NPC placement and live positions. The
serializer does not resolve dispatch identity or change Y/depth/branch layout.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.movement_authoring import patch_movement_target
from .npc_script_allocation import allocated_scripts
from .project import ProjectError,digest
from .project_copy import source_key


def validate(project, draft):
    if 'movement' not in draft:
        return
    value = draft['movement']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC movement belong to their script donor; clear movement before changing donor')
    project._validate_movements(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC movement require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._movement_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('movement', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC movement are not source-qualified')
    context.patch(entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = dict(row['values'],**entries.get(row['semantic_id'],{}))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC movement inspection')
    return dict(schema_version='legaia.npc-movement-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_dispatch='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC movement review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['movement'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('movement', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if 'facing' in proposed:
        from .npc_facing import qualify
        qualify(project,proposed,proposed['facing']['entries'])
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC movement entry is not qualified by its script donor')
    _, changes = project._movement_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC movement review')
    return dict(schema_version='legaia.npc-movement-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-movement-targets.v1')),
                gameplay_verified=False, runtime_dispatch='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC movement Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC movement changed; review again')
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
            raise ProjectError('NPC movement allocation belongs to another scene')
        if 'movement' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['movement'])))
    return patch_allocated_movement(context, candidate, allocations, requests) if requests else (candidate, None)



def patch_allocated_movement(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for movement_id,values in sorted(entries.items()):
            target=targets[movement_id]
            _,changes=patch_movement_target(source_record,entry,target['pc'],values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            _,clone_changes=patch_movement_target(clone,entry,target['pc'],values,base_offset=start)
            relative=target['decoded_byte_offset']-source_offset
            # Retain opcode, extended context and NPC_RUN's extra dispatch byte.
            if clone[target['pc']:relative]!=source_record[target['pc']:relative]:
                raise ProjectError('NPC movement dispatch/header preimage differs from source')
            # Verify source-identical requested operands as well as changed ones.
            for field in values:
                at=relative+target['operand_offsets'][field]
                if clone[at]!=source_record[at]:raise ProjectError('NPC movement operand preimage differs from source')
            if len(changes)!=len(clone_changes):raise ProjectError('NPC movement candidate instruction differs from source')
            for change,current in zip(changes,clone_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte')):
                    raise ProjectError('NPC movement candidate instruction differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length:raise ProjectError('NPC movement spans overlap or escape their clone')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,movement_id=movement_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC movement changed MAN structure')
    return result,dict(schema_version='legaia.npc-movement-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_movement_operands_only',gameplay_verified=False,runtime_dispatch='not_asserted',npc_placement_changed=False)
