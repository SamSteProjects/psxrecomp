"""Source-qualified topology review; exact current selections are ephemeral."""
from hashlib import sha256
import json
from importer.assets import decode_tmd
from importer.model_face_removal import remove_faces, FORMAT
from .project import ProjectError
from .scene_preview import source_key
from importer.model_primitives import inspect_model_primitives


def _budget(report, maximum):
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > maximum:
        raise ProjectError('Model face removal metadata exceeds its report budget')
    return report


def source(project, asset_id, expected_key):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Face removal requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    effective = project.read_model_replacement(asset_id, binding) if binding else original
    objects = inspect_model_primitives(effective)['objects']
    report = dict(schema_version='legaia.model-face-removal-source.v1', asset_id=asset_id,
                  source_sha256=sha256(original).hexdigest(), effective_sha256=sha256(effective).hexdigest(),
                  project_source_key=expected_key, objects=[dict(object_index=obj['object_index'],
                  vertex_count=obj['vertex_count'], primitives=[dict(primitive_index=row['primitive_index'],
                  corner_count=row['corner_count']) for row in obj['primitives']]) for obj in objects],
                  removed_faces=binding['removed_faces'] if binding and binding['format'] == FORMAT else [])
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face removal inspection')
    return _budget(report, 4 * 1024 * 1024)


def prepare(project, asset_id, selections, expected_sha256, expected_key):
    if project.mode != 'edit' or not expected_key or source_key(project) != expected_key:
        raise ProjectError('Face removal requires the current Edit source scene')
    original = project._model_source(asset_id, project.active_scene)
    binding = project.model_overrides.get(asset_id)
    effective = project.read_model_replacement(asset_id, binding) if binding else original
    if sha256(effective).hexdigest() != expected_sha256:
        raise ProjectError('Model changed since face removal inspection')
    previous = binding['removed_faces'] if binding and binding['format'] == FORMAT else []
    candidate, removed = remove_faces(original, effective, previous, selections)
    report = dict(schema_version='legaia.model-face-removal.v1', asset_id=asset_id,
                  source_sha256=sha256(original).hexdigest(), effective_sha256=expected_sha256,
                  proposed_sha256=sha256(candidate).hexdigest(), project_source_key=expected_key,
                  selections=selections, removed_faces=removed, previous_removed_faces=previous,
                  current_preview=decode_tmd(effective), preview=decode_tmd(candidate),
                  project_changed=False, gameplay_verified=False, _effective=effective)
    if source_key(project) != expected_key:
        raise ProjectError('Project changed during face removal review')
    return candidate, removed, report


def review(*args):
    report = prepare(*args)[2]
    report.pop('_effective')
    return _budget(report, 64 * 1024 * 1024)
