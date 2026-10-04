"""Reviewed object duplication with stable clone identities and retained base edits."""
from copy import deepcopy
from hashlib import sha256
import struct
from importer.assets import decode_tmd
from importer.model_face_ledger import (append_object_ledger,_operations,_reserved_faces,_reserved_groups,
                                      MAX_METADATA_BYTES,MAX_LEDGER_FACES,MAX_LEDGER_VECTORS,MAX_BATCHES,MAX_OPERATIONS)
from importer.model_object_ledger import source_objects,apply_object_allocation
from importer.model_object_allocation import MAX_NEW_OBJECTS
from importer.model_group_allocation import MAX_NEW_GROUPS
from importer.model_primitives import inspect_model_primitives
from importer.model_face_removal import _groups
from .model_face_addition import _context,_budget,FORMAT
from .project import ProjectError,digest
from .scene_preview import source_key

LIMITATIONS=[
 'Creates independent native objects by copying complete qualified Current object layouts.',
 'Existing object indices remain unchanged. Every copied group/face receives a new stable authored identity.',
 'Packets, vectors, pads, opaque object metadata and material bindings are inherited; no rig or pose is inferred.',
 'Clone requests must cover all Current donor groups and faces in native order. Empty native groups are not supported.',
 'No scene hierarchy, animation channels, new textures, packet families or arbitrary mesh replacement are created.',
 'Review is read-only; Apply is one Undo step. Runtime rendering and gameplay remain unverified.',
]


def source(project,asset_id,expected_key):
    original,effective,base,_,_,audit=_context(project,asset_id,expected_key)
    objects=audit.get('objects',list(source_objects(base).values()))
    packets=inspect_model_primitives(effective,include_normal_references=True)['objects']
    groups=[[] for _ in packets]
    for owner,start,count,stride,first in _groups(effective,{'objects':packets}):
        groups[owner].append(dict(group_index=len(groups[owner]),primitive_count=count,first_primitive_index=first))
    native=[]
    for owner,obj in enumerate(packets):
        vert,nv,normal,nn,prim,claimed,opaque=struct.unpack_from('<7I',effective,12+owner*28)
        end=min([offset+12 for offset,count in ((vert,nv),(normal,nn)) if count] or [len(effective)])
        native.append(dict(object_index=owner,table_offsets=[vert,normal,prim],opaque_metadata=opaque,
            primitive_byte_length=end-prim-12,groups=groups[owner],
            primitive_sha256=sha256(effective[prim+12:end]).hexdigest(),
            vertex_sha256=sha256(effective[vert+12:vert+12+nv*8]).hexdigest(),
            normal_sha256=sha256(effective[normal+12:normal+12+nn*8]).hexdigest()))
    report=dict(schema_version='legaia.model-object-allocation-source.v1',asset_id=asset_id,
        source_sha256=sha256(original).hexdigest(),effective_sha256=sha256(effective).hexdigest(),
        project_source_key=expected_key,topology=deepcopy(audit),object_identities=deepcopy(objects),
        objects=packets,native_objects=native,
        preview=decode_tmd(effective),remaining_object_budget=MAX_NEW_OBJECTS-audit.get('allocated_object_count',0),
        remaining_group_budget=MAX_NEW_GROUPS-audit.get('allocated_group_count',0),
        remaining_face_budget=MAX_LEDGER_FACES-audit['authored_face_count'],
        remaining_vector_budget=MAX_LEDGER_VECTORS-audit.get('allocated_vector_count',0),
        remaining_batch_budget=MAX_BATCHES-audit['batch_count'],remaining_operation_budget=MAX_OPERATIONS-audit['operation_count'],
        limitations=list(LIMITATIONS),project_changed=False,gameplay_verified=False)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during object allocation inspection')
    return _budget(report,64*1024*1024)


def prepare(project,asset_id,requests,expected_sha256,expected_key):
    _budget(requests,MAX_METADATA_BYTES)
    original,effective,base,base_binding,ledger,current=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:raise ProjectError('Model changed since object allocation inspection')
    candidate,updated,audit=append_object_ledger(base,ledger,requests)
    operations=_operations(ledger);objects={row['object_id']:row for row in current.get('objects',source_objects(base).values())}
    reserved_objects={obj['object_id'] for op in operations if op['kind']=='allocate_objects' for obj in op['requests']}
    independent,_,_,allocation=apply_object_allocation(effective,{row['face_id']:row for row in current['faces']},
        objects,requests,_reserved_faces(operations),_reserved_groups(operations),reserved_objects)
    if independent!=candidate:raise ProjectError('Object allocation differs from complete ledger replay')
    binding=dict(format=FORMAT,source_scene_id=project.active_scene,source_sha256=sha256(original).hexdigest(),
        asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=base_binding,ledger=updated)
    report=dict(schema_version='legaia.model-object-allocation-review.v1',asset_id=asset_id,
        source_sha256=binding['source_sha256'],effective_sha256=expected_sha256,proposed_sha256=binding['asset_sha256'],
        project_source_key=expected_key,requests=deepcopy(requests),allocation=allocation,topology=audit,
        current_preview=decode_tmd(effective),preview=decode_tmd(candidate),limitations=list(LIMITATIONS),
        project_changed=False,gameplay_verified=False)
    report['review_key']=digest(dict(asset_id=asset_id,source_key=expected_key,effective_sha256=expected_sha256,
        proposed_sha256=binding['asset_sha256'],requests=requests))
    if source_key(project)!=expected_key:raise ProjectError('Project changed during object allocation review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args):return prepare(*args)[2]
