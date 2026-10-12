"""Fresh PLAYER GLB motion Review/Apply and independently replayed retained input."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import re
from importer.player_animation_glb import import_player_action_glb
from importer.player_battle import actions
from importer.core import ImportError as RetailImportError
from .player_action_authoring import _snapshot,prepare_review
from .player_action_store import _path,retain,publish
from .project import ProjectError,digest,atomic_write

MAX_BYTES=4*1024*1024
KEYS={'schema_version','glb_sha256','glb_byte_length','source_file_sha256','source_file_byte_length','source_action_sha256','fps','equipped','animation_index','object_node_indices','import_digest'}

def _input_path(project,key):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key):raise ProjectError('PLAYER GLB input identity is invalid')
    path=project.root/'Authored'/'PLAYER'/'ActionInputs'/(key+'.glb')
    if not path.resolve().is_relative_to(project.root.resolve()):raise ProjectError('PLAYER GLB input escapes project root')
    return path

def _decode(value):
    if not isinstance(value,str) or not 1<=len(value)<=MAX_BYTES*4//3+4:raise ProjectError('PLAYER motion GLB must be at most 4 MiB')
    try:content=b64decode(value,validate=True)
    except (ValueError,TypeError) as e:raise ProjectError('PLAYER motion GLB requires exact base64 bytes') from e
    if not 1<=len(content)<=MAX_BYTES:raise ProjectError('PLAYER motion GLB must be at most 4 MiB')
    return content

def validate_input(project,retail,slot,action_slot,value):
    if not isinstance(value,dict) or set(value)!=KEYS or value['schema_version']!='legaia.player-action-glb-input.v1':raise ProjectError('PLAYER retained GLB metadata changed')
    glb=_input_path(project,value['glb_sha256']);source=_path(project,value['source_file_sha256'])
    for path,key,size,limit in [(glb,value['glb_sha256'],value['glb_byte_length'],MAX_BYTES),(source,value['source_file_sha256'],value['source_file_byte_length'],4*1024*1024)]:
        if type(size) is not int or not 1<=size<=limit or not path.is_file() or path.stat().st_size!=size or sha256(path.read_bytes()).hexdigest()!=key:raise ProjectError('PLAYER retained GLB input/source missing or changed')
    raw=source.read_bytes()
    import struct
    desc=struct.unpack_from('<I',retail)[0]
    if raw[:16]!=retail[:16] or raw[desc:]!=retail[desc:]:raise ProjectError('PLAYER retained motion baseline changed protected model/source bytes')
    try:_,report=import_player_action_glb(raw,value['source_file_sha256'],slot,action_slot,value['source_action_sha256'],value['equipped'],glb.read_bytes(),fps=value['fps'],animation_index=value['animation_index'],object_node_indices=value['object_node_indices'])
    except (RetailImportError,TypeError,KeyError,ValueError) as e:raise ProjectError('PLAYER retained GLB cannot replay its original import') from e
    if digest(report)!=value['import_digest']:raise ProjectError('PLAYER retained GLB replay receipt changed')

def prepare(project,action_slot,expected_current_sha256,expected_action_sha256,glb_base64,fps,animation_index,object_node_indices,**context):
    record,retail,current,clip,_,_,_=_snapshot(project,action_slot,**context)
    if sha256(current).hexdigest()!=expected_current_sha256 or clip['source_record']['sha256']!=expected_action_sha256:raise ProjectError('PLAYER GLB Current changed; inspect again')
    content=_decode(glb_base64)
    try:candidate,analysis=import_player_action_glb(current,expected_current_sha256,record['player_index'],action_slot,expected_action_sha256,context['equipped'],content,fps=fps,animation_index=animation_index,object_node_indices=object_node_indices)
    except RetailImportError as e:raise ProjectError(str(e)) from e
    _,_,result=prepare_review(project,action_slot,expected_current_sha256,expected_action_sha256,analysis['edits'],**context)
    _,bank=actions(candidate,record['player_index'],'0'*64)
    if sha256(bank).hexdigest()!=result['projection']['proposed_bank_sha256']:raise ProjectError('PLAYER GLB import differs from canonical native action replay')
    evidence=dict(schema_version='legaia.player-action-glb-input.v1',glb_sha256=sha256(content).hexdigest(),glb_byte_length=len(content),source_file_sha256=expected_current_sha256,source_file_byte_length=len(current),source_action_sha256=expected_action_sha256,fps=fps,equipped=deepcopy(context['equipped']),animation_index=animation_index,object_node_indices=deepcopy(object_node_indices),import_digest=digest(analysis))
    if result['binding'] is not None and f'{action_slot:04d}' in result['binding']['actions']:result['binding']['actions'][f'{action_slot:04d}']['glb_import']=evidence
    result.update(operation='import_player_action_glb',glb_import=analysis,retained_input=evidence)
    result.pop('review_key');result['review_key']=digest(result)
    return record,retail,current,content,result

def review(project,**args):return prepare(project,**args)[4]

def apply(project,review_key,**args):
    record,retail,current,content,result=prepare(project,**args)
    if result['review_key']!=review_key:raise ProjectError('PLAYER GLB Apply requires its exact fresh Review')
    if not result['projection']['channels']:raise ProjectError('PLAYER GLB Apply has no native changes')
    retain(project,current)
    path=_input_path(project,result['retained_input']['glb_sha256'])
    if path.exists():
        if path.read_bytes()!=content:raise ProjectError('PLAYER retained GLB bytes changed')
    else:atomic_write(path,content)
    publish(project,record,retail,result['binding'])
    return dict(schema_version='legaia.player-action-apply.v1',binding=result['binding'],retained_input=result['retained_input'],history_steps=1,project_changed=True,gameplay_verified=False)
