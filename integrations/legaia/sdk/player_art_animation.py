"""Read-only explicit ME archive previews on qualified PLAYER assemblies."""
from base64 import b64encode
from copy import deepcopy
from importer import player_art_animation as native
from importer.core import ImportError
from importer.player_battle import decode_part, _sources, assemble_tmd
from hashlib import sha256
from importer.animation import pose_vertices
from .project import ProjectError
from .battle_character_resources import _fresh, _disc


def resources(project, expected_project_path, expected_source_key):
    _fresh(project, expected_project_path, expected_source_key)
    try:
        catalog = native.discover(project.disc_path)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    _disc(project, catalog)
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.player-art-resources.v1', project_path=str(project.root),
                project_source_key=expected_source_key, catalog=catalog, layer='retail',
                read_only=True, project_changed=False, gameplay_verified=False)


def playback(project, expected_project_path, expected_source_key, asset_id, catalog_source_key, equipped,
             art_source_key, stream_id, art_record_id, layer, expected_current_sha256):
    _fresh(project, expected_project_path, expected_source_key)
    context = dict(expected_project_path=expected_project_path, expected_source_key=expected_source_key,
                   asset_id=asset_id, catalog_source_key=catalog_source_key, equipped=equipped)
    if layer == 'current':
        from .player_model_authoring import current
        base = current(project, **context)
        if expected_current_sha256 != base['effective_file_sha256']:
            raise ProjectError('PLAYER Current changed; inspect the assembly again')
        effective_hash = base['effective_file_sha256']
        tmd_base64 = base['tmd_base64']
    elif layer == 'retail':
        if expected_current_sha256 is not None:
            raise ProjectError('Retail art preview accepts no Current identity')
        from .player_battle import preview
        base = preview(project, **context)
        effective_hash = base['record']['source_record']['sha256']
        digest, files = _sources(project.disc_path)
        original = files[base['record']['player_index']][3]
        if digest != base['record']['source_record']['disc']['sha256'] or sha256(original).hexdigest() != effective_hash:
            raise ProjectError('PLAYER art Retail model source changed')
        _, _, tmd = assemble_tmd(original, equipped)
        if sha256(tmd).hexdigest() != base['assembly']['tmd_sha256']:
            raise ProjectError('PLAYER art Retail assembly source changed')
        tmd_base64 = b64encode(tmd).decode('ascii')
    else:
        raise ProjectError('Choose Retail or Current PLAYER geometry')
    try:
        catalog, stream, slot, decoded = native.load_stream(project.disc_path, stream_id, art_source_key)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    _disc(project, catalog)
    if stream['model_asset_id'] != asset_id or stream['player_index'] != base['record']['player_index']:
        raise ProjectError('PLAYER art stream belongs to another character')
    art = None
    if art_record_id is not None:
        art = next((r for r in catalog['records'] if r['semantic_id'] == art_record_id), None)
        if art is None or stream_id not in art['eligible_stream_ids'] or art['player_index'] != stream['player_index']:
            raise ProjectError('Art record does not reference the explicitly selected archive stream')
    parts = base['assembly']['animation_part_indices']
    if len(parts) != len(base['geometry']['objects']) or any(type(p) is not int or not 0 <= p < stream['part_count'] for p in parts):
        raise ProjectError('PLAYER assembly part mapping exceeds the selected art rig')
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.player-art-playback.v1', project_path=str(project.root),
                project_source_key=expected_source_key, catalog_source_key=catalog_source_key,
                art_source_key=art_source_key, base_inspection=base, stream=stream, art_record=art,
                layer=layer, effective_file_sha256=effective_hash, source_slot_base64=b64encode(slot).decode('ascii'),
                source_tmd_base64=tmd_base64,
                decoded_stream_base64=b64encode(decoded).decode('ascii'), archive_selection='explicit_source_archive_not_observed_residency',
                timing='not_observed', read_only=True, project_changed=False, gameplay_verified=False)


def frame_transforms(base, stream, decoded, frame_index):
    if type(frame_index) is not int or not 0 <= frame_index < stream['frame_count']:
        raise ProjectError('Choose an existing whole PLAYER art frame')
    start = 2 + frame_index * stream['part_count'] * 9
    parts = [decode_part(decoded[start + i * 9:start + (i + 1) * 9]) for i in range(stream['part_count'])]
    return [dict(object_index=i, part_index=part, **parts[part]) for i, part in enumerate(base['assembly']['animation_part_indices'])]


