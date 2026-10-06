"""Historical fixed-layout model authoring inputs; never replay authority."""
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError, atomic_write, canonical, digest

MAX_RECEIPTS=32
MAX_GLB_BYTES=32*1024*1024
MAX_BYTES=64*1024*1024
FIELDS={'schema_version','asset_id','scene_id','glb_sha256','byte_length','binding','candidate_sha256','review_key','receipt_key'}

def _hash(value):return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def validate_record(record):
    if not isinstance(record,dict) or set(record)!=FIELDS or record['schema_version']!='legaia.model-source.v1':raise ProjectError('Invalid model source receipt fields')
    if any(not _hash(record[k]) for k in ('glb_sha256','candidate_sha256','review_key','receipt_key')):raise ProjectError('Invalid model source digest')
    if type(record['byte_length']) is not int or not 28<=record['byte_length']<=MAX_GLB_BYTES:raise ProjectError('Model source exceeds its GLB byte budget')
    if not isinstance(record['asset_id'],str) or not record['asset_id'].startswith('asset://') or not 9<=len(record['asset_id'])<=512:raise ProjectError('Model source requires a stable asset identity')
    if not isinstance(record['scene_id'],str) or not record['scene_id'].startswith('scene://') or not 9<=len(record['scene_id'])<=160:raise ProjectError('Model source requires a stable scene identity')
    b=record['binding']
    if not isinstance(b,dict) or b.get('asset_id')!=record['asset_id'] or b.get('scene_id')!=record['scene_id'] or b.get('schema_version') not in ('legaia.model-glb-binding.v1','legaia.model-glb-binding.v2','legaia.model-glb-binding.v3'):raise ProjectError('Model source binding identity changed')
    from .model_glb import _json_size
    _json_size(b,128*1024,'Model source binding')
    if 'external_object_nodes' in b:
        nodes=b['external_object_nodes'];objects=b.get('profile',{}).get('objects') if isinstance(b.get('profile'),dict) else None
        if not isinstance(objects,list) or not 1<=len(objects)<=1024 or not isinstance(nodes,list) or len(nodes)!=len(objects) or any(type(v) is not int or not 0<=v<1024 for v in nodes) or len(set(nodes))!=len(nodes):raise ProjectError('Model source object mapping changed')
    if digest({k:v for k,v in record.items() if k!='receipt_key'})!=record['receipt_key']:raise ProjectError('Model source receipt changed')
    return deepcopy(record)

def validate_collection(records):
    if not isinstance(records,dict) or len(records)>MAX_RECEIPTS:raise ProjectError('Model sources require at most 32 receipts')
    sizes={}
    for key,record in records.items():
        validate_record(record)
        if key!=record['receipt_key']:raise ProjectError('Model source collection identity changed')
        h,size=record['glb_sha256'],record['byte_length']
        if h in sizes and sizes[h]!=size:raise ProjectError('Conflicting model source lengths')
        sizes[h]=size
    if sum(sizes.values())>MAX_BYTES:raise ProjectError('Model sources exceed 64 MiB')
    return deepcopy(records)

def source_path(project,record):
    validate_record(record)
    path=project.root/'Authored'/'Models'/'GLBSources'/(record['glb_sha256']+'.glb')
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Model source path escapes project')
    return path

def read_source(project,record):
    path=source_path(project,record)
    if not path.is_file() or path.stat().st_size!=record['byte_length']:raise ProjectError('Model source is missing or changed size')
    raw=path.read_bytes()
    if len(raw)!=record['byte_length'] or sha256(raw).hexdigest()!=record['glb_sha256']:raise ProjectError('Model source content hash changed')
    return raw

def validate_files(project,records):
    validate_collection(records);seen=set()
    for record in records.values():
        if record['glb_sha256'] not in seen:read_source(project,record);seen.add(record['glb_sha256'])

def retain(project,records,content,binding,candidate_sha256,review_key):
    validate_collection(records)
    if not isinstance(content,bytes) or not 28<=len(content)<=MAX_GLB_BYTES:raise ProjectError('Model source requires immutable bounded GLB bytes')
    if not isinstance(binding,dict):raise ProjectError('Model source requires its binding JSON')
    from importer.animation_glb import _read_glb
    _read_glb(content)
    record=dict(schema_version='legaia.model-source.v1',asset_id=binding.get('asset_id'),scene_id=binding.get('scene_id'),
                glb_sha256=sha256(content).hexdigest(),byte_length=len(content),binding=deepcopy(binding),candidate_sha256=candidate_sha256,review_key=review_key)
    record['receipt_key']=digest(record);after=deepcopy(records);after[record['receipt_key']]=record;validate_collection(after)
    path=source_path(project,record)
    if path.exists():
        if read_source(project,record)!=content:raise ProjectError('Model source hash path changed')
    else:atomic_write(path,content)
    if read_source(project,record)!=content:raise ProjectError('Model source readback changed')
    return after,deepcopy(record)

