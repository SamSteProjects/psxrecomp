"""Read-only World face-growth sources and native model/carrier proposals.

Reviewed Apply uses shared persistence and history; editor controls remain separate.
"""
import base64
import json
import re
from copy import deepcopy
from hashlib import sha256
from importer.assets import decode_tmd
from importer.model_face_ledger import replay_face_ledger, append_face_ledger
from importer.model_primitives import inspect_model_primitives
from importer.model_face_addition import add_model_faces
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner, source as native_source
from .worldmap_model_allocation import retained, qualify_carrier, FACE_FORMAT


def _budget(value, maximum):
    if len(json.dumps(value, allow_nan=False).encode('utf-8')) > maximum:
        raise ProjectError('World face proposal exceeds its metadata budget')
    return value


def _context(project, request, additions=False):
    fields = {'asset_id','source_key','member_sha256','effective_sha256'}
    if additions: fields.add('requests')
    if (not isinstance(request,dict) or set(request)!=fields or project.mode!='edit'
            or request['source_key']!=state_key(project) or not owner(request['asset_id'])):
        raise ProjectError('World face authoring requires the exact Current Edit source')
    if any(not isinstance(request[k],str) or not re.fullmatch('[0-9a-f]{64}',request[k])
           for k in ('member_sha256','effective_sha256')):
        raise ProjectError('World face authoring requires native and effective hashes')
    _budget(request,128*1024)
    identifier=request['asset_id']; original,native=native_source(project,identifier)
    binding=project.model_overrides.get(identifier)
    effective=project.read_model_replacement(identifier,binding) if binding else original
    if sha256(original).hexdigest()!=request['member_sha256'] or sha256(effective).hexdigest()!=request['effective_sha256']:
        raise ProjectError('World face source changed; inspect Current again')
    base,base_binding,ledger=retained(project,identifier,original,binding,effective)
    replayed,topology=replay_face_ledger(base,ledger)
    if replayed!=effective: raise ProjectError('World face ledger differs from Current native bytes')
    return original,native,effective,base,base_binding,ledger,topology


def _fresh(project,request):
    if project.mode!='edit' or state_key(project)!=request['source_key']:
        raise ProjectError('World source changed during face inspection or Review')


def source(project,request):
    original,native,effective,base,base_binding,ledger,topology=_context(project,request)
    value=dict(schema_version='legaia.worldmap-model-face-source.v1',project_path=str(project.root),
        request=deepcopy(request),source_record=deepcopy(native),topology=topology,
        objects=inspect_model_primitives(effective,include_normal_references=True)['objects'],
        current_preview=decode_tmd(effective),read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,request)
    return _budget(value,16*1024*1024)


def prepare(project,request):
    original,native,effective,base,base_binding,ledger,current_topology=_context(project,request,True)
    candidate,updated,topology=append_face_ledger(base,ledger,request['requests'])
    faces={row['face_id']:row for row in current_topology['faces']}
    additions=[]
    for row in request['requests']:
        donor=faces[row['donor_face_id']]
        additions.append(dict(face_id=row['face_id'],object_index=donor['object_index'],
            group_index=donor['group_index'],donor_primitive_index=donor['current_primitive_index'],fields=deepcopy(row['fields'])))
    independent,addition=add_model_faces(effective,request['effective_sha256'],additions)
    if independent!=candidate: raise ProjectError('World face candidate differs from direct native addition')
    composed,carrier=qualify_carrier(project,request['asset_id'],original,native,effective,candidate,base_binding,updated)
    binding=dict(format=FACE_FORMAT,source_scene_id=owner(request['asset_id']),
        source_sha256=sha256(original).hexdigest(),asset_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate),base_binding=deepcopy(base_binding),ledger=deepcopy(updated))
    value=dict(schema_version='legaia.worldmap-model-face-addition-review.v2',project_path=str(project.root),
        request=deepcopy(request),source_record=deepcopy(native),
        current_sha256=sha256(effective).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
        current_byte_length=len(effective),proposed_byte_length=len(candidate),
        proposed_model_base64=base64.b64encode(candidate).decode('ascii'),
        binding=binding,base_binding=deepcopy(base_binding),ledger=updated,current_topology=current_topology,topology=topology,addition=addition,
        current_preview=decode_tmd(effective),proposed_preview=decode_tmd(candidate),
        composed_models=composed,carrier=carrier,read_only=True,project_changed=False,
        gameplay_verified=False,build_ready=False,scope='native-face-addition-and-carrier-review-only')
    _budget(value,16*1024*1024);value['review_key']=digest(value);_fresh(project,request)
    return candidate,value


def review(project,request):
    return prepare(project,request)[1]


def apply(project,request,review_key):
    candidate,report=prepare(project,request)
    if review_key!=report['review_key']:
        raise ProjectError('World face addition differs from its fresh reviewed candidate')
    project._publish_model_ledger(request['asset_id'],candidate,report['binding'],request['source_key'],'World face addition')


def preview(project, request, review_key):
    """Fresh textured scene graphs for a face proposal; no files or history written."""
    from copy import copy
    from .worldmap_geometry import inspect
    candidate, report = prepare(project, request)
    if report['review_key'] != review_key:
        raise ProjectError('World face preview requires its exact fresh Review')
    scene = request['asset_id'].split('/')[2]
    retail = inspect(project, scene, request['source_key'], texture_layer='retail', model_layer='retail')
    current = inspect(project, scene, request['source_key'], texture_layer='current', model_layer='current')
    view = copy(project)
    view.model_overrides = deepcopy(project.model_overrides)
    view.model_overrides[request['asset_id']] = deepcopy(report['binding'])
    original_read = project.read_model_replacement
    def read(identifier, binding):
        if identifier == request['asset_id']:
            if binding != report['binding']:
                raise ProjectError('World face preview lost its reviewed binding')
            return candidate
        return original_read(identifier, binding)
    view.read_model_replacement = read
    proposed = inspect(view, scene, state_key(view), texture_layer='current', model_layer='current')
    proposed['project_source_key'] = request['source_key']
    proposed['model_layer'] = 'proposed'
    proposed['representation'] = 'proposed-source'
    value = dict(schema_version='legaia.worldmap-model-face-preview.v1',
        project_path=str(project.root), request=deepcopy(request), review_key=review_key,
        current_sha256=request['effective_sha256'], proposed_sha256=report['proposed_sha256'],
        retail_graph=retail, current_graph=current, proposed_graph=proposed,
        read_only=True, project_changed=False, gameplay_verified=False)
    _budget(value, 64*1024*1024)
    _fresh(project, request)
    return value
