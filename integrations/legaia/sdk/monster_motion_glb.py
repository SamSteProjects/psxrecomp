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
