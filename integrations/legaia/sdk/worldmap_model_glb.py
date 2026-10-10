"""Source-bound Current World model GLB authoring export; no project mutation."""
import base64
import json
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner
from .worldmap_model_source import inspect
from .worldmap_geometry import inspect as geometry
from importer.assets import decode_tmd
from importer.model_glb import export_model_glb, import_model_glb


def export(project, request):
    fields={'asset_id','source_key','member_sha256','effective_sha256'}
    if not isinstance(request,dict) or set(request)!=fields:
        raise ProjectError('World model GLB export requires exact inspected Current source fields')
    source=inspect(project,{k:v for k,v in request.items() if k!='effective_sha256'}|{'layer':'current'})
    if source['tmd_sha256']!=request['effective_sha256']:
        raise ProjectError('World Current model changed; inspect again before GLB export')
    content=base64.b64decode(source['tmd_base64'],validate=True)
    scene=request['asset_id'].split('/')[2]
    view=geometry(project,scene,request['source_key'],texture_layer='current')
    asset=next((a for a in view['scene_graph']['assets'] if a['asset_id']==request['asset_id']),None)
    if asset is None or asset['source_record']!=source['source_record']:
        raise ProjectError('World GLB texture view lost native model ownership')
    preview=decode_tmd(content)
    preview['textures']=deepcopy(asset['preview']['textures'])
    glb,profile=export_model_glb(content,preview)
    if not 28<=len(glb)<=32*1024*1024:
        raise ProjectError('World model GLB exceeds its export byte budget')
    candidate,_=import_model_glb(content,glb,profile)
    if candidate!=content:
        raise ProjectError('World model GLB failed exact Current native roundtrip')
    binding=dict(schema_version='legaia.worldmap-model-glb-binding.v1',asset_id=request['asset_id'],
        source_scene_id=owner(request['asset_id']),project_source_key=request['source_key'],
        source_sha256=request['member_sha256'],effective_sha256=request['effective_sha256'],
        profile=profile,scope='existing-native-model-layout')
    if len(json.dumps(binding,allow_nan=False).encode('utf-8'))>128*1024:
        raise ProjectError('World GLB binding exceeds its metadata budget')
    if project.mode!='edit' or state_key(project)!=request['source_key']:
        raise ProjectError('World source changed during GLB export')
    return dict(schema_version='legaia.worldmap-model-glb-export.v1',project_path=str(project.root),
        request=dict(request),source_record=source['source_record'],binding=binding,
        glb_byte_length=len(glb),glb_sha256=sha256(glb).hexdigest(),
        glb_base64=base64.b64encode(glb).decode('ascii'),
        native_roundtrip_sha256=sha256(candidate).hexdigest(),read_only=True,
        project_changed=False,gameplay_verified=False)
