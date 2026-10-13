"""Reviewed whole-pool Retail restoration without deleting recovery inputs."""
from base64 import b64encode
from copy import copy, deepcopy
from hashlib import sha256
import re
import struct

from importer.core import ImportError as NativeError
from importer.monster_textures import layout, pixels
from importer.serialization import serialize_lzs_decoded
from .battle_character_resources import _fresh
from .monster_palettes import snapshot, validate
from .project import ProjectError, digest


def _state(project):
    return digest({name: getattr(project, name, {}) for name in (
        'monster_palette_overrides', 'monster_model_overrides',
        'monster_motion_overrides', 'monster_record_overrides')})


def _capture(project, expected_project_path, expected_source_key, asset_id, palette_index):
    _fresh(project, expected_project_path, expected_source_key)
    if type(palette_index) is not int or not 0 <= palette_index < 15:
        raise ProjectError('Monster texture restoration requires an existing palette')
    state = _state(project)
    catalog, record, original, current, raw, used = snapshot(project, asset_id)
    source = record['source_record']; start = source['byte_offset']; end = start + source['byte_length']
    retail, width = layout(original, start); pool, current_width = layout(current, start)
    if (end != len(original) or len(current) != len(original) or width != current_width
            or source['compressed_bytes_consumed'] != used
            or sha256(original).hexdigest() != source['containing_sha256']
            or sha256(retail).hexdigest() != source['sha256']):
        raise ProjectError('Monster texture source layout or consumed slot span changed')
    owner = deepcopy(project.monster_palette_overrides.get(asset_id))
    view = pixels(pool, width, palette_index)
    view['rgba_base64'] = b64encode(view.pop('rgba')).decode('ascii')
    view['stp_base64'] = b64encode(view.pop('stp')).decode('ascii')
    value = dict(schema_version='legaia.monster-texture-restoration-inspection.v1',
        project_path=str(project.root), project_source_key=expected_source_key,
        catalog_source_key=catalog['source_key'], record=record, palette_index=palette_index,
        owner_before=owner, owner_sha256=digest(owner), current_block_sha256=sha256(current).hexdigest(),
        current_pool_sha256=sha256(pool).hexdigest(), retail_pool_sha256=sha256(retail).hexdigest(),
        current_block_base64=b64encode(current).decode('ascii'), retail_block_base64=b64encode(original).decode('ascii'),
        current_pool_base64=b64encode(pool).decode('ascii'), retail_pool_base64=b64encode(retail).decode('ascii'),
        preview=view, layer='current', read_only=True, project_changed=False, gameplay_verified=False)
    _fresh(project, expected_project_path, expected_source_key)
    if _state(project) != state:
        raise ProjectError('Monster owners changed during texture restoration inspection')
    return value, original, current, raw, used, state


def inspect(project, **args):
    return _capture(project, **args)[0]


