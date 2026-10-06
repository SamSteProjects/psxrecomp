"""Reviewed equal-span text edits owned by an appended NPC, never its donor."""
from copy import deepcopy
from .project import ProjectError, digest
from .project_copy import source_key

def validate(draft):
    from importer.dialogue_authoring import MAX_EDIT_RUNS, validate_run_id, validate_dialogue_text
    value=draft.get('dialogue')
    if 'dialogue' not in draft:return
    if not isinstance(value,dict) or set(value)!={'donor_entity_id','runs'} or value['donor_entity_id']!=draft['donor_entity_id']:
        raise ProjectError('NPC dialogue belongs to its recorded donor; clear dialogue before changing donor')
    if not isinstance(value['runs'],dict) or not 1<=len(value['runs'])<=MAX_EDIT_RUNS:
        raise ProjectError('NPC dialogue requires a bounded nonempty run collection')
    for run,text in value['runs'].items():
        validate_run_id(draft['donor_entity_id'],run);validate_dialogue_text(text)

def source(project,entity_id):
    draft=project.actor_drafts.get(entity_id) if isinstance(entity_id,str) else None
    if project.mode!='edit' or not isinstance(draft,dict) or draft['scene_id']!=project.active_scene:
        raise ProjectError('NPC dialogue requires an active-scene draft in Edit mode')
    project._validate_actor_draft(entity_id,draft);key=source_key(project)
    context=project._dialogue_context(draft['donor_entity_id'])
    options=context.options(draft['donor_entity_id']);runs=deepcopy(draft.get('dialogue',{}).get('runs',{}))
    context.patch(runs)
    for row in options['runs']:
        row['authored_text']=runs.get(row['semantic_id'])
        row['effective_text']=runs.get(row['semantic_id'],row['text']).ljust(row['byte_length'])
    if source_key(project)!=key:raise ProjectError('Project changed during NPC dialogue inspection')
    return dict(schema_version='legaia.npc-dialogue-source.v1',entity_id=entity_id,scene_id=draft['scene_id'],project_source_key=key,draft=deepcopy(draft),options=options,gameplay_verified=False,runtime_binding='not_asserted')

def review(project,request):
    if not isinstance(request,dict) or set(request)!={'entity_id','runs'} or not isinstance(request['runs'],dict):
        raise ProjectError('NPC dialogue review requires identity and complete run edits')
    report=source(project,request['entity_id']);draft=report['draft'];proposed=deepcopy(draft)
    if request['runs']:proposed['dialogue']=dict(donor_entity_id=draft['donor_entity_id'],runs=deepcopy(request['runs']))
    else:proposed.pop('dialogue',None)
    project._validate_actor_draft(request['entity_id'],proposed)
    context=project._dialogue_context(draft['donor_entity_id']);_,changes=context.patch(request['runs'])
    allowed={r['semantic_id'] for r in report['options']['runs']}
    if set(request['runs'])-allowed:raise ProjectError('NPC dialogue run is not supported by its donor')
    if source_key(project)!=report['project_source_key']:raise ProjectError('Project changed during NPC dialogue review')
    return dict(schema_version='legaia.npc-dialogue-review.v1',entity_id=request['entity_id'],project_source_key=report['project_source_key'],current=draft,proposed=proposed,changes=changes,review_key=digest(dict(source=report['project_source_key'],request=request,algorithm='npc-equal-span-dialogue.v1')),gameplay_verified=False,runtime_binding='not_asserted')

def apply(project,command):
    if set(command)!={'type','entity_id','runs','review_key'}:raise ProjectError('NPC dialogue Apply requires exact reviewed fields')
    report=review(project,{k:command[k] for k in ('entity_id','runs')})
    if command['review_key']!=report['review_key']:raise ProjectError('NPC dialogue changed; review again')
    if report['current']==report['proposed']:return
    project.actor_drafts[command['entity_id']]=deepcopy(report['proposed'])
    project.undo_stack.append(dict(target='actor_drafts',entity_id=command['entity_id'],before=report['current'],after=deepcopy(report['proposed'])))
    project.redo_stack.clear()

def patch_clones(project,scene_id,context,candidate,actor_audit):
    """Patch only audited appended spans; verify retail glyph preimages again."""
    from hashlib import sha256
    from importer.man_layout import read_man_layout
    layout=read_man_layout(candidate);records={(r['partition'],r['record_index']):r for r in layout['records']}
    output=bytearray(candidate);audit=[];used=set();total=0
    for allocation in actor_audit['drafts']:
        identifier=allocation['draft_id'];draft=project.actor_drafts[identifier]
        if draft['scene_id']!=scene_id:raise ProjectError('NPC dialogue scene differs from allocation')
        value=draft.get('dialogue')
        if not value:continue
        validate(draft);donor=draft['donor_entity_id']
        donor_offset,donor_bytes,_=context.verified_record(donor)
        _,changes=context.patch(value['runs'])
        record=records[(1,allocation['record_index'])]
        if record['byte_length']!=len(donor_bytes) or record['record_index']!=allocation['record_index'] or allocation['donor']['record_index']!=int(donor.rsplit('/',1)[1]):raise ProjectError('NPC dialogue allocation differs from donor record')
        for change in changes:
            relative=change['decoded_byte_offset']-donor_offset;size=change['byte_length'];offset=record['byte_offset']+relative
            if not 0<=relative<=len(donor_bytes)-size or any(i in used for i in range(offset,offset+size)) or candidate[offset:offset+size].hex()!=change['before_hex']:raise ProjectError('NPC dialogue clone span or glyph preimage differs')
            total+=size
            if total>65536:raise ProjectError('NPC dialogue exceeds the scene-wide 65536-byte span budget')
            used.update(range(offset,offset+size));output[offset:offset+size]=bytes.fromhex(change['after_hex'])
            audit.append(dict(change,draft_id=identifier,donor_entity_id=donor,record_index=record['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=offset))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC dialogue changed MAN record layout')
    return result,dict(changes=audit,source_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),gameplay_verified=False)
