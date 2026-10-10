"""Fresh World same-layout TMD/vector JSON Review and shared-history Apply."""
import base64
import json
import re
from hashlib import sha256
from .project import ProjectError,digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner,source
from importer.model_authoring import replace_model_shape,replace_model_content
from importer.model_json import import_shape_json


def prepare(project,request):
    fields={'asset_id','source_key','member_sha256','effective_sha256','format','content_base64'}
    if (not isinstance(request,dict) or set(request)!=fields or project.mode!='edit'
            or request['source_key']!=state_key(project) or not owner(request['asset_id'])
            or request['format'] not in ('tmd','json','content-tmd')):
        raise ProjectError('World model replacement requires current Edit source and TMD/vector JSON')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k]) for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World model replacement requires inspected native and effective hashes')
    text=request['content_base64'];maximum=4*1024*1024 if request['format']!='json' else 16*1024*1024
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
    candidate=content if request['format']!='json' else import_shape_json(effective,request['effective_sha256'],content)[0]
    from .worldmap_model_allocation import FORMATS,CONTENT_FORMAT,FACE_FORMAT
    if binding and binding['format'] in FORMATS:
        from copy import deepcopy
        from .model_face_addition import base_content
        from importer.model_face_ledger import append_content_ledger
        if request['format']!='content-tmd':replace_model_shape(effective,request['effective_sha256'],candidate)
        candidate,pending=replace_model_content(effective,request['effective_sha256'],candidate,allow_normal_references=True)
        base=base_content(project,request['asset_id'],original,binding)
        replay,ledger,_=append_content_ledger(base,binding['ledger'],candidate)
        if replay!=candidate:raise ProjectError('Allocated content differs from complete native ledger replay')
        proposed=deepcopy(binding)
        if candidate!=effective:
            proposed.update(format=FACE_FORMAT if binding['format']==FACE_FORMAT else CONTENT_FORMAT,asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),ledger=ledger)
        report=dict(schema_version='legaia.worldmap-model-replacement.v3',project_path=str(project.root),
            request={k:v for k,v in request.items() if k!='content_base64'},input_sha256=sha256(content).hexdigest(),
            source_record=native,proposed_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),
            changes_from_retail=None,changes_from_current=sorted(pending,key=lambda r:r['byte_offset']),
            changed=candidate!=effective,clears_override=False,scope='allocated-TMD-existing-layout-content',
            proposed_binding=proposed,project_changed=False,gameplay_verified=False)
        if len(json.dumps(report,allow_nan=False).encode('utf-8'))>16*1024*1024:
            raise ProjectError('Allocated content Review exceeds its metadata budget')
        report['review_key']=digest(report)
        if project.mode!='edit' or state_key(project)!=request['source_key']:raise ProjectError('World source changed during allocated content Review')
        return candidate,report
    extended=request['format']=='content-tmd' or binding is not None and binding['format']!='tmd-shape'
    if request['format']!='content-tmd':replace_model_shape(effective,request['effective_sha256'],candidate)
    if extended:
        candidate,changes=replace_model_content(original,request['member_sha256'],candidate,allow_normal_references=True)
        _,pending=replace_model_content(effective,request['effective_sha256'],candidate,allow_normal_references=True)
        changes.sort(key=lambda r:r['byte_offset']);pending.sort(key=lambda r:r['byte_offset'])
    else:
        candidate,changes=replace_model_shape(original,request['member_sha256'],candidate)
        _,pending=replace_model_shape(effective,request['effective_sha256'],candidate)
    report=dict(schema_version='legaia.worldmap-model-replacement.v2' if extended else 'legaia.worldmap-model-replacement.v1',project_path=str(project.root),
                request={k:v for k,v in request.items() if k!='content_base64'},input_sha256=sha256(content).hexdigest(),
                source_record=native,proposed_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),
                changes_from_retail=changes,changes_from_current=pending,changed=candidate!=effective,
                clears_override=candidate==original,scope='existing-TMD-layout-content' if extended else 'existing-TMD-vertex-normal-XYZ-only',
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
    if report['changed']:
        if 'proposed_binding' in report:
            project._publish_model_ledger(request['asset_id'],candidate,report['proposed_binding'],request['source_key'],'World allocated content')
        else:project.set_model_replacement(request['asset_id'],candidate)
    return report


