"""Source-bound PNG texture review and ordinary TIM replacement commands."""
from __future__ import annotations

import base64
from copy import deepcopy
from hashlib import sha256
import json
import math

from .project import ProjectError, digest

MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_BINDING_BYTES = 128 * 1024
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 2097152
BINDING_KEYS = {'schema_version', 'asset_id', 'scene_id', 'source_sha256',
                'effective_sha256', 'project_source_key', 'profile'}
QUANTIZATION_KEYS = {'color_max_error', 'color_rms_error', 'quantized_pixel_count',
                     'distinct_requested_words', 'output_palette_size', 'stp_changed_pixels',
                     'forced_black_stp_pixels', 'forced_transparent_stp_pixels'}
LIMITATIONS = [
    'Fixed TIM dimensions, bit depth, VRAM rectangles and source carrier capacities.',
    'PNG RGB uses numeric samples; alpha must be binary. PSX STP is a separate flag.',
    'Existing mode retains palette words; rebuild changes only the selected palette row.',
    'The indexed image plane is shared by every source palette row.',
    'Export a fresh image and binding after any project source change.',
    'Static scene texture associations do not establish live VRAM residency or gameplay acceptance.',
]


def _json_size(value, maximum, label):
    try:
        content = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             sort_keys=True, separators=(',', ':')).encode('utf-8')
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ProjectError(f'{label} requires finite JSON metadata') from exc
    if len(content) > maximum:
        raise ProjectError(f'{label} exceeds its {maximum}-byte metadata budget')


def _content(content):
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_PNG_BYTES:
        raise ProjectError('Choose a PNG file no larger than 8 MiB')


def _current(project, binding):
    from .scene_preview import source_key
    if source_key(project) != binding['project_source_key']:
        raise ProjectError('Texture export is stale; export the current texture and binding again')


def _snapshot(project, asset_id, palette_index):
    from importer.pipeline import _disc_context
    from importer.texture_png import export_texture_png
    from .scene_preview import source_key
    if project.mode != 'edit':
        raise ProjectError('Texture PNG authoring requires Edit mode')
    if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 512 or not asset_id.startswith('texture://'):
        raise ProjectError('Choose an imported texture in the active scene')
    if type(palette_index) is not int or not 0 <= palette_index <= 65535:
        raise ProjectError('Choose an integer source palette index')
    key = source_key(project)
    if not key or not project.disc_path:
        raise ProjectError('Texture PNG authoring requires a verified imported scene source')
    with _disc_context(project.disc_path):
        context = project._texture_context(asset_id)
        options = context.options(asset_id)
        if not options['supported']:
            raise ProjectError(options.get('reason') or 'Texture carrier is not authorable')
        retail = context.original_tim(asset_id)
        authored = project.texture_overrides.get(asset_id)
        effective = project.read_texture_replacement(authored) if authored else retail
        context.validate_replacement(asset_id, effective)
        if len(retail) > 1024 * 1024 or len(effective) > 1024 * 1024:
            raise ProjectError('Texture PNG authoring requires a TIM of at most 1 MiB')
        png, stp, profile = export_texture_png(effective, palette_index)
        _content(png); _content(stp)
        binding = dict(schema_version='legaia.texture-png-binding.v1', asset_id=asset_id,
                       scene_id=project.active_scene, source_sha256=sha256(retail).hexdigest(),
                       effective_sha256=sha256(effective).hexdigest(), project_source_key=key,
                       profile=deepcopy(profile))
        _json_size(binding, MAX_BINDING_BYTES, 'Texture PNG binding')
    _current(project, binding)
    return dict(binding=binding, retail=retail, effective=effective, png=png, stp=stp)


def _quantization(analysis, profile):
    value = analysis.get('quantization') if isinstance(analysis, dict) else None
    if not isinstance(value, dict) or set(value) != QUANTIZATION_KEYS:
        raise ProjectError('Texture PNG decoder must report all quantization diagnostics')
    for field in ('color_max_error', 'color_rms_error'):
        if type(value[field]) not in (int, float) or not math.isfinite(value[field]) or not 0 <= value[field] <= 255:
            raise ProjectError('Texture quantization errors must be finite RGB8 sample errors')
    pixels = profile['width'] * profile['height']
    for field in QUANTIZATION_KEYS - {'color_max_error', 'color_rms_error'}:
        maximum = (pixels if profile['bpp'] == 24 else min(65536, pixels)) if field == 'distinct_requested_words' else (
            profile['entry_count'] if field == 'output_palette_size' else pixels)
        if type(value[field]) is not int or not 0 <= value[field] <= maximum:
            raise ProjectError(f'Texture quantization count is invalid: {field}')
    return deepcopy(value)


def _report(snapshot, png, stp, candidate, analysis, palette_mode):
    from importer.texture_authoring import texture_payload_changes, _validate
    binding = snapshot['binding']; profile = binding['profile']
    _validate(snapshot['retail'], candidate)
    _validate(snapshot['effective'], candidate)
    changes = texture_payload_changes(snapshot['retail'], candidate)
    pending = texture_payload_changes(snapshot['effective'], candidate)
    report = {key: binding[key] for key in BINDING_KEYS - {'schema_version', 'profile'}}
    report.update(schema_version='legaia.texture-png-review.v1',
                  proposed_sha256=sha256(candidate).hexdigest(), png_sha256=sha256(png).hexdigest(),
                  stp_png_sha256=sha256(stp).hexdigest() if stp is not None else None,
                  palette_mode=palette_mode, palette_index=profile['palette_index'],
                  width=profile['width'], height=profile['height'], bpp=profile['bpp'],
                  palette_count=profile['palette_count'], changes=changes, pending_changes=pending,
                  quantization=_quantization(analysis, profile), limitations=list(LIMITATIONS),
                  project_changed=False, gameplay_verified=False, scope='TIM-existing-layout-palette-and-image')
    report['review_key'] = digest(dict(binding=binding, png_sha256=report['png_sha256'],
                                     stp_png_sha256=report['stp_png_sha256'], palette_mode=palette_mode,
                                     proposed_sha256=report['proposed_sha256'], changes=changes,
                                     pending_changes=pending, quantization=report['quantization']))
    _json_size(report, MAX_REPORT_BYTES, 'Texture PNG review')
    return report


