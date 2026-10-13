"""Reviewed whole-model owner removal with literal composed-slot preservation."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError, digest
from .battle_character_resources import _fresh
from .monster_model_authoring import snapshot, model_baseline, texture_context
from .monster_models import effective, validate
from .monster_motions import compose as compose_motion
from importer.monster_archive import decode_catalog
from importer.monster_model_authoring import source as model_source
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError


def _sha(data):
    return sha256(data).hexdigest()


def _encoded(data):
    return b64encode(data).decode()


def _prepare(project, expected_current_block_sha256, **context):
    record, texture, original, current, raw, used = snapshot(project, **context)
    if _sha(current) != expected_current_block_sha256:
        raise ProjectError('Monster Current slot changed; inspect before restoring its model')
    identifier = record['semantic_id']
    owner = project.monster_model_overrides.get(identifier)
    if not owner:
        raise ProjectError('Selected monster model has no authored model to restore')
    source = record['source_record']
    start, size = source['byte_offset'], source['byte_length']
    end = start + size
    owned = effective(project, original, record, texture, owner)
    retail = original[start:end]
    normalized = model_baseline(original, current, raw, record)
    if owned == retail or normalized[start:end] != owned:
        raise ProjectError('Monster whole-model restoration has no qualified native changes')
    catalog = decode_catalog(raw, source['disc']['sha256'])
    # The source TMD extent contains opaque action neighbors. Replace its Retail
    # extent first, then recompose every Current motion owner over that extent.
    candidate = current[:start] + retail + current[end:]
    candidate = compose_motion(original, catalog, record['monster_id'],
                               project.monster_motion_overrides, candidate, project=project)
    expected = [(start + row['byte_offset'], row['after_byte'], row['before_byte'])
                for row in owner['edits']]
    actual = [(i, a, b) for i, (a, b) in enumerate(zip(current, candidate)) if a != b]
    if len(candidate) != len(current) or not expected or actual != expected:
        raise ProjectError('Monster restoration must reverse only the owned model byte ledger')
    if current[:0x4c] != candidate[:0x4c]:
        raise ProjectError('Monster restoration changed the Current record header')
    motions = []
    for clip in catalog['animations']:
        if clip['monster_id'] != record['monster_id']:
            continue
        native = clip['source_record']; at = native['byte_offset']; stop = at + native['byte_length']
        before, after = current[at:stop], candidate[at:stop]
        if before != after:
            raise ProjectError('Monster model restoration changed Current motion bytes')
        motions.append(dict(animation_id=clip['semantic_id'], source_record=deepcopy(native),
                            current_sha256=_sha(before), candidate_sha256=_sha(after)))
    after = deepcopy(project.monster_model_overrides)
    after.pop(identifier)
    validate(project, after)
    try:
        compressed = source['compressed_stream_offset']
        _, capacity = serialize_lzs_decoded(raw[compressed:compressed + used], len(original),
                                           candidate, 'monster-model-restoration')
    except NativeError as e:
        raise ProjectError(str(e)) from e
    owned_offsets = {row[0] for row in expected}
    unchanged = bytes(v for i, v in enumerate(current) if i not in owned_offsets)
    removed = [dict(import_index=i, sha256=r['glb_sha256'], byte_length=r['glb_byte_length'])
               for i, r in enumerate(owner['inputs'])]
    pool_start = texture['source_record']['byte_offset'] if texture else len(current)
    projection = dict(schema_version='legaia.monster-model-restoration-projection.v1', asset_id=identifier,
        byte_offset=start, byte_length=size, source_block_sha256=_sha(current), candidate_block_sha256=_sha(candidate),
        source_tmd_sha256=_sha(owned), candidate_tmd_sha256=_sha(retail), byte_change_count=len(expected),
        unchanged_outside_ledger_sha256=_sha(unchanged), unchanged_header_sha256=_sha(current[:0x4c]),
        unchanged_pool_sha256=_sha(current[pool_start:]) if texture else None,
        removed_active_inputs=removed, preserved_motion_streams=motions)
    value = dict(schema_version='legaia.monster-model-restoration-review.v1', operation='restore_retail_model',
        project_path=str(project.root), project_source_key=context['expected_source_key'],
        catalog_source_key=context['catalog_source_key'], asset_id=identifier, record=record,
        projection=projection, capacity=capacity, model_binding=deepcopy(owner),
        current_tmd_base64=_encoded(owned), retail_tmd_base64=_encoded(retail), candidate_tmd_base64=_encoded(retail),
        current_block_base64=_encoded(current), candidate_block_base64=_encoded(candidate),
        motion_bindings={k:deepcopy(v) for k,v in project.monster_motion_overrides.items()
                         if v['source_record']['monster_id'] == record['monster_id']},
        layer='proposed', persistence='not_applied', read_only=True, project_changed=False, gameplay_verified=False)
    value.update(texture_context(project, texture, original, current))
    value['review_key'] = digest(value)
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    return value, after, record, texture, original, current, candidate, raw


def review(project, **args):
    return _prepare(project, **args)[0]


def apply(project, review_key, **args):
    value, after, *_ = _prepare(project, **args)
    if value['review_key'] != review_key or not value['projection']['byte_change_count']:
        raise ProjectError('Monster model restoration requires its exact fresh changed Review')
    before = deepcopy(project.monster_model_overrides)
    project.monster_model_overrides = after
    project.undo_stack.append(dict(target='monster_model_overrides', before=before, after=deepcopy(after),
                                  label='Restore Retail Monster Model'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.monster-model-restoration-apply.v1', asset_id=args['asset_id'],
                removed_active_inputs=value['projection']['removed_active_inputs'],
                history_steps=1, project_changed=True, gameplay_verified=False)


def proposed_preview(project, review_key, **args):
    from .monster_archive import current_preview
    value, _, record, texture, original, current, candidate, raw = _prepare(project, **args)
    if value['review_key'] != review_key:
        raise ProjectError('Monster restoration preview requires its exact fresh Review')
    context = {k:args[k] for k in ('expected_project_path','expected_source_key','asset_id','catalog_source_key')}
    before = current_preview(project, **context)
    if before['source_tmd_base64'] != value['current_tmd_base64'] or before['model_binding'] != value['model_binding']:
        raise ProjectError('Monster Current preview differs from its reviewed model')
    proposed = deepcopy(before)
    normalized = model_baseline(original, candidate, raw, record)
    try:
        _, geometry = model_source(normalized, record, texture)
    except NativeError as e:
        raise ProjectError(str(e)) from e
    for crop in geometry['textures']:
        for key in ('rgba','stp'):
            if key in crop:
                crop[key + '_base64'] = _encoded(crop.pop(key))
    proposed.update(geometry=geometry, source_tmd_base64=value['candidate_tmd_base64'],
                    model_binding=None, current_block_sha256=value['projection']['candidate_block_sha256'],
                    layer='proposed_native_model')
    before['current_block_sha256'] = value['projection']['source_block_sha256']
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    return dict(schema_version='legaia.monster-model-restoration-preview.v1',
        project_path=str(project.root), project_source_key=context['expected_source_key'], review_key=review_key,
        review=value, current_preview=before, proposed_preview=proposed,
        layer='proposed', persistence='not_applied', read_only=True, project_changed=False, gameplay_verified=False)
