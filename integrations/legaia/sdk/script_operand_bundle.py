"""Atomic scene-scoped script operand transfers through the existing single-owner service."""
from copy import copy,deepcopy
import json
from .project import ProjectError,digest
from .script_operand_files import SCHEMA as FILE_SCHEMA,KINDS,parse_json,parse as parse_file,review as review_file

SCHEMA='legaia.script-operand-bundle.v1'
CONTEXTS={'ScriptBranches':'_branch_context','ScriptMovement':'_movement_context','ScriptFacing':'_facing_context','ScriptFlags':'_flag_context','ScriptWaits':'_wait_context','ScriptModelSelectors':'_model_selector_context','Transitions':'_transition_context'}

def owner_file(value,row):
    return dict(schema_version=FILE_SCHEMA,scene_id=value['scene_id'],source_import_sha256=value['source_import_sha256'],owner_id=row['owner_id'],components=row['components'])

def parse(content):
    value=parse_json(content)
    if not isinstance(value,dict) or set(value)!={'schema_version','scene_id','source_import_sha256','owners'} or value['schema_version']!=SCHEMA:
        raise ProjectError('Unsupported operand bundle fields or schema')
    owners=value['owners']
    if not isinstance(owners,list) or len(owners)>128:raise ProjectError('Operand bundle is limited to 128 owners')
    if not isinstance(value['scene_id'],str) or not isinstance(value['source_import_sha256'],str) or len(value['source_import_sha256'])!=64 or any(c not in '0123456789abcdef' for c in value['source_import_sha256']):raise ProjectError('Operand bundle requires scene and imported source hash')
    seen=set();total=0
    for row in owners:
        if not isinstance(row,dict) or set(row)!={'owner_id','components'} or not isinstance(row['owner_id'],str) or len(row['owner_id'])>512 or row['owner_id'] in seen:raise ProjectError('Invalid or duplicate operand bundle owner')
        seen.add(row['owner_id']);file=parse_file(json.dumps(owner_file(value,row)))
        total+=sum(len(component['entries']) for component in file['components'].values())
    if total>256:raise ProjectError('Operand bundle is limited to 256 instruction entries in total')
    return value

def _composition(project,scene):
    """Compare every actual serialized byte write, including pre-existing scene edits."""
    writes={};sources=[]
    for owner,components in sorted(project.overrides.items()):
        numeric=set(components)&set(KINDS)
        if not numeric:continue
        document=project._dialogue_document(owner)
        if 'scene://'+document['scene']['name']!=scene:continue
        sources.append(owner)
        for component in sorted(numeric):
            modified,audit=getattr(project,CONTEXTS[component])(owner).patch(components[component]['entries'])
            for row in audit:
                offset=row.get('decoded_byte_offset');width=row.get('byte_length',1)
                if type(offset) is not int or type(width) is not int or width not in (1,2,4) or offset<0 or offset+width>len(modified):raise ProjectError('Invalid source-qualified operand byte audit')
                for at in range(offset,offset+width):
                    byte=modified[at]
                    if at in writes and writes[at][0]!=byte:raise ProjectError('Operand owners request conflicting writes to shared source bytes')
                    writes[at]=(byte,owner,component)
    return sources

def review(project,content):
    from importer.pipeline import _disc_context
    from .resources import _verify
    value=parse(content);scene=value['scene_id'];document=project.imports.get(scene)
    if not project.disc_path or scene!=project.active_scene or document is None:raise ProjectError('Open the bundle source scene with its user-owned disc')
    before_all=deepcopy(project.overrides);staged=copy(project);staged.overrides=deepcopy(before_all);staged.undo_stack=[];staged.redo_stack=[]
    reports=[]
    with _disc_context(project.disc_path):
        _verify(project,document)
        if digest(document)!=value['source_import_sha256']:raise ProjectError('Operand bundle differs from imported source')
        for row in sorted(value['owners'],key=lambda row:row['owner_id']):
            report=review_file(staged,row['owner_id'],json.dumps(owner_file(value,row)))
            if report['after'] is None:staged.overrides.pop(row['owner_id'],None)
            else:staged.overrides[row['owner_id']]=deepcopy(report['after'])
            reports.append(report)
        sources=_composition(staged,scene)
    if project.overrides!=before_all:raise ProjectError('Project changed during operand bundle review')
    report=dict(schema_version='legaia.script-operand-bundle-review.v1',scene_id=scene,source_import_sha256=value['source_import_sha256'],owners=reports,owner_count=len(reports),change_count=sum(row['change_count'] for row in reports),source_entity_ids=sources)
    report['review_key']=digest(dict(project_root=str(project.root),file=value,overrides=before_all))
    return report

def export_file(project):
    from importer.pipeline import _disc_context
    from .resources import _verify
    scene=project.active_scene;document=project.imports.get(scene)
    if not project.disc_path or document is None:raise ProjectError('Import the bundle source scene with its user-owned disc')
    with _disc_context(project.disc_path):
        _verify(project,document);owners=[]
        for owner,components in sorted(project.overrides.items()):
            numeric={kind:deepcopy(value) for kind,value in components.items() if kind in KINDS}
            if numeric and project._dialogue_document(owner)==document:owners.append(dict(owner_id=owner,components=numeric))
        value=dict(schema_version=SCHEMA,scene_id=scene,source_import_sha256=digest(document),owners=owners)
        review(project,json.dumps(value))
    return value

def apply(project,command):
    if set(command)!={'type','content','review_key'}:raise ProjectError('Operand bundle import requires file and reviewed key only')
    report=review(project,command['content'])
    if command['review_key']!=report['review_key']:raise ProjectError('Operand bundle or project changed since review')
    changed=[row for row in report['owners'] if row['before']!=row['after']]
    if not changed:return
    before={row['owner_id']:row['before'] for row in changed};after={row['owner_id']:row['after'] for row in changed}
    for owner,components in after.items():
        if components is None:project.overrides.pop(owner,None)
        else:project.overrides[owner]=deepcopy(components)
    project.undo_stack.append(dict(target='entity_overrides',entity_ids=sorted(before),source_entity_ids=sorted(set(report['source_entity_ids'])|{row['owner_id'] for row in report['owners']}),before=before,after=deepcopy(after)))
    project.redo_stack.clear()
