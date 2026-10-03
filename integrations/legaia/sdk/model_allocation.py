"""Read-only Retail/Current allocation metadata for future topology authoring."""
from hashlib import sha256
import json
from importer.model_allocation import inspect_model_allocation
from .project import ProjectError
from .scene_preview import source_key


def source(project, asset_id, expected_key):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Model allocation inspection requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    current = project.read_model_replacement(asset_id, binding) if binding else original
    report = dict(schema_version='legaia.model-allocation-source.v1', asset_id=asset_id,
        project_source_key=expected_key, source_sha256=sha256(original).hexdigest(),
        effective_sha256=sha256(current).hexdigest(), retail=inspect_model_allocation(original),
        current=inspect_model_allocation(current), project_changed=False, gameplay_verified=False)
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during model allocation inspection')
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > 4*1024*1024:
        raise ProjectError('Model allocation metadata exceeds its report budget')
    return report
