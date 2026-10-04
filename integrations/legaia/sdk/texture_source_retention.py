"""Upgrade a legacy GLB image receipt without changing native texture bytes."""
from copy import deepcopy

from .project import ProjectError, digest
from .scene_preview import source_key


def _prepare(project, asset_id, expected_sha256, expected_source_key, content):
    if project.mode != 'edit':
        raise ProjectError('Retaining texture sources requires Edit mode')
    if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 512:
        raise ProjectError('Choose an authored texture')
    binding = deepcopy(project.texture_overrides.get(asset_id))
    if not binding or binding['asset_sha256'] != expected_sha256:
        raise ProjectError('Authored texture changed; reopen its source receipt')
    project._validate_texture_binding(binding)
    receipt = binding.get('glb_source')
    if not receipt or 'glb_byte_length' in receipt:
        raise ProjectError('Choose an older GLB image receipt without a retained source')
    key = source_key(project)
    if not key or key != expected_source_key or binding['source_scene_id'] != project.active_scene:
        raise ProjectError('Texture source context changed; review again')
    if not isinstance(content, bytes) or not 28 <= len(content) <= 32 * 1024 * 1024:
        raise ProjectError('Choose the original GLB file, at most 32 MiB')
    from importer.texture_glb import extract_glb_png
    extracted = extract_glb_png(content, receipt['image_index'], receipt['glb_sha256'], receipt['png_sha256'])
    if extracted['image']['name'] != receipt['name']:
        raise ProjectError('GLB image name differs from the recorded source')
    native = project.read_texture_replacement(binding)
    retained = dict(receipt, glb_byte_length=len(content))
    report = dict(schema_version='legaia.texture-source-retention.v1', asset_id=asset_id,
                  effective_sha256=expected_sha256, project_source_key=key, source=retained,
                  native_bytes_changed=False, project_changed=False, gameplay_verified=False)
    report['review_key'] = digest(dict(binding=binding, report=report))
    return report, native


def review(project, asset_id, expected_sha256, source_key, content):
    return _prepare(project, asset_id, expected_sha256, source_key, content)[0]


def apply(project, asset_id, expected_sha256, source_key, content, review_key):
    report, native = _prepare(project, asset_id, expected_sha256, source_key, content)
    if not isinstance(review_key, str) or report['review_key'] != review_key:
        raise ProjectError('Original GLB retention requires the current reviewed file')
    project.set_texture_replacement(asset_id, native, glb_source=report['source'], glb_content=content)
    return dict(report, project_changed=True)