def export_texture(project, asset_id, palette_index=0):
    from importer.texture_png import import_texture_png
    snapshot = _snapshot(project, asset_id, palette_index)
    candidate, analysis = import_texture_png(snapshot['effective'], snapshot['png'],
        snapshot['binding']['profile'], 'existing', snapshot['stp'])
    report = _report(snapshot, snapshot['png'], snapshot['stp'], candidate, analysis, 'existing')
    if candidate != snapshot['effective'] or report['pending_changes']['total_change_count']:
        raise ProjectError('PNG export failed exact effective-source roundtrip')
    _current(project, snapshot['binding'])
    return snapshot['png'], snapshot['stp'], deepcopy(snapshot['binding']), report


def _glb_receipt(source, png):
    if source is None:return None
    if not isinstance(source,dict) or set(source)!={'content_base64','image_index','glb_sha256','png_sha256'}:
        raise ProjectError('GLB texture provenance requires exact file and image selection')
    encoded=source['content_base64']
    if not isinstance(encoded,str) or not 1<=len(encoded)<=44739244:
        raise ProjectError('GLB texture provenance requires at most 32 MiB')
    try:content=base64.b64decode(encoded,validate=True)
    except ValueError as exc:raise ProjectError('GLB texture provenance requires valid base64') from exc
    from importer.texture_glb import extract_glb_png
    extracted=extract_glb_png(content,source['image_index'],source['glb_sha256'],source['png_sha256'])
    if base64.b64decode(extracted['png_base64'])!=png:
        raise ProjectError('Edited PNG differs from the selected embedded GLB image')
    row=extracted['image']
    return dict(glb_sha256=extracted['glb_sha256'],png_sha256=row['png_sha256'],image_index=row['image_index'],name=row['name'])


def _prepare(project, asset_id, png, binding, palette_mode='existing', stp=None,glb_source=None):
    from importer.texture_png import import_texture_png
    _content(png)
    if stp is not None:
        _content(stp)
    if (not isinstance(binding, dict) or set(binding) != BINDING_KEYS or
            binding.get('schema_version') != 'legaia.texture-png-binding.v1'):
        raise ProjectError('Choose the SDK texture PNG binding JSON sidecar')
    _json_size(binding, MAX_BINDING_BYTES, 'Texture PNG binding')
    if palette_mode not in ('existing', 'rebuild') or not isinstance(binding.get('profile'), dict):
        raise ProjectError('Choose existing or rebuild palette mode with a source profile')
    snapshot = _snapshot(project, asset_id, binding['profile'].get('palette_index'))
    if digest(binding) != digest(snapshot['binding']):
        raise ProjectError('Texture binding differs from the current source or effective texture; export again')
    candidate, analysis = import_texture_png(snapshot['effective'], png, snapshot['binding']['profile'], palette_mode, stp)
    report = _report(snapshot, png, stp, candidate, analysis, palette_mode)
    receipt=_glb_receipt(glb_source,png)
    if receipt is not None:
        report['glb_source']=receipt
        report['review_key']=digest(dict(review_key=report['review_key'],glb_source=receipt))
        _json_size(report,MAX_REPORT_BYTES,'Texture PNG review')
    _current(project, snapshot['binding'])
    return candidate, report, snapshot


def preview_import(project, asset_id, png, binding, palette_mode='existing', stp=None,glb_source=None):
    return _prepare(project, asset_id, png, binding, palette_mode, stp,glb_source)[1]


def pixels_import(project, asset_id, png, binding, palette_mode='existing', stp=None,glb_source=None):
    from importer.texture_png import export_texture_png
    candidate, report, snapshot = _prepare(project, asset_id, png, binding, palette_mode, stp,glb_source)
    proposed, _, _ = export_texture_png(candidate, report['palette_index'])
    _content(proposed)
    result = dict(report=report, current_png_base64=base64.b64encode(snapshot['png']).decode('ascii'),
                  proposed_png_base64=base64.b64encode(proposed).decode('ascii'),
                  width=report['width'], height=report['height'])
    _json_size(result, 24 * 1024 * 1024, 'Texture pixel preview')
    _current(project, binding)
    return result


def scene_import(project, asset_id, png, binding, palette_mode, stp, review_key,glb_source=None):
    candidate, report, _ = _prepare(project, asset_id, png, binding, palette_mode, stp,glb_source)
    if review_key != report['review_key']:
        raise ProjectError('PNG, flags, palette mode or project changed after review; review again')
    return candidate, report


def apply_import(project, asset_id, png, binding, palette_mode, stp, review_key,glb_source=None):
    candidate, report, snapshot = _prepare(project, asset_id, png, binding, palette_mode, stp,glb_source)
    if review_key != report['review_key']:
        raise ProjectError('PNG, flags, palette mode or project changed after review; review again')
    if not report['pending_changes']['total_change_count']:
        raise ProjectError('PNG has no quantized texture changes to apply')
    if candidate == snapshot['retail']:
        project.command(dict(type='clear_texture_replacement', asset_id=asset_id))
    else:
        project.set_texture_replacement(asset_id, candidate,glb_source=report.get('glb_source'))
    return report
