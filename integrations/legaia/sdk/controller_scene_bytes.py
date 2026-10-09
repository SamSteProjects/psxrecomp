"""Reviewed project-local controller scene-state byte operands; no live scene-state byte writes."""
from copy import deepcopy
from hashlib import sha256
import re
from .project import ProjectError, digest
from importer.core import ImportError as RetailImportError
from importer.controller_scene_bytes import ControllerSceneByteAuthoringContext, validate_scene_byte_values
from .controller_source_report import controller_report as _report

COMPONENT='ControllerSceneBytes'
SCHEMA='legaia.controller-scene-bytes.v1'


def validate(project,owner,value):
    from .controller_system_flags import scene_document
    scene_document(project,owner)
    if (not isinstance(value,dict) or set(value)!={'source_record_sha256','entries'} or
            not isinstance(value['source_record_sha256'],str) or re.fullmatch('[a-f0-9]{64}',value['source_record_sha256']) is None or
            not isinstance(value['entries'],dict) or not 1<=len(value['entries'])<=1024):
        raise ProjectError('Controller scene-state byte requests require a source record hash and bounded entries')
    prefix=owner.replace('scene://','script://',1)+'/scene-byte/'
    for identity,fields in value['entries'].items():
        if not isinstance(identity,str) or re.fullmatch(re.escape(prefix)+r'[a-f0-9]{4}',identity) is None:
            raise ProjectError('Controller scene-state byte request belongs to another source owner')
        try:validate_scene_byte_values(fields)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    return deepcopy(value)


def compose(source,current,entries):
    context=ControllerSceneByteAuthoringContext(source)
    _,changes=context.patch(entries)
    result=bytearray(current)
    if len(result)!=len(source._man):raise RetailImportError('Controller scene-state byte composition changed MAN extent')
    for change in changes:
        at=change['decoded_byte_offset']
        if result[at:at+1].hex()!=change['before_hex']:
            raise RetailImportError('Controller scene-state byte composition overlaps another authored operand')
        result[at:at+1]=bytes.fromhex(change['after_hex'])
    return bytes(result)


def _prepare(project,owner):
    from .controller_system_flags import prepare
    key,selectors,offset,record,entry,components,current,_=prepare(project,owner)
    context=ControllerSceneByteAuthoringContext(selectors._source)
    return key,selectors,context,offset,record,entry,components,current,context.options(owner)


def snapshot(project,owner):
    from .controller_system_flags import state_key
    try:key,selectors,context,offset,record,entry,components,current,options=_prepare(project,owner)
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    entries=components.get(COMPONENT,{}).get('entries',{})
    targets=[]
    for target in options['targets']:
        at=target['decoded_byte_offset']
        targets.append(dict(deepcopy(target),authored_values=deepcopy(entries.get(target['semantic_id'])),
                            current_values=dict(value=current[at])))
    if key!=state_key(project):raise ProjectError('Controller scene-state byte source changed during inspection')
    return dict(schema_version=SCHEMA,owner_id=owner,state_key=key,source_record_sha256=sha256(record).hexdigest(),
        current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),source=options['source'],
        source_report=_report(owner,context._man,offset,record,entry,context._source),current_report=_report(owner,current,offset,record,entry,context._source,components.get('ControllerSystemFlags',{}).get('entries',{})),
        targets=targets,supported=bool(targets),reason=options['reason'],limitations=options['limitations']+[
            'Project Review/Apply, history and persistence support encoded operands. Native Build serializes qualified operands; editor controls remain pending; runtime byte meaning/effects and gameplay remain unverified.'],gameplay_verified=False)


def review(project,owner,operand,value):
    from .controller_system_flags import compose as compose_controller,state_key
    if value is not None:
        try:validate_scene_byte_values(value)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    try:
        key,selectors,context,offset,record,entry,components,current,options=_prepare(project,owner)
        target=next((t for t in options['targets'] if t['semantic_id']==operand),None)
        if target is None:raise ProjectError('Choose a source-qualified controller scene-state byte request')
        entries=deepcopy(components.get(COMPONENT,{}).get('entries',{}))
        if value is None or value==target['values']:entries.pop(operand,None)
        else:entries[operand]=deepcopy(value)
        proposed=deepcopy(components)
        if entries:proposed[COMPONENT]=validate(project,owner,dict(source_record_sha256=sha256(record).hexdigest(),entries=entries))
        else:proposed.pop(COMPONENT,None)
        candidate=compose_controller(selectors,owner,proposed)
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    differences=[i for i,(a,b) in enumerate(zip(current,candidate)) if a!=b]
    if any(i not in range(target['decoded_byte_offset'],target['decoded_byte_offset']+1) for i in differences):
        raise ProjectError('Controller scene-state byte Review changed unrelated source bytes')
    proof=dict(owner_id=owner,operand_id=operand,value=deepcopy(value),state_key=key,source_record_sha256=sha256(record).hexdigest(),
        current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),proposed_record_sha256=sha256(candidate[offset:offset+len(record)]).hexdigest(),proposed=proposed)
    if key!=state_key(project):raise ProjectError('Controller scene-state byte source changed during Review')
    return dict(schema_version=SCHEMA,**proof,review_key=digest(proof),source_report=_report(owner,context._man,offset,record,entry,context._source),
        current_report=_report(owner,current,offset,record,entry,context._source,components.get('ControllerSystemFlags',{}).get('entries',{})),proposed_report=_report(owner,candidate,offset,record,entry,context._source,components.get('ControllerSystemFlags',{}).get('entries',{})),
        changed_decoded_byte_offsets=differences,no_op=components==proposed,native_bytes_changed=current!=candidate,
        project_changed=False,gameplay_verified=False)


def apply(project,command):
    if set(command)!={'type','entity_id','operand_id','value','review_key'} or command['type']!='set_controller_scene_byte':
        raise ProjectError('Controller scene-state byte Apply requires exact reviewed inputs')
    result=review(project,command['entity_id'],command['operand_id'],command['value'])
    if result['review_key']!=command['review_key']:raise ProjectError('Controller scene-state byte source or draft changed; review again')
    if result['no_op']:raise ProjectError('Controller scene-state byte request has no authored change')
    owner=command['entity_id'];before=deepcopy(project.overrides.get(owner));after=result['proposed'] or None
    if after is None:project.overrides.pop(owner,None)
    else:project.overrides[owner]=deepcopy(after)
    project.undo_stack.append(dict(entity_id=owner,before=before,after=deepcopy(after)));project.redo_stack.clear()
