"""Project navigation metadata bound to original decoded script record boundaries."""
from copy import deepcopy
import re
import uuid
from .project import ProjectError, digest
from .metadata_text import metadata_name

COMMANDS = {'create_script_bookmark', 'rename_script_bookmark', 'update_script_bookmark', 'delete_script_bookmark'}

def _document(project, owner):
    if isinstance(owner, str) and '/controllers/' in owner:
        match=re.fullmatch(r'(scene://[A-Za-z0-9_-]{1,128})/controllers/man-p1/0000',owner)
        if not match or match[1] not in project.imports:
            raise ProjectError('Controller bookmark requires its exact imported scene owner')
        return project.imports[match[1]]
    return project._dialogue_document(owner)

def validate(project, identifier, value):
    try:
        if not isinstance(identifier, str) or not identifier.startswith('bookmark://') or str(uuid.UUID(identifier[11:])) != identifier[11:]:
            raise ValueError()
    except ValueError:
        raise ProjectError('Invalid script bookmark identity') from None
    if (not isinstance(value, dict) or set(value) != {'id','name','scene_id','import_sha256','owner_id','pc','source_record_sha256','mnemonic'} or
            value['id'] != identifier or not isinstance(value['name'],str) or value['name'] != value['name'].strip() or not 1 <= len(value['name']) <= 80 or
            not isinstance(value['scene_id'],str) or value['scene_id'] not in project.imports or value['import_sha256'] != digest(project.imports[value['scene_id']]) or
            not isinstance(value['owner_id'],str) or type(value['pc']) is not int or not 0 <= value['pc'] <= 65535 or
            not isinstance(value['source_record_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',value['source_record_sha256']) or
            not isinstance(value['mnemonic'],str) or not 1 <= len(value['mnemonic']) <= 128):
        raise ProjectError('Script bookmark has invalid source metadata')
    metadata_name(value['name'], 'Script bookmark name')
    if _document(project,value['owner_id'])['scene']['semantic_id'] != value['scene_id']:
        raise ProjectError('Script bookmark owner differs from its imported scene')

def review_key(project, value):
    return digest({'project_root':str(project.root),'bookmark':value})

def _inspection(project, owner, document):
    from importer.pipeline import _disc_context, import_scene
    from importer.script_inspection import inspect_actor_script
    from importer.trigger_scripts import inspect_partition_two_script
    if not project.disc_path:raise ProjectError('Saving script bookmarks requires the project source disc')
    with _disc_context(project.disc_path):
        scene=document['scene']['name']
        if import_scene(project.disc_path,scene)!=document:
            raise ProjectError('Bookmark source differs from freshly verified imported evidence')
        if '/controllers/' in owner:
            from importer.scene_controller import inspect_scene_controller
            result=inspect_scene_controller(project.disc_path,scene)
            if result['semantic_id']!=owner.replace('scene://','script://') or result['scene_id']!=document['scene']['semantic_id'] or result['read_only'] is not True:
                raise ProjectError('Controller bookmark source ownership changed')
            return {**result,'record':{**result['record'],'sha256':result['source_record']['sha256']}}
        if '/scripts/man-p2/' in owner:
            result=inspect_partition_two_script(project.disc_path,scene,int(owner.rsplit('/',1)[1]))
            return {**result['inspection'],'record':result['record']}
        actor=next(row for row in document['actors'] if row['semantic_id']==owner)
        return inspect_actor_script(project.disc_path,scene,actor)

def _boundary(project, owner, pc, expected):
    document=_document(project,owner)
    if document['scene']['semantic_id'] != project.active_scene:
        raise ProjectError('Script bookmarks require the active imported scene')
    if type(pc) is not int or not 0 <= pc <= 65535:
        raise ProjectError('Script bookmark requires a bounded integer record offset')
    report=_inspection(project,owner,document)
    if expected != report['record']['sha256']:
        raise ProjectError('Script bookmark source record changed; reopen inspection')
    matches=[row['mnemonic'] for row in report['instructions'] if row['pc']==pc]+['DIALOGUE_SEGMENT' for row in report['dialogues'] if row['pc']==pc]
    if len(matches)!=1:
        raise ProjectError('Script bookmark offset is not a unique decoded Retail boundary')
    return dict(scene_id=project.active_scene,import_sha256=digest(document),owner_id=owner,pc=pc,source_record_sha256=expected,mnemonic=matches[0])

def command(project, body):
    kind=body['type']
    if kind=='create_script_bookmark':
        if set(body)!={'type','owner_id','pc','source_record_sha256','name'}:
            raise ProjectError('Save bookmark requires exact source, offset and name fields')
        if len(project.script_bookmarks)>=256:raise ProjectError('Project supports at most 256 script bookmarks')
        identifier='bookmark://'+str(uuid.uuid4());before=None
        after=dict(id=identifier,name=body['name'],**_boundary(project,body['owner_id'],body['pc'],body['source_record_sha256']))
    else:
        required={'type','bookmark_id','review_key'}|({'name'} if kind=='rename_script_bookmark' else {'pc','source_record_sha256'} if kind=='update_script_bookmark' else set())
        if set(body)!=required:raise ProjectError('Bookmark command has unsupported fields')
        identifier=body['bookmark_id']
        if not isinstance(identifier,str) or identifier not in project.script_bookmarks:raise ProjectError('Saved script bookmark is unavailable')
        before=deepcopy(project.script_bookmarks[identifier]);validate(project,identifier,before)
        if body['review_key']!=review_key(project,before):raise ProjectError('Bookmark changed; refresh before editing it')
        after=deepcopy(before)
        if kind=='rename_script_bookmark':after['name']=body['name']
        elif kind=='update_script_bookmark':after.update(_boundary(project,before['owner_id'],body['pc'],body['source_record_sha256']))
        else:after=None
    if after is not None:
        if isinstance(after['name'],str):after['name']=after['name'].strip()
        validate(project,identifier,after)
        if any(key!=identifier and row['owner_id']==after['owner_id'] and row['name'].casefold()==after['name'].casefold() for key,row in project.script_bookmarks.items()):
            raise ProjectError('A bookmark with this name already exists for this script')
    if before==after:return
    if after is None:project.script_bookmarks.pop(identifier)
    else:project.script_bookmarks[identifier]=after
    project.undo_stack.append(dict(target='script_bookmarks',bookmark_id=identifier,scene_id=(after or before)['scene_id'],before=before,after=deepcopy(after)))
    project.redo_stack.clear()
