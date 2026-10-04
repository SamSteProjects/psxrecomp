"""Review native group allocation against stable Current identities before Apply."""
from copy import deepcopy
from hashlib import sha256
import struct
from importer.assets import decode_tmd
from importer.model_face_ledger import (append_group_ledger,_apply_group_allocation,_operations,
    _reserved_faces,MAX_LEDGER_FACES,MAX_BATCHES,MAX_OPERATIONS,MAX_METADATA_BYTES)
from importer.model_group_allocation import MAX_NEW_GROUPS
from importer.model_primitives import inspect_model_primitives
from importer.model_face_removal import _groups
from .model_face_addition import _context,_budget,FORMAT
from .project import ProjectError,digest
from .scene_preview import source_key

LIMITATIONS=[
    'Creates native packet groups in an existing object using a qualified Current donor layout.',
    'Descriptor flags, mode and opaque footer are inherited. Faces use typed Current vertex, normal, UV and RGB fields.',
    'All face donors must belong to the selected Current group. Stable identities remain reserved after deletion.',
    'No new native objects, vector rows, packet families, textures or animations are created by this command.',
    'Review does not change the project. Apply is one Undo step. Gameplay remains unverified.',
]


def source(project,asset_id,expected_key):
    original,effective,_,_,_,audit=_context(project,asset_id,expected_key)
    allocated=audit.get('allocated_group_count',0)
    objects=inspect_model_primitives(effective,include_normal_references=True)['objects']
    normal_vectors=[]
    packet_groups=[[] for _ in objects]
    for owner,start,count,stride,first in _groups(effective,{'objects':objects}):
        packet_groups[owner].append(dict(group_index=len(packet_groups[owner]),byte_offset=start,
            primitive_count=count,first_primitive_index=first,stride=stride,
            flags=struct.unpack_from('<H',effective,start+2)[0],mode=effective[start+7],
            descriptor_sha256=sha256(effective[start:start+8]).hexdigest(),
            footer_sha256=sha256(effective[start+8+count*stride:start+8+(count+1)*stride]).hexdigest()))
    for obj in objects:
        at=12+struct.unpack_from('<I',effective,20+obj['object_index']*28)[0]
        normal_vectors.append([list(struct.unpack_from('<3h',effective,at+index*8))
                               for index in range(obj['normal_count'])])
    report=dict(schema_version='legaia.model-group-allocation-source.v1',asset_id=asset_id,
        source_sha256=sha256(original).hexdigest(),effective_sha256=sha256(effective).hexdigest(),
        project_source_key=expected_key,allocated_group_count=allocated,
        remaining_group_budget=MAX_NEW_GROUPS-allocated,
        remaining_face_budget=MAX_LEDGER_FACES-audit['authored_face_count'],
        remaining_batch_budget=MAX_BATCHES-audit['batch_count'],
        remaining_operation_budget=MAX_OPERATIONS-audit['operation_count'],
        group_limit=MAX_NEW_GROUPS,face_limit=MAX_LEDGER_FACES,
        objects=objects,normal_vectors=normal_vectors,packet_groups=packet_groups,
        table_offsets=[[struct.unpack_from('<I',effective,12+obj['object_index']*28+field)[0]
                        for field in (0,8,16)] for obj in objects],
        topology=deepcopy(audit),preview=decode_tmd(effective),limitations=list(LIMITATIONS),
        project_changed=False,gameplay_verified=False)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during group allocation inspection')
    return _budget(report,64*1024*1024)


def prepare(project,asset_id,requests,expected_sha256,expected_key):
    _budget(requests,MAX_METADATA_BYTES)
    original,effective,base,base_binding,ledger,current=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since group allocation inspection')
    candidate,updated,audit=append_group_ledger(base,ledger,requests)
    operations=_operations(ledger)
    reserved_groups={group['group_id'] for op in operations if op['kind']=='allocate_groups' for group in op['requests']}
    independent,_,allocation=_apply_group_allocation(effective,{row['face_id']:row for row in current['faces']},
        requests,_reserved_faces(operations),reserved_groups)
    if independent!=candidate:raise ProjectError('Group allocation differs from complete ledger replay')
    binding=dict(format=FORMAT,source_scene_id=project.active_scene,source_sha256=sha256(original).hexdigest(),
        asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=base_binding,ledger=updated)
    report=dict(schema_version='legaia.model-group-allocation-review.v1',asset_id=asset_id,
        source_sha256=binding['source_sha256'],effective_sha256=expected_sha256,proposed_sha256=binding['asset_sha256'],
        project_source_key=expected_key,requests=deepcopy(requests),allocation=allocation,topology=audit,
        current_preview=decode_tmd(effective),preview=decode_tmd(candidate),limitations=list(LIMITATIONS),
        project_changed=False,gameplay_verified=False)
    report['review_key']=digest(dict(asset_id=asset_id,source_key=expected_key,effective_sha256=expected_sha256,
        proposed_sha256=binding['asset_sha256'],requests=requests))
    if source_key(project)!=expected_key:raise ProjectError('Project changed during group allocation review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args):return prepare(*args)[2]
