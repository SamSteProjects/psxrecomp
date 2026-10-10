"""Fresh World same-layout TMD/vector JSON Review and shared-history Apply."""
import base64
import json
import re
from hashlib import sha256
from .project import ProjectError,digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner,source
from importer.model_authoring import replace_model_shape
from importer.model_json import import_shape_json


def prepare(project,request):
    fields={'asset_id','source_key','member_sha256','effective_sha256','format','content_base64'}
    if (not isinstance(request,dict) or set(request)!=fields or project.mode!='edit'
            or request['source_key']!=state_key(project) or not owner(request['asset_id'])
            or request['format'] not in ('tmd','json')):
        raise ProjectError('World model replacement requires current Edit source and TMD/vector JSON')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World model replacement requires inspected native and effective hashes')
    text=request['content_base64'];maximum=4*1024*1024 if request['format']=='tmd' else 16*1024*1024
    if not isinstance(text,str) or not 1<=len(text)<=4*((maximum+2)//3):
        raise ProjectError('World model replacement exceeds its byte budget')
    try:content=base64.b64decode(text,validate=True)
    except ValueError as exc:raise ProjectError('World model replacement requires canonical base64 bytes') from exc
    if not 1<=len(content)<=maximum or base64.b64encode(content).decode('ascii')!=text:
        raise ProjectError('World model replacement byte coverage differs')
    original,native=source(project,request['asset_id']);binding=project.model_overrides.get(request['asset_id'])
    effective=project.read_model_replacement(request['asset_id'],binding) if binding else original
    if sha256(original).hexdigest()!=request['member_sha256'] or sha256(effective).hexdigest()!=request['effective_sha256']:
        raise ProjectError('World model source changed; inspect Current again')
    candidate=content if request['format']=='tmd' else import_shape_json(effective,request['effective_sha256'],content)[0]
    candidate,changes=replace_model_shape(original,request['member_sha256'],candidate)
    _,pending=replace_model_shape(effective,request['effective_sha256'],candidate)
    report=dict(schema_version='legaia.worldmap-model-replacement.v1',project_path=str(project.root),
                request={k:v for k,v in request.items() if k!='content_base64'},input_sha256=sha256(content).hexdigest(),
                source_record=native,proposed_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),
                changes_from_retail=changes,changes_from_current=pending,changed=candidate!=effective,
                clears_override=candidate==original,scope='existing-TMD-vertex-normal-XYZ-only',
                project_changed=False,gameplay_verified=False)
    if len(json.dumps(report,allow_nan=False).encode('utf-8'))>16*1024*1024:
        raise ProjectError('World model Review exceeds its metadata budget')
    report['review_key']=digest(report)
    if project.mode!='edit' or request['source_key']!=state_key(project):raise ProjectError('World model source changed during Review')
    return candidate,report


def review(project,request):return prepare(project,request)[1]


def apply(project,request,review_key):
    candidate,report=prepare(project,request)
    if report['review_key']!=review_key:raise ProjectError('World model Apply requires the exact freshly qualified Review')
    if report['changed']:project.set_model_replacement(request['asset_id'],candidate)
    return report
