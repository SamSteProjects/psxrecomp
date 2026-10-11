"""Private rigid World clip interchange; timing is caller selected, never observed."""
from base64 import b64decode, b64encode
from copy import deepcopy
from hashlib import sha256
import math

from .project import ProjectError
from .worldmap_placement_allocation import _fresh


def encode_inspected_clip(receipt, layer, fps):
    """Receipt must already be freshly source-qualified by inspect below."""
    from importer.animation import decode_animation_record
    from importer.export import encode_model_glb
    if layer not in ('retail', 'current') or type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120:
        raise ProjectError('World animation export requires Retail or Current and an explicit rate 1–120 fps')
    source=receipt['source']['before'] if layer=='current' else receipt
    pose=receipt['preview']; geometry=deepcopy(receipt['source']['current_model_geometry'] if layer=='current' else receipt['_export_geometry'])
    # Retail inspection carries the raw model separately through Current scene;
    # inspect supplies it explicitly, rather than deriving raw vertices from a pose.
    clip=decode_animation_record(b64decode(pose['record_base64'],validate=True))
    if clip['bone_count']!=len(geometry['objects']) or clip['frame_count']!=pose['frame_count']:
        raise ProjectError('World export clip channels differ from the verified Current model')
    geometry.update(frames=deepcopy(clip['frames']),semantic_id=source['model_asset_id'],
                    source_record=deepcopy(source['model_source']),representation=f'world-{layer}-animation-current-model')
    content,model_audit=encode_model_glb(geometry,clip_fps=fps)
    index=pose['record_index']
    audit=dict(schema_version='legaia.world-animation-export.v1',project_path=receipt['project_path'],
        scene=receipt['scene'],source_key=receipt['source_key'],entity_id=receipt['entity_id'],
        animation_id=f'animation://{receipt["scene"]}/worldmap/anm/{index:04d}',
        model_asset_id=source['model_asset_id'],layer=layer,frame_count=pose['frame_count'],channel_count=pose['channel_count'],
        bank_sha256=pose['bank_sha256'],record_sha256=pose['record_sha256'],fps=fps,
        timing_evidence='caller_selected_rate_not_verified_retail_timing',placement_included=False,
        coordinate_transform='[x,-y,z]',read_only=True,project_changed=False,gameplay_verified=False,
        glb_sha256=sha256(content).hexdigest(),byte_length=len(content),model_export=model_audit)
    return dict(schema_version='legaia.world-animation-export-response.v1',
        filename=f'{receipt["scene"]}-world-animation-{index:04d}-{layer}.glb',
        glb_base64=b64encode(content).decode('ascii'),audit=audit)


def inspect(project, body):
    fields={'scene','source_key','entity_id','layer','fps','bank_sha256','record_sha256'}
    if not isinstance(body,dict) or set(body)!=fields or body['layer'] not in ('retail','current'):
        raise ProjectError('World clip export requires exact inspected identity, layer, hashes and explicit rate')
    if type(body['fps']) not in (int,float) or not math.isfinite(body['fps']) or not 1<=body['fps']<=120:
        raise ProjectError('Choose an explicit World clip export rate 1–120 fps')
    from .worldmap_animation_edit import current
    from .worldmap_object_animation import inspect as retail
    if body['layer']=='current':
        receipt=current(project,body['scene'],body['source_key'],body['entity_id'],0)
    else:
        receipt=retail(project,body['scene'],body['source_key'],body['entity_id'],0)
        from .worldmap_current_placements import inspect as scene
        view=scene(project,body['scene'],body['source_key'])
        entity=next(e for e in view['scene_graph']['entities'] if e['entity_id']==body['entity_id'])
        receipt['_export_geometry']=deepcopy(next(a['preview'] for a in view['scene_graph']['assets'] if a['asset_id']==entity['asset_id']))
    if any(receipt['preview'][key]!=body[key] for key in ('bank_sha256','record_sha256')):
        raise ProjectError('World animation export differs from the inspected clip; inspect again')
    result=encode_inspected_clip(receipt,body['layer'],body['fps'])
    _fresh(project,body['source_key'])
    return result