def apply(project,asset,candidate,content,binding,report):
    before=deepcopy((project.model_overrides,project.model_sources,project.undo_stack,project.redo_stack))
    after,record=retain(project,project.model_sources,content,binding,report['proposed_sha256'],report['review_key'])
    from .scene_preview import source_key
    if source_key(project)!=binding['project_source_key']:raise ProjectError('Model source context changed before Apply')
    try:
        length=len(project.undo_stack);project.set_model_replacement(asset,candidate)
        if len(project.undo_stack)!=length+1:raise ProjectError('Model source retention requires one native history step')
        project.model_sources=after
        project.undo_stack[-1]=dict(target='model_source_import',before=dict(model_overrides=before[0],model_sources=before[1]),after=dict(model_overrides=deepcopy(project.model_overrides),model_sources=deepcopy(after)))
    except Exception:
        project.model_overrides,project.model_sources,project.undo_stack,project.redo_stack=before;raise
    return record

def catalog(project,asset_id,expected_source_key):
    from .scene_preview import source_key
    if not _hash(expected_source_key) or source_key(project)!=expected_source_key:raise ProjectError('Model source recovery context changed')
    project._model_source(asset_id,project.active_scene)
    validate_collection(project.model_sources)
    rows=[deepcopy(r) for r in project.model_sources.values() if r['asset_id']==asset_id and r['scene_id']==project.active_scene]
    validate_files(project,{r['receipt_key']:r for r in rows})
    if source_key(project)!=expected_source_key:raise ProjectError('Model source recovery context changed')
    return dict(schema_version='legaia.model-sources.v1',asset_id=asset_id,scene_id=project.active_scene,project_source_key=expected_source_key,imports=rows,historical_inputs=True,project_changed=False)

