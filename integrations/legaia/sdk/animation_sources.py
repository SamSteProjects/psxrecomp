"""Project-local original animation inputs; historical receipts are not authority.

Native authoring still requires fresh SDK Review. This service retains exact
GLB bytes and binding/mapping choices for recovery, without importing payloads
into source provenance or treating an old receipt as an executable command.
"""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID

from .project import ProjectError, atomic_write, canonical, digest

MAX_RECEIPTS = 32
MAX_GLB_BYTES = 32 * 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024 * 1024
FIELDS = {'schema_version','kind','scene_id','target_id','glb_sha256','byte_length',
          'binding','animation_index','source_frame_indices','candidate_sha256',
          'review_key','receipt_key'}


def _hash(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def validate_record(record):
    if not isinstance(record,dict) or set(record)!=FIELDS or record['schema_version']!='legaia.animation-source.v1':
        raise ProjectError('Invalid animation source receipt fields')
    if record['kind'] not in ('imported','retained'):
        raise ProjectError('Unknown animation source kind')
    if any(not _hash(record[k]) for k in ('glb_sha256','candidate_sha256','review_key','receipt_key')):
        raise ProjectError('Invalid animation source digest')
    if type(record['byte_length']) is not int or not 28<=record['byte_length']<=MAX_GLB_BYTES:
        raise ProjectError('Animation source exceeds its GLB byte budget')
    scene=record['scene_id'];target=record['target_id'];binding=record['binding']
    if not isinstance(scene,str) or not scene.startswith('scene://') or not 9<=len(scene)<=160:
        raise ProjectError('Animation source requires a stable scene identity')
    if not isinstance(target,str) or len(target)>512:
        raise ProjectError('Animation source requires a stable target identity')
    if not isinstance(binding,dict) or len(canonical(binding))>128*1024 or binding.get('scene_id')!=scene:
        raise ProjectError('Animation source binding differs from its scene or byte budget')
    index=record['animation_index']
    if index is not None and (type(index) is not int or not 0<=index<64):
        raise ProjectError('Animation source has an invalid selected clip')
    frames=record['source_frame_indices']
    if record['kind']=='imported':
        if (binding.get('schema_version') not in ('legaia.animation-glb-binding.v1','legaia.animation-glb-binding.v2')
                or binding.get('entity_id')!=target or not target.startswith(scene+'/actors/') or frames is not None):
            raise ProjectError('Imported animation source identity changed')
    else:
        try: valid_uuid=str(UUID(target))==target
        except (ValueError,AttributeError): valid_uuid=False
        if (not valid_uuid or binding.get('schema_version')!='legaia.animation-record-glb-binding.v1'
                or binding.get('record_id')!=target or not isinstance(frames,list) or not 1<=len(frames)<=4096
                or any(type(v) is not int or not 0<=v<65536 for v in frames)):
            raise ProjectError('Retained animation source identity or mapping changed')
    if digest({k:v for k,v in record.items() if k!='receipt_key'})!=record['receipt_key']:
        raise ProjectError('Animation source receipt changed')
    return deepcopy(record)


def validate_collection(records):
    if not isinstance(records,dict) or len(records)>MAX_RECEIPTS:
        raise ProjectError('Animation sources require at most 32 receipts')
    sizes={}
    for key,record in records.items():
        validate_record(record)
        if key!=record['receipt_key']:raise ProjectError('Animation receipt key differs from its collection identity')
        h=record['glb_sha256'];size=record['byte_length']
        if h in sizes and sizes[h]!=size:raise ProjectError('Conflicting animation source byte lengths')
        sizes[h]=size
    if sum(sizes.values())>MAX_SOURCE_BYTES:raise ProjectError('Animation sources exceed 64 MiB')
    return deepcopy(records)


def source_path(project,record):
    validate_record(record)
    path=project.root/'Authored'/'Animations'/'Sources'/(record['glb_sha256']+'.glb')
    if not path.resolve().is_relative_to(project.root.resolve()):
        raise ProjectError('Animation source path escapes project')
    return path


def read_source(project,record):
    path=source_path(project,record)
    if not path.is_file() or path.stat().st_size!=record['byte_length']:
        raise ProjectError('Animation source is missing or changed size')
    content=path.read_bytes()
    if len(content)!=record['byte_length'] or sha256(content).hexdigest()!=record['glb_sha256']:
        raise ProjectError('Animation source content hash changed')
    return content


def retain(project,records,content,*,kind,target_id,binding,animation_index,source_frame_indices,candidate_sha256,review_key):
    """Prepare checked source metadata; callers own the native/history transaction."""
    validate_collection(records)
    if not isinstance(content,bytes) or not 28<=len(content)<=MAX_GLB_BYTES:
        raise ProjectError('Animation source requires immutable bounded GLB bytes')
    if not isinstance(binding,dict):raise ProjectError('Animation source requires its binding JSON')
    from importer.animation_glb import _read_glb
    doc,_ = _read_glb(content)
    clips=doc.get('animations',[])
    if not isinstance(clips,list) or len(clips)>64 or (animation_index is None and len(clips)>1) or (animation_index is not None and (type(animation_index) is not int or not 0<=animation_index<len(clips))):
        raise ProjectError('Animation source selection differs from its uploaded GLB')
    record=dict(schema_version='legaia.animation-source.v1',kind=kind,
        scene_id=binding.get('scene_id'),target_id=target_id,glb_sha256=sha256(content).hexdigest(),
        byte_length=len(content),binding=deepcopy(binding),animation_index=animation_index,
        source_frame_indices=deepcopy(source_frame_indices),candidate_sha256=candidate_sha256,review_key=review_key)
    record['receipt_key']=digest(record)
    after=deepcopy(records);after[record['receipt_key']]=record
    validate_collection(after)
    path=source_path(project,record)
    if path.exists():
        if read_source(project,record)!=content:raise ProjectError('Animation source hash path changed')
    else:atomic_write(path,content)
    if read_source(project,record)!=content:raise ProjectError('Animation source readback changed')
    return after,deepcopy(record)


def validate_files(project,records):
    validate_collection(records)
    seen=set()
    for record in records.values():
        if record['glb_sha256'] not in seen:
            read_source(project,record);seen.add(record['glb_sha256'])


def apply(project,command,content,**recipe):
    """Retain inputs and native changes in the same atomic history entry."""
    before=deepcopy((project.overrides,project.animation_sources,project.undo_stack,project.redo_stack))
    after,record=retain(project,project.animation_sources,content,**recipe)
    from .scene_preview import source_key
    if source_key(project)!=recipe['binding']['project_source_key']:
        raise ProjectError('Animation source project changed before Apply')
    try:
        length=len(project.undo_stack)
        project.command(command)
        if len(project.undo_stack)!=length+1:
            raise ProjectError('Animation source retention requires one native history step')
        project.animation_sources=after
        project.undo_stack[-1]=dict(target='animation_source_import',
            before=dict(overrides=before[0],animation_sources=before[1]),
            after=dict(overrides=deepcopy(project.overrides),animation_sources=deepcopy(after)))
    except Exception:
        project.overrides,project.animation_sources,project.undo_stack,project.redo_stack=before
        raise
    return record


def catalog(project,scene_id,target_id,kind,expected_source_key):
    from .scene_preview import source_key
    if not isinstance(scene_id,str) or not _hash(expected_source_key) or scene_id!=project.active_scene or source_key(project)!=expected_source_key:
        raise ProjectError('Animation source recovery context changed')
    if kind not in ('imported','retained') or not isinstance(target_id,str) or not 1<=len(target_id)<=512:
        raise ProjectError('Animation source recovery requires a stable target')
    validate_collection(project.animation_sources)
    rows=[deepcopy(r) for r in project.animation_sources.values()
          if (r['scene_id'],r['target_id'],r['kind'])==(scene_id,target_id,kind)]
    validate_files(project,{r['receipt_key']:r for r in rows})
    if source_key(project)!=expected_source_key:raise ProjectError('Animation source recovery context changed')
    return dict(schema_version='legaia.animation-sources.v1',scene_id=scene_id,target_id=target_id,kind=kind,
                project_source_key=expected_source_key,imports=rows,project_changed=False,historical_inputs=True)


def download(project,receipt_key,**request):
    import base64
    result=catalog(project,**request)
    record=next((r for r in result['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('Animation source receipt is absent from Current')
    raw=read_source(project,record)
    from .scene_preview import source_key
    if source_key(project)!=request['expected_source_key']:raise ProjectError('Animation source recovery context changed')
    return dict(result,selected=record,glb_base64=base64.b64encode(raw).decode('ascii'))


def review_removal(project,receipt_key,**request):
    """Review removal from Current; preserve native content and undo source bytes."""
    if project.mode!='edit':raise ProjectError('Animation source removal requires Edit mode')
    value=catalog(project,**request)
    record=next((r for r in value['imports'] if r['receipt_key']==receipt_key),None)
    if record is None:raise ProjectError('Animation source receipt is absent from Current')
    shared=sum(r['glb_sha256']==record['glb_sha256'] for r in project.animation_sources.values())
    report=dict(schema_version='legaia.animation-source-removal.v1',
        scene_id=value['scene_id'],target_id=value['target_id'],kind=value['kind'],
        project_source_key=value['project_source_key'],receipt_key=receipt_key,
        glb_sha256=record['glb_sha256'],receipt_count_before=len(project.animation_sources),
        receipt_count_after=len(project.animation_sources)-1,
        registered_bytes_released=record['byte_length'] if shared==1 else 0,
        shared_blob_receipts=shared,native_content_changed=False,source_file_deleted=False,
        collection_key=digest(project.animation_sources),native_key=digest(project.overrides))
    report['review_key']=digest(report)
    return report


def remove_command(project,command):
    expected={'type','scene_id','target_id','kind','expected_source_key','receipt_key','review_key'}
    if set(command)!=expected:raise ProjectError('Animation source removal requires exact reviewed fields')
    request={k:command[k] for k in ('scene_id','target_id','kind','expected_source_key')}
    report=review_removal(project,command['receipt_key'],**request)
    if not _hash(command['review_key']) or command['review_key']!=report['review_key']:
        raise ProjectError('Animation sources changed; review removal again')
    before=deepcopy(project.animation_sources);after=deepcopy(before)
    del after[command['receipt_key']]
    validate_files(project,after)
    project.animation_sources=after
    project.undo_stack.append(dict(target='animation_sources',before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return report


def _library_key(project):
    return digest(dict(project_path=str(project.root),mode=project.mode,
                       sources=project.animation_sources,native=project.overrides))


def library(project,expected_project_path):
    """Project-wide historical inputs, independent of active scene or selection."""
    if not isinstance(expected_project_path,str) or expected_project_path!=str(project.root):
        raise ProjectError('Animation input library project changed')
    key=_library_key(project)
    validate_files(project,project.animation_sources)
    rows=sorted((deepcopy(r) for r in project.animation_sources.values()),
                key=lambda r:(r['scene_id'],r['kind'],r['target_id'],r['receipt_key']))
    sizes={r['glb_sha256']:r['byte_length'] for r in rows}
    if key!=_library_key(project):raise ProjectError('Animation input library changed')
    return dict(schema_version='legaia.animation-source-library.v1',project_path=str(project.root),
                library_key=key,mode=project.mode,imports=rows,receipt_count=len(rows),
                distinct_glb_count=len(sizes),registered_byte_length=sum(sizes.values()),
                project_changed=False,historical_inputs=True)


def _library_receipt(project,receipt_key,expected_project_path,expected_library_key):
    value=library(project,expected_project_path)
    if not _hash(expected_library_key) or value['library_key']!=expected_library_key:
        raise ProjectError('Animation input library changed; refresh it')
    row=next((r for r in value['imports'] if r['receipt_key']==receipt_key),None)
    if row is None:raise ProjectError('Animation input receipt is absent from Current')
    return value,row


def library_download(project,receipt_key,expected_project_path,expected_library_key):
    import base64
    value,row=_library_receipt(project,receipt_key,expected_project_path,expected_library_key)
    raw=read_source(project,row)
    if value['library_key']!=_library_key(project):raise ProjectError('Animation input library changed')
    return dict(value,selected=row,glb_base64=base64.b64encode(raw).decode('ascii'))


def library_removal_review(project,receipt_key,expected_project_path,expected_library_key):
    if project.mode!='edit':raise ProjectError('Animation input removal requires Edit mode')
    value,row=_library_receipt(project,receipt_key,expected_project_path,expected_library_key)
    shared=sum(r['glb_sha256']==row['glb_sha256'] for r in value['imports'])
    report=dict(schema_version='legaia.animation-library-removal.v1',project_path=value['project_path'],
        library_key=value['library_key'],receipt_key=receipt_key,glb_sha256=row['glb_sha256'],
        scene_id=row['scene_id'],target_id=row['target_id'],kind=row['kind'],
        receipt_count_before=value['receipt_count'],receipt_count_after=value['receipt_count']-1,
        registered_bytes_released=row['byte_length'] if shared==1 else 0,
        native_content_changed=False,source_file_deleted=False)
    report['review_key']=digest(report)
    return report


def library_remove_command(project,command):
    if set(command)!={'type','receipt_key','expected_project_path','expected_library_key','review_key'}:
        raise ProjectError('Animation library removal requires exact reviewed fields')
    report=library_removal_review(project,**{k:command[k] for k in ('receipt_key','expected_project_path','expected_library_key')})
    if not _hash(command['review_key']) or report['review_key']!=command['review_key']:
        raise ProjectError('Animation input removal changed; review again')
    before=deepcopy(project.animation_sources);after=deepcopy(before)
    del after[command['receipt_key']]
    project.animation_sources=after
    project.undo_stack.append(dict(target='animation_sources',before=before,after=deepcopy(after)))
    project.redo_stack.clear()
    return report
