"""Reviewed saved World ANM overrides, explicit shared scope and one history entry."""
from copy import copy,deepcopy
from hashlib import sha256
from importer.worldmap_object_animation import resolve_object_animation
from .worldmap_animation_review import review as native_review
from .worldmap_animation_binding import COMPONENT,SCHEMA,owner,verify,normalize
from .worldmap_placement_allocation import _fresh
from .project import ProjectError,digest
import json


def review(project,scene,key,entity_id,frame_index,edits,shared_record):
    if shared_record is not True:raise ProjectError('World ANM edits require explicit shared-record consent')
    native=native_review(project,scene,key,entity_id,frame_index,edits)
    bank,current,source,disc_hash,_=verify(project,scene)
    if source!=native['before']['animation_source'] or sha256(bank).hexdigest()!=native['before']['preview']['bank_sha256']:
        raise ProjectError('World animation Review changed its native source carrier')
    identifier=owner(scene);old=deepcopy(project.overrides.get(identifier));index=f"{native['audit']['record_index']:04d}"
    binding=deepcopy((old or {}).get(COMPONENT)) or dict(schema_version=SCHEMA,scene=scene,source_disc_sha256=disc_hash,source_bank_sha256=sha256(bank).hexdigest(),entries={})
    canonical=normalize(native['audit'])
    if canonical:binding['entries'][index]=dict(source_record_sha256=native['audit']['source_record_sha256'],edits=canonical)
    else:binding['entries'].pop(index,None)
    after={COMPONENT:binding} if binding['entries'] else None
    view=copy(project);view.overrides=deepcopy(project.overrides)
    if after:view.overrides[identifier]=after
    else:view.overrides.pop(identifier,None)
    _,proposed,_,_,_=verify(view,scene)
    start=native['audit']['byte_offset'];end=start+native['audit']['byte_length']
    if current[:start]!=proposed[:start] or current[end:]!=proposed[end:]:raise ProjectError('World animation edit changed another saved record')
    bind=native['before']['binding']['bind'];geometry=native['current_model_geometry']
    result=dict(schema_version='legaia.world-animation-edit-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,entity_id=entity_id,frame_index=frame_index,animation_id=native['animation_id'],edits=deepcopy(edits),
        shared_record=True,source=native,before_binding=(old or {}).get(COMPONENT),binding=after[COMPONENT] if after else None,
        current_preview=resolve_object_animation(bind,current,geometry,frame_index),
        proposed_preview=resolve_object_animation(bind,proposed,geometry,frame_index),
        current_bank_sha256=sha256(current).hexdigest(),proposed_bank_sha256=sha256(proposed).hexdigest(),
        changed_bytes=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(current,proposed)) if a!=b],
        project_change=old!=after,read_only=True,project_changed=False,gameplay_verified=False,build_ready=False)
    result['review_key']=digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>160*1024*1024:raise ProjectError('World animation saved Review exceeds its private response budget')
    _fresh(project,key)
    return result


def apply(project,command):
    fields={'type','scene','source_key','entity_id','frame_index','edits','shared_record','review_key'}
    if not isinstance(command,dict) or set(command)!=fields or command['type']!='set_world_animation_channels':
        raise ProjectError('World animation Apply requires the exact reviewed source, channels and shared consent')
    result=review(project,command['scene'],command['source_key'],command['entity_id'],command['frame_index'],command['edits'],command['shared_record'])
    if result['review_key']!=command['review_key']:raise ProjectError('World animation Review changed; review again')
    if not result['project_change']:return result
    identifier=owner(command['scene']);before=deepcopy(project.overrides.get(identifier));after={COMPONENT:deepcopy(result['binding'])} if result['binding'] else None
    _fresh(project,command['source_key'])
    if after:project.overrides[identifier]=after
    else:project.overrides.pop(identifier,None)
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()
    return result


def current(project,scene,key,entity_id,frame_index):
    native=native_review(project,scene,key,entity_id,frame_index,[])
    bank,composed,source,_,audits=verify(project,scene)
    if source!=native['before']['animation_source'] or sha256(bank).hexdigest()!=native['before']['preview']['bank_sha256']:
        raise ProjectError('Current World animation has conflicting source carrier evidence')
    result=dict(schema_version='legaia.world-animation-current.v1',project_path=str(project.root),scene=scene,
        source_key=key,entity_id=entity_id,frame_index=frame_index,animation_id=native['animation_id'],
        source=native,binding=deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT)),
        preview=resolve_object_animation(native['before']['binding']['bind'],composed,native['current_model_geometry'],frame_index),
        audits=audits,representation='current-model-current-world-animation',read_only=True,project_changed=False,gameplay_verified=False)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>160*1024*1024:raise ProjectError('Current World animation exceeds its private response budget')
    _fresh(project,key)
    return result