def download(project,asset_id,expected_source_key,receipt_key):
    import base64
    result=catalog(project,asset_id,expected_source_key);record=next((r for r in result['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('Model source receipt is absent from Current')
    raw=read_source(project,record)
    from .scene_preview import source_key
    if source_key(project)!=expected_source_key:raise ProjectError('Model source recovery context changed')
    return dict(result,selected=record,glb_base64=base64.b64encode(raw).decode('ascii'))


def review_removal(project,asset_id,expected_source_key,receipt_key):
    if project.mode!='edit':raise ProjectError('Model input removal requires Edit mode')
    value=catalog(project,asset_id,expected_source_key)
    record=next((r for r in value['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('Model source receipt is absent from Current')
    shared=sum(r['glb_sha256']==record['glb_sha256'] for r in project.model_sources.values())
    native={k:v for k,v in project._document().items() if k!='model_sources'}
    report=dict(schema_version='legaia.model-source-removal.v1',asset_id=asset_id,scene_id=value['scene_id'],
                project_path=str(project.root),project_source_key=expected_source_key,receipt_key=receipt_key,
                glb_sha256=record['glb_sha256'],receipt_count_before=len(project.model_sources),receipt_count_after=len(project.model_sources)-1,
                shared_blob_receipts=shared,registered_bytes_released=record['byte_length'] if shared==1 else 0,
                collection_key=digest(project.model_sources),native_key=digest(native),native_content_changed=False,source_file_deleted=False)
    report['review_key']=digest(report);return report

def remove_command(project,command):
    if set(command)!={'type','asset_id','expected_source_key','receipt_key','review_key'}:raise ProjectError('Model source removal requires exact reviewed fields')
    report=review_removal(project,**{k:command[k] for k in ('asset_id','expected_source_key','receipt_key')})
    if not _hash(command['review_key']) or command['review_key']!=report['review_key']:raise ProjectError('Model sources changed; review removal again')
    before=deepcopy(project.model_sources);after=deepcopy(before);del after[command['receipt_key']]
    validate_files(project,after)
    project.model_sources=after
    project.undo_stack.append(dict(target='model_sources',before=before,after=deepcopy(after)));project.redo_stack.clear()
    return report


def _library_key(project):
    return digest(dict(project_path=str(project.root),mode=project.mode,
                       sources=project.model_sources,native=project.model_overrides))


def library(project,expected_project_path):
    """Qualified historical model inputs, independent of scene and selection."""
    if not isinstance(expected_project_path,str) or expected_project_path!=str(project.root):
        raise ProjectError('Model input library project changed')
    key=_library_key(project)
    validate_files(project,project.model_sources)
    rows=sorted((deepcopy(r) for r in project.model_sources.values()),
                key=lambda r:(r['scene_id'],r['asset_id'],r['receipt_key']))
    sizes={r['glb_sha256']:r['byte_length'] for r in rows}
    if key!=_library_key(project):raise ProjectError('Model input library changed')
    return dict(schema_version='legaia.model-source-library.v1',project_path=str(project.root),
                library_key=key,mode=project.mode,imports=rows,receipt_count=len(rows),
                distinct_glb_count=len(sizes),registered_byte_length=sum(sizes.values()),
                project_changed=False,historical_inputs=True)


def _library_receipt(project,receipt_key,expected_project_path,expected_library_key):
    value=library(project,expected_project_path)
    if not _hash(expected_library_key) or value['library_key']!=expected_library_key:
        raise ProjectError('Model input library changed; refresh it')
    row=next((r for r in value['imports'] if r['receipt_key']==receipt_key),None)
    if row is None:raise ProjectError('Model input receipt is absent from Current')
    return value,row


def library_download(project,receipt_key,expected_project_path,expected_library_key):
    import base64
    value,row=_library_receipt(project,receipt_key,expected_project_path,expected_library_key)
    raw=read_source(project,row)
    if value['library_key']!=_library_key(project):raise ProjectError('Model input library changed')
    return dict(value,selected=row,glb_base64=base64.b64encode(raw).decode('ascii'))


def library_removal_review(project,receipt_key,expected_project_path,expected_library_key):
    if project.mode!='edit':raise ProjectError('Model input removal requires Edit mode')
    value,row=_library_receipt(project,receipt_key,expected_project_path,expected_library_key)
    shared=sum(r['glb_sha256']==row['glb_sha256'] for r in value['imports'])
    report=dict(schema_version='legaia.model-library-removal.v1',project_path=value['project_path'],
        library_key=value['library_key'],receipt_key=receipt_key,glb_sha256=row['glb_sha256'],
        scene_id=row['scene_id'],asset_id=row['asset_id'],
        receipt_count_before=value['receipt_count'],receipt_count_after=value['receipt_count']-1,
        registered_bytes_released=row['byte_length'] if shared==1 else 0,
        native_content_changed=False,source_file_deleted=False)
    report['review_key']=digest(report)
    return report


def library_remove_command(project,command):
    if set(command)!={'type','receipt_key','expected_project_path','expected_library_key','review_key'}:
        raise ProjectError('Model library removal requires exact reviewed fields')
    report=library_removal_review(project,**{k:command[k] for k in ('receipt_key','expected_project_path','expected_library_key')})
    if not _hash(command['review_key']) or report['review_key']!=command['review_key']:
        raise ProjectError('Model input removal changed; review again')
    before=deepcopy(project.model_sources);after=deepcopy(before);del after[command['receipt_key']]
    validate_files(project,after)
    project.model_sources=after
    project.undo_stack.append(dict(target='model_sources',before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return report


def compare_native(project,receipt_key,expected_project_path,expected_library_key):
    """Read current qualified native bytes; historical receipts never authorize writes."""
    value,row=_library_receipt(project,receipt_key,expected_project_path,expected_library_key)
    scene=row['scene_id'];evidence=digest(project.imports.get(scene))
    from importer.pipeline import _disc_context
    if not project.disc_path:raise ProjectError('Native model comparison requires the matching retail disc')
    disc=project.disc_path
    with _disc_context(disc):
        original=project._model_source(row['asset_id'],scene)
        binding=project.model_overrides.get(row['asset_id'])
        current=project.read_model_replacement(row['asset_id'],binding) if binding is not None else original
        if not isinstance(original,bytes) or not isinstance(current,bytes) or not 1<=len(current)<=4*1024*1024:
            raise ProjectError('Native model comparison requires bounded immutable bytes')
        if project.disc_path!=disc or value['library_key']!=_library_key(project) or evidence!=digest(project.imports.get(scene)):
            raise ProjectError('Native model comparison context changed')
        current_hash=sha256(current).hexdigest()
        report=dict(schema_version='legaia.model-source-native-comparison.v1',
            project_path=value['project_path'],library_key=value['library_key'],receipt_key=receipt_key,
            scene_id=scene,asset_id=row['asset_id'],historical_candidate_sha256=row['candidate_sha256'],
            source_sha256=sha256(original).hexdigest(),current_sha256=current_hash,current_byte_length=len(current),
            representation='authored' if binding is not None else 'retail',
            matches_current=current_hash==row['candidate_sha256'],project_changed=False,native_content_changed=False)
    if project.disc_path!=disc or value['library_key']!=_library_key(project) or evidence!=digest(project.imports.get(scene)):
        raise ProjectError('Native model comparison context changed')
    return report
