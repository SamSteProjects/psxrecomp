"""Source-qualified low-nibble facing edits in allocated NPC script records.

This serializer does not establish initial heading, runtime dispatch or execution.
"""
from copy import deepcopy
from hashlib import sha256
from importer.facing_authoring import patch_facing_sector,PRESERVATION_MASK
from importer.man_layout import read_man_layout
from importer.core import ImportError as NativeError
from .npc_script_allocation import allocated_scripts
from .project import ProjectError,digest
from .project_copy import source_key


def effective_record(project,draft,context):
    offset,record,entry=context._source.verified_record(draft['donor_entity_id'])
    if 'movement' in draft:
        movement=project._movement_context(draft['donor_entity_id'])
        if movement._man!=context._man:raise ProjectError('NPC facing/movement source snapshots differ')
        candidate,_=movement.patch(draft['movement']['entries']);record=candidate[offset:offset+len(record)]
    return record,entry,offset


def qualify(project,draft,entries,context=None):
    context=context or project._facing_context(draft['donor_entity_id']);options=context.options(draft['donor_entity_id']);targets={r['semantic_id']:r for r in options['targets']}
    if set(entries)-set(targets):raise ProjectError('NPC facing entry is not supported by its source donor')
    context.patch(entries);record,entry,offset=effective_record(project,draft,context)
    for identifier,values in entries.items():patch_facing_sector(record,entry,targets[identifier]['pc'],values,base_offset=offset)
    return context


def validate(project, draft):
    if 'facing' not in draft:
        return
    value = draft['facing']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC facing belong to their script donor; clear facing before changing donor')
    project._validate_facing(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC facing require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._facing_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('facing', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC facing are not source-qualified')
    qualify(project,draft,entries,context=context)
    current,entry,source_offset=effective_record(project,draft,context)
    for row in options['targets']:
        try:
            patch_facing_sector(current,entry,row['pc'],row['values'])
            row['effective_supported']=True;row['effective_reason']=None
        except NativeError as error:
            row['effective_supported']=False;row['effective_reason']=str(error)
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC facing inspection')
    return dict(schema_version='legaia.npc-facing-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_dispatch='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC facing review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['facing'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('facing', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC facing entry is not qualified by its script donor')
    qualify(project,proposed,request['entries'])
    _, changes = project._facing_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC facing review')
    return dict(schema_version='legaia.npc-facing-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-facing-targets.v1')),
                gameplay_verified=False, runtime_dispatch='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC facing Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC facing changed; review again')
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
            raise ProjectError('NPC facing allocation belongs to another scene')
        if 'facing' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['facing'])))
    return patch_allocated_facing(context, candidate, allocations, requests) if requests else (candidate, None)


def patch_allocated_facing(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for facing_id,values in sorted(entries.items()):
            target=targets[facing_id];relative=target['decoded_byte_offset']-source_offset;pc=target['pc']
            _,changes=patch_facing_sector(source_record,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Only dispatch/opcode bytes are immutable here: composed movement may
            # already have changed NPC_RUN X/Z and its move selector.
            header_end=pc+(2 if target['target_context'] is not None else 1)+(target['mnemonic']=='NPC_RUN')
            if clone[pc:header_end]!=source_record[pc:header_end]:
                raise ProjectError('NPC facing dispatch/opcode preimage differs from source')
            if target['mnemonic']=='CAM_CFG' and clone[relative+1]!=source_record[relative+1]:
                raise ProjectError('NPC facing CAM_CFG mode differs from source')
            if clone[relative]!=source_record[relative]:
                raise ProjectError('NPC facing operand preimage differs from source')
            _,current_changes=patch_facing_sector(clone,entry,pc,values,base_offset=start)
            if len(changes)!=len(current_changes):raise ProjectError('NPC facing candidate instruction differs from source')
            for change,current in zip(changes,current_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte','before_sector','after_sector')):
                    raise ProjectError('NPC facing candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length or change['before_byte']&PRESERVATION_MASK!=change['after_byte']&PRESERVATION_MASK:
                    raise ProjectError('NPC facing spans overlap, escape their clone or change upper flags')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,facing_id=facing_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC facing changed MAN structure')
    return result,dict(schema_version='legaia.npc-facing-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_facing_nibbles_only',gameplay_verified=False,runtime_dispatch='not_asserted',initial_heading='not_asserted',npc_placement_changed=False)
