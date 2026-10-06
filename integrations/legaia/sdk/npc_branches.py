"""Independent source-qualified branch words in final appended NPC records.

Branch edits are composed last: original instructions and message boundaries stay
qualified even when changed edges make some of them unreachable. No VM executes.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError, digest
from .project_copy import source_key


def effective_man(project,draft,context):
    candidate=bytearray(context._man);occupied=set()
    adapters=[('dialogue',project._dialogue_context,'runs'),('movement',project._movement_context,'entries'),('facing',project._facing_context,'entries'),('flags',project._flag_context,'entries'),('waits',project._wait_context,'entries')]
    for field,factory,key in adapters:
        if field not in draft:continue
        adapter=factory(draft['donor_entity_id'])
        if adapter._man!=context._man:raise ProjectError('NPC branch composition source snapshots differ')
        if field=='facing':
            from .npc_facing import qualify
            qualify(project,draft,draft[field][key],context=adapter)
        changed,_=adapter.patch(draft[field][key])
        for at,(before,after) in enumerate(zip(context._man,changed)):
            if before==after:continue
            if at in occupied:raise ProjectError('NPC branch composition overlaps other authored operands')
            occupied.add(at);candidate[at]=after
    return bytes(candidate)


def validate(project, draft):
    if 'branches' not in draft:
        return
    value = draft['branches']
    if not isinstance(value, dict) or set(value) != {'donor_entity_id', 'entries'} or value['donor_entity_id'] != draft['donor_entity_id']:
        raise ProjectError('NPC branches belong to their script donor; clear branches before changing donor')
    project._validate_branches(draft['donor_entity_id'], {'entries': value['entries']})


def source(project, identifier):
    draft = project.actor_drafts.get(identifier) if isinstance(identifier, str) else None
    if project.mode != 'edit' or not isinstance(draft, dict) or draft['scene_id'] != project.active_scene:
        raise ProjectError('NPC branches require an active-scene draft in Edit mode')
    project._validate_actor_draft(identifier, draft);key = source_key(project)
    context = project._branch_context(draft['donor_entity_id'])
    options = context.options(draft['donor_entity_id'])
    entries = draft.get('branches', {}).get('entries', {})
    if set(entries) - {r['semantic_id'] for r in options['targets']}:
        raise ProjectError('Current NPC branches are not source-qualified')
    context.patch_composed(effective_man(project,draft,context),entries)
    for row in options['targets']:
        row['authored_values'] = deepcopy(entries.get(row['semantic_id']))
        row['effective_values'] = deepcopy(entries.get(row['semantic_id'], row['values']))
    if source_key(project) != key:
        raise ProjectError('Project changed during NPC branch inspection')
    return dict(schema_version='legaia.npc-branches-source.v1', entity_id=identifier,
                scene_id=draft['scene_id'], project_source_key=key, draft=deepcopy(draft),
                options=options, gameplay_verified=False, runtime_termination='not_asserted')


def review(project, request):
    if not isinstance(request, dict) or set(request) != {'entity_id', 'entries'} or not isinstance(request['entries'], dict):
        raise ProjectError('NPC branch review requires identity and complete typed entries')
    report = source(project, request['entity_id']);draft = report['draft'];proposed = deepcopy(draft)
    if request['entries']:
        proposed['branches'] = dict(donor_entity_id=draft['donor_entity_id'], entries=deepcopy(request['entries']))
    else:
        proposed.pop('branches', None)
    project._validate_actor_draft(request['entity_id'], proposed)
    if set(request['entries']) - {r['semantic_id'] for r in report['options']['targets']}:
        raise ProjectError('NPC branch entry is not qualified by its script donor')
    context=project._branch_context(draft['donor_entity_id'])
    _, changes = context.patch_composed(effective_man(project,proposed,context),request['entries'])
    if source_key(project) != report['project_source_key']:
        raise ProjectError('Project changed during NPC branch review')
    return dict(schema_version='legaia.npc-branches-review.v1', entity_id=request['entity_id'],
                project_source_key=report['project_source_key'], request=deepcopy(request),
                current=draft, proposed=proposed, changes=changes,
                review_key=digest(dict(source=report['project_source_key'], request=request, algorithm='npc-branch-targets.v1')),
                gameplay_verified=False, runtime_termination='not_asserted')


def apply(project, command):
    if set(command) != {'type', 'entity_id', 'entries', 'review_key'}:
        raise ProjectError('NPC branch Apply requires exact reviewed fields')
    report = review(project, {k: command[k] for k in ('entity_id', 'entries')})
    if command['review_key'] != report['review_key']:
        raise ProjectError('NPC branches changed; review again')
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
            raise ProjectError('NPC branch allocation belongs to another scene')
        if 'branches' not in draft:
            continue
        validate(project, draft)
        requests.append(dict(draft_id=row['draft_id'], **deepcopy(draft['branches'])))
    return patch_allocated_branches(context, candidate, allocations, requests) if requests else (candidate, None)



def patch_allocated_branches(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];record=item['source_record'];start=item['start'];length=item['length']
        # The existing native adapter owns source graph and condition qualification.
        # Bind this clone to its immutable donor slot for that request only; never
        # derive source boundaries from authored or newly reached candidate bytes.
        rebound=bytearray(original);rebound[source_offset:source_offset+length]=output[start:start+length]
        patched,changes=context.patch_composed(bytes(rebound),item['entries'])
        clone=patched[source_offset:source_offset+length]
        allowed=set()
        for change in changes:
            relative=change['record_relative_byte_offset'];span=set(range(start+relative,start+relative+2))
            if not 0<=relative<=length-2 or span&occupied:
                raise ProjectError('NPC branch words overlap or escape their clone')
            occupied.update(span);allowed.update(range(relative,relative+2))
            changed_bytes=[dict(row,source_decoded_byte_offset=row['decoded_byte_offset'],decoded_byte_offset=start+row['decoded_byte_offset']-source_offset) for row in change['changed_bytes']]
            audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,record_index=item['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=start+relative,changed_bytes=changed_bytes))
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(output[start:start+length],clone))):
            raise ProjectError('NPC branch composition changed an unaudited clone byte')
        output[start:start+length]=clone
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC branch composition changed MAN structure')
    return result,dict(schema_version='legaia.npc-branches-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_branch_target_words_only',gameplay_verified=False,branch_activation='not_asserted',runtime_termination='not_asserted',npc_placement_changed=False)
