"""Source-qualified flag bit operands owned by final appended NPC records.

Only bit indices serialize here; runtime variables, story meaning and execution
remain unknown. The imported flag adapter owns width and side-effect exclusions.
"""
from copy import deepcopy
from hashlib import sha256
from importer.flag_authoring import patch_flag_bit
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def validate(project, draft):
    if 'flags' not in draft:
        return
    value = draft['flags']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC flags belong to their script donor; clear flags before changing donor')
    project._validate_flags(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC flags require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._flag_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('flags', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC flags are not source-qualified')
    context.patch(entries)
    offset,record,_=context._source.verified_record(draft['donor_entity_id'])
    for row in options['targets']:
        row['before_raw']=record[row['decoded_byte_offset']-offset]
        row['preservation_mask']=224
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC flag inspection')
    return dict(schema_version='legaia.npc-flags-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_variable_identity='not_asserted', story_meaning='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC flag review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['flags'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('flags', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC flag entry is not qualified by its script donor')
    _, changes = project._flag_context(draft['donor_entity_id']).patch(request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC flag review')
    return dict(schema_version='legaia.npc-flags-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-flag-targets.v1')),
                gameplay_verified=False, runtime_variable_identity='not_asserted', story_meaning='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC flag Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC flags changed; review again')
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
            raise ProjectError('NPC flag allocation belongs to another scene')
        if 'flags' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['flags'])))
    return patch_allocated_flags(context, candidate, allocations, requests) if requests else (candidate, None)



def patch_allocated_flags(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for flag_id,values in sorted(entries.items()):
            target=targets[flag_id];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset
            _,changes=patch_flag_bit(source_record,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Bind the full opcode, any extended context and complete operand,
            # even for a source-identical no-op request.
            if clone[pc:relative+1]!=source_record[pc:relative+1]:
                raise ProjectError('NPC flag dispatch or operand preimage differs from source')
            _,current_changes=patch_flag_bit(clone,entry,pc,values,base_offset=start)
            if len(changes)!=len(current_changes):raise ProjectError('NPC flag candidate instruction differs from source')
            for change,current in zip(changes,current_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte','before_bit','after_bit')):
                    raise ProjectError('NPC flag candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length or change['before_byte']&0xe0!=change['after_byte']&0xe0:
                    raise ProjectError('NPC flag spans overlap, escape their clone or change upper bits')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,flag_id=flag_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC flags changed MAN structure')
    return result,dict(schema_version='legaia.npc-flags-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_flag_bit_indices_only',gameplay_verified=False,runtime_variable_identity='not_asserted',story_meaning='not_asserted',npc_placement_changed=False)
