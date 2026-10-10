"""Read-only native World group allocation and complete carrier qualification."""
import base64
import struct
from copy import deepcopy
from hashlib import sha256
from importer.assets import decode_tmd
from importer.model_primitives import inspect_model_primitives
from importer.model_face_removal import _groups
from importer.model_face_ledger import (append_group_ledger, _apply_group_allocation,
    _operations, _reserved_faces, _reserved_groups)
from .worldmap_model_faces import _context, _fresh, _budget
from .worldmap_model_allocation import qualify_carrier, GROUP_FORMAT, OBJECT_FORMAT
from .project import ProjectError, digest


def source(project, request):
    _, native, effective, _, _, _, topology = _context(project, request)
    objects = inspect_model_primitives(effective, include_normal_references=True)['objects']
    groups = []
    ordinals = {}
    for owner, start, count, stride, first in _groups(effective, {'objects': objects}):
        index = ordinals.get(owner, 0)
        ordinals[owner] = index + 1
        groups.append(dict(object_index=owner, group_index=index, primitive_count=count,
            first_primitive_index=first, stride=stride, flags=struct.unpack_from('<H', effective, start+2)[0],
            mode=effective[start+7], descriptor_sha256=sha256(effective[start:start+8]).hexdigest(),
            footer_sha256=sha256(effective[start+8+count*stride:start+8+(count+1)*stride]).hexdigest(),
            face_ids=[f['face_id'] for f in topology['faces']
                if f['object_index']==owner and f['group_index']==index]))
    value = dict(schema_version='legaia.worldmap-model-group-source.v1', project_path=str(project.root),
        request=deepcopy(request), source_record=deepcopy(native), topology=topology,
        objects=objects, groups=groups, current_preview=decode_tmd(effective),
        read_only=True, project_changed=False, gameplay_verified=False)
    _fresh(project, request)
    return _budget(value, 16*1024*1024)


def prepare(project, request):
    original, native, effective, base, base_binding, ledger, current_topology = _context(project, request, True)
    candidate, updated, topology = append_group_ledger(base, ledger, request['requests'])
    operations = _operations(ledger)
    independent, _, allocation = _apply_group_allocation(effective,
        {row['face_id']: row for row in current_topology['faces']}, request['requests'],
        _reserved_faces(operations), _reserved_groups(operations))
    if independent != candidate:
        raise ProjectError('World group proposal differs from complete retained replay')
    composed, carrier = qualify_carrier(project, request['asset_id'], original, native,
        effective, candidate, base_binding, updated)
    binding = dict(format=OBJECT_FORMAT if updated['schema_version']=='legaia.model-face-addition-ledger.v7' else GROUP_FORMAT,source_scene_id='worldmap://'+request['asset_id'].split('/')[2]+'/models',
        source_sha256=request['member_sha256'],asset_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate),base_binding=deepcopy(base_binding),ledger=deepcopy(updated))
    value = dict(schema_version='legaia.worldmap-model-group-review.v2', project_path=str(project.root),
        request=deepcopy(request), source_record=deepcopy(native),
        current_sha256=sha256(effective).hexdigest(), proposed_sha256=sha256(candidate).hexdigest(),
        current_byte_length=len(effective), proposed_byte_length=len(candidate),
        proposed_model_base64=base64.b64encode(candidate).decode('ascii'),
        binding=binding, base_binding=deepcopy(base_binding), ledger=updated, current_topology=current_topology,
        topology=topology, allocation=allocation, current_preview=decode_tmd(effective),
        proposed_preview=decode_tmd(candidate), composed_models=composed, carrier=carrier,
        read_only=True, project_changed=False, gameplay_verified=False, build_ready=False,
        scope='native-group-allocation-and-carrier-review-only')
    _budget(value, 16*1024*1024)
    value['review_key'] = digest(value)
    _fresh(project, request)
    return candidate, value


def review(project, request):
    return prepare(project, request)[1]


def apply(project, request, review_key):
    candidate, report = prepare(project, request)
    if report['review_key'] != review_key:
        raise ProjectError('World group allocation differs from its fresh reviewed candidate')
    project._publish_model_ledger(request['asset_id'],candidate,report['binding'],request['source_key'],'World group allocation')


def preview(project, request, review_key):
    from .worldmap_model_faces import _preview_candidate
    candidate, report = prepare(project, request)
    if report['review_key'] != review_key:
        raise ProjectError('World group preview requires its exact fresh Review')
    return _preview_candidate(project,request,review_key,candidate,report,'legaia.worldmap-model-group-preview.v1')
