"""Portable editor selections with Retail-row or allocation provenance."""
from copy import deepcopy
from hashlib import sha256
import re,uuid
from .project import ProjectError,digest
from .scene_selection_sets import _name
from .scene_preview import source_key

COMMANDS={'create_model_vertex_group','rename_model_vertex_group','update_model_vertex_group','delete_model_vertex_group'}

def indices(value):
    if (not isinstance(value,list) or not 1<=len(value)<=4096 or
            any(type(i) is not int or not 0<=i<65536 for i in value) or len(set(value))!=len(value)):
        raise ProjectError('Vertex group needs 1..4096 unique object-local row indices')
    return sorted(value)

def validate(project,identifier,value):
    try:
        if not isinstance(identifier,str) or not identifier.startswith('vertex-group://') or str(uuid.UUID(identifier[15:]))!=identifier[15:]:raise ValueError()
    except ValueError:raise ProjectError('Invalid saved vertex group identity') from None
    fields={'id','name','scene_id','import_sha256','asset_id','object_index','indices','source_sha256','allocation_key'}
    if not isinstance(value,dict) or set(value)!=fields or value['id']!=identifier or not isinstance(value['scene_id'],str) or value['scene_id'] not in project.imports:
        raise ProjectError('Invalid saved vertex group record')
    if not isinstance(value['asset_id'],str) or value['import_sha256']!=digest(project.imports[value['scene_id']]) or value['asset_id'] not in {a['semantic_id'] for a in project.imports[value['scene_id']]['assets']['models']}:
        raise ProjectError('Saved vertex group differs from its imported model/scene')
    if _name(value['name'])!=value['name'] or type(value['object_index']) is not int or not 0<=value['object_index']<1024 or indices(value['indices'])!=value['indices']:
        raise ProjectError('Invalid saved vertex group name, object or indices')
    if not isinstance(value['source_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',value['source_sha256']) or value['allocation_key'] is not None and (not isinstance(value['allocation_key'],str) or not re.fullmatch('[0-9a-f]{64}',value['allocation_key'])):
        raise ProjectError('Invalid saved vertex group source fingerprint')

def binding(project,asset,owner,members,key,expected_hash=None):
    from .model_face_addition import _context
    from importer.assets import decode_tmd
    if not isinstance(asset,str) or type(owner) is not int:raise ProjectError('Saved group requires a model identity and integer object index')
    original,effective,_,_,ledger,_=_context(project,asset,key)
    if expected_hash is not None and sha256(effective).hexdigest()!=expected_hash:raise ProjectError('Model changed before saving vertex selection')
    selected=indices(members);current=decode_tmd(effective);retail=decode_tmd(original)
    if type(owner) is not int or not 0<=owner<len(current['objects']) or selected[-1]>=current['objects'][owner]['vertex_count']:
        raise ProjectError('Saved group escapes its current object-local table')
    allocated=owner>=len(retail['objects']) or selected[-1]>=retail['objects'][owner]['vertex_count']
    allocations=[op for op in ledger.get('operations',[]) if op.get('kind') in ('allocate_vectors','allocate_objects')]
    if allocated and not allocations:raise ProjectError('Allocated vertex ownership is unavailable')
    return dict(source_sha256=sha256(original).hexdigest(),allocation_key=digest(allocations) if allocated else None)

def review_key(project,value):return digest(dict(root=str(project.root),model_vertex_group=value))

def saved(project,identifier,key):
    value=deepcopy(project.model_vertex_groups.get(identifier)) if isinstance(identifier,str) else None
    validate(project,identifier,value)
    if key!=review_key(project,value):raise ProjectError('Saved group changed since review')
    return value

def review(project,identifier,key,expected_source_key):
    value=saved(project,identifier,key)
    if project.active_scene!=value['scene_id']:raise ProjectError('Load the saved group source scene before recall')
    current=binding(project,value['asset_id'],value['object_index'],value['indices'],expected_source_key)
    if current!={field:value[field] for field in current}:raise ProjectError('Saved vertex group ownership changed; recall rejected')
    if source_key(project)!=expected_source_key:raise ProjectError('Project changed during saved group recall')
    return dict(schema_version='legaia.model-vertex-group-review.v1',**value,review_key=review_key(project,value),project_source_key=expected_source_key,read_only=True)

def command(project,body):
    if project.mode!='edit' or not isinstance(body,dict) or not isinstance(body.get('type'),str) or body['type'] not in COMMANDS:raise ProjectError('Saved vertex group commands require Edit mode')
    kind=body['type']
    if kind=='create_model_vertex_group':
        if set(body)!={'type','asset_id','object_index','indices','name','expected_sha256','source_key'}:raise ProjectError('Save group requires exact model, object, indices, name and inspected source')
        if len(project.model_vertex_groups)>=128:raise ProjectError('Project is limited to128 saved vertex groups')
        identifier='vertex-group://'+str(uuid.uuid4());before=None
        after=dict(id=identifier,name=_name(body['name']),scene_id=project.active_scene,import_sha256=digest(project.imports.get(project.active_scene)),asset_id=body['asset_id'],object_index=body['object_index'],indices=indices(body['indices']),**binding(project,body['asset_id'],body['object_index'],body['indices'],body['source_key'],body['expected_sha256']))
    else:
        extra={'name'} if kind=='rename_model_vertex_group' else {'indices','expected_sha256','source_key'} if kind=='update_model_vertex_group' else set()
        if set(body)!={'type','group_id','review_key'}|extra:raise ProjectError('Saved group command has unsupported fields')
        identifier=body['group_id'];before=saved(project,identifier,body['review_key']);after=deepcopy(before)
        if kind=='rename_model_vertex_group':after['name']=_name(body['name'])
        elif kind=='update_model_vertex_group':
            if project.active_scene!=before['scene_id']:raise ProjectError('Load the saved group scene before updating membership')
            after.update(binding(project,before['asset_id'],before['object_index'],body['indices'],body['source_key'],body['expected_sha256']));after['indices']=indices(body['indices'])
        else:after=None
    if after is not None:
        validate(project,identifier,after)
        if any(k!=identifier and v['asset_id']==after['asset_id'] and v['name'].casefold()==after['name'].casefold() for k,v in project.model_vertex_groups.items()):raise ProjectError('A vertex group with this name already exists for the model')
    if before==after:return
    if after is None:project.model_vertex_groups.pop(identifier)
    else:project.model_vertex_groups[identifier]=after
    project.undo_stack.append(dict(target='model_vertex_groups',group_id=identifier,scene_id=(after or before)['scene_id'],before=before,after=deepcopy(after)));project.redo_stack.clear()
