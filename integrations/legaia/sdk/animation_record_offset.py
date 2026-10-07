"""Stage native translation or wrapped per-axis rotation offsets on retained frames."""
from copy import deepcopy
from hashlib import sha256

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record
from importer.animation_authoring import patch_animation_channels
from .animation_record_edit import options, prepare
from .animation_record_ledger import verified_source
from .project import ProjectError
from .scene_preview import source_key


def _stage(project, scene_id, record_id, source_frame_indices, edits, object_index,
           start, end, delta, expected_source_key, rotation=False):
    field = 'rotation_psx' if rotation else 'translation'
    limit = 4080 if rotation else 4095
    current = options(project, scene_id, record_id, expected_source_key)
    entry = current['entry']
    if (not current['edit_available'] or not isinstance(source_frame_indices, list)
            or not 1 <= len(source_frame_indices) <= current['maximum_frame_count']
            or type(object_index) is not int or not 0 <= object_index < entry['object_count']
            or type(start) is not int or type(end) is not int
            or not 0 <= start <= end < len(source_frame_indices)
            or not isinstance(delta, dict) or not delta or set(delta) - set('xyz')
            or any(type(v) is not int or not -limit <= v <= limit or (rotation and v % 16 != 0) for v in delta.values())):
        raise ProjectError('Choose bounded output frames, an existing rigid object and exact native offsets' + (' on the sixteen-unit rotation grid' if rotation else ''))
    source, _ = verified_source(project, scene_id)
    index = int(entry['donor_animation_id'].rsplit('/', 1)[1])
    at, stop = animation_record_ranges(source)[index]
    captured, _ = patch_animation_channels(source[at:stop], entry['donor_record_sha256'], entry['donor_edits'])
    before, _ = allocate_animation_record(captured, entry['effective_donor_record_sha256'], source_frame_indices, edits)
    frames = decode_animation_record(before)['frames']
    changed = []
    result = deepcopy(edits)
    rows = {(r['frame_index'], r['object_index']): r for r in result}
    for frame in range(start, end + 1):
        values = frames[frame]['object_transforms'][object_index][field]
        for axis, amount in sorted(delta.items()):
            if amount == 0:
                continue
            old = values['xyz'.index(axis)]
            new = (old + amount) % 4096 if rotation else old + amount
            if not rotation and not -2048 <= new <= 2047:
                raise ProjectError('Translation offset exceeds a selected frame signed twelve-bit native axis')
            row = rows.get((frame, object_index))
            if row is None:
                row = dict(frame_index=frame, object_index=object_index)
                rows[(frame, object_index)] = row
                result.append(row)
            row.setdefault(field, {})[axis] = new
            changed.append(dict(frame_index=frame, axis=axis, before=old, after=new))
    result.sort(key=lambda r: (r['frame_index'], r['object_index']))
    # Reuse the complete existing ledger/reference validation. This stages a
    # detached draft; no reviewed mutation or initial assignment is published.
    _, reviewed = prepare(project, scene_id, record_id, source_frame_indices, result, expected_source_key)
    if source_key(project) != expected_source_key:
        raise ProjectError('Animation offset source changed during staging')
    return dict(schema_version='legaia.animation-record-rotation-offset.v1' if rotation else 'legaia.animation-record-offset.v1', scene_id=scene_id,
        record_id=record_id, project_source_key=expected_source_key,
        source_frame_indices=deepcopy(source_frame_indices), before_edits=deepcopy(edits), edits=result,
        object_index=object_index, start=start, end=end, delta=deepcopy(delta),
        before_record_sha256=sha256(before).hexdigest(), after_record_sha256=reviewed['candidate_record_sha256'],
        changed_axes=changed, project_changed=False, gameplay_verified=False)


def stage(project, scene_id, record_id, source_frame_indices, edits, object_index,
          start, end, delta, expected_source_key):
    return _stage(project, scene_id, record_id, source_frame_indices, edits, object_index,
                  start, end, delta, expected_source_key)


def stage_rotation(project, scene_id, record_id, source_frame_indices, edits, object_index,
                   start, end, delta, expected_source_key):
    return _stage(project, scene_id, record_id, source_frame_indices, edits, object_index,
                  start, end, delta, expected_source_key, rotation=True)
