"""Stage exact additive translations on a retained clip's effective native frames."""
from copy import deepcopy
from hashlib import sha256

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record
from importer.animation_authoring import patch_animation_channels
from .animation_record_edit import options, prepare
from .animation_record_ledger import verified_source
from .project import ProjectError
from .scene_preview import source_key


def stage(project, scene_id, record_id, source_frame_indices, edits, object_index,
          start, end, delta, expected_source_key):
    current = options(project, scene_id, record_id, expected_source_key)
    entry = current['entry']
    if (not current['edit_available'] or not isinstance(source_frame_indices, list)
            or not 1 <= len(source_frame_indices) <= current['maximum_frame_count']
            or type(object_index) is not int or not 0 <= object_index < entry['object_count']
            or type(start) is not int or type(end) is not int
            or not 0 <= start <= end < len(source_frame_indices)
            or not isinstance(delta, dict) or not delta or set(delta) - set('xyz')
            or any(type(v) is not int or not -4095 <= v <= 4095 for v in delta.values())):
        raise ProjectError('Choose bounded output frames, an existing rigid object and exact translation offsets')
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
        values = frames[frame]['object_transforms'][object_index]['translation']
        for axis, amount in sorted(delta.items()):
            if amount == 0:
                continue
            old = values['xyz'.index(axis)]
            new = old + amount
            if not -2048 <= new <= 2047:
                raise ProjectError('Translation offset exceeds a selected frame signed twelve-bit native axis')
            row = rows.get((frame, object_index))
            if row is None:
                row = dict(frame_index=frame, object_index=object_index)
                rows[(frame, object_index)] = row
                result.append(row)
            row.setdefault('translation', {})[axis] = new
            changed.append(dict(frame_index=frame, axis=axis, before=old, after=new))
    result.sort(key=lambda r: (r['frame_index'], r['object_index']))
    # Reuse the complete existing ledger/reference validation. This stages a
    # detached draft; no reviewed mutation or initial assignment is published.
    _, reviewed = prepare(project, scene_id, record_id, source_frame_indices, result, expected_source_key)
    if source_key(project) != expected_source_key:
        raise ProjectError('Animation offset source changed during staging')
    return dict(schema_version='legaia.animation-record-offset.v1', scene_id=scene_id,
        record_id=record_id, project_source_key=expected_source_key,
        source_frame_indices=deepcopy(source_frame_indices), before_edits=deepcopy(edits), edits=result,
        object_index=object_index, start=start, end=end, delta=deepcopy(delta),
        before_record_sha256=sha256(before).hexdigest(), after_record_sha256=reviewed['candidate_record_sha256'],
        changed_axes=changed, project_changed=False, gameplay_verified=False)
