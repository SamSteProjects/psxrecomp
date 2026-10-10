"""Read-only World TMD/vector exchange through shared source codecs."""
import base64
import re
from copy import deepcopy
from .project import ProjectError
from .worldmap_authoring import state_key
from importer.worldmap_model_authoring import model_identity, read_worldmap_model
from hashlib import sha256


def inspect(project, request):
    fields={'asset_id','source_key','member_sha256'}
    layered=isinstance(request,dict) and 'layer' in request
    if layered:fields.add('layer')
    if (not isinstance(request,dict) or set(request)!=fields or project.mode!='edit'
            or not project.disc_path or request['source_key']!=state_key(project)
            or not model_identity(request['asset_id']) or not isinstance(request['member_sha256'],str)
            or not re.fullmatch('[0-9a-f]{64}',request['member_sha256'])):
        raise ProjectError('World TMD inspection requires the current Edit source and native member hash')
    if layered and request['layer'] not in ('retail','current'):
        raise ProjectError('Choose Retail or Current World model source')
    content, shape, source=read_worldmap_model(project.disc_path,request['asset_id'])
    if source['decoded_member_sha256']!=request['member_sha256']:
        raise ProjectError('World TMD member changed; refresh source resources')
    identities={doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities!={'sha256:'+source['disc_sha256']}:
        raise ProjectError('World TMD source differs from the imported disc')
    original=content
    effective=project.read_model_replacement(request['asset_id'],project.model_overrides[request['asset_id']]) if layered and request['asset_id'] in project.model_overrides else original
    if layered and request['layer']=='current':
        from importer.model_json import export_shape_json
        content=effective;shape=export_shape_json(content)
    if not 1<=len(content)<=4*1024*1024 or not 1<=len(shape)<=16*1024*1024:
        raise ProjectError('World TMD or vector JSON exceeds its byte budget')
    result=dict(schema_version='legaia.worldmap-model-source.v1',project_path=str(project.root),
                request=dict(request),source_record=source,tmd_byte_length=len(content),
                tmd_sha256=sha256(content).hexdigest(),tmd_base64=base64.b64encode(content).decode('ascii'),
                shape_byte_length=len(shape),shape_sha256=sha256(shape).hexdigest(),
                shape_base64=base64.b64encode(shape).decode('ascii'),layer='retail',read_only=True,
                project_changed=False,gameplay_verified=False)
    if layered:
        result.update(schema_version='legaia.worldmap-model-source.v2',layer=request['layer'],
                      source_tmd_sha256=sha256(original).hexdigest(),effective_tmd_sha256=sha256(effective).hexdigest(),
                      authored=effective!=original,retail_tmd_base64=base64.b64encode(original).decode('ascii'))
    binding=project.model_overrides.get(request['asset_id'])
    if layered and binding and binding['format'] in ('world-tmd-vector-allocation-v1','world-tmd-vector-content-v1','world-tmd-face-addition-v1') and request['layer']=='current':
        from .model_face_addition import base_content
        base=base_content(project,request['asset_id'],original,binding)
        result.update(schema_version='legaia.worldmap-model-source.v5' if binding['format']=='world-tmd-face-addition-v1' else 'legaia.worldmap-model-source.v4',model_format=binding['format'],
                      allocation_binding=deepcopy(binding),base_byte_length=len(base),
                      base_tmd_base64=base64.b64encode(base).decode('ascii'))
    elif layered and binding and binding['format'] not in ('tmd-shape','world-tmd-vector-allocation-v1','world-tmd-vector-content-v1','world-tmd-face-addition-v1'):
        from importer.model_authoring import replace_model_content
        _,changes=replace_model_content(original,source['decoded_member_sha256'],content,allow_normal_references=True)
        result.update(schema_version='legaia.worldmap-model-source.v3',model_format=binding['format'],content_changes=sorted(changes,key=lambda r:r['byte_offset']))
    if project.mode!='edit' or request['source_key']!=state_key(project):
        raise ProjectError('World TMD source changed during inspection')
    return result