def frame_geometry(base, stream, decoded, frame_index):
    transforms = frame_transforms(base, stream, decoded, frame_index)
    geometry = deepcopy(base['geometry'])
    geometry['vertices'] = pose_vertices(geometry['vertices'], geometry['objects'], transforms)
    geometry['bounds'] = dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],
                            max=[max(v[i] for v in geometry['vertices']) for i in range(3)])
    geometry.update(posed=True, coordinate_system='retail_psx_actor_local_y_down')
    geometry.pop('triangle_normals', None)
    geometry.pop('normal_preview', None)
    return geometry, transforms


def pose(project, frame_index, **context):
    from base64 import b64decode
    receipt = playback(project, **context)
    geometry, transforms = frame_geometry(receipt['base_inspection'], receipt['stream'],
                                         b64decode(receipt['decoded_stream_base64']), frame_index)
    _fresh(project, context['expected_project_path'], context['expected_source_key'])
    return dict(schema_version='legaia.player-art-pose.v1', playback=receipt, geometry=geometry,
                object_transforms=transforms, frame_index=frame_index, read_only=True,
                project_changed=False, gameplay_verified=False)


def export_choice(mode, frame_index, fps):
    import math
    if mode not in ('pose', 'clip'):
        raise ProjectError('Choose a PLAYER art pose or full clip')
    if mode == 'pose' and (type(frame_index) is not int or frame_index < 0 or fps is not None):
        raise ProjectError('Art pose requires a whole frame and no rate')
    if mode == 'clip' and (frame_index is not None or type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120):
        raise ProjectError('Art clip requires an interchange rate 1–120 and no frame')


def encode_export(receipt, mode, frame_index, fps, decoded, motion=None):
    from importer.export import encode_model_glb
    base, stream = receipt['base_inspection'], receipt['stream']
    geometry = deepcopy(base['geometry'])
    geometry['representation'] = 'player-art-current-motion-selected-equipment-assembly' if motion else 'player-art-selected-equipment-assembly'
    geometry['source_record'] = dict(model=base['record']['source_record'],
                                   current_sha256=receipt['effective_file_sha256'],
                                   player_assembly=base['assembly'], stream=stream['source_record'],
                                   art_record=receipt['art_record'], layer=receipt['layer'])
    geometry['animation'] = dict(semantic_id=stream['semantic_id'], label=stream['name'],
                                 source_record=stream['source_record'], timing='not_observed',
                                 archive_selection=receipt['archive_selection'])
    if motion:
        geometry['source_record']['motion'] = deepcopy(motion)
        geometry['animation']['motion_layer'] = 'current'
    if mode == 'pose':
        posed, transforms = frame_geometry(base, stream, decoded, frame_index)
        geometry['frames'] = [dict(posed, object_transforms=transforms)]
        geometry['animation']['source_frame_index'] = frame_index
    else:
        geometry['frames'] = [dict(object_transforms=frame_transforms(base, stream, decoded, i))
                              for i in range(stream['frame_count'])]
    try:
        content, audit = encode_model_glb(geometry, 0 if mode == 'pose' else None,
                                         clip_fps=fps if mode == 'clip' else None)
    except ImportError as error:
        raise ProjectError(str(error)) from error
    suffix = f'frame-{frame_index}' if mode == 'pose' else 'clip'
    prefix = 'player-art-current-motion' if motion else 'player-art'
    filename = f'{prefix}-{stream["player_index"]}-{stream["archive_role"]}-{stream["stream_index"]}-{receipt["layer"]}-{suffix}.glb'
    return dict(schema_version='legaia.player-art-export.v1', playback=receipt, mode=mode,
                frame_index=frame_index, fps=fps, filename=filename, audit=audit,
                glb_base64=b64encode(content).decode('ascii'), read_only=True,
                project_changed=False, gameplay_verified=False)


def export(project, mode, frame_index, fps, **context):
    from base64 import b64decode
    export_choice(mode, frame_index, fps)
    receipt=playback(project,**context)
    result=encode_export(receipt,mode,frame_index,fps,b64decode(receipt['decoded_stream_base64']))
    _fresh(project,context['expected_project_path'],context['expected_source_key'])
    return result
