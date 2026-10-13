"""Fresh monster motion GLB proposal Review, before retained Apply integration."""
from base64 import b64decode,b64encode
from hashlib import sha256
from .project import ProjectError,digest
from .battle_character_resources import _fresh
from .monster_motion_authoring import snapshot
from .monster_motions import current_clip
from importer.monster_animation_glb import import_motion
from importer.core import ImportError as NativeError
from importer.serialization import serialize_lzs_decoded
from copy import deepcopy
from .project import atomic_write
import re


def review(project,animation_id,expected_current_block_sha256,glb_base64,fps,animation_index,object_node_indices,**context):
    clip,original,current,raw,used,_,stream=snapshot(project,animation_id,0,0,**context)
    if sha256(current).hexdigest()!=expected_current_block_sha256:raise ProjectError('Monster Current slot changed; inspect its motion again')
    if not isinstance(glb_base64,str) or not 1<=len(glb_base64)<=11200000:raise ProjectError('Monster motion GLB must be at most 8 MiB')
    try:content=b64decode(glb_base64,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('Monster motion GLB requires exact base64 bytes') from e
    if not 28<=len(content)<=8*1024*1024:raise ProjectError('Monster motion GLB must be at most 8 MiB')
    try:
        candidate,analysis=import_motion(current,current_clip(current,clip),content,fps=fps,animation_index=animation_index,object_node_indices=object_node_indices);at=clip['source_record']['compressed_stream_offset'];_,capacity=serialize_lzs_decoded(raw[at:at+used],len(original),candidate,'monster-motion-glb')
    except NativeError as e:raise ProjectError(str(e)) from e
    start=clip['source_record']['byte_offset'];end=start+clip['source_record']['byte_length']
    value=dict(schema_version='legaia.monster-motion-glb-review.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],catalog_source_key=context['catalog_source_key'],asset_id=context['asset_id'],clip=clip,input_sha256=sha256(content).hexdigest(),input_byte_length=len(content),fps=fps,animation_index=animation_index,object_node_indices=object_node_indices,current_block_sha256=expected_current_block_sha256,candidate_block_sha256=sha256(candidate).hexdigest(),analysis=analysis,capacity=capacity,source_motion_base64=b64encode(stream).decode(),candidate_motion_base64=b64encode(candidate[start:end]).decode(),layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_fresh(project,context['expected_project_path'],context['expected_source_key']);return value


def path(project,key,suffix):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key) or suffix not in ('glb','motion'):raise ProjectError('Monster motion input identity changed')
    target=project.root/'Authored'/'MonsterMotionInputs'/(key+'.'+suffix)
    if not target.resolve().is_relative_to(project.root.resolve()):raise ProjectError('Monster motion input escapes project root')
    return target


def read(project,key,size,suffix):
    target=path(project,key,suffix)
    if type(size) is not int or not 1<=size<=(8*1024*1024 if suffix=='glb' else 146882) or not target.is_file() or target.stat().st_size!=size:raise ProjectError('Monster motion input missing or changed size')
    content=target.read_bytes()
    if sha256(content).hexdigest()!=key:raise ProjectError('Monster motion input hash changed')
    return content


def retain(project,content,suffix):
    key=sha256(content).hexdigest();target=path(project,key,suffix)
    if target.exists():read(project,key,len(content),suffix)
    else:atomic_write(target,content)
    return key


def validate_input(project,original,clip,receipt):
    keys={'schema_version','asset_id','model_asset_id','source_record','glb_sha256','glb_byte_length','source_motion_sha256','source_motion_byte_length','fps','animation_index','object_node_indices','import_digest'}
    if not isinstance(receipt,dict) or set(receipt)!=keys or receipt['schema_version']!='legaia.monster-motion-glb-input.v1' or receipt['asset_id']!=clip['semantic_id'] or receipt['model_asset_id']!=clip['model_asset_id'] or receipt['source_record']!=clip['source_record'] or receipt['source_motion_byte_length']!=clip['source_record']['byte_length']:raise ProjectError('Monster motion GLB input provenance changed')
    content=read(project,receipt['glb_sha256'],receipt['glb_byte_length'],'glb');stream=read(project,receipt['source_motion_sha256'],receipt['source_motion_byte_length'],'motion');at=clip['source_record']['byte_offset'];end=at+len(stream);baseline=original[:at]+stream+original[end:]
    try:_,analysis=import_motion(baseline,current_clip(baseline,clip),content,fps=receipt['fps'],animation_index=receipt['animation_index'],object_node_indices=receipt['object_node_indices'])
    except (NativeError,TypeError,ValueError,KeyError) as e:raise ProjectError('Monster original motion GLB cannot replay') from e
    if digest(analysis)!=receipt['import_digest']:raise ProjectError('Monster original motion GLB replay changed')
    return content,stream


def proposal_binding(project,clip,original,candidate,value):
    from .monster_motion_authoring import merge_review_rows
    rows={(e['frame_index'],e['part_index']):deepcopy(e) for e in project.monster_motion_overrides.get(clip['semantic_id'],{}).get('edits',[])}
    for edit in value['analysis']['edits']:
        merge_review_rows(rows,original,clip,dict(frame_index=edit['frame_index'],part_index=edit['part_index'],projection=dict(after={k:edit[k] for k in ('translation','rotation_psx')})))
    if not rows:return None
    derived=current_clip(candidate,clip)
    return dict(schema_version='legaia.monster-motion-override.v1',asset_id=clip['semantic_id'],source_record=deepcopy(clip['source_record']),edits=[rows[k] for k in sorted(rows)],current_motion_sha256=derived['source_record']['sha256'],current_entry_sha256=derived['source_record']['entry_sha256'])


def prepare(project,review_key,**args):
    value=review(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Monster GLB requires exact fresh Review')
    context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')};clip,original,current,_,_,_,_=snapshot(project,args['animation_id'],0,0,**context);at=clip['source_record']['byte_offset'];end=at+clip['source_record']['byte_length'];candidate=current[:at]+b64decode(value['candidate_motion_base64'])+current[end:]
    return value,clip,original,current,candidate,proposal_binding(project,clip,original,candidate,value)


def apply(project,review_key,**args):
    from .monster_motions import validate
    value,clip,original,current,candidate,binding=prepare(project,review_key,**args)
    if not value['analysis']['edits']:raise ProjectError('Monster GLB Apply requires native changes')
    content=b64decode(args['glb_base64']);stream=b64decode(value['source_motion_base64']);receipt=dict(schema_version='legaia.monster-motion-glb-input.v1',asset_id=clip['semantic_id'],model_asset_id=clip['model_asset_id'],source_record=deepcopy(clip['source_record']),glb_sha256=retain(project,content,'glb'),glb_byte_length=len(content),source_motion_sha256=retain(project,stream,'motion'),source_motion_byte_length=len(stream),fps=args['fps'],animation_index=args['animation_index'],object_node_indices=deepcopy(args['object_node_indices']),import_digest=digest(value['analysis']))
    before=deepcopy(project.monster_motion_overrides);after=deepcopy(before)
    if binding:binding['glb_import']=receipt;after[clip['semantic_id']]=binding
    else:after.pop(clip['semantic_id'],None)
    validate(project,after);project.monster_motion_overrides=after;project.undo_stack.append(dict(target='monster_motion_overrides',before=before,after=deepcopy(after),label='Monster GLB motion import'));project.redo_stack.clear()
    return dict(history_steps=1,retained_input=receipt,project_changed=True,gameplay_verified=False)


def proposed_pose(project,review_key,frame_index,**args):
    from .monster_archive import current_pose
    from importer.monster_motion import frame
    from importer.animation import pose_vertices
    value,clip,original,current,candidate,binding=prepare(project,review_key,**args);context={k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')};before=current_pose(project,**context,animation_id=clip['semantic_id'],frame_index=frame_index);derived=current_clip(candidate,clip)
    try:transforms,stream=frame(candidate,derived,frame_index)
    except NativeError as e:raise ProjectError(str(e)) from e
    proposed=deepcopy(before);g=deepcopy(before['base_preview']['geometry']);g['vertices']=pose_vertices(g['vertices'],g['objects'],transforms);g.pop('triangle_normals',None);g.pop('normal_preview',None);g.update(posed=True,coordinate_system='retail_psx_actor_local_y_down',bounds=dict(min=[min(v[i] for v in g['vertices']) for i in range(3)],max=[max(v[i] for v in g['vertices']) for i in range(3)]))
    proposed.update(geometry=g,object_transforms=transforms,source_motion_base64=b64encode(stream).decode(),source_entry_base64=b64encode(candidate[clip['source_record']['entry_offset']:clip['source_record']['entry_end']]).decode(),motion_binding=binding,current_clip=derived,layer='proposed_native_frame')
    _fresh(project,context['expected_project_path'],context['expected_source_key']);return dict(schema_version='legaia.monster-glb-pose.v1',project_path=str(project.root),project_source_key=context['expected_source_key'],review_key=review_key,review=value,frame_index=frame_index,current_pose=before,proposed_pose=proposed,layer='proposed',persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
