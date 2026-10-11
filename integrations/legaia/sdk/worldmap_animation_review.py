"""Read-only World ANM edit/pose Review from an evidenced placed-object bind."""
from base64 import b64decode
from copy import deepcopy
from .project import ProjectError,digest
from .worldmap_object_animation import inspect
from .worldmap_current_placements import inspect as current_placements
from .worldmap_placement_allocation import _fresh
from importer.worldmap_animation_authoring import patch_world_animation_bank
from importer.worldmap_object_animation import resolve_object_animation
from importer.core import ImportError
import json


def review(project,scene,key,entity_id,frame_index,edits):
    _fresh(project,key)
    before=inspect(project,scene,key,entity_id,frame_index)
    preview=before['preview'];bank=b64decode(preview['bank_base64'])
    try:proposed,audit=patch_world_animation_bank(bank,preview['bank_sha256'],preview['record_index'],preview['record_sha256'],edits)
    except ImportError as exc:raise ProjectError(str(exc)) from exc
    current=current_placements(project,scene,key)
    asset=next((a for a in current['scene_graph']['assets'] if a['asset_id']==before['model_asset_id']),None)
    if not asset or asset['source_record']!=before['model_source']:
        raise ProjectError('World animation Review changed its Current model source')
    posed=resolve_object_animation(before['binding']['bind'],proposed,asset['preview'],frame_index)
    result=dict(schema_version='legaia.worldmap-animation-review.v1',project_path=str(project.root),scene=scene,
        source_key=key,entity_id=entity_id,frame_index=frame_index,edits=deepcopy(edits),
        animation_id=f"animation://{scene}/worldmap/anm/{preview['record_index']:04d}",
        before=before,proposed_preview=posed,audit=audit,read_only=True,project_changed=False,
        gameplay_verified=False,build_ready=False,
        limitations=['This Review does not save an authored binding or produce native Build output.',
            'The selected ANM record is shared by every source selector pointing to it.',
            'Timing, looping, runtime activation and fixed-point GTE rounding remain unverified.'])
    result['review_key']=digest(result)
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>80*1024*1024:
        raise ProjectError('World animation Review exceeds its private response budget')
    _fresh(project,key)
    return result
