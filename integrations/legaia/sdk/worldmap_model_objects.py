"""Read-only World object donors and complete native object/carrier proposals.

Objects are native model parts, not scene entities or new World placements.
The proposal family is deliberately not admitted by persistence until its
shared command, Current scene and package paths are qualified.
"""
import base64
import struct
from copy import deepcopy
from hashlib import sha256
from importer.assets import decode_tmd
from importer.model_primitives import inspect_model_primitives
from importer.model_face_removal import _groups
from importer.model_face_ledger import (append_object_ledger, _operations,
    _reserved_faces, _reserved_groups)
from importer.model_object_ledger import source_objects, apply_object_allocation
from .worldmap_model_faces import _context, _fresh, _budget
from .worldmap_model_allocation import qualify_carrier
from .worldmap_model_binding import owner
from .project import ProjectError, digest


FORMAT = 'world-tmd-object-allocation-v1'


def source(project, request):
    _, native, effective, base, _, _, topology = _context(project, request)
    packets = inspect_model_primitives(effective, include_normal_references=True)['objects']
    groups = [[] for _ in packets]
    for object_index, start, count, stride, first in _groups(effective, {'objects': packets}):
        index = len(groups[object_index])
        groups[object_index].append(dict(group_index=index, primitive_count=count,
            first_primitive_index=first, flags=struct.unpack_from('<H', effective, start+2)[0],
            mode=effective[start+7], stride=stride,
            descriptor_sha256=sha256(effective[start:start+8]).hexdigest(),
            footer_sha256=sha256(effective[start+8+count*stride:start+8+(count+1)*stride]).hexdigest(),
            face_ids=[f['face_id'] for f in topology['faces']
                if f['object_index']==object_index and f['group_index']==index]))
    layouts = []
    for index in range(len(packets)):
        vert, nv, normal, nn, prim, claimed, opaque = struct.unpack_from('<7I', effective, 12+index*28)
        end = min([offset+12 for offset, count in ((vert,nv),(normal,nn)) if count] or [len(effective)])
        layouts.append(dict(object_index=index, table_offsets=[vert,normal,prim],
            vertex_count=nv, normal_count=nn, primitive_count=claimed, opaque_metadata=opaque,
            primitive_byte_length=end-prim-12, groups=groups[index],
            primitive_sha256=sha256(effective[prim+12:end]).hexdigest(),
            vertex_sha256=sha256(effective[vert+12:vert+12+nv*8]).hexdigest(),
            normal_sha256=sha256(effective[normal+12:normal+12+nn*8]).hexdigest()))
    value = dict(schema_version='legaia.worldmap-model-object-source.v1', project_path=str(project.root),
        request=deepcopy(request), source_record=deepcopy(native), topology=topology,
        object_identities=deepcopy(topology.get('objects',list(source_objects(base).values()))),
        objects=packets, native_objects=layouts, current_preview=decode_tmd(effective),
        read_only=True, project_changed=False, gameplay_verified=False)
    _fresh(project,request)
    return _budget(value,16*1024*1024)


def prepare(project, request):
    original, native, effective, base, base_binding, ledger, current = _context(project,request,True)
    candidate, updated, topology = append_object_ledger(base,ledger,request['requests'])
    operations = _operations(ledger)
    objects = {row['object_id']:row for row in current.get('objects',source_objects(base).values())}
    reserved = {obj['object_id'] for op in operations if op['kind']=='allocate_objects' for obj in op['requests']}
    independent, _, _, allocation = apply_object_allocation(effective,
        {row['face_id']:row for row in current['faces']}, objects, request['requests'],
        _reserved_faces(operations), _reserved_groups(operations), reserved)
    if independent != candidate:
        raise ProjectError('World object proposal differs from complete retained replay')
    composed, carrier = qualify_carrier(project,request['asset_id'],original,native,
        effective,candidate,base_binding,updated)
    binding = dict(format=FORMAT,source_scene_id=owner(request['asset_id']),
        source_sha256=request['member_sha256'],asset_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate),base_binding=deepcopy(base_binding),ledger=deepcopy(updated))
    value = dict(schema_version='legaia.worldmap-model-object-review.v1',project_path=str(project.root),
        request=deepcopy(request),source_record=deepcopy(native),
        current_sha256=sha256(effective).hexdigest(),proposed_sha256=sha256(candidate).hexdigest(),
        current_byte_length=len(effective),proposed_byte_length=len(candidate),
        proposed_model_base64=base64.b64encode(candidate).decode('ascii'),binding=binding,
        base_binding=deepcopy(base_binding),ledger=updated,current_topology=current,topology=topology,
        allocation=allocation,current_preview=decode_tmd(effective),proposed_preview=decode_tmd(candidate),
        composed_models=composed,carrier=carrier,read_only=True,project_changed=False,
        gameplay_verified=False,build_ready=False,scope='native-object-allocation-and-carrier-review-only')
    _budget(value,16*1024*1024)
    value['review_key'] = digest(value)
    _fresh(project,request)
    return candidate,value


def review(project, request):
    return prepare(project,request)[1]
