"""Fixed-layout monster TMD GLB projection into its original decoded slot."""
from copy import deepcopy
from hashlib import sha256
from .core import ImportError
from .assets import decode_tmd
from .model_glb import export_model_glb,import_model_glb
from .model_authoring import replace_model_content
from .monster_textures import layout,material_crops


def source(data,record,texture):
    origin=record['source_record'];at=origin['byte_offset'];length=origin['byte_length']
    if at<0x4c or at+length>len(data):raise ImportError('Monster model extent changed')
    tmd=data[at:at+length]
    if sha256(tmd).hexdigest()!=origin['sha256']:raise ImportError('Monster model source changed')
    geometry=decode_tmd(tmd);geometry.update(semantic_id=record['semantic_id'],source_record=deepcopy(origin),texture_scope='monster_source_pool')
    if texture is None:geometry['textures']=[]
    else:
        if texture['monster_id']!=record['monster_id'] or texture['model_asset_id']!=record['semantic_id']:raise ImportError('Monster model texture owner changed')
        pool,width=layout(data,texture['source_record']['byte_offset']);geometry['textures']=material_crops(geometry,pool,width,texture['semantic_id'])
    return tmd,geometry


def export(data,record,texture):
    tmd,geometry=source(data,record,texture);glb,profile=export_model_glb(tmd,geometry)
    binding=dict(schema_version='legaia.monster-model-glb-binding.v1',asset_id=record['semantic_id'],source_record=deepcopy(record['source_record']),current_block_sha256=sha256(data).hexdigest(),profile=profile)
    return glb,binding


def convert(data,record,texture,binding,content):
    _,fresh=export(data,record,texture)
    if binding!=fresh:raise ImportError('Monster authoring GLB source binding changed')
    tmd,_=source(data,record,texture);candidate,analysis=import_model_glb(tmd,content,binding['profile'])
    candidate,changes=replace_model_content(tmd,sha256(tmd).hexdigest(),candidate,allow_normal_references=True)
    at=record['source_record']['byte_offset'];end=at+len(tmd);proposed=data[:at]+candidate+data[end:]
    if len(proposed)!=len(data) or proposed[:at]!=data[:at] or proposed[end:]!=data[end:]:raise ImportError('Monster model projection escaped its fixed source extent')
    geometry=decode_tmd(candidate);geometry.update(semantic_id=record['semantic_id'],source_record=deepcopy(record['source_record']),texture_scope='monster_source_pool')
    if texture is not None:
        pool,width=layout(proposed,texture['source_record']['byte_offset']);geometry['textures']=material_crops(geometry,pool,width,texture['semantic_id'])
    else:geometry['textures']=[]
    return proposed,dict(schema_version='legaia.monster-model-projection.v1',source_block_sha256=sha256(data).hexdigest(),candidate_block_sha256=sha256(proposed).hexdigest(),source_tmd_sha256=sha256(tmd).hexdigest(),candidate_tmd_sha256=sha256(candidate).hexdigest(),candidate_tmd_byte_length=len(candidate),changes=changes,glb_analysis=analysis,geometry=geometry,project_changed=False,gameplay_verified=False)
