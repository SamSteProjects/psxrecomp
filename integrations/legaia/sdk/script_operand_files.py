"""Source-bound authored operand metadata; existing fixed-width editors remain authoritative."""
from copy import copy,deepcopy
import json
from .project import ProjectError,digest

SCHEMA='legaia.script-operand-file.v1'
ANIMATION_SCHEMA='legaia.script-operand-file.v2'

def file_schema(components):
    return ANIMATION_SCHEMA if 'ScriptAnimationOperands' in components else SCHEMA

MAX_BYTES=65536
KINDS={
    'ScriptAnimationOperands':('apply_script_animation_operands','animation_operand_id'),
    'ScriptBranches':('set_branch','branch_id'),
    'ScriptMovement':('set_movement_target','movement_id'),
    'ScriptFacing':('set_facing_target','facing_id'),
    'ScriptFlags':('set_flag_bit','flag_id'),
    'ScriptWaits':('set_wait_target','wait_id'),
    'ScriptEffectColors':('set_effect_color_target','effect_color_id'),
    'ScriptModelSelectors':('set_model_selector_target','model_selector_id'),
    'Transitions':('set_transition_entry','transition_id'),
}

def parse_json(content):
    if not isinstance(content,str):raise ProjectError('Operand file must be UTF-8 JSON')
    try:
        if len(content.encode('utf-8'))>MAX_BYTES:raise ProjectError('Operand file exceeds 64 KiB')
        def pairs(rows):
            result={}
            for key,value in rows:
                if key in result:raise ProjectError('Duplicate operand file key')
                result[key]=value
            return result
        def constant(_):raise ProjectError('Nonfinite operand file value')
        value=json.loads(content,object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,RecursionError,UnicodeError) as exc:raise ProjectError('Invalid operand JSON') from exc
    return value

def parse(content):
    value=parse_json(content)
    if not isinstance(value,dict) or set(value)!={'schema_version','scene_id','source_import_sha256','owner_id','components'} or value['schema_version'] not in (SCHEMA,ANIMATION_SCHEMA):
        raise ProjectError('Unsupported operand file fields or schema')
    if not isinstance(value['source_import_sha256'],str) or len(value['source_import_sha256'])!=64 or any(c not in '0123456789abcdef' for c in value['source_import_sha256']):
        raise ProjectError('Operand file requires an imported source hash')
    components=value['components']
    if not isinstance(components,dict) or not set(components)<=set(KINDS):raise ProjectError('Unsupported operand component')
    if value['schema_version']!=file_schema(components):raise ProjectError('Operand file version differs from its authored components')
    total=0
    for component in components.values():
        if not isinstance(component,dict) or set(component)!={'entries'} or not isinstance(component['entries'],dict) or not component['entries']:
            raise ProjectError('Operand component requires nonempty entries')
        total+=len(component['entries'])
        if any(not isinstance(key,str) or len(key)>512 or not isinstance(row,dict) for key,row in component['entries'].items()):raise ProjectError('Invalid operand entry')
    if total>256:raise ProjectError('Operand file is limited to 256 instruction entries')
    return value

def _source(project,owner):
    from .resources import _verify
    document=project._dialogue_document(owner)
    scene='scene://'+document['scene']['name']
    if scene!=project.active_scene:raise ProjectError('Open the operand owner source scene first')
    _verify(project,document)
    return scene,digest(document)

def review(project,owner,content):
    from importer.pipeline import _disc_context
    if not project.disc_path:raise ProjectError('Operand transfer requires the project user-owned disc')
    value=parse(content)
    if value['owner_id']!=owner:raise ProjectError('Operand file belongs to a different script owner')
    before=deepcopy(project.overrides.get(owner));staged=copy(project)
    staged.overrides=deepcopy(project.overrides);staged.undo_stack=[];staged.redo_stack=[];staged.mode='edit'
    with _disc_context(project.disc_path):
        scene,source=_source(project,owner)
        staged._dialogue_context(owner).options(owner)
        if value['scene_id']!=scene or value['source_import_sha256']!=source:raise ProjectError('Operand file differs from imported source')
        rows=[]
        for component in sorted(value['components'], key=lambda key: (key == 'ScriptBranches', key)):
            kind,key_field=KINDS[component]
            for identifier,values in sorted(value['components'][component]['entries'].items()):
                previous=deepcopy((before or {}).get(component,{}).get('entries',{}).get(identifier))
                if component == 'ScriptAnimationOperands':
                    from .script_animation_operands import review as animation_review
                    inspected,_=animation_review(staged,owner,identifier,values)
                    staged.command(dict(type=kind,entity_id=owner,animation_operand_id=identifier,values=values,review_key=inspected['review']['review_key']))
                elif component == 'ScriptBranches':
                    from .script_branches import review as branch_review
                    inspected, _ = branch_review(staged, owner, identifier, values)
                    if not inspected['review']['no_op']:
                        staged.command(dict(type=kind, entity=owner, branch_id=identifier, value=values, review_key=inspected['review']['review_key']))
                else:
                    staged.command(dict(type=kind,entity_id=owner,**{key_field:identifier},values=values))
                actual = deepcopy(staged.overrides.get(owner, {}).get(component, {}).get('entries', {}).get(identifier))
                rows.append(dict(component=component,operand_id=identifier,before=previous,after=deepcopy(values),changed=previous!=actual))
        if project.overrides.get(owner)!=before:raise ProjectError('Script owner changed during review')
    after=deepcopy(staged.overrides.get(owner))
    report=dict(schema_version='legaia.script-operand-review.v1',owner_id=owner,scene_id=scene,source_import_sha256=source,entries=rows,change_count=sum(row['changed'] for row in rows),before=before,after=after,
        limitations=['Each supplied entry replaces its authored operand fields. Other entries and components remain unchanged.','No instructions, dialogue, record layout or runtime state are transferred; qualified branch words may change encoded edges. Execution and gameplay remain unverified.'])
    report['review_key']=digest(dict(project_root=str(project.root),file=value,before=before,after=after))
    return report

def export_file(project,owner):
    from importer.pipeline import _disc_context
    if not project.disc_path:raise ProjectError('Operand transfer requires the project user-owned disc')
    with _disc_context(project.disc_path):scene,source=_source(project,owner)
    components={key:deepcopy(value) for key,value in project.overrides.get(owner,{}).items() if key in KINDS}
    value=dict(schema_version=file_schema(components),scene_id=scene,source_import_sha256=source,owner_id=owner,components=components)
    content=json.dumps(value,ensure_ascii=True,indent=2)+'\n'
    review(project,owner,content)
    return value

def apply(project,command):
    if set(command)!={'type','entity_id','content','review_key'}:raise ProjectError('Operand import requires owner, file and reviewed key only')
    report=review(project,command['entity_id'],command['content'])
    if command['review_key']!=report['review_key']:raise ProjectError('Operand file or owner changed since review')
    if report['before']==report['after']:return
    owner=report['owner_id']
    if report['after'] is None:project.overrides.pop(owner,None)
    else:project.overrides[owner]=deepcopy(report['after'])
    project.undo_stack.append(dict(entity_id=owner,before=report['before'],after=deepcopy(report['after'])))
    project.redo_stack.clear()
