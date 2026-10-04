"""Bounded, source-qualified coordinated scene animation preview.

Frames remain actor-local PSX Y-down vertices. Existing scene geometry keys,
instance matrices and material bindings are retained by the caller. This service
does not author a schedule, infer retail timing or observe gameplay state.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
import re

from importer.core import ImportError as RetailImportError
from importer.animation import pose_vertices
from .project import ProjectError
from .scene_preview import preview_project, source_key


MAX_TRACKS = 128
MAX_INSTANCES = 512
MAX_FRAMES = 4096
MAX_VERTICES_PER_FRAME = 100000
MAX_FRAME_VERTICES = 1000000
MAX_FRAME_NORMAL_CORNERS = 3000000
MAX_METADATA_BYTES = 64 * 1024 * 1024
ELIGIBLE_POSES = frozenset(('reference_party_idle', 'reference_global_loop',
    'imported_scene_animation_frame0', 'authored_scene_animation_frame0',
    'authored_initial_animation_frame0'))
_SCENE_POSES = ELIGIBLE_POSES - {'reference_party_idle', 'reference_global_loop'}
_RANGES = ('object_index', 'vertex_start', 'vertex_count', 'triangle_start', 'triangle_count')
_MATERIAL_FIELDS = ('textured', 'clut', 'tpage', 'semi_transparent')
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def _text(value, label, *, nullable=False):
    if value is None and nullable:
        return value
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ProjectError(f'Scene animation requires a bounded {label}')
    return value


def _hash(value, label, *, nullable=False):
    if value is None and nullable:
        return value
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ProjectError(f'Scene animation requires a verified {label}')
    return value


def _vertices(value, count=None):
    if not isinstance(value, list) or not value or count is not None and len(value) != count:
        raise ProjectError('Scene animation frame vertex count differs from its source geometry')
    for vertex in value:
        if not isinstance(vertex, list) or len(vertex) != 3:
            raise ProjectError('Scene animation vertices require three finite source coordinates')
        for coordinate in vertex:
            try:
                valid = type(coordinate) in (int, float) and math.isfinite(coordinate)
            except OverflowError:
                valid = False
            if not valid:
                raise ProjectError('Scene animation vertices require three finite source coordinates')


def _mesh(preview):
    if not isinstance(preview, dict):
        raise ProjectError('Scene animation requires a complete verified model preview')
    vertices = preview.get('vertices')
    _vertices(vertices)
    triangles = preview.get('triangles')
    if (not isinstance(triangles, list) or not triangles or
            any(not isinstance(t, list) or len(t) != 3 or
                any(type(i) is not int or not 0 <= i < len(vertices) for i in t) for t in triangles)):
        raise ProjectError('Scene animation source triangles differ from bounded source geometry')
    objects = preview.get('objects')
    if not isinstance(objects, list) or not objects:
        raise ProjectError('Scene animation requires verified ordered object ranges')
    ranges, nv, nt = [], 0, 0
    for index, obj in enumerate(objects):
        if (not isinstance(obj, dict) or any(type(obj.get(k)) is not int for k in _RANGES) or
                obj['object_index'] != index or obj['vertex_start'] != nv or obj['triangle_start'] != nt or
                obj['vertex_count'] < 0 or obj['triangle_count'] < 0):
            raise ProjectError('Scene animation requires verified ordered object ranges')
        nv += obj['vertex_count']; nt += obj['triangle_count']
        ranges.append([obj[k] for k in _RANGES])
    if nv != len(vertices) or nt != len(triangles):
        raise ProjectError('Scene animation object ranges do not cover the source geometry')
    materials, mapping = preview.get('materials'), preview.get('triangle_materials')
    if (not isinstance(materials, list) or not materials or not isinstance(mapping, list) or
            len(mapping) != len(triangles) or
            any(type(i) is not int or not 0 <= i < len(materials) for i in mapping)):
        raise ProjectError('Scene animation requires the source material mapping')
    bindings = []
    for material in materials:
        if not isinstance(material, dict) or any(k not in material for k in _MATERIAL_FIELDS):
            raise ProjectError('Scene animation material bindings are incomplete')
        if type(material['textured']) is not bool or type(material['semi_transparent']) is not bool:
            raise ProjectError('Scene animation material bindings are malformed')
        if (material['textured'] and any(type(material[k]) is not int or not 0 <= material[k] <= 65535
                                        for k in ('clut', 'tpage')) or
                not material['textured'] and any(material[k] is not None for k in ('clut', 'tpage'))):
            raise ProjectError('Scene animation material bindings are malformed')
        bindings.append([material[k] for k in _MATERIAL_FIELDS])
    arrays = {}
    for key in ('triangle_uvs', 'triangle_colors'):
        if key in preview:
            if not isinstance(preview[key], list) or len(preview[key]) != len(triangles):
                raise ProjectError('Scene animation source face data is incomplete')
            arrays[key] = preview[key]
    return dict(triangles=triangles, objects=ranges, materials=bindings,
                triangle_materials=mapping, **arrays)


def _json_size(value):
    try:
        size = 0
        for piece in json.JSONEncoder(separators=(',', ':'), allow_nan=False).iterencode(value):
            size += len(piece.encode('utf-8'))
            if size > MAX_METADATA_BYTES:
                return size
        return size
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProjectError('Scene animation metadata is not bounded finite JSON') from exc


def _object_pose_scope(loaded, baseline, frames):
    """Keep a qualified V7 channel prefix without inventing clone channels."""
    marker = 'verified_existing_channels_with_explicit_unposed_native_objects'
    if loaded.get('pose_scope') != marker:
        if baseline.get('pose_scope') == marker:
            raise ProjectError('Scene animation lost its explicit unposed object scope')
        return None
    objects = loaded['objects']
    excluded = loaded.get('unposed_object_indices')
    if (baseline.get('pose_scope') != marker or
            baseline.get('unposed_object_indices') != excluded or
            not isinstance(excluded, list) or not excluded or
            any(type(i) is not int for i in excluded)):
        raise ProjectError('Scene animation unposed object scope differs from its canonical pose')
    known = len(objects) - len(excluded)
    if known < 1 or excluded != list(range(known, len(objects))) or loaded.get('posed') is not False:
        raise ProjectError('Scene animation requires an evidenced existing channel prefix')
    prefix = sum(obj['vertex_count'] for obj in objects[:known])
    for frame in frames:
        if (not isinstance(frame, dict) or frame.get('posed') is not True or
                frame.get('coordinate_system') != 'retail_psx_actor_local_y_down' or
                not isinstance(frame.get('object_transforms'), list) or
                len(frame['object_transforms']) != known):
            raise ProjectError('Scene animation cannot assign channels to unposed native objects')
        for index, channel in enumerate(frame['object_transforms']):
            if not isinstance(channel, dict) or type(channel.get('object_index')) is not int or channel['object_index'] != index:
                raise ProjectError('Scene animation existing channel ownership is invalid')
            angles = channel.get('rotation_psx')
            if (not isinstance(angles, list) or len(angles) != 3 or
                    any(type(a) is not int or not 0 <= a < 4096 for a in angles)):
                raise ProjectError('Scene animation existing rotation words are invalid')
            _vertices([channel.get('translation')])
        try:
            expected = pose_vertices(loaded['vertices'][:prefix], objects[:known], frame['object_transforms'])
        except RetailImportError as exc:
            raise ProjectError('Scene animation existing channel prefix is invalid') from exc
        expected += loaded['vertices'][prefix:]
        if frame.get('vertices') != expected:
            raise ProjectError('Scene animation changed its evidenced pose or unposed native vectors')
    return dict(kind='existing_channel_prefix', object_count=len(objects), posed_object_count=known,
                unposed_object_indices=deepcopy(excluded), unposed_vertex_start=prefix)


def _normal_pose(loaded, baseline, frames, budget, scope=None):
    """Optional source vectors and channels; never derive normals from positions."""
    metadata = loaded.get('normal_preview')
    if not isinstance(metadata, dict) or metadata.get('status') != 'source_unposed':
        return None
    canonical = baseline.get('normal_source', baseline)
    if not isinstance(canonical, dict):
        raise ProjectError('Scene normal source evidence is malformed')
    if (loaded.get('posed') is not False or
            metadata.get('coordinate_system') != 'retail_tmd_object_local' or
            loaded.get('triangle_normals') != canonical.get('triangle_normals')):
        raise ProjectError('Scene normal channels differ from canonical source vectors')
    normals = loaded.get('triangle_normals')
    if (not isinstance(normals, list) or len(normals) != len(loaded['triangles']) or
            len(normals) > 100000):
        raise ProjectError('Scene normal source triangle layout is invalid')
    if len(normals) * 3 * len(frames) > budget:
        return None
    for row in normals:
        if row is not None and (not isinstance(row, list) or len(row) != 3 or
                any(not isinstance(v, list) or len(v) != 3 or
                    any(type(n) is not int or not -32768 <= n <= 32767 for n in v) for v in row)):
            raise ProjectError('Scene normal source vectors are not signed16 corners')
    for obj in loaded['objects']:
        lo, hi = obj['vertex_start'], obj['vertex_start'] + obj['vertex_count']
        for triangle in loaded['triangles'][obj['triangle_start']:obj['triangle_start']+obj['triangle_count']]:
            if any(not lo <= vertex < hi for vertex in triangle):
                raise ProjectError('Scene normal triangle crosses its rigid source object')
    channels = []
    for frame in frames:
        if (not isinstance(frame, dict) or frame.get('posed') is not True or
                frame.get('coordinate_system') != 'retail_psx_actor_local_y_down' or
                not isinstance(frame.get('object_transforms'), list)):
            return None
        transforms = []
        for channel in frame['object_transforms']:
            if not isinstance(channel, dict) or type(channel.get('object_index')) is not int:
                raise ProjectError('Scene normal channel is invalid')
            angles, translation = channel.get('rotation_psx'), channel.get('translation')
            if (not isinstance(angles, list) or len(angles) != 3 or
                    any(type(a) is not int or not 0 <= a < 4096 for a in angles)):
                raise ProjectError('Scene normal rotation words are invalid')
            _vertices([translation])
            transforms.append(dict(object_index=channel.get('object_index'),
                                   rotation_psx=deepcopy(angles), translation=deepcopy(translation)))
        try:
            if scope is None:
                expected = pose_vertices(loaded['vertices'], loaded['objects'], transforms)
            else:
                prefix = scope['unposed_vertex_start']; known = scope['posed_object_count']
                expected = pose_vertices(loaded['vertices'][:prefix], loaded['objects'][:known], transforms)
                expected += loaded['vertices'][prefix:]
        except RetailImportError as exc:
            raise ProjectError('Scene normal channel mapping is invalid') from exc
        if expected != frame['vertices']:
            raise ProjectError('Scene normal channels do not reproduce the qualified vertex sample')
        channels.append(dict(posed=True,coordinate_system='retail_psx_actor_local_y_down',
                             object_transforms=transforms))
    source = {key: deepcopy(loaded[key]) for key in
              ('posed','vertices','triangles','objects','triangle_normals','normal_preview')}
    if scope is not None:
        source['pose_scope'] = deepcopy(scope)
    return dict(source=source,frames=channels)


def _current(project, scene_id, expected_source_key):
    if (project.mode != 'edit' or project.active_scene != scene_id or
            source_key(project) != expected_source_key):
        raise ProjectError('Scene animation source or Edit mode changed; refresh the scene')


def prepare_scene_animation(project, scene, animation_loader, representation, expected_source_key):
    """Prepare one complete source-qualified clip for each eligible geometry key.

    The callback receives detached (representative_instance, project_asset).
    Whole unavailable/budget-limited tracks contribute explicit actor coverage.
    Only a retail decode availability error is downgraded; malformed data rejects.
    """
    if representation not in ('authored', 'retail'):
        raise ProjectError('Scene animation representation must be authored or retail')
    if not isinstance(scene, dict) or scene.get('schema') != 'legaia.scene-preview.v1':
        raise ProjectError('Scene animation requires the fresh verified scene preview')
    scene_id = _text(scene.get('scene_id'), 'active scene identity')
    expected_source_key = _hash(expected_source_key, 'project source key')
    _current(project, scene_id, expected_source_key)
    if (scene.get('project_source_key') != expected_source_key or
            _hash(scene.get('source_key'), 'scene source key') != source_key(preview_project(project, representation))):
        raise ProjectError('Scene animation scene representation or project source is stale')
    if not callable(animation_loader):
        raise ProjectError('Scene animation requires a verified complete clip loader')
    document = project.imports.get(scene_id)
    if not isinstance(document, dict):
        raise ProjectError('Scene animation requires an imported active scene')
    actors = {a['semantic_id'] for a in document.get('actors', [])}
    assets, entities = scene.get('assets'), scene.get('entities')
    if (not isinstance(assets, list) or len(assets) > MAX_TRACKS or
            not isinstance(entities, list) or len(entities) > MAX_INSTANCES):
        raise ProjectError('Scene animation exceeds its existing geometry or instance budget')
    by_geometry, ids, grouped, reasons = {}, set(), {}, {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise ProjectError('Scene animation source geometry binding is malformed')
        key = _hash(asset.get('geometry_key'), 'geometry key')
        _text(asset.get('asset_id'), 'asset identity')
        if key in by_geometry:
            raise ProjectError('Scene animation source geometry key is duplicated')
        by_geometry[key] = asset
    participants = []
    for instance in entities:
        if not isinstance(instance, dict):
            raise ProjectError('Scene animation source instance is malformed')
        entity_id = _text(instance.get('entity_id'), 'entity identity')
        if entity_id in ids:
            raise ProjectError('Scene animation entity identity is duplicated')
        ids.add(entity_id)
        key = _hash(instance.get('geometry_key'), 'instance geometry key', nullable=True)
        asset_id = _text(instance.get('asset_id'), 'instance asset identity', nullable=True)
        if type(instance.get('renderable')) is not bool:
            raise ProjectError('Scene animation instance renderability is malformed')
        if instance['renderable'] and (key is None or asset_id is None):
            raise ProjectError('Scene animation renderable instance has no exact geometry binding')
        if key is not None and (key not in by_geometry or by_geometry[key]['asset_id'] != asset_id):
            raise ProjectError('Scene animation instance geometry differs from its exact asset binding')
        if instance.get('kind') == 'environment':
            continue
        pose_kind = _text(instance.get('pose_kind'), 'instance pose kind')
        participants.append(instance)
        if entity_id not in actors and not (entity_id in getattr(project, 'actor_drafts', {}) and
                project.actor_drafts[entity_id].get('scene_id') == scene_id):
            raise ProjectError('Scene animation actor identity is outside the active imported scene')
        if not instance['renderable'] or key is None or pose_kind not in ELIGIBLE_POSES:
            reasons[entity_id] = instance.get('reason') or f'{pose_kind}: no supported source animation clip'
            _text(reasons[entity_id], 'unavailable reason')
            continue
        source_actor_id = _text(instance.get('source_actor_id'), 'source actor identity')
        if source_actor_id not in actors or asset_id not in project.assets.records:
            raise ProjectError('Scene animation source actor or model is outside verified imported evidence')
        canonical = by_geometry[key].get('pose_kind')
        if (canonical not in ELIGIBLE_POSES or
                canonical != pose_kind and not (canonical in _SCENE_POSES and pose_kind in _SCENE_POSES)):
            raise ProjectError('Scene animation pose kind differs from its canonical geometry binding')
        grouped.setdefault(key, []).append(instance)
    tracks, admitted, total_vertices, track_bytes, budget_rejections = [], set(), 0, 0, 0
    normal_corners = 0
    for key in sorted(grouped):
        members = grouped[key]
        representative = members[0]
        asset = by_geometry[key]
        baseline = asset.get('preview')
        baseline_mesh = _mesh(baseline)
        count = len(baseline['vertices'])
        reason = None
        try:
            loaded = animation_loader(deepcopy(representative), deepcopy(project.assets.records[asset['asset_id']]))
        except RetailImportError as exc:
            reason = str(exc) or 'Source animation decode is unavailable'
        if reason is None:
            if _mesh(loaded) != baseline_mesh:
                raise ProjectError('Scene animation clip changed the source mesh, object ranges or material mapping')
            animation = loaded.get('animation')
            frames = loaded.get('frames')
            if (not isinstance(animation, dict) or type(animation.get('frame_count')) is not int or
                    animation['frame_count'] <= 0 or not isinstance(frames, list) or
                    len(frames) != animation['frame_count']):
                raise ProjectError('Scene animation requires the complete existing clip frame count')
            if animation.get('asset_semantic_id') != asset['asset_id']:
                raise ProjectError('Scene animation clip belongs to a different source model')
            clip_id = _text(animation.get('source_clip_id', animation.get('semantic_id', animation.get('clip_id'))), 'stable source clip identity')
            if not re.fullmatch(r'animation://[A-Za-z0-9_./-]{1,512}', clip_id):
                raise ProjectError('Scene animation requires a stable animation asset identity, not a short label or guest address')
            frame_count = len(frames)
            usage = frame_count * count
            if frame_count > MAX_FRAMES or count > MAX_VERTICES_PER_FRAME or total_vertices + usage > MAX_FRAME_VERTICES:
                reason = 'Animation preview budget exceeded; complete source track omitted'
                budget_rejections += 1
            else:
                values = []
                for index, frame in enumerate(frames):
                    if isinstance(frame, dict):
                        if frame.get('frame_index', index) != index or type(frame.get('frame_index', index)) is not int:
                            raise ProjectError('Scene animation frame order differs from the source clip')
                        vertices = frame.get('vertices')
                    else:
                        vertices = frame
                    _vertices(vertices, count)
                    values.append(deepcopy(vertices))
                if values[0] != baseline['vertices']:
                    raise ProjectError('Scene animation frame 0 differs from the canonical scene pose')
                track = dict(geometry_key=key, asset_id=asset['asset_id'], clip_id=clip_id,
                             pose_kind=asset['pose_kind'], frame_count=frame_count, vertex_count=count, frames=values)
                scope = _object_pose_scope(loaded, baseline, frames)
                if scope is not None:
                    track['pose_scope'] = scope
                normal_pose = _normal_pose(loaded, baseline, frames, MAX_FRAME_NORMAL_CORNERS-normal_corners, scope)
                if normal_pose is not None:
                    track['normal_pose'] = normal_pose
                used_bytes = _json_size(track)
                if normal_pose is not None and track_bytes + used_bytes > MAX_METADATA_BYTES:
                    del track['normal_pose']
                    normal_pose = None
                    used_bytes = _json_size(track)
                if track_bytes + used_bytes > MAX_METADATA_BYTES:
                    reason = 'Animation preview JSON budget exceeded; complete source track omitted'
                    budget_rejections += 1
                else:
                    tracks.append(track); admitted.add(key)
                    if normal_pose is not None:
                        normal_corners += len(normal_pose['source']['triangles']) * 3 * frame_count
                    total_vertices += usage; track_bytes += used_bytes
        if reason is not None:
            if not isinstance(reason, str) or len(reason) > 512:
                reason = 'Source animation decode is unavailable; details exceed the bounded report'
            for member in members:
                reasons[member['entity_id']] = reason
    instances, unavailable = [], []
    for instance in participants:
        if instance['entity_id'] in reasons:
            unavailable.append({k: instance.get(k) for k in ('entity_id', 'geometry_key', 'asset_id', 'pose_kind')})
            unavailable[-1]['reason'] = reasons[instance['entity_id']]
        elif instance['geometry_key'] in admitted:
            instances.append({k: instance[k] for k in ('entity_id', 'geometry_key', 'asset_id', 'source_actor_id')})
        else:
            raise ProjectError('Scene animation actor coverage is incomplete')
    limitations = ['Transient source animation preview; no game scheduling or runtime state is authored or observed.',
                   'Clips share an integer preview tick and loop by viewer convention; display rate does not establish retail timing.',
                   'Source actor-local Y-down coordinates are retained; existing instance transforms and material bindings remain canonical.',
                   'Static, unsupported and unavailable actors are reported explicitly; environment and terrain are excluded.']
    if budget_rejections:
        limitations.append(f'{budget_rejections} complete source track(s) omitted by the animation preview budgets.')
    result = dict(schema_version='legaia.scene-animation.v1', scene_id=scene_id,
        project_source_key=expected_source_key, scene_source_key=scene['source_key'], representation=representation,
        tracks=tracks, instances=instances, unavailable_instances=unavailable,
        metrics=dict(animated_instances=len(instances), static_or_unavailable_instances=len(unavailable),
            track_count=len(tracks), frame_vertex_count=total_vertices,
            max_frame_count=max((track['frame_count'] for track in tracks), default=0)),
        limitations=limitations, project_changed=False, gameplay_verified=False)
    if _json_size(result) > MAX_METADATA_BYTES:
        raise ProjectError('Scene animation report exceeds its 64 MiB finite metadata budget')
    _current(project, scene_id, expected_source_key)
    if source_key(preview_project(project, representation)) != scene['source_key']:
        raise ProjectError('Scene animation representation changed while loading clips')
    return result
