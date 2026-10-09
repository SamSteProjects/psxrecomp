"""Reviewed reversal of effective native poses; no project mutation or timing inference."""
from copy import deepcopy
from hashlib import sha256
from importer.animation import decode_animation_record
from importer.animation_authoring import patch_animation_channels
from .project import ProjectError

def reverse_range(project, entity_id, start, end, object_index):
    if not any(a['semantic_id'] == entity_id for a in project.imports.get(project.active_scene, {}).get('actors', [])):
        raise ProjectError('Pose reversal requires an actor in the active scene')
    effective, binding = project.animation_record_source(entity_id, 'effective')
    decoded = decode_animation_record(effective)
    frames, objects = decoded['frame_count'], decoded['bone_count']
    if (type(start) is not int or type(end) is not int or not 0 <= start < end < frames or
            (object_index is not None and (type(object_index) is not int or not 0 <= object_index < objects))):
        raise ProjectError('Choose two distinct existing frames and a supported object scope')
    selected = range(objects) if object_index is None else [object_index]
    if (end-start+1)*len(selected) > 4096:
        raise ProjectError('Reversed poses exceed the 4096-channel budget')
    proposed = []
    for frame in range(start, end+1):
        for obj in selected:
            channel = decoded['frames'][start+end-frame]['object_transforms'][obj]
            proposed.append(dict(frame_index=frame, object_index=obj,
                translation=dict(zip('xyz', channel['translation'])),
                rotation_psx=dict(zip('xyz', channel['rotation_psx']))))
    old = project.overrides.get(entity_id, {}).get('AnimationChannels', {}).get('edits', [])
    edits = deepcopy([r for r in old if r['frame_index'] < start or r['frame_index'] > end or
                      (object_index is not None and r['object_index'] != object_index)]) + deepcopy(proposed)
    edits.sort(key=lambda r: (r['frame_index'], r['object_index']))
    value = dict(animation_id=binding['semantic_id'], source_record_sha256=binding['source_record']['record_sha256'], edits=edits)
    project._validate_animation_override(entity_id, value)
    after, changes = patch_animation_channels(effective, sha256(effective).hexdigest(), proposed)
    return dict(animation_id=binding['semantic_id'], source_record_sha256=binding['source_record']['record_sha256'],
        before_record_sha256=sha256(effective).hexdigest(), after_record_sha256=sha256(after).hexdigest(),
        start=start, end=end, object_index=object_index, proposed=proposed, value=value, changed_axes=len(changes))
