"""Reviewed GLB animation interchange through ordinary AnimationChannels commands.

The binding sidecar describes an export of the current effective shared clip.
Import contributes only changed axes, retaining each actor's existing ownership.
It never imports meshes, allocates animation records or infers retail timing.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math

from .project import ProjectError, digest


def _snapshot(project, entity_id: str, fps: float) -> dict:
    from importer.animation import decode_animation_record
    from importer.pipeline import _disc_context
    from importer.scene_animation import load_scene_actor_animation_catalog
    from .scene_preview import source_key

    if project.mode != 'edit':
        raise ProjectError('Animation GLB authoring requires Edit mode')
    if type(fps) not in (int, float) or not 1 <= fps <= 120 or not math.isfinite(fps):
        raise ProjectError('Choose an explicit animation interchange rate from 1 to 120 fps')
    document = project.imports.get(project.active_scene)
    actor = next((item for item in (document or {}).get('actors', [])
                  if item['semantic_id'] == entity_id), None)
    if actor is None:
        raise ProjectError('Animation GLB authoring requires an imported actor in the active scene')
    if 'ActorAllocatedAnimation' in project.overrides.get(entity_id,{}):
        raise ProjectError('Allocated initial clip GLB interchange is not implemented; clear its assignment before exporting an imported clip')
    key = source_key(project)
    if not key:
        raise ProjectError('Animation GLB authoring requires a verified scene source')
    with _disc_context(project.disc_path):
        assigned = any(name in project.overrides.get(entity_id, {})
                       for name in ('ActorAppearance', 'ActorAnimation'))
        model_source = actor
        if assigned:
            from .actor_animation import source_actor
            model_source = project.appearance_source_actor(entity_id, verify_disc=True)
            actor = source_actor(project, entity_id, verify_disc=True)
        channel_owner = actor['semantic_id']
        options = project.animation_authoring_options(channel_owner)
        source_binding = options['binding']
        catalog = load_scene_actor_animation_catalog(project.disc_path, document['scene']['name'])
        asset = next(item for item in document['assets']['models']
                     if item['semantic_id'] == source_binding['asset_semantic_id'])
        retail, _ = catalog.authored_animation_record(
            actor, asset, [], source_binding['source_record']['record_sha256'])
        owners = {item['semantic_id']: deepcopy(project.overrides[item['semantic_id']]['AnimationChannels'])
                  for item in document['actors']
                  if 'AnimationChannels' in project.overrides.get(item['semantic_id'], {})}
        bank, _ = catalog.authored_bank(owners)
        start = source_binding['source_record']['byte_offset']
        effective = bank[start:start + len(retail)]
        decoded = decode_animation_record(effective)
        if decoded['bone_count'] > 64:
            raise ProjectError('Animation GLB interchange supports at most 64 existing rigid objects')
        if decoded['frame_count'] * decoded['bone_count'] > 4096:
            raise ProjectError('Animation GLB interchange exceeds 4096 existing channels')
        binding = {
            'schema_version': 'legaia.animation-glb-binding.v1',
            'entity_id': entity_id, 'scene_id': project.active_scene,
            'asset_id': asset['semantic_id'], 'animation_id': source_binding['semantic_id'],
            'source_record_sha256': hashlib.sha256(retail).hexdigest(),
            'effective_record_sha256': hashlib.sha256(effective).hexdigest(),
            'project_source_key': key, 'frame_count': decoded['frame_count'],
            'object_count': decoded['bone_count'], 'clip_fps': float(fps),
            'coordinate_conversion': '[x,-y,z]; rigid Rz*Ry*Rx',
            'node_names': [f'object-{index}' for index in range(decoded['bone_count'])],
        }
        if assigned:
            binding.update(schema_version='legaia.animation-glb-binding.v2',
                           channel_owner_entity_id=channel_owner,
                           model_source_entity_id=model_source['semantic_id'])
    if source_key(project) != key:
        raise ProjectError('Project changed while verifying the animation export')
    return dict(binding=binding, actor=actor, asset=asset, catalog=catalog,
                retail=retail, effective=effective, owners=owners, start=start,
                channel_owner=channel_owner)


def _current(project, binding: dict) -> None:
    from .scene_preview import source_key
    if source_key(project) != binding['project_source_key']:
        raise ProjectError('Animation export is stale; export the current clip and binding again')


def export_clip(project, entity_id: str, fps: float) -> tuple[dict, dict, dict]:
    snapshot = _snapshot(project, entity_id, fps)
    animation = snapshot['catalog'].authored_bank_preview(
        snapshot['actor'], snapshot['asset'], snapshot['owners'])
    animation['entity_id'] = entity_id
    _current(project, snapshot['binding'])
    return animation, deepcopy(snapshot['asset']), deepcopy(snapshot['binding'])


def _axes(value: dict | None) -> dict:
    result = {}
    for edit in (value or {}).get('edits', []):
        for field in ('translation', 'rotation_psx'):
            for axis, number in edit.get(field, {}).items():
                result[(edit['frame_index'], edit['object_index'], field, axis)] = number
    return result


def _prepare(project, entity_id: str, content: bytes, binding: dict, *, animation_index=None) -> tuple[dict, dict, dict]:
    from importer.animation import decode_animation_record
    from importer.animation_glb import import_animation_glb
    if not isinstance(binding, dict) or binding.get('schema_version') not in (
            'legaia.animation-glb-binding.v1', 'legaia.animation-glb-binding.v2'):
        raise ProjectError('Choose the SDK animation export binding JSON sidecar')
    snapshot = _snapshot(project, entity_id, binding.get('clip_fps'))
    # JavaScript JSON serialization writes an integral 15.0 as 15. Preserve
    # one canonical numeric representation without relaxing identity fields.
    normalized_binding = dict(binding, clip_fps=float(binding['clip_fps']))
    if digest(normalized_binding) != digest(snapshot['binding']):
        raise ProjectError('Animation export binding differs from the current source or ownership; export again')
    binding = snapshot['binding']
    candidate, analysis = import_animation_glb(snapshot['effective'], content, fps=binding['clip_fps'], animation_index=animation_index)
    retail = decode_animation_record(snapshot['retail'])
    channel_owner = snapshot['channel_owner']
    before = _axes(snapshot['owners'].get(channel_owner))
    after = dict(before)
    for row in analysis['changes']:
        field, axis = row['field'].split('.')
        key = (row['frame_index'], row['object_index'], field, axis)
        original = retail['frames'][key[0]]['object_transforms'][key[1]][field]['xyz'.index(axis)]
        if row['after_value'] == original:
            after.pop(key, None)
        else:
            after[key] = row['after_value']
    edits = {}
    for (frame, obj, field, axis), value in sorted(after.items()):
        edit = edits.setdefault((frame, obj), {'frame_index': frame, 'object_index': obj})
        edit.setdefault(field, {})[axis] = value
    value = dict(animation_id=binding['animation_id'], source_record_sha256=binding['source_record_sha256'],
                 edits=list(edits.values()))
    proposed_owners = deepcopy(snapshot['owners'])
    if edits:
        proposed_owners[channel_owner] = value
    else:
        proposed_owners.pop(channel_owner, None)
    bank, _ = snapshot['catalog'].authored_bank(proposed_owners)
    if bank[snapshot['start']:snapshot['start'] + len(candidate)] != candidate:
        raise ProjectError('Another actor owns a retained shared axis; resolve its contribution before importing this change')
    candidate_hash = hashlib.sha256(candidate).hexdigest()
    glb_hash = hashlib.sha256(content).hexdigest()
    report = dict(analysis,
        schema_version='legaia.animation-glb-review.v1', entity_id=entity_id,
        project_source_key=binding['project_source_key'], candidate_sha256=candidate_hash,
        glb_sha256=glb_hash, changed_axes=len(analysis['changes']), project_changed=False,
        animation_id=binding['animation_id'], source_record_sha256=binding['source_record_sha256'],
        effective_record_sha256=binding['effective_record_sha256'],
        ownership=dict(actor_axis_count_before=len(before), actor_axis_count_after=len(after),
            other_contributors=sorted(owner for owner, contribution in snapshot['owners'].items()
                                      if owner != channel_owner and contribution['animation_id'] == binding['animation_id'])),
        limitations=['Existing rigid-object channels and frame count only; mesh edits are ignored.',
                     'Constant unit-scale tracks are accepted; native scale animation is unsupported.',
                     'Rigid parent TRS and static matrices are baked to scene-space poses; skinning remains unsupported.',
                     'The selected interchange rate does not establish retail playback timing.',
                     'Translation is rounded to source integers; Euler rotations use the existing eight-bit angle lattice.',
                     'Normal Build retains source capacities; runtime playback remains unverified.'])
    if binding['schema_version'] == 'legaia.animation-glb-binding.v2':
        report['ownership']['channel_owner_entity_id'] = channel_owner
        report['limitations'].append(
            f'Channel edits belong to imported clip witness {channel_owner}; all users of this shared clip are affected. Initial model/clip assignments remain separate.')
    review_identity = dict(binding=binding, glb_sha256=glb_hash,
                           candidate_sha256=candidate_hash, proposed_value=value)
    if animation_index is not None:
        # Distinct clips may quantize to identical native poses. The explicit
        # choice must remain part of authorization even when their bytes match.
        review_identity['file_animation_index'] = animation_index
    report['review_key'] = digest(review_identity)
    command = (dict(type='set_animation_channels', entity_id=channel_owner, value=value) if edits else
               dict(type='clear_animation_channels', entity_id=channel_owner))
    snapshot['proposed_owners'] = proposed_owners
    _current(project, binding)
    return snapshot, command, report


def preview_import(project, entity_id: str, content: bytes, binding: dict, *, animation_index=None) -> dict:
    return _prepare(project, entity_id, content, binding, animation_index=animation_index)[2]


def pose_import(project, entity_id: str, content: bytes, binding: dict, *, animation_index=None) -> tuple[dict, dict]:
    snapshot, _, report = _prepare(project, entity_id, content, binding, animation_index=animation_index)
    animation = snapshot['catalog'].authored_bank_preview(
        snapshot['actor'], snapshot['asset'], snapshot['proposed_owners'])
    animation['entity_id'] = entity_id
    animation['representation'] = 'file_preview'
    animation['proposal'] = report
    _current(project, binding)
    return animation, deepcopy(snapshot['asset'])


def apply_import(project, entity_id: str, content: bytes, binding: dict, review_key: str, *, animation_index=None) -> dict:
    _, command, report = _prepare(project, entity_id, content, binding, animation_index=animation_index)
    if review_key != report['review_key']:
        raise ProjectError('GLB or project changed after review; review the animation again')
    if not report['changed_axes']:
        raise ProjectError('GLB has no source-quantized animation changes to apply')
    project.command(command)
    return report