def _prepare(project, expected_current_block_sha256, expected_current_pool_sha256,
             expected_owner_sha256, **context):
    if project.mode != 'edit':
        raise ProjectError('Whole monster texture restoration requires Edit mode')
    for key in (expected_current_block_sha256, expected_current_pool_sha256, expected_owner_sha256):
        if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
            raise ProjectError('Inspect the complete Current texture owner before restoration')
    observed, original, current, raw, used, state = _capture(project, **context)
    if (observed['current_block_sha256'] != expected_current_block_sha256
            or observed['current_pool_sha256'] != expected_current_pool_sha256
            or observed['owner_sha256'] != expected_owner_sha256):
        raise ProjectError('Monster Current slot or texture owner changed; inspect again')
    owner = observed['owner_before']
    if owner is None:
        raise ProjectError('Selected monster texture has no authored owner to restore')
    record = observed['record']; source = record['source_record']
    start = source['byte_offset']; end = start + source['byte_length']
    pool = current[start:end]; retail = original[start:end]
    if pool == retail:
        raise ProjectError('Whole monster texture restoration has no native changes')
    candidate = current[:start] + retail + current[end:]
    after = deepcopy(project.monster_palette_overrides); after.pop(context['asset_id'])
    validate(project, after)
    proposed_project = copy(project); proposed_project.monster_palette_overrides = after
    if snapshot(proposed_project, context['asset_id'])[3] != candidate:
        raise ProjectError('Restoration differs from complete remaining-owner composition')
    try:
        compressed = source['compressed_stream_offset']
        _, capacity = serialize_lzs_decoded(raw[compressed:compressed+used], len(original), candidate,
                                          'monster-whole-texture-restoration')
    except NativeError as error:
        raise ProjectError(str(error)) from error
    receipt = owner.get('png_import', {})
    removed = [receipt[key] for key in ('png_sha256', 'stp_sha256') if receipt.get(key)]
    projection = dict(schema_version='legaia.monster-texture-restoration-projection.v1',
        asset_id=context['asset_id'], byte_offset=start, byte_length=len(pool),
        source_block_sha256=observed['current_block_sha256'], candidate_block_sha256=sha256(candidate).hexdigest(),
        source_pool_sha256=observed['current_pool_sha256'], candidate_pool_sha256=source['sha256'],
        unchanged_neighbor_sha256=sha256(current[:start]+current[end:]).hexdigest(),
        byte_change_count=sum(a != b for a, b in zip(pool, retail)),
        restored_palette_word_count=sum(struct.unpack_from('<H', pool, at)[0] != struct.unpack_from('<H', retail, at)[0]
                                        for at in range(0, 480, 2)),
        restored_image_byte_count=sum(a != b for a, b in zip(pool[480:], retail[480:])),
        removed_active_input_sha256=removed, retained_input_files_changed=False)
    value = dict(schema_version='legaia.monster-texture-restoration-review.v1', operation='restore_retail_texture_pool',
        project_path=str(project.root), project_source_key=context['expected_source_key'],
        catalog_source_key=observed['catalog_source_key'], record=record, palette_index=context['palette_index'],
        owner_before=owner, owner_sha256=observed['owner_sha256'], projection=projection, capacity=capacity,
        current_block_base64=observed['current_block_base64'], candidate_block_base64=b64encode(candidate).decode('ascii'),
        current_pool_base64=observed['current_pool_base64'], retail_pool_base64=observed['retail_pool_base64'],
        candidate_pool_base64=observed['retail_pool_base64'], layer='proposed', persistence='not_applied',
        read_only=True, project_changed=False, gameplay_verified=False)
    value['review_key'] = digest(value)
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    if _state(project) != state:
        raise ProjectError('Monster owners changed during whole texture restoration Review')
    return value, after, current, candidate


def review(project, **args):
    return _prepare(project, **args)[0]


def proposed_preview(project, review_key, **args):
    value, _, current, candidate = _prepare(project, **args)
    if value['review_key'] != review_key:
        raise ProjectError('Monster texture preview requires its exact fresh whole-pool Review')
    at = value['projection']['byte_offset']; palette = value['palette_index']; width = value['record']['width']
    views = {}
    for key, block in (('current', current), ('proposed', candidate)):
        view = pixels(block[at:], width, palette)
        view['rgba_base64'] = b64encode(view.pop('rgba')).decode('ascii')
        view['stp_base64'] = b64encode(view.pop('stp')).decode('ascii'); views[key+'_preview'] = view
    _fresh(project, args['expected_project_path'], args['expected_source_key'])
    return dict(schema_version='legaia.monster-texture-restoration-preview.v1',
        project_path=str(project.root), project_source_key=args['expected_source_key'], review_key=review_key,
        review=value, **views, layer='proposed', persistence='not_applied', read_only=True,
        project_changed=False, gameplay_verified=False)


def apply(project, review_key, **args):
    value, after, _, _ = _prepare(project, **args)
    if value['review_key'] != review_key or not value['projection']['byte_change_count']:
        raise ProjectError('Monster texture Apply requires an exact fresh changed whole-pool Review')
    before = deepcopy(project.monster_palette_overrides)
    project.monster_palette_overrides = after
    project.undo_stack.append(dict(target='monster_palette_overrides', before=before, after=deepcopy(after),
                                  label='Restore Retail Monster Texture Pool'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.monster-texture-restoration-apply.v1', asset_id=args['asset_id'],
        removed_active_input_sha256=value['projection']['removed_active_input_sha256'],
        retained_input_files_changed=False, history_steps=1, project_changed=True, gameplay_verified=False)
