"""Source-bound, reviewed GLB model interchange through normal replacements.

The external binding describes the effective, unposed source model at export.
Its profile is regenerated from verified source bytes before every import. GLB
mesh data never establishes source ownership, material bindings or capacities.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path

from .project import ProjectError, digest


MAX_GLB_BYTES = 32 * 1024 * 1024
MAX_PROFILE_BYTES = 128 * 1024
MAX_AUDIT_ROWS = 65536
MAX_REVIEW_BYTES = 16 * 1024 * 1024
BINDING_KEYS = {'schema_version', 'asset_id', 'scene_id', 'source_sha256',
                'effective_sha256', 'project_source_key', 'profile'}
QUANTIZATION_KEYS = {'vertex_max_error', 'uv_max_error', 'color_max_error', 'normal_max_error',
                     'quantized_component_count'}
LIMITATIONS = [
    'Existing object, vertex and primitive layout only; no insertion or allocation.',
    'Existing packet corner references may select existing vertices in the same object; counts and capacities remain unchanged.',
    'Source vertex and stored normal coordinates, UVs and qualified raw RGB attributes are rounded to their existing integer domains.',
    'RGB edits use _LEGAIA_SOURCE_RGB in the raw 0..255 byte domain; display COLOR_0 and shader colors are ignored.',
    'The profile and binding describe this exact effective export; export again after project changes.',
    'Normal edits use _LEGAIA_SOURCE_NORMAL signed source words; existing normal references, material words, images and opaque bytes remain unchanged.',
    'The viewport does not reproduce retail normal-based lighting; exact normal words are reviewed as source fields.',
    'Normal Build retains source capacities; gameplay remains unverified.',
]


def _json_size(value, maximum: int, label: str) -> None:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             sort_keys=True, separators=(',', ':')).encode('utf-8')
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ProjectError(f'{label} must be finite JSON metadata') from exc
    if len(encoded) > maximum:
        raise ProjectError(f'{label} exceeds its {maximum}-byte metadata budget')


def _content(content: bytes) -> None:
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_GLB_BYTES:
        raise ProjectError('Choose a GLB file no larger than 32 MiB')


def _quantization(analysis: dict) -> dict:
    if not isinstance(analysis, dict):
        raise ProjectError('Model GLB decoder returned an invalid analysis')
    value = analysis.get('quantization')
    if not isinstance(value, dict) or set(value) != QUANTIZATION_KEYS:
        raise ProjectError('Model GLB decoder must report all source quantization diagnostics')
    for key in QUANTIZATION_KEYS - {'quantized_component_count'}:
        if type(value[key]) not in (int, float) or not math.isfinite(value[key]) or value[key] < 0:
            raise ProjectError('Model GLB quantization errors must be finite nonnegative numbers')
    count = value['quantized_component_count']
    if type(count) is not int or not 0 <= count <= MAX_AUDIT_ROWS:
        raise ProjectError('Model GLB quantized component count exceeds its bounded report')
    return deepcopy(value)


def _texture_preview(project, asset: dict, preview: dict) -> dict:
    """Fresh crop associations, without editor caches or source-state mutations."""
    from importer.textures import (associate_material, load_asset_texture_catalog,
                                   load_scene_texture_catalog, uses_field_party_textures)
    from .resources import apply_texture_overrides

    result = deepcopy(preview)
    result['textures'] = []
    scene = asset.get('source_record', {}).get('prot_entry_name')
    if scene == 'befect_data':
        scene = project.imports[project.active_scene]['scene']['name']
    if not scene:
        return result
    # Keep authored source textures visible, but never import images or material
    # shader edits. The scene key binds these catalogs to the effective export.
    for binding in project.texture_overrides.values():
        if binding['source_scene_id'] == 'scene://' + scene:
            project.read_texture_replacement(binding)
    scene_catalog = apply_texture_overrides(
        project, load_scene_texture_catalog(project.disc_path, scene))
    catalog = load_asset_texture_catalog(project.disc_path, asset, scene_catalog)
    result['texture_scope'] = 'field_party' if uses_field_party_textures(asset) else 'scene'
    result['texture_catalog'] = catalog.metadata()
    budget = 2 * 1024 * 1024
    for index, material in enumerate(result.get('materials', [])):
        material['blend'] = {
            'enabled': bool(material.get('semi_transparent')),
            'mode': ((material['tpage'] >> 5) & 3) if material.get('textured') else 0,
            'texel_gate': 'stp_bit' if material.get('textured') else 'all_fragments',
            'evidence': 'decoded_primitive_ABE_and_tpage_ABR; untextured_ABR0_reference_default',
        }
        if not material.get('textured'):
            result['textures'].append(dict(material_index=index, status='untextured',
                                           reason='Material uses vertex colors'))
            continue
        uvs = [uv for triangle_index, material_index in enumerate(result['triangle_materials'])
               if material_index == index for uv in (result['triangle_uvs'][triangle_index] or [])]
        if not uvs or index >= 32:
            result['textures'].append(dict(material_index=index, status='unsupported',
                                           reason='Missing texture coordinates or bounded preview limit'))
            continue
        bounds = (min(uv[0] for uv in uvs), min(uv[1] for uv in uvs),
                  max(uv[0] for uv in uvs), max(uv[1] for uv in uvs))
        texture = deepcopy(associate_material(catalog, material, bounds))
        rgba, stp = texture.pop('rgba', None), texture.pop('stp', None)
        if rgba is not None:
            if stp is None or len(stp) * 4 != len(rgba) or any(bit not in (0, 1) for bit in stp):
                raise ProjectError('Texture transparency mask does not match decoded pixels')
            if len(rgba) + len(stp) > budget:
                texture = dict(status='unsupported', reason='Decoded texture preview byte budget exceeded')
            else:
                budget -= len(rgba) + len(stp)
                texture['rgba_base64'] = base64.b64encode(rgba).decode('ascii')
                texture['stp_base64'] = base64.b64encode(stp).decode('ascii')
        texture['material_index'] = index
        result['textures'].append(texture)
    return result


def _snapshot(project, asset_id: str) -> dict:
    from importer.assets import decode_tmd, load_model_preview
    from importer.model_authoring import preview_model_shape, replace_model_content
    from importer.model_glb import export_model_glb
    from importer.pipeline import _disc_context
    from .scene_preview import source_key

    if project.mode != 'edit':
        raise ProjectError('Model GLB authoring requires Edit mode')
    if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 512:
        raise ProjectError('Choose an imported model asset')
    document = project.imports.get(project.active_scene)
    asset = next((item for item in (document or {}).get('assets', {}).get('models', [])
                  if item.get('semantic_id') == asset_id), None)
    if asset is None or not project.disc_path:
        raise ProjectError('Model GLB authoring requires an imported model in the active scene')
    key = source_key(project)
    if not key:
        raise ProjectError('Model GLB authoring requires a verified scene source')
    asset = deepcopy(asset)
    with _disc_context(project.disc_path):
        retail = project._model_source(asset_id, project.active_scene)
        authored = project.model_overrides.get(asset_id)
        effective = project.read_model_replacement(asset_id, authored) if authored else retail
        replace_model_content(retail, sha256(retail).hexdigest(), effective)
        preview = load_model_preview(Path(project.disc_path), asset)
        source_geometry = decode_tmd(retail)
        if preview.get('posed') or any(preview.get(field) != source_geometry[field] for field in
                ('objects', 'vertices', 'triangles', 'triangle_uvs', 'triangle_colors',
                 'triangle_materials', 'materials')):
            raise ProjectError('Model export preview differs from the verified unposed source')
        if authored:
            preview = preview_model_shape(preview, effective, authored)
        preview = _texture_preview(project, asset, preview)
        glb, profile = export_model_glb(effective, preview)
        _content(glb)
        if not isinstance(profile, dict) or profile.get('schema_version') != 'legaia.model-glb-profile.v4':
            raise ProjectError('Model GLB exporter returned an invalid source profile')
        _json_size(profile, MAX_PROFILE_BYTES, 'Model GLB profile')
        binding = dict(schema_version='legaia.model-glb-binding.v1', asset_id=asset_id,
                       scene_id=project.active_scene, source_sha256=sha256(retail).hexdigest(),
                       effective_sha256=sha256(effective).hexdigest(), project_source_key=key,
                       profile=deepcopy(profile))
        _json_size(binding, MAX_PROFILE_BYTES, 'Model GLB binding')
    if source_key(project) != key:
        raise ProjectError('Project changed while verifying the model GLB export')
    return dict(binding=binding, retail=retail, effective=effective, glb=glb)


def _current(project, binding: dict) -> None:
    from .scene_preview import source_key
    if source_key(project) != binding['project_source_key']:
        raise ProjectError('Model export is stale; export the current model and binding again')


def _audits(snapshot: dict, candidate: bytes) -> tuple[list, list]:
    from importer.model_authoring import replace_model_content
    _, changes = replace_model_content(snapshot['retail'], snapshot['binding']['source_sha256'], candidate)
    _, pending = replace_model_content(snapshot['effective'], snapshot['binding']['effective_sha256'], candidate)
    if len(changes) > MAX_AUDIT_ROWS or len(pending) > MAX_AUDIT_ROWS:
        raise ProjectError('Model GLB changes exceed the bounded review audit')
    # Qualified existing normal words, corner references, positions, UVs and RGB
    # can add pending changes; no count allocation
    # or packet ownership changes are admitted by the fresh source profile.
    if any(row['kind'] not in ('vertex', 'normal') and
           not (row['kind'] == 'primitive' and row['field'] in ('uv', 'color', 'vertex_index')) for row in pending):
        raise ProjectError('Model GLB import changed an unsupported source field')
    return changes, pending


def _report(snapshot: dict, content: bytes, candidate: bytes, analysis: dict) -> dict:
    from importer.model_primitives import inspect_model_primitives
    binding = snapshot['binding']
    changes, pending = _audits(snapshot, candidate)
    objects = inspect_model_primitives(snapshot['effective'])['objects']
    report = {key: binding[key] for key in BINDING_KEYS - {'schema_version', 'profile'}}
    report.update(schema_version='legaia.model-glb-review.v1',
                  proposed_sha256=sha256(candidate).hexdigest(), glb_sha256=sha256(content).hexdigest(),
                  changes=deepcopy(changes), pending_changes=deepcopy(pending),
                  quantization=_quantization(analysis), limitations=list(LIMITATIONS),
                  object_count=len(objects), vertex_count=sum(obj['vertex_count'] for obj in objects),
                  primitive_count=sum(len(obj['primitives']) for obj in objects),
                  project_changed=False, gameplay_verified=False,
                  scope='TMD-existing-layout-content')
    report['review_key'] = digest(dict(binding=binding, glb_sha256=report['glb_sha256'],
                                     proposed_sha256=report['proposed_sha256'],
                                     changes=changes, pending_changes=pending,
                                     quantization=report['quantization']))
    _json_size(report, MAX_REVIEW_BYTES, 'Model GLB review')
    return report


def export_model(project, asset_id: str) -> tuple[bytes, dict, dict]:
    from importer.model_glb import import_model_glb
    snapshot = _snapshot(project, asset_id)
    candidate, analysis = import_model_glb(snapshot['effective'], snapshot['glb'],
                                          snapshot['binding']['profile'])
    report = _report(snapshot, snapshot['glb'], candidate, analysis)
    if candidate != snapshot['effective'] or report['pending_changes']:
        raise ProjectError('Model GLB export failed exact effective-source roundtrip')
    _current(project, snapshot['binding'])
    return snapshot['glb'], deepcopy(snapshot['binding']), report


def _prepare(project, asset_id: str, content: bytes, binding: dict) -> tuple[bytes, dict]:
    from importer.model_glb import import_model_glb
    _content(content)
    if (not isinstance(binding, dict) or set(binding) != BINDING_KEYS or
            binding.get('schema_version') != 'legaia.model-glb-binding.v1'):
        raise ProjectError('Choose the SDK model export binding JSON sidecar')
    _json_size(binding, MAX_PROFILE_BYTES, 'Model GLB binding')
    snapshot = _snapshot(project, asset_id)
    if digest(binding) != digest(snapshot['binding']):
        raise ProjectError('Model export binding differs from the current source or effective model; export again')
    candidate, analysis = import_model_glb(snapshot['effective'], content, snapshot['binding']['profile'])
    report = _report(snapshot, content, candidate, analysis)
    _current(project, snapshot['binding'])
    return candidate, report


def preview_import(project, asset_id: str, content: bytes, binding: dict) -> dict:
    return _prepare(project, asset_id, content, binding)[1]


def pose_import(project, asset_id: str, content: bytes, binding: dict) -> tuple[bytes, dict]:
    """Return a qualified replacement for the parent's existing pose composer."""
    return _prepare(project, asset_id, content, binding)


def apply_import(project, asset_id: str, content: bytes, binding: dict, review_key: str) -> dict:
    candidate, report = _prepare(project, asset_id, content, binding)
    if review_key != report['review_key']:
        raise ProjectError('GLB or project changed after review; review the model again')
    if not report['pending_changes']:
        raise ProjectError('GLB has no source-quantized model changes to apply')
    project.set_model_replacement(asset_id, candidate)
    return report
