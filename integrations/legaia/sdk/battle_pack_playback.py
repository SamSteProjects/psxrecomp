"""Bounded complete Retail reference-pack clips for cached local playback."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256

from importer.animation import decode_bone_transform, pose_vertices
from importer.battle_pack_animation import decode_catalogue, record as decode_record
from importer.battle_character_catalog import decode_catalog
from importer.core import ImportError as NativeError
from importer.pipeline import _disc_context
from .battle_character_resources import _fresh, _disc, preview as model_preview
from .project import ProjectError


def playback(project, expected_project_path, expected_source_key, model_id,
             model_source_key, animation_id, animation_source_key):
    _fresh(project, expected_project_path, expected_source_key)
    try:
        with _disc_context(project.disc_path) as (_, digest, _, archive):
            model_entry = archive.read_entry(archive.entry(1204))
            models = decode_catalog(model_entry, digest)
            animations, bank = decode_catalogue(archive.read_entry(archive.entry(1203)), digest)
            _disc(project, models); _disc(project, animations)
            if models['source_key'] != model_source_key or animations['source_key'] != animation_source_key:
                raise ProjectError('Battle pack model or animation source changed')
            model = next((m for m in models['models'] if m['semantic_id'] == model_id), None)
            clip = next((c for c in animations['clips'] if c['semantic_id'] == animation_id), None)
            if (model is None or clip is None or clip['model_asset_id'] != model_id
                    or model['pool_index'] not in (0, 1, 2)
                    or clip['association'] != 'pinned_pack_object_order_and_retail_channel_count'
                    or clip['bone_count'] != model['source_record']['object_count']):
                raise ProjectError('Choose a matching Retail reference-pack model and clip; unmatched rigs cannot play')
            source = clip['source_record']; at = source['byte_offset']
            stream = bank[at:at+source['byte_length']]
            layout = decode_record(stream)
            model_source = model['source_record']; start = model_source['byte_offset']
            tmd = model_entry[start:start+model_source['byte_length']]
            if (sha256(stream).hexdigest() != source['sha256']
                    or sha256(tmd).hexdigest() != model_source['sha256']
                    or any(layout[key] != clip[key] for key in layout)):
                raise ProjectError('Battle pack complete stream or source model bytes changed')
        raw = model_preview(project, expected_project_path, expected_source_key, model_id, model_source_key, 0)
        if raw['record'] != model:
            raise ProjectError('Battle pack playback model differs from its qualified preview')
        geometry = deepcopy(raw['preview'])
        transforms = [dict(object_index=i, **decode_bone_transform(stream[8+i*8:16+i*8]))
                      for i in range(clip['bone_count'])]
        geometry['vertices'] = pose_vertices(geometry['vertices'], geometry['objects'], transforms)
        geometry.update(posed=True, coordinate_system='retail_psx_actor_local_y_down',
            bounds=dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],
                        max=[max(v[i] for v in geometry['vertices']) for i in range(3)]))
        geometry.pop('triangle_normals', None); geometry.pop('normal_preview', None)
    except NativeError as error:
        raise ProjectError(str(error)) from error
    _fresh(project, expected_project_path, expected_source_key)
    return dict(schema_version='legaia.battle-pack-playback.v1', project_path=str(project.root),
        project_source_key=expected_source_key, model_id=model_id, model_source_key=model_source_key,
        animation_id=animation_id, animation_source_key=animation_source_key, model=model, clip=clip,
        source_bank_base64=b64encode(bank).decode('ascii'), source_bank_sha256=sha256(bank).hexdigest(),
        source_motion_base64=b64encode(stream).decode('ascii'), source_motion_sha256=sha256(stream).hexdigest(),
        source_model_base64=b64encode(tmd).decode('ascii'), source_model_sha256=sha256(tmd).hexdigest(),
        raw_geometry=raw['preview'], geometry=geometry, object_transforms=transforms, frame_index=0,
        representation='retail-reference-pack-not-player-assembly', layer='retail', read_only=True,
        project_changed=False, gameplay_verified=False, timing='unresolved', runtime_state='not_observed')
