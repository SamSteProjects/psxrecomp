"""Reviewed persistent controller branches with immutable Retail ownership."""
from copy import deepcopy
from hashlib import sha256
import re
from .project import ProjectError,digest
from importer.core import ImportError as RetailImportError
from importer.branch_authoring import validate_branch_values
from importer.controller_branches import ControllerBranchAuthoringContext

COMPONENT='ControllerBranches'
SCHEMA='legaia.controller-branches.v1'


def validate(project,owner,value):
    from .controller_system_flags import scene_document
    scene_document(project,owner)
    if not isinstance(value,dict) or set(value)!={'source_record_sha256','entries'} or not isinstance(value['source_record_sha256'],str) or re.fullmatch('[a-f0-9]{64}',value['source_record_sha256']) is None or not isinstance(value['entries'],dict) or not 1<=len(value['entries'])<=1024:
        raise ProjectError('Controller branches require a source record hash and bounded entries')
    prefix=owner.replace('scene://','script://',1)+'/branch/'
    for identity,fields in value['entries'].items():
        if not isinstance(identity,str) or re.fullmatch(re.escape(prefix)+r'[a-f0-9]{4}',identity) is None:
            raise ProjectError('Controller branch belongs to another source owner')
        try:validate_branch_values(fields)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    return deepcopy(value)


def _prepare(project,owner):
    from .controller_system_flags import prepare,COMPONENT as SELECTORS
    key,selectors,offset,record,entry,components,current,_=prepare(project,owner)
    context=ControllerBranchAuthoringContext(selectors._source,system_selectors=components.get(SELECTORS,{}).get('entries',{}))
    return key,selectors,context,offset,record,components,current,context.options(owner)


def _targets(options,components):
    entries=components.get(COMPONENT,{}).get('entries',{})
    return [dict(deepcopy(row),authored_value=deepcopy(entries.get(row['semantic_id'])),
                 current_target_pc=entries.get(row['semantic_id'],row['values'])['target_pc']) for row in options['targets']]


def snapshot(project,owner):
    from .controller_system_flags import state_key
    try:
        key,selectors,context,offset,record,components,current,options=_prepare(project,owner)
        report=context.inspect_owner(owner,current) if options['supported'] else None
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    if key!=state_key(project):raise ProjectError('Controller branch source changed during inspection')
    return dict(schema_version=SCHEMA,owner_id=owner,state_key=key,source_record_sha256=sha256(record).hexdigest(),
        current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),source_report=options['inspection'],current_report=report,
        targets=_targets(options,components),destinations=deepcopy(options['destinations']),supported=options['supported'],
        reason=options['reason'],limitations=options['limitations'],gameplay_verified=False)


def review(project,owner,operand,value):
    from .controller_system_flags import compose,state_key
    if value is not None:
        try:validate_branch_values(value)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    try:
        key,selectors,context,offset,record,components,current,options=_prepare(project,owner)
        target=next((row for row in options['targets'] if row['semantic_id']==operand),None)
        if target is None:raise ProjectError('Choose a source-qualified controller branch')
        entries=deepcopy(components.get(COMPONENT,{}).get('entries',{}))
        if value is None or value==target['values']:entries.pop(operand,None)
        else:entries[operand]=deepcopy(value)
        proposed=deepcopy(components)
        if entries:proposed[COMPONENT]=validate(project,owner,dict(source_record_sha256=sha256(record).hexdigest(),entries=entries))
        else:proposed.pop(COMPONENT,None)
        candidate=compose(selectors,owner,proposed)
        current_report=context.inspect_owner(owner,current);proposed_report=context.inspect_owner(owner,candidate)
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    differences=[i for i,(a,b) in enumerate(zip(current,candidate)) if a!=b]
    if any(i not in (target['decoded_byte_offset'],target['decoded_byte_offset']+1) for i in differences):
        raise ProjectError('Controller branch Review changed unrelated source bytes')
    current_pcs={r['pc'] for r in current_report['instructions']+current_report['dialogues']}
    proposed_pcs={r['pc'] for r in proposed_report['instructions']+proposed_report['dialogues']}
    proof=dict(owner_id=owner,operand_id=operand,value=deepcopy(value),state_key=key,source_record_sha256=sha256(record).hexdigest(),
        current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),proposed_record_sha256=sha256(candidate[offset:offset+len(record)]).hexdigest(),proposed=proposed)
    if key!=state_key(project):raise ProjectError('Controller branch source changed during Review')
    return dict(schema_version=SCHEMA,**proof,review_key=digest(proof),source_report=options['inspection'],current_report=current_report,
        proposed_report=proposed_report,targets=_targets(options,components),destinations=deepcopy(options['destinations']),
        changed_decoded_byte_offsets=differences,newly_unreachable_source_pcs=sorted(current_pcs-proposed_pcs),newly_reached_source_pcs=sorted(proposed_pcs-current_pcs),
        no_op=components==proposed,native_bytes_changed=current!=candidate,project_changed=False,gameplay_verified=False)


def apply(project,command):
    if set(command)!={'type','entity_id','operand_id','value','review_key'}:raise ProjectError('Controller branch Apply requires exact reviewed inputs')
    result=review(project,command['entity_id'],command['operand_id'],command['value'])
    if result['review_key']!=command['review_key']:raise ProjectError('Controller branch source or draft changed; review again')
    if result['no_op']:raise ProjectError('Controller branch has no authored change')
    owner=command['entity_id'];before=deepcopy(project.overrides.get(owner));after=result['proposed'] or None
    if after is None:project.overrides.pop(owner,None)
    else:project.overrides[owner]=deepcopy(after)
    project.undo_stack.append(dict(entity_id=owner,before=before,after=deepcopy(after)));project.redo_stack.clear()
