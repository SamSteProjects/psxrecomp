"""Fresh World rigid GLB proposals through the existing full-bank Review."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256

from importer.animation import decode_animation_record
from importer.animation_glb import import_animation_glb,MAX_GLB_BYTES
from .project import ProjectError,digest
from .worldmap_animation_export import encode_inspected_clip
from .worldmap_animation_edit import current,review
from .worldmap_placement_allocation import _fresh


def prepare_inspected_import(held,content,binding,animation_index=None,object_nodes=None):
    """Convert a qualified snapshot/file to canonical Retail-relative rows."""
    if not isinstance(content,bytes) or not 28<=len(content)<=MAX_GLB_BYTES:
        raise ProjectError('Choose a bounded World animation GLB')
    if not isinstance(binding,dict) or binding.get('schema_version')!='legaia.world-animation-export.v1':
        raise ProjectError('Choose the fresh World clip export audit JSON')
    layer=binding.get('layer');fps=binding.get('fps')
    source=held['source']['before']
    if layer=='current':export_receipt=held
    elif layer=='retail':export_receipt=dict(deepcopy(source),_export_geometry=deepcopy(held['source']['current_model_geometry']))
    else:raise ProjectError('World GLB requires an exported Retail or Current binding')
    expected=encode_inspected_clip(export_receipt,layer,fps)['audit']
    if digest(binding)!=digest(expected):
        raise ProjectError('World export audit differs from the current clip/model snapshot; export again')
    baseline=b64decode(held['preview']['record_base64'],validate=True)
    candidate,analysis=import_animation_glb(baseline,content,fps=fps,animation_index=animation_index,object_node_indices=object_nodes)
    proposed=decode_animation_record(candidate);retail=decode_animation_record(b64decode(source['preview']['record_base64'],validate=True))
    if proposed['bone_count']!=retail['bone_count'] or proposed['frame_count']!=retail['frame_count']:
        raise ProjectError('World GLB import must retain the native clip layout')
    edits=[]
    for frame in proposed['frames']:
        f=frame['frame_index']
        for transform in frame['object_transforms']:
            obj=transform['object_index'];before=retail['frames'][f]['object_transforms'][obj]
            row=dict(frame_index=f,object_index=obj)
            for field in ('translation','rotation_psx'):
                axes={axis:value for axis,value,original in zip('xyz',transform[field],before[field]) if value!=original}
                if axes:row[field]=axes
            if len(row)>2:edits.append(row)
    if len(edits)>4096:raise ProjectError('World GLB import exceeds the saved channel-row budget')
    return candidate,edits,analysis


def inspect(project,scene,key,entity_id,frame_index,content,binding,shared_record,animation_index=None,object_nodes=None):
    if shared_record is not True:raise ProjectError('World GLB import requires explicit shared-record consent')
    held=current(project,scene,key,entity_id,frame_index)
    candidate,edits,analysis=prepare_inspected_import(held,content,binding,animation_index,object_nodes)
    native=review(project,scene,key,entity_id,frame_index,edits,True)
    if b64decode(native['proposed_preview']['record_base64'],validate=True)!=candidate:
        raise ProjectError('World GLB candidate differs from the independently reconstructed proposed record')
    result=dict(schema_version='legaia.world-animation-glb-review.v1',project_path=str(project.root),
        scene=scene,source_key=key,entity_id=entity_id,frame_index=frame_index,
        binding=deepcopy(binding),animation_index=animation_index,object_nodes=deepcopy(object_nodes),
        glb_sha256=sha256(content).hexdigest(),byte_length=len(content),candidate_record_sha256=sha256(candidate).hexdigest(),
        analysis=analysis,native_review=native,shared_record=True,read_only=True,project_changed=False,gameplay_verified=False)
    result['review_key']=digest(result)
    _fresh(project,key)
    return result


def validate_input_binding(binding,target):
    import re
    fields={'schema_version','scene_id','scene','animation_id','entity_id','asset_id','project_source_key','object_count','frame_count','source_record_sha256','export_audit'}
    if not isinstance(binding,dict) or set(binding) not in (fields,fields|{'external_object_nodes'}):raise ProjectError('World input binding fields changed')
    scene=binding['scene']
    if (scene not in ('map01','map02','map03') or binding['schema_version']!='legaia.world-animation-glb-input-binding.v1'
            or binding['scene_id']!=f'scene://{scene}/worldmap' or binding['animation_id']!=target
            or not isinstance(target,str) or not re.fullmatch(r'animation://'+scene+r'/worldmap/anm/[0-9]{4}',target)
            or not isinstance(binding['entity_id'],str) or not re.fullmatch(r'scene://'+scene+r'/worldmap/placements/[0-9a-f]{4}',binding['entity_id'])
            or not isinstance(binding['asset_id'],str) or not re.fullmatch(r'asset://'+scene+r'/worldmap/models/[0-9]{4}',binding['asset_id'])
            or type(binding['object_count']) is not int or not 1<=binding['object_count']<=64
            or type(binding['frame_count']) is not int or not 1<=binding['frame_count']<=512
            or any(not isinstance(binding[k],str) or not re.fullmatch(r'[0-9a-f]{64}',binding[k]) for k in ('project_source_key','source_record_sha256'))):
        raise ProjectError('World input source/clip identity changed')
    audit=binding['export_audit']
    if (not isinstance(audit,dict) or audit.get('schema_version')!='legaia.world-animation-export.v1' or audit.get('scene')!=scene
            or audit.get('animation_id')!=target or audit.get('entity_id')!=binding['entity_id'] or audit.get('model_asset_id')!=binding['asset_id']
            or audit.get('source_key')!=binding['project_source_key'] or audit.get('frame_count')!=binding['frame_count'] or audit.get('channel_count')!=binding['object_count']):
        raise ProjectError('World input export audit changed')
    return deepcopy(binding)


def apply(project,scene,key,entity_id,frame_index,content,binding,shared_record,review_key,animation_index=None,object_nodes=None):
    result=inspect(project,scene,key,entity_id,frame_index,content,binding,shared_record,animation_index,object_nodes)
    if result['review_key']!=review_key:raise ProjectError('World GLB or project changed after Review')
    native=result['native_review']
    if not native['project_change']:raise ProjectError('World GLB has no native change to apply')
    from .animation_sources import retain
    held=current(project,scene,key,entity_id,frame_index)
    input_binding=dict(schema_version='legaia.world-animation-glb-input-binding.v1',scene_id=f'scene://{scene}/worldmap',scene=scene,
        animation_id=native['animation_id'],entity_id=entity_id,asset_id=binding['model_asset_id'],project_source_key=key,
        object_count=native['proposed_preview']['channel_count'],frame_count=native['proposed_preview']['frame_count'],
        source_record_sha256=held['source']['before']['preview']['record_sha256'],export_audit=deepcopy(binding))
    if object_nodes is not None:input_binding['external_object_nodes']=deepcopy(object_nodes)
    before=deepcopy((project.overrides,project.animation_sources,project.undo_stack,project.redo_stack))
    after,record=retain(project,project.animation_sources,content,kind='world',target_id=native['animation_id'],binding=input_binding,
        animation_index=animation_index,source_frame_indices=None,candidate_sha256=result['candidate_record_sha256'],review_key=review_key)
    _fresh(project,key)
    try:
        length=len(project.undo_stack)
        project.command(dict(type='set_world_animation_channels',scene=scene,source_key=key,entity_id=entity_id,frame_index=frame_index,
            edits=native['edits'],shared_record=True,review_key=native['review_key']))
        if len(project.undo_stack)!=length+1:raise ProjectError('World GLB requires one native history step')
        project.animation_sources=after
        project.undo_stack[-1]=dict(target='animation_source_import',before=dict(overrides=before[0],animation_sources=before[1]),
            after=dict(overrides=deepcopy(project.overrides),animation_sources=deepcopy(after)))
    except Exception:
        project.overrides,project.animation_sources,project.undo_stack,project.redo_stack=before
        raise
    return dict(result,retained_input=record)


def compare_input(project,catalog,row):
    from .worldmap_animation_binding import verify
    from importer.animation import animation_record_ranges
    from .animation_sources import _library_key
    binding=validate_input_binding(row['binding'],row['target_id']);retail,current,_,_,_=verify(project,binding['scene'])
    index=int(row['target_id'].rsplit('/',1)[1]);ranges=animation_record_ranges(retail)
    if not 0<=index<len(ranges):raise ProjectError('World input clip is absent from Retail')
    start,end=ranges[index]
    if sha256(retail[start:end]).hexdigest()!=binding['source_record_sha256']:raise ProjectError('Historical World clip differs from Retail source')
    record=current[start:end];decoded=decode_animation_record(record);current_hash=sha256(record).hexdigest()
    if catalog['library_key']!=_library_key(project):raise ProjectError('World input comparison changed')
    return dict(schema_version='legaia.animation-source-native-comparison.v1',project_path=catalog['project_path'],library_key=catalog['library_key'],
        receipt_key=row['receipt_key'],scene_id=row['scene_id'],target_id=row['target_id'],kind='world',clip_id=row['target_id'],comparison_scope='world_shared_clip',
        historical_candidate_sha256=row['candidate_sha256'],current_sha256=current_hash,current_byte_length=len(record),frame_count=decoded['frame_count'],
        object_count=decoded['bone_count'],active_in_native_bank=True,matches_current=current_hash==row['candidate_sha256'],project_changed=False,native_content_changed=False)
