"""Retained original mesh inputs, sealed to qualified native ledger spans."""
from copy import copy,deepcopy
from hashlib import sha256
from importer.model_face_ledger import _operations,replay_face_ledger
from .project import ProjectError,digest,atomic_write

MAX_SOURCES=32
MAX_BYTES=64*1024*1024

def operations(binding):return _operations(binding['ledger'])

def carry(project,asset,binding):
    previous=project.model_overrides.get(asset,{})
    result=deepcopy(binding)
    if previous.get('mesh_imports') and 'mesh_imports' not in result:
        if result['format']!='tmd-face-addition-v1':raise ProjectError('Mesh sources require their retained topology ledger')
        result['mesh_imports']=deepcopy(previous['mesh_imports'])
    return result

def attach(project,asset,binding,content,recipe,expected_key):
    from .scene_preview import source_key
    if source_key(project)!=expected_key:raise ProjectError('Mesh source context changed before retention')
    result=carry(project,asset,binding)
    prior=project.model_overrides.get(asset,{})
    start=len(operations(prior)) if prior.get('format')=='tmd-face-addition-v1' else 0
    rows=operations(result);span=rows[start:]
    if not span:raise ProjectError('Mesh source retention requires new native ledger operations')
    record=dict(schema_version='legaia.model-mesh-source.v1',asset_id=asset,
        glb_sha256=sha256(content).hexdigest(),byte_length=len(content),
        first_operation=start,operation_count=len(span),operations_sha256=digest(span),
        input_sha256=span[0]['input_sha256'],proposed_sha256=span[-1]['proposed_sha256'],recipe=deepcopy(recipe))
    record['receipt_key']=digest(record)
    result.setdefault('mesh_imports',[]).append(record)
    _metadata(asset,result)
    path=_path(project,record)
    if path.exists():
        if path.read_bytes()!=content:raise ProjectError('Retained mesh source hash path changed')
    else:atomic_write(path,content)
    return result

def _path(project,record):
    path=project.root/'Authored'/'Models'/'Sources'/(record['glb_sha256']+'.glb')
    if not path.resolve().is_relative_to(project.root):raise ProjectError('Mesh source path escapes project')
    return path

def read_source(project,record):
    path=_path(project,record)
    if not path.is_file() or path.stat().st_size!=record['byte_length']:raise ProjectError('Retained mesh source is missing or changed size')
    content=path.read_bytes()
    if len(content)!=record['byte_length'] or sha256(content).hexdigest()!=record['glb_sha256']:raise ProjectError('Retained mesh source hash changed')
    return content

def _metadata(asset,binding):
    records=binding.get('mesh_imports',[])
    if not isinstance(records,list) or not 1<=len(records)<=MAX_SOURCES:raise ProjectError('Mesh source receipts require 1 through 32 entries')
    fields={'schema_version','asset_id','glb_sha256','byte_length','first_operation','operation_count','operations_sha256','input_sha256','proposed_sha256','recipe','receipt_key'}
    rows=operations(binding);end=0;total={}
    for record in records:
        if (not isinstance(record,dict) or set(record)!=fields or record['schema_version']!='legaia.model-mesh-source.v1' or record['asset_id']!=asset
                or any(not isinstance(record[k],str) or len(record[k])!=64 or any(c not in '0123456789abcdef' for c in record[k]) for k in ('glb_sha256','operations_sha256','input_sha256','proposed_sha256','receipt_key'))
                or type(record['byte_length']) is not int or not 28<=record['byte_length']<=32*1024*1024
                or type(record['first_operation']) is not int or record['first_operation']<end
                or type(record['operation_count']) is not int or not 1<=record['operation_count']<=64):
            raise ProjectError('Invalid mesh source identity, byte budget or ledger ownership')
        start=record['first_operation'];end=start+record['operation_count'];span=rows[start:end]
        if end>len(rows) or digest(span)!=record['operations_sha256'] or span[0]['input_sha256']!=record['input_sha256'] or span[-1]['proposed_sha256']!=record['proposed_sha256']:
            raise ProjectError('Retained mesh source ledger span changed')
        if digest({k:v for k,v in record.items() if k!='receipt_key'})!=record['receipt_key']:raise ProjectError('Mesh source receipt changed')
        recipe=record['recipe'];common={'material_colors','scene_index','uv_set','source_scale','source_offset','source_rotation'}
        single=common|{'kind','donor_face_id','new_group','replace_group','replace_object','preserve_primitives','primitive_index'}
        batch=common|{'kind','mappings','replace_objects'}
        if not isinstance(recipe,dict) or (recipe.get('kind')=='single' and set(recipe)!=single) or (recipe.get('kind')=='batch' and set(recipe)!=batch) or recipe.get('kind') not in ('single','batch'):
            raise ProjectError('Mesh source import recipe fields changed')
        if record['glb_sha256'] in total and total[record['glb_sha256']]!=record['byte_length']:raise ProjectError('Conflicting retained mesh source lengths')
        total[record['glb_sha256']]=record['byte_length']
    if sum(total.values())>MAX_BYTES:raise ProjectError('Model retained mesh inputs exceed 64 MiB')
    return records