def preview(project,request,review_key):
    """Read-only object-local geometry for an exact, freshly recomputed Review."""
    from importer.assets import decode_tmd
    candidate,report=prepare(project,request)
    if report['review_key']!=review_key:
        raise ProjectError('World model preview requires the exact freshly qualified Review')
    original,native=source(project,request['asset_id'])
    if native!=report['source_record'] or sha256(original).hexdigest()!=request['member_sha256']:
        raise ProjectError('World model native source changed during comparison')
    binding=project.model_overrides.get(request['asset_id'])
    effective=project.read_model_replacement(request['asset_id'],binding) if binding else original
    if sha256(effective).hexdigest()!=request['effective_sha256']:
        raise ProjectError('World model Current bytes changed during comparison')
    def geometry(content):
        decoded=decode_tmd(content)
        return {k:decoded[k] for k in ('vertices','triangles')}
    value=dict(schema_version='legaia.worldmap-model-comparison.v1',project_path=str(project.root),
        asset_id=request['asset_id'],source_key=request['source_key'],review_key=review_key,
        current_sha256=request['effective_sha256'],proposed_sha256=report['proposed_sha256'],
        current=geometry(effective),proposed=geometry(candidate),
        coordinate_system='retail_tmd_object_local_y_down',read_only=True,
        project_changed=False,gameplay_verified=False)
    if len(json.dumps(value,allow_nan=False).encode('utf-8'))>16*1024*1024:
        raise ProjectError('World model comparison exceeds its geometry budget')
    if request['source_key']!=state_key(project):
        raise ProjectError('World model source changed during comparison')
    return value


def material_preview(project,request,review_key):
    """Current/proposed model graphs with fresh Current TIM association; never Apply."""
    import copy
    from .worldmap_geometry import inspect as inspect_geometry
    from .worldmap_current_textures import compose
    from importer.model_authoring import preview_model_shape
    candidate,report=prepare(project,request)
    if report['review_key']!=review_key:raise ProjectError('Material preview requires the exact freshly qualified Review')
    current=inspect_geometry(project,request['asset_id'].split('/')[2],request['source_key'],texture_layer='current',model_layer='current')
    proposed=copy.deepcopy(current)
    asset=next((a for a in proposed['scene_graph']['assets'] if a['asset_id']==request['asset_id']),None)
    if asset is None or asset['source_record']!=report['source_record']:raise ProjectError('Material proposal lost native source ownership')
    changes=report['changes_from_current'] if 'proposed_binding' in report else report['changes_from_retail']
    normal=any(r['kind']=='primitive' and r['field']=='normal_index' for r in changes)
    material=any(r['kind']=='primitive_group' or r['kind']=='primitive' and r['field'] in ('clut','tpage') for r in changes)
    primitive=any(r['kind']=='primitive' for r in changes)
    binding=dict(format='tmd-content-v3' if normal else 'tmd-content-v2' if material else 'tmd-content-v1' if primitive else 'tmd-shape',source_scene_id=owner(request['asset_id']),source_sha256=request['member_sha256'],asset_sha256=report['proposed_sha256'],byte_length=len(candidate))
    if 'proposed_binding' in report:binding=report['proposed_binding']
    asset['preview']=preview_model_shape(asset['preview'],candidate,binding)
    compose(project,proposed,force=True)
    for preview in [proposed['preview']]+[a['preview'] for a in proposed['scene_graph']['assets']]:
        for texture in preview.get('textures',[]):
            for raw,encoded in (('rgba','rgba_base64'),('stp','stp_base64')):
                if raw in texture:texture[encoded]=base64.b64encode(texture.pop(raw)).decode('ascii')
    proposed['model_layer']='proposed';proposed['representation']='proposed-source';proposed.pop('model_authoring',None)
    value=dict(schema_version='legaia.worldmap-model-material-comparison.v1',project_path=str(project.root),asset_id=request['asset_id'],source_key=request['source_key'],review_key=review_key,current_sha256=request['effective_sha256'],proposed_sha256=report['proposed_sha256'],current_graph=current,proposed_graph=proposed,read_only=True,project_changed=False,gameplay_verified=False)
    if len(json.dumps(value,allow_nan=False).encode('utf-8'))>64*1024*1024:raise ProjectError('World material comparison exceeds its response budget')
    if project.mode!='edit' or state_key(project)!=request['source_key']:raise ProjectError('World source changed during material comparison')
    return value
