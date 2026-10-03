"""Reviewed, source-qualified material commands without model allocation."""
from copy import deepcopy
from hashlib import sha256
import json

from .project import ProjectError, digest

MAX_METADATA = 16 * 1024 * 1024
MAX_AUDIT = 600000
LIMITATIONS = [
    'Existing qualified primitive bindings and shared packet-group ABE only; no allocation or lighting/type changes.',
    'CLUT coordinates and texture page/depth use source VRAM address semantics, not object transforms.',
    'Group ABE affects every listed source primitive; the model replacement affects every model consumer.',
    'Source-encoded ABR is read only: observed renderers clear those bits and combine caller state.',
    'Unknown/reserved bits, row color/command bytes, normal references, footers and layout remain source owned.',
    'Static texture associations do not prove live VRAM residency, palette animation or hardware blend appearance.',
    'Normal Build retains source capacities; gameplay verification remains deferred.',
]


def _bounded(value, label):
    try:
        content = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             sort_keys=True, separators=(',', ':')).encode('utf-8')
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ProjectError(f'{label} requires finite JSON metadata') from exc
    if len(content) > MAX_METADATA:
        raise ProjectError(f'{label} exceeds its 16 MiB metadata budget')


def _current(project, binding):
    from .scene_preview import source_key
    if project.mode != 'edit' or project.active_scene != binding['scene_id'] or source_key(project) != binding['project_source_key']:
        raise ProjectError('Model material source changed; reopen the material editor')


def _snapshot(project, asset_id):
    from importer.model_materials import inspect_model_materials
    from importer.model_authoring import replace_model_content
    from importer.pipeline import _disc_context
    from .scene_preview import source_key
    if project.mode != 'edit':
        raise ProjectError('Model material authoring requires Edit mode')
    if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 512 or not asset_id.startswith('asset://'):
        raise ProjectError('Choose an imported model asset')
    document = project.imports.get(project.active_scene)
    if not document or not project.disc_path or not any(item['semantic_id'] == asset_id for item in document.get('assets', {}).get('models', [])):
        raise ProjectError('Model material authoring requires an imported model in the active scene')
    key = source_key(project)
    if not key:
        raise ProjectError('Model material authoring requires a verified scene source')
    with _disc_context(project.disc_path):
        retail = project._model_source(asset_id, project.active_scene)
        authored = project.model_overrides.get(asset_id)
        effective = project.read_model_replacement(asset_id, authored) if authored else retail
        replace_model_content(retail, sha256(retail).hexdigest(), effective, allow_normal_references=True)
        current = inspect_model_materials(effective)
        original = inspect_model_materials(retail)
    binding = dict(schema_version='legaia.model-material-source.v1', asset_id=asset_id,
                   scene_id=project.active_scene, source_sha256=sha256(retail).hexdigest(),
                   effective_sha256=sha256(effective).hexdigest(), project_source_key=key,
                   objects=current['objects'], retail_objects=original['objects'], limitations=list(LIMITATIONS))
    _bounded(binding, 'Model material source'); _current(project, binding)
    return dict(binding=binding, retail=retail, effective=effective)


def snapshot(project, asset_id):
    return deepcopy(_snapshot(project, asset_id)['binding'])


def prepare(project, asset_id, edits, expected_sha256, expected_source_key):
    from importer.model_materials import patch_model_materials
    from importer.model_authoring import replace_model_content
    from importer.assets import decode_tmd
    if not isinstance(edits, list) or not 1 <= len(edits) <= 256:
        raise ProjectError('Model material review requires 1 to 256 source edits')
    _bounded(edits, 'Model material draft')
    source = _snapshot(project, asset_id); binding = source['binding']
    if expected_sha256 != binding['effective_sha256'] or expected_source_key != binding['project_source_key']:
        raise ProjectError('Model material source or current model changed; reopen the editor')
    candidate, pending = patch_model_materials(source['effective'], expected_sha256, edits)
    _, changes = replace_model_content(source['retail'], binding['source_sha256'], candidate, allow_normal_references=True)
    if len(changes) > MAX_AUDIT or len(pending) > MAX_AUDIT:
        raise ProjectError('Model material changes exceed the bounded audit')
    if any(row['kind'] != 'primitive_group' and not (row['kind'] == 'primitive' and row['field'] in ('clut', 'tpage')) for row in pending):
        raise ProjectError('Model material draft changed a source-owned geometry field')
    report = {key: binding[key] for key in ('asset_id', 'scene_id', 'source_sha256', 'effective_sha256', 'project_source_key')}
    report.update(schema_version='legaia.model-material-review.v1', proposed_sha256=sha256(candidate).hexdigest(),
                  coordinate_changes=changes, changes_from_current=pending, project_changed=False,
                  gameplay_verified=False, limitations=list(LIMITATIONS))
    report['review_key'] = digest(dict(binding=binding, edits=edits, proposed_sha256=report['proposed_sha256'],
                                      changes=changes, pending=pending))
    report['preview'] = decode_tmd(candidate); report['current_preview'] = decode_tmd(source['effective'])
    _bounded(report, 'Model material review'); _current(project, binding)
    return candidate, report


def reviewed(project, asset_id, edits, expected_sha256, expected_source_key, review_key):
    candidate, report = prepare(project, asset_id, edits, expected_sha256, expected_source_key)
    if not isinstance(review_key, str) or review_key != report['review_key']:
        raise ProjectError('Model material draft changed after review; review it again')
    return candidate, report


def apply(project, asset_id, edits, expected_sha256, expected_source_key, review_key):
    candidate, report = reviewed(project, asset_id, edits, expected_sha256, expected_source_key, review_key)
    if not report['changes_from_current']:
        raise ProjectError('Model material draft has no changes to apply')
    project.set_model_replacement(asset_id, candidate)
    report.pop('preview'); report.pop('current_preview')
    return report