def validate(project,asset,binding,base):
    """Reconstruct each import from its original input and preceding native ledger."""
    records=_metadata(asset,binding);rows=operations(binding)
    for record in records:
        content=read_source(project,record)
        start=record['first_operation'];end=start+record['operation_count']
        def prefix(length):return dict(schema_version=binding['ledger']['schema_version'],source_sha256=binding['ledger']['source_sha256'],source_byte_length=binding['ledger']['source_byte_length'],operations=deepcopy(rows[:length]))
        # Mesh allocations always produce v5+ ledgers with operations, including an empty prefix.
        before_ledger=prefix(start);before,_=replay_face_ledger(base,before_ledger)
        after,_=replay_face_ledger(base,prefix(end))
        view=copy(project);view.mode='edit';view.active_scene=binding['source_scene_id'];view.model_overrides=deepcopy(project.model_overrides)
        initial={k:deepcopy(v) for k,v in binding.items() if k!='mesh_imports'}
        initial.update(asset_sha256=sha256(before).hexdigest(),byte_length=len(before),ledger=before_ledger)
        view.model_overrides[asset]=initial
        read=project.read_model_replacement
        view.read_model_replacement=lambda owner,item:before if owner==asset and item.get('asset_sha256')==initial['asset_sha256'] else read(owner,item)
        from .scene_preview import source_key
        key=source_key(view);recipe=deepcopy(record['recipe']);kind=recipe.pop('kind')
        if kind=='single':
            from .model_mesh_append import prepare
            donor=recipe.pop('donor_face_id');candidate,_,_=prepare(view,asset,content,donor,initial['asset_sha256'],key,**recipe)
        else:
            from .model_mesh_batch import prepare
            mappings=recipe.pop('mappings');candidate,_,_=prepare(view,asset,content,mappings,initial['asset_sha256'],key,**recipe)
        if candidate!=after:raise ProjectError('Retained GLB recipe differs from its native ledger result')
    return deepcopy(records)

def catalog(project,asset,key):
    from .scene_preview import source_key
    if source_key(project)!=key:raise ProjectError('Mesh source context changed')
    if not isinstance(asset,str) or not isinstance(key,str):raise ProjectError('Mesh source requires exact model identity and context')
    project._model_source(asset,project.active_scene)
    binding=project.model_overrides.get(asset)
    if binding:project.read_model_replacement(asset,binding)
    records=deepcopy(binding.get('mesh_imports',[])) if binding else []
    if source_key(project)!=key:raise ProjectError('Mesh source context changed during recovery')
    return dict(schema_version='legaia.model-mesh-sources.v1',asset_id=asset,project_source_key=key,imports=records,project_changed=False)

def download(project,asset,key,receipt):
    result=catalog(project,asset,key)
    record=next((row for row in result['imports'] if row['receipt_key']==receipt),None)
    if record is None:raise ProjectError('Retained mesh source receipt is absent from Current')
    import base64
    content=read_source(project,record)
    from .scene_preview import source_key
    if source_key(project)!=key:raise ProjectError('Mesh source context changed during download')
    return dict(result,selected=record,content_base64=base64.b64encode(content).decode())
