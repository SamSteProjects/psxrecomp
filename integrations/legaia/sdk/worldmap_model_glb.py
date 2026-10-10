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
    view=geometry(project,scene,request['source_key'],texture_layer='current',model_layer='current')
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


def prepare_import(project,request):
    """Convert against a freshly regenerated Current binding, then native Review."""
    from .project import digest
    from .worldmap_model_replacement import prepare
    if not isinstance(request,dict) or set(request)!={'asset_id','source_key','member_sha256','effective_sha256','binding','glb_base64'}:
        raise ProjectError('World GLB import requires its exact Current context, GLB and export binding')
    encoded=request['glb_base64']
    if not isinstance(encoded,str) or not 40<=len(encoded)<=4*((32*1024*1024+2)//3):
        raise ProjectError('World GLB exceeds its input byte budget')
    try:content=base64.b64decode(encoded,validate=True)
    except ValueError as exc:raise ProjectError('World GLB requires canonical base64 bytes') from exc
    if not 28<=len(content)<=32*1024*1024 or base64.b64encode(content).decode('ascii')!=encoded:
        raise ProjectError('World GLB byte coverage changed')
    binding=request['binding']
    if not isinstance(binding,dict) or len(json.dumps(binding,allow_nan=False).encode('utf-8'))>128*1024:
        raise ProjectError('World GLB binding exceeds its metadata budget')
    context={k:request[k] for k in ('asset_id','source_key','member_sha256','effective_sha256')}
    fresh=export(project,context)
    if digest({k:v for k,v in binding.items() if k!='external_object_nodes'})!=digest(fresh['binding']):raise ProjectError('World GLB binding differs from Current; export again')
    if 'external_object_nodes' in binding:
        nodes=binding['external_object_nodes']
        if not isinstance(nodes,list) or len(nodes)!=len(fresh['binding']['profile']['objects']) or any(type(n) is not int or not 0<=n<1024 for n in nodes) or len(set(nodes))!=len(nodes):
            raise ProjectError('World GLB mapping requires one distinct bounded node per native object')
    source=inspect(project,{k:v for k,v in context.items() if k!='effective_sha256'}|{'layer':'current'})
    effective=base64.b64decode(source['tmd_base64'],validate=True)
    if sha256(effective).hexdigest()!=context['effective_sha256']:raise ProjectError('World Current model changed during GLB conversion')
    candidate,analysis=import_model_glb(effective,content,binding['profile'],**({'object_node_indices':binding['external_object_nodes']} if 'external_object_nodes' in binding else {}))
    native_request={**context,'format':'content-tmd','content_base64':base64.b64encode(candidate).decode('ascii')}
    candidate,native_review=prepare(project,native_request)
    report=dict(schema_version='legaia.worldmap-model-glb-review.v1',project_path=str(project.root),
        request=context,binding=deepcopy(binding),glb_sha256=sha256(content).hexdigest(),glb_byte_length=len(content),
        candidate_base64=base64.b64encode(candidate).decode('ascii'),native_review=native_review,
        analysis=analysis,project_changed=False,gameplay_verified=False)
    report['review_key']=digest(report)
    if len(json.dumps(report,allow_nan=False).encode('utf-8'))>24*1024*1024:raise ProjectError('World GLB Review exceeds its response budget')
    if project.mode!='edit' or state_key(project)!=request['source_key']:raise ProjectError('World source changed during GLB Review')
    return candidate,content,report


def review_import(project,request):return prepare_import(project,request)[2]


def apply_import(project,request,review_key):
    candidate,content,report=prepare_import(project,request)
    if report['review_key']!=review_key:raise ProjectError('World GLB Apply requires its exact fresh Review')
    if not report['native_review']['changed']:raise ProjectError('World GLB has no quantized Current changes to Apply')
    from .model_glb_sources import apply as retain_source
    retain_source(project,request['asset_id'],candidate,content,request['binding'],
                  dict(proposed_sha256=report['native_review']['proposed_sha256'],review_key=review_key))
    return report
