"""Project-local display names for retained clips; never native animation data."""
from copy import deepcopy
import re
from .project import ProjectError, digest
from .scene_preview import source_key

COMMANDS={'set_animation_label','clear_animation_label'}
def target(project,asset_id):
    match=re.fullmatch(r'animation://([a-z0-9]{1,12})/authored-record/([0-9a-f-]{36})',asset_id) if isinstance(asset_id,str) else None
    if not match:raise ProjectError('Choose a retained animation asset identity')
    scene='scene://'+match[1]
    ledger=project.overrides.get(scene,{}).get('AnimationRecords',{})
    if scene not in project.imports or not any(row['record_id']==match[2] for row in ledger.get('records',[])):raise ProjectError('Named animation must remain a retained clip in its imported scene')
    return scene

def name(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=80 or any(ord(c)<32 or ord(c)==127 or 0xD800<=ord(c)<=0xDFFF for c in value):raise ProjectError('Clip name requires 1–80 Unicode characters without controls')
    return value.strip()

def validate_collection(project):
    labels=project.animation_labels
    if not isinstance(labels,dict) or len(labels)>8192:raise ProjectError('Invalid animation display-name collection')
    for asset,value in labels.items():
        scene=target(project,asset)
        if not isinstance(value,dict) or set(value)!={'scene_id','import_sha256','name'} or value['scene_id']!=scene or value['import_sha256']!=digest(project.imports[scene]) or name(value['name'])!=value['name']:raise ProjectError('Animation display name differs from its imported identity')

def key(project):return digest(dict(root=str(project.root),labels=project.animation_labels))

def command(project,body):
    kind=body['type'];fields={'type','asset_id','expected_source_key','expected_labels_key'}|({'name'} if kind=='set_animation_label' else set())
    if kind not in COMMANDS or set(body)!=fields:raise ProjectError('Animation display-name command requires exact fields')
    scene=target(project,body['asset_id'])
    if project.mode!='edit' or scene!=project.active_scene or body['expected_source_key']!=source_key(project) or body['expected_labels_key']!=key(project):raise ProjectError('Animation name source changed; reopen the asset')
    validate_collection(project);asset=body['asset_id'];before=deepcopy(project.animation_labels.get(asset))
    after=dict(scene_id=scene,import_sha256=digest(project.imports[scene]),name=name(body['name'])) if kind=='set_animation_label' else None
    if before==after:return
    if after is not None and asset not in project.animation_labels and len(project.animation_labels)>=8192:raise ProjectError('Animation display-name budget exhausted')
    if after is None:project.animation_labels.pop(asset,None)
    else:project.animation_labels[asset]=after
    project.undo_stack.append(dict(target='animation_labels',asset_id=asset,scene_id=scene,before=before,after=deepcopy(after)));project.redo_stack.clear()
