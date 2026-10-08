"""Native NPC-owned named scene-change arrival bytes; no runtime simulation.

Only qualified SCENE_CHANGE entry X/Z/direction bytes serialize here. Names and
complete dispatch/preimages remain bound to the imported donor instruction.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.transition_authoring import patch_transition_entry
from importer.script_inspection import _instruction
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def validate(project, draft):
    if 'transitions' not in draft:
        return
    value=draft['transitions']
    if not isinstance(value,dict) or set(value)!={'donor_entity_id','entries'} or value['donor_entity_id']!=draft['donor_entity_id']:
        raise ProjectError('NPC transitions belong to their script donor; clear transitions before changing donor')
    project._validate_transitions(draft['donor_entity_id'],{'entries':value['entries']})
    project._transition_context(draft['donor_entity_id']).patch(value['entries'])


def source(project, identifier):
    draft=project.actor_drafts.get(identifier) if isinstance(identifier,str) else None
    if project.mode!='edit' or not isinstance(draft,dict) or draft['scene_id']!=project.active_scene:
        raise ProjectError('NPC transitions require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier,draft);key=source_key(project)
    context=project._transition_context(draft['donor_entity_id'])
    options=context.options(draft['donor_entity_id'])
    entries=draft.get('transitions',{}).get('entries',{})
    context.patch(entries)
    from importer.transition_authoring import reference_entry_interpretation
    for row in options['transitions']:
        record_offset,record,_=context._source.verified_record(draft['donor_entity_id'])
        instruction=_instruction(record,row['pc'])
        row.update(mnemonic=instruction['mnemonic'],target_context=instruction['target_context'],
            instruction_length=instruction['length'],raw_instruction_hex=instruction['raw_hex'],record_byte_offset=record_offset)
        row['authored_values']=deepcopy(entries.get(row['semantic_id']))
        row['effective_values']=dict(row['values'],**entries.get(row['semantic_id'],{}))
        row['effective_interpretation']=reference_entry_interpretation(row['effective_values'])
    if source_key(project)!=key:raise ProjectError('Project changed during NPC transition inspection')
    return dict(schema_version='legaia.npc-transitions-source.v1',entity_id=identifier,
        scene_id=draft['scene_id'],project_source_key=key,draft=deepcopy(draft),options=options,
        gameplay_verified=False,transition_activation='not_asserted',destination_name_changed=False)


def review(project, request):
    if not isinstance(request,dict) or set(request)!={'entity_id','entries'} or not isinstance(request['entries'],dict):
        raise ProjectError('NPC transition review requires identity and complete typed entries')
    report=source(project,request['entity_id']);draft=report['draft'];proposed=deepcopy(draft)
    if request['entries']:
        proposed['transitions']=dict(donor_entity_id=draft['donor_entity_id'],entries=deepcopy(request['entries']))
    else:proposed.pop('transitions',None)
    project._validate_actor_draft(request['entity_id'],proposed)
    _,changes=project._transition_context(draft['donor_entity_id']).patch(request['entries'])
    # Qualify composition with existing script fields, including branch changes.
    from .npc_current_script import proposed_inspection
    inspection=proposed_inspection(project,request['entity_id'],proposed)
    if source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during NPC transition review')
    return dict(schema_version='legaia.npc-transitions-review.v1',entity_id=request['entity_id'],
        project_source_key=report['project_source_key'],request=deepcopy(request),current=draft,
        proposed=proposed,changes=changes,inspection=inspection,
        review_key=digest(dict(source=report['project_source_key'],request=request,algorithm='npc-transition-arrivals.v1')),
        gameplay_verified=False,transition_activation='not_asserted',destination_name_changed=False)


def apply(project, command):
    if set(command)!={'type','entity_id','entries','review_key'}:
        raise ProjectError('NPC transition Apply requires exact reviewed fields')
    report=review(project,{k:command[k] for k in ('entity_id','entries')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC transitions changed; review again')
    if report['current']==report['proposed']:return
    project.actor_drafts[command['entity_id']]=deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts',entity_id=command['entity_id'],before=report['current'],after=deepcopy(report['proposed'])))
    project.redo_stack.clear()


def patch_project(project, scene_id, context, candidate, allocations):
    requests=[]
    for row in allocations['drafts']:
        draft=project.actor_drafts[row['draft_id']]
        if draft['scene_id']!=scene_id:raise ProjectError('NPC transition allocation belongs to another scene')
        if 'transitions' in draft:
            validate(project,draft)
            requests.append(dict(draft_id=row['draft_id'],**deepcopy(draft['transitions'])))
    return patch_allocated_transitions(context,candidate,allocations,requests) if requests else (candidate,None)


def patch_allocated_transitions(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests,target_key='transitions')
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];source=item['source_record'];entry=item['entry'];start=item['start'];length=item['length']
        for identifier,values in sorted(item['entries'].items()):
            target=item['targets'][identifier];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset;node=_instruction(source,pc)
            _,source_changes=patch_transition_entry(source,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Bind all source arguments even for partial/no-op requests: an
            # edited destination or context must never be silently inherited.
            if relative+3!=pc+node['length'] or clone[pc:relative+3]!=source[pc:relative+3]:
                raise ProjectError('NPC transition instruction, destination or arrival preimage differs from source')
            _,clone_changes=patch_transition_entry(clone,entry,pc,values,base_offset=start)
            if len(source_changes)!=len(clone_changes):raise ProjectError('NPC transition candidate instruction differs from source')
            for change,current in zip(source_changes,clone_changes):
                if any(change[k]!=current[k] for k in ('field','pc','record_relative_byte_offset','before_byte','after_byte')):
                    raise ProjectError('NPC transition candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length:raise ProjectError('NPC transition bytes overlap or escape their clone')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,transition_id=identifier,record_index=item['record_index'],mnemonic=node['mnemonic'],target_context=node['target_context'],destination=target['destination'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,byte_length=1))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC transitions changed MAN structure')
    return result,dict(schema_version='legaia.npc-transitions-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_named_transition_arrival_bytes_only',gameplay_verified=False,transition_activation='not_asserted',destination_name_changed=False,npc_placement_changed=False)
