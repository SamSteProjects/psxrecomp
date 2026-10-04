"""Reviewed native vector allocations retain the independently qualified base."""
from copy import deepcopy
from hashlib import sha256
from importer.assets import decode_tmd
from importer.model_face_ledger import append_vector_ledger,MAX_LEDGER_VECTORS
from importer.model_vector_allocation import append_model_vectors,MAX_ADDRESSABLE_VECTORS,MAX_NEW_VECTORS
from importer.model_primitives import inspect_model_primitives
from .model_face_addition import _context,_budget,FORMAT
from .project import ProjectError
from .scene_preview import source_key


def source(project,asset_id,expected_key):
    original,effective,_,_,_,audit=_context(project,asset_id,expected_key)
    allocated=audit.get('allocated_vector_count',0)
    report=dict(schema_version='legaia.model-vector-allocation-source.v1',asset_id=asset_id,
        source_sha256=sha256(original).hexdigest(),effective_sha256=sha256(effective).hexdigest(),
        project_source_key=expected_key,allocated_vector_count=allocated,
        remaining_vector_budget=MAX_LEDGER_VECTORS-allocated,new_vector_limit=MAX_NEW_VECTORS,
        addressable_table_limit=MAX_ADDRESSABLE_VECTORS,
        objects=[dict(object_index=obj['object_index'],vertex_count=obj['vertex_count'],normal_count=obj['normal_count'],
            primitive_count=len(obj['primitives'])) for obj in inspect_model_primitives(effective,include_normal_references=True)['objects']],
        topology=deepcopy(audit),preview=decode_tmd(effective),project_changed=False,gameplay_verified=False)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during vector allocation inspection')
    return _budget(report,64*1024*1024)


def prepare(project,asset_id,requests,expected_sha256,expected_key):
    original,effective,base,base_binding,ledger,_=_context(project,asset_id,expected_key)
    if sha256(effective).hexdigest()!=expected_sha256:
        raise ProjectError('Model changed since vector allocation inspection')
    candidate,updated,audit=append_vector_ledger(base,ledger,requests)
    independent,allocation=append_model_vectors(effective,expected_sha256,requests)
    if independent!=candidate:raise ProjectError('Vector allocation differs from complete ledger replay')
    binding=dict(format=FORMAT,source_scene_id=project.active_scene,source_sha256=sha256(original).hexdigest(),
        asset_sha256=sha256(candidate).hexdigest(),byte_length=len(candidate),base_binding=base_binding,ledger=updated)
    report=dict(schema_version='legaia.model-vector-allocation-review.v1',asset_id=asset_id,
        source_sha256=binding['source_sha256'],effective_sha256=expected_sha256,proposed_sha256=binding['asset_sha256'],
        project_source_key=expected_key,requests=deepcopy(requests),allocation=allocation,topology=audit,
        current_preview=decode_tmd(effective),preview=decode_tmd(candidate),project_changed=False,gameplay_verified=False)
    if source_key(project)!=expected_key:raise ProjectError('Project changed during vector allocation review')
    return candidate,binding,_budget(report,64*1024*1024)


def review(*args):return prepare(*args)[2]
