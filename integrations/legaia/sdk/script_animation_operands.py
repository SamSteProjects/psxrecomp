"""Source-owned animation argument Review/Apply; no inferred clip bindings."""
from copy import deepcopy
from hashlib import sha256
import re
from importer.animation_operand_authoring import AnimationOperandAuthoringContext, SPECS, validate_animation_operand_values
from importer.core import ImportError
from .project import ProjectError, digest
from .script_branches import state_key

COMPONENT = 'ScriptAnimationOperands'
SCHEMA = 'legaia.script-animation-operands.v1'


def validate(project, owner, value):
    project._dialogue_document(owner)
    if (not isinstance(value, dict) or set(value) != {'entries'} or
            not isinstance(value['entries'], dict) or not 1 <= len(value['entries']) <= 1024):
        raise ProjectError('Animation script operands require a bounded nonempty entry collection')
    prefix='script://'+owner.removeprefix('scene://')+'/animation-operands/'
    for key, fields in value['entries'].items():
        if not isinstance(key,str) or not re.fullmatch(re.escape(prefix)+r'[0-9a-f]{4}',key):
            raise ProjectError('Animation operand identity must belong to its imported source owner')
        mnemonic=next((name for name,spec in SPECS.items() if isinstance(fields,dict) and set(fields)=={k for k,_ in spec}),None)
        try: validate_animation_operand_values(mnemonic,fields)
        except ImportError as error: raise ProjectError(str(error)) from error
    return deepcopy(value)


def context(project,owner):
    return AnimationOperandAuthoringContext(project._dialogue_context(owner))


def options(project,owner):
    result=context(project,owner).options(owner)
    authored=project.overrides.get(owner,{}).get(COMPONENT,{}).get('entries',{})
    known=set()
    for target in result['targets']:
        key=target['semantic_id'];known.add(key)
        target['authored_values']=deepcopy(authored.get(key))
        target['effective_values']=deepcopy(authored.get(key,target['values']))
        validate_animation_operand_values(target['mnemonic'],target['effective_values'])
    result.update(schema_version=SCHEMA,owner_id=owner,state_key=state_key(project),
                  unresolved_overrides=sorted(set(authored)-known),gameplay_verified=False)
    return result


def compose(context, baseline, working, entries, previous=(), *, appended=False):
    """Hold complete requested instructions, including no-ops, against other edits."""
    if context._man != baseline:
        raise ProjectError('Animation operand composition differs from verified MAN source')
    if appended:
        candidate,audit=context.patch_appended(working,entries)
    else:
        if len(working)!=len(baseline):raise ProjectError('Animation operand composition changed MAN length')
        candidate,audit=context.patch(entries,original=baseline)
        occupied={i for row in previous for i in range(row['decoded_byte_offset'],row['decoded_byte_offset']+row.get('byte_length',1))}
        spans=set()
        for _,_,offset,record,_,pc,node,_,_ in context._requests(entries):
            at=offset+pc;size=node['length'];span=set(range(at,at+size))
            if span & (occupied|spans) or working[at:at+size]!=record[pc:pc+size]:
                raise ProjectError('Animation script instruction overlaps another authored MAN edit')
            spans.update(span)
        result=bytearray(working)
        for row in audit:
            at=row['decoded_byte_offset'];size=row['byte_length']
            result[at:at+size]=candidate[at:at+size]
        candidate=bytes(result)
    for row in audit:
        row.update(semantic_id=row['owner_id'],record_index=int(row['owner_id'].rsplit('/',1)[1]),
                   scope='script-animation-operands-only')
    return candidate,audit


def _current(source,owner,components):
    from .script_branches import _compose
    from importer.branch_authoring import BranchAuthoringContext
    plain=_compose(source,owner,components)
    branches=components.get('ScriptBranches',{}).get('entries',{})
    if not branches:return plain
    ctx=BranchAuthoringContext(source,system_selectors=components.get('ScriptSystemFlags',{}).get('entries',{}))
    return ctx.patch_composed(plain,branches)[0]


def review(project,owner,key,values):
    if project.mode!='edit':raise ProjectError('Animation script authoring requires Edit mode')
    document=project._dialogue_document(owner)
    if document['scene']['semantic_id']!=project.active_scene:
        raise ProjectError('Animation script authoring requires its active imported scene')
    initial_key=state_key(project)
    ctx=context(project,owner);source=ctx._source
    report=ctx.options(owner);target=next((row for row in report['targets'] if row['semantic_id']==key),None)
    if target is None:raise ProjectError('Animation instruction is not qualified by its source owner')
    if values is not None:
        validate(project,owner,{'entries':{key:values}})
        validate_animation_operand_values(target['mnemonic'],values)
    components=deepcopy(project.overrides.get(owner,{}));before=deepcopy(components.get(COMPONENT))
    entries=deepcopy((before or {}).get('entries',{}))
    if values is None or values==target['values']:entries.pop(key,None)
    else:entries[key]=deepcopy(values)
    after={'entries':entries} if entries else None
    current=_current(source,owner,components)
    if after:components[COMPONENT]=after
    else:components.pop(COMPONENT,None)
    proposed=_current(source,owner,components)
    offset,record,entry=source.verified_record(owner)
    size=len(record);current_record=current[offset:offset+size];proposed_record=proposed[offset:offset+size]
    changed=[offset+i for i,(a,b) in enumerate(zip(current_record,proposed_record)) if a!=b]
    if state_key(project)!=initial_key:raise ProjectError('Animation authoring inputs changed during Review')
    proof=dict(state_key=initial_key,owner_id=owner,animation_operand_id=key,values=values,
               source_man_sha256=sha256(source._man).hexdigest(),current_record_sha256=sha256(current_record).hexdigest(),
               proposed_record_sha256=sha256(proposed_record).hexdigest(),component=after)
    from importer.script_inspection import inspect_record
    result=dict(schema_version=SCHEMA,owner_id=owner,state_key=initial_key,source=report['source'],
                target=deepcopy(target),limitations=report['limitations'],gameplay_verified=False,
                current_report=inspect_record(current_record,entry),proposed_report=inspect_record(proposed_record,entry),
                review=dict(review_key=digest(proof),animation_operand_id=key,values=deepcopy(values),
                            no_op=before==after,changed_byte_offsets=changed,
                            current_instruction_hex=current_record[target['pc']:target['pc']+target['instruction_length']].hex(),
                            proposed_instruction_hex=proposed_record[target['pc']:target['pc']+target['instruction_length']].hex(),
                            current_record_sha256=proof['current_record_sha256'],proposed_record_sha256=proof['proposed_record_sha256']))
    return result,after


def apply(project,command):
    if set(command)!={'type','entity_id','animation_operand_id','values','review_key'}:
        raise ProjectError('Animation operand Apply requires exact reviewed owner, target, values and key')
    owner=command['entity_id'];result,after=review(project,owner,command['animation_operand_id'],command['values'])
    if command['review_key']!=result['review']['review_key'] or state_key(project)!=result['state_key']:
        raise ProjectError('Animation authoring state changed; Review again')
    before=deepcopy(project.overrides.get(owner));components=deepcopy(before or {})
    if after:components[COMPONENT]=after
    else:components.pop(COMPONENT,None)
    components=components or None
    if before==components:return
    if components is None:project.overrides.pop(owner,None)
    else:project.overrides[owner]=components
    project.undo_stack.append(dict(entity_id=owner,before=before,after=deepcopy(components)))
    project.redo_stack.clear()
