"""Reviewed cell-local X/Z placement of a static decoration selection."""
from copy import deepcopy
from hashlib import sha256
import re
import struct

from .project import ProjectError, digest
from .project_copy import source_key
from importer.environment_authoring import patch_environment_overrides, patch_environment_transforms


def _prepare(project, scene, entity_ids):
    if project.mode != 'edit' or not isinstance(scene, str) or scene not in project.imports or scene != project.active_scene:
        raise ProjectError('Decoration group requires the active imported scene in Edit mode')
    if not isinstance(entity_ids, list) or not 2 <= len(entity_ids) <= 128 or any(not isinstance(item, str) for item in entity_ids) or len(set(entity_ids)) != len(entity_ids):
        raise ProjectError('Decoration group requires 2..128 unique decoration identities')
    prefix = 'environment://' + scene.removeprefix('scene://') + '/field-map/decorations/'
    cells = []
    for identifier in sorted(entity_ids):
        suffix = identifier.removeprefix(prefix)
        if not identifier.startswith(prefix) or not re.fullmatch(r'[0-9]{5}', suffix) or int(suffix) >= 16384:
            raise ProjectError('Decoration group identity is outside the canonical scene grid')
        cells.append((identifier, int(suffix)))
    before = source_key(project)
    original = project._environment_source(scene)
    source_hash = sha256(original).hexdigest()
    patch_environment_transforms(original, source_hash, [])
    authored = deepcopy(project.overrides.get(scene, {}).get('Environment'))
    if authored:
        project._validate_environment(scene, authored)
        patch_environment_overrides(original, authored)
    value = deepcopy(authored) if authored else dict(source_sha256=source_hash, edits=[], instances=[])
    shared, _ = patch_environment_transforms(original, value['source_sha256'], value.get('edits', []))
    instances = {item['cell_index']: deepcopy(item) for item in value.get('instances', [])}
    targets = []
    for identifier, cell in cells:
        word = struct.unpack_from('<H', original, 0x8000 + cell * 2)[0]
        record = word & 511
        flags = struct.unpack_from('<H', original, record * 32 + 18)[0]
        if record < 4 or not word & 0x2000 or flags & 4:
            raise ProjectError('Decoration group supports static source decoration cells only')
        retail_axes = dict(zip('xyz', struct.unpack_from('<3h', original, record * 32)))
        inherited = dict(zip('xyz', struct.unpack_from('<3h', shared, record * 32)))
        entry = deepcopy(instances.get(cell, dict(cell_index=cell)))
        offset = deepcopy(entry.get('offset', {}))
        current_axes = {**inherited, **offset}
        def position(axes):
            return dict(x=(cell % 128) * 128 + axes['x'] + 64, z=(cell // 128) * 128 - axes['z'] + 64)
        targets.append(dict(entity_id=identifier, cell_index=cell, retail=position(retail_axes), current=position(current_axes)))
    return dict(before=before, original=original, source_hash=source_hash, authored=authored, value=value,
                shared=shared, instances=instances, targets=targets)


def _merge(project, scene, context, proposed):
    """Merge per-cell world positions once, retaining inherited and unrelated axes."""
    value = context['value']
    instances = context['instances']
    targets = deepcopy(context['targets'])
    for target in targets:
        cell = target['cell_index']
        point = proposed[target['entity_id']]
        target['proposed'] = deepcopy(point)
        inherited = dict(zip('xyz', struct.unpack_from('<3h', context['shared'],
                             (struct.unpack_from('<H', context['original'], 0x8000 + cell * 2)[0] & 511) * 32)))
        entry = deepcopy(instances.get(cell, dict(cell_index=cell)))
        offset = deepcopy(entry.get('offset', {}))
        axes = dict(x=point['x'] - (cell % 128) * 128 - 64,
                    z=(cell // 128) * 128 + 64 - point['z'])
        if any(type(v) is not int or not -32768 <= v <= 32767 for v in axes.values()):
            raise ProjectError('Decoration group offset exceeds the signed MAP descriptor range')
        for axis in ('x', 'z'):
            if axes[axis] == inherited[axis]:
                offset.pop(axis, None)
            else:
                offset[axis] = axes[axis]
        if offset:
            entry['offset'] = offset
        else:
            entry.pop('offset', None)
        if len(entry) > 1:
            instances[cell] = entry
        else:
            instances.pop(cell, None)
    # Preserve the exact original metadata for any placement no-op.
    if all(t['current'] == t['proposed'] for t in targets) and context['authored'] is not None:
        value = deepcopy(context['authored'])
    elif instances or 'instances' in value:
        value['instances'] = [instances[cell] for cell in sorted(instances)]
    if value.get('edits') or value.get('instances'):
        project._validate_environment(scene, value)
    patch_environment_overrides(context['original'], value)
    if source_key(project) != context['before']:
        raise ProjectError('Project changed while reviewing decoration group')
    normalized = value if value.get('edits') or value.get('instances') else None
    return dict(targets=targets, affected_count=sum(t['current'] != t['proposed'] for t in targets),
                project_change=context['authored'] != normalized, value=value)


def review(project, scene, entity_ids, delta):
    if not isinstance(delta, dict) or set(delta) != {'x', 'z'} or any(type(v) is not int or not -65535 <= v <= 65535 for v in delta.values()):
        raise ProjectError('Decoration group requires exact integer X/Z offsets within -65535..65535')
    context = _prepare(project, scene, entity_ids)
    proposed = {t['entity_id']: {axis: t['current'][axis] + delta[axis] for axis in ('x', 'z')}
                for t in context['targets']}
    merged = _merge(project, scene, context, proposed)
    identities = sorted(entity_ids)
    key = digest(dict(project_source_key=context['before'], scene=scene, source_sha256=context['source_hash'], entity_ids=identities, delta=delta))
    return dict(schema_version='legaia.environment-group-review.v1', project_source_key=context['before'], scene_id=scene,
                source_sha256=context['source_hash'], review_key=key, entity_ids=identities, delta=deepcopy(delta),
                **merged, scope='static-decoration-instance-transform-only', gameplay_verified=False)


def apply(project, command):
    if not isinstance(command, dict) or set(command) != {'type', 'entity_id', 'entity_ids', 'delta', 'review_key'}:
        raise ProjectError('Decoration group Apply requires owner, selection, offset and current review key only')
    result = review(project, command['entity_id'], command['entity_ids'], command['delta'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('Decoration group inputs changed since review')
    value = result['value']
    project.command(dict(type='set_environment_transforms', entity_id=command['entity_id'], value=value)
                    if value.get('edits') or value.get('instances') else dict(type='clear_environment_transforms', entity_id=command['entity_id']))
