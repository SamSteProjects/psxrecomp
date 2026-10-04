"""Source-qualified face additions with a retained, independently valid base edit."""
from copy import deepcopy
from hashlib import sha256
import json

from importer.assets import decode_tmd
from importer.model_face_ledger import create_face_ledger, replay_face_ledger, append_face_ledger
from importer.model_primitives import inspect_model_primitives
from .project import ProjectError
from .scene_preview import source_key

FORMAT = 'tmd-face-addition-v1'
BASE_FORMATS = {'tmd-shape', 'tmd-content-v1', 'tmd-content-v2', 'tmd-content-v3', 'tmd-face-removal-v1'}


def base_content(project, asset_id, original, binding):
    base = binding['base_binding']
    if base is None:
        return original
    if (not isinstance(base, dict) or base.get('format') not in BASE_FORMATS
            or base.get('source_scene_id') != binding['source_scene_id']
            or base.get('source_sha256') != binding['source_sha256']):
        raise ProjectError('Face addition base must be an independently qualified same-source edit')
    return project.read_model_replacement(asset_id, base)


def _context(project, asset_id, expected_key):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Face addition requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    effective = project.read_model_replacement(asset_id, binding) if binding else original
    if binding and binding['format'] == FORMAT:
        base = base_content(project, asset_id, original, binding)
        ledger, base_binding = deepcopy(binding['ledger']), deepcopy(binding['base_binding'])
    else:
        base, base_binding = effective, deepcopy(binding)
        ledger = create_face_ledger(base)
    current, audit = replay_face_ledger(base, ledger)
    if current != effective:
        raise ProjectError('Face addition ledger differs from the current model')
    return original, effective, base, base_binding, ledger, audit


def _budget(report, maximum):
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > maximum:
        raise ProjectError('Face addition report exceeds metadata budget')
    return report


def source(project, asset_id, expected_key):
    original, effective, _, _, _, audit = _context(project, asset_id, expected_key)
    report = dict(schema_version='legaia.model-face-addition-source.v1', asset_id=asset_id,
        source_sha256=sha256(original).hexdigest(), effective_sha256=sha256(effective).hexdigest(),
        project_source_key=expected_key, topology=audit,
        objects=inspect_model_primitives(effective, include_normal_references=True)['objects'],
        preview=decode_tmd(effective),
        project_changed=False, gameplay_verified=False)
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face addition inspection')
    return _budget(report, 64*1024*1024)


def prepare(project, asset_id, requests, expected_sha256, expected_key):
    original, effective, base, base_binding, ledger, _ = _context(project, asset_id, expected_key)
    if sha256(effective).hexdigest() != expected_sha256:
        raise ProjectError('Model changed since face addition inspection')
    candidate, updated, audit = append_face_ledger(base, ledger, requests)
    binding = dict(format=FORMAT, source_scene_id=project.active_scene,
        source_sha256=sha256(original).hexdigest(), asset_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate), base_binding=base_binding, ledger=updated)
    report = dict(schema_version='legaia.model-face-addition-review.v1', asset_id=asset_id,
        source_sha256=binding['source_sha256'], effective_sha256=expected_sha256,
        proposed_sha256=binding['asset_sha256'], project_source_key=expected_key,
        topology=audit, current_preview=decode_tmd(effective), preview=decode_tmd(candidate),
        project_changed=False, gameplay_verified=False)
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face addition review')
    return candidate, binding, _budget(report, 64*1024*1024)


def review(*args):
    return prepare(*args)[2]
