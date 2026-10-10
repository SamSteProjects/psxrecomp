"""Read-only World TMD/vector exchange through shared source codecs."""
import base64
import re
from .project import ProjectError
from .worldmap_authoring import state_key
from importer.worldmap_model_authoring import model_identity, read_worldmap_model
from hashlib import sha256


def inspect(project, request):
    fields={'asset_id','source_key','member_sha256'}
    if (not isinstance(request,dict) or set(request)!=fields or project.mode!='edit'
            or not project.disc_path or request['source_key']!=state_key(project)
            or not model_identity(request['asset_id']) or not isinstance(request['member_sha256'],str)
            or not re.fullmatch('[0-9a-f]{64}',request['member_sha256'])):
        raise ProjectError('World TMD inspection requires the current Edit source and native member hash')
    content, shape, source=read_worldmap_model(project.disc_path,request['asset_id'])
    if source['decoded_member_sha256']!=request['member_sha256']:
        raise ProjectError('World TMD member changed; refresh source resources')
    identities={doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities!={'sha256:'+source['disc_sha256']}:
        raise ProjectError('World TMD source differs from the imported disc')
    if not 1<=len(content)<=4*1024*1024 or not 1<=len(shape)<=16*1024*1024:
        raise ProjectError('World TMD or vector JSON exceeds its byte budget')
    result=dict(schema_version='legaia.worldmap-model-source.v1',project_path=str(project.root),
                request=dict(request),source_record=source,tmd_byte_length=len(content),
                tmd_sha256=sha256(content).hexdigest(),tmd_base64=base64.b64encode(content).decode('ascii'),
                shape_byte_length=len(shape),shape_sha256=sha256(shape).hexdigest(),
                shape_base64=base64.b64encode(shape).decode('ascii'),layer='retail',read_only=True,
                project_changed=False,gameplay_verified=False)
    if project.mode!='edit' or request['source_key']!=state_key(project):
        raise ProjectError('World TMD source changed during inspection')
    return result
