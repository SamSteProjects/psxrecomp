"""Metadata discovery of evidenced scene MAN-to-ANM bindings.

Uses the existing identity-verified scene animation reader. This catalogs
initial MAN associations only; it neither decodes preview geometry nor invents
clip names, runtime animation state, playback rate or model compatibility.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .core import ImportError, canonical_json, validate_metadata_only
from .pipeline import REFERENCE_COMMIT
from .scene_animation import load_scene_actor_animation_catalog


def load_animation_asset_catalog(disc: Any, scene: str) -> dict:
    """Return deterministic metadata; callers select an evidenced actor to preview.

    Asset IDs are the existing animation://scene/scene-anm/NNNN identities.
    Bindings carry exact imported actor/model references. The convenient search
    arrays contain only those references, not arbitrary same-sized models.
    """
    catalog = load_scene_actor_animation_catalog(disc, scene)
    discovered = catalog.referenced_animation_metadata()
    assets: dict[str, dict] = {}
    for metadata in discovered["bindings"]:
        identity = metadata["semantic_id"]
        index = metadata["source_record"]["record_index"]
        common = {
            "semantic_id": identity, "asset_kind": "animation", "kind": "animation", "scope": "scene",
            "name": f"Scene animation {index:04d}", "record_index": index,
            "source_record": deepcopy(metadata["source_record"]),
            "frame_count": metadata["frame_count"], "channel_count": metadata["bone_count"],
            "bone_count": metadata["bone_count"], "timing": deepcopy(metadata["timing"]),
            "looping": metadata["looping"], "coordinate_system": metadata["coordinate_system"],
            "reference_commit": REFERENCE_COMMIT,
            "association_kind": "verified_man_header_scene_anm_record_plus_one",
            "compatibility_scope": "observed_imported_MAN_bindings_only",
            "limitations": [
                "Initial MAN association; scripts may change model or animation after spawning.",
                "Playback rate, looping, anatomical hierarchy and runtime clip state are unresolved.",
                "Only listed actor/model bindings are evidenced; equal channel counts do not establish other compatible models.",
            ],
        }
        if identity not in assets:
            assets[identity] = dict(common, bindings=[])
        elif canonical_json({k: assets[identity][k] for k in common}) != canonical_json(common):
            raise ImportError("animation source metadata disagrees across imported actor bindings")
        assets[identity]["bindings"].append({
            "actor_semantic_id": metadata["actor_semantic_id"],
            "model_asset_semantic_id": metadata["asset_semantic_id"],
            "initial_animation_id": metadata["association"]["animation_id"],
            "actor_source_record": deepcopy(metadata["association"]["actor_source_record"]),
            "association_kind": metadata["association"]["kind"],
        })
    records = [assets[key] for key in sorted(assets)]
    for asset in records:
        asset["bindings"].sort(key=lambda b: (b["actor_semantic_id"], b["model_asset_semantic_id"]))
        asset["actor_semantic_ids"] = sorted({b["actor_semantic_id"] for b in asset["bindings"]})
        asset["asset_semantic_ids"] = sorted({b["model_asset_semantic_id"] for b in asset["bindings"]})
    result = {
        "schema_version": "legaia.animation-asset-catalog.v1", "scene": discovered["scene"],
        "reference_commit": REFERENCE_COMMIT, "scope": "referenced-scene-man-initial-animations",
        "source_record": deepcopy(discovered["source_record"]),
        "scene_anm_record_count": discovered["scene_anm_record_count"], "asset_count": len(records),
        "actor_count": discovered["actor_count"], "binding_count": len(discovered["bindings"]),
        "unavailable_binding_count": len(discovered["unavailable_bindings"]),
        "assets": records, "unavailable_bindings": deepcopy(discovered["unavailable_bindings"]),
        "unreferenced_records": "not_advertised_or_decoded_by_this_catalog",
        "runtime_state": "not_observed", "metadata_only": True,
        "limitations": [
            "Referenced initial MAN animations only; unreferenced scene ANM records are not advertised or decoded.",
            f"{len(records)} animation assets cover {len(discovered['bindings'])} evidenced bindings among {discovered['actor_count']} imported actors; the scene ANM table has {discovered['scene_anm_record_count']} records.",
            f"{len(discovered['unavailable_bindings'])} actor bindings are unavailable; unavailable_bindings retains per-actor reasons. Global banks and zero initial IDs are not guessed.",
            "Playback timing, looping and runtime clip state are unknown; scripts may replace initial assignments.",
        ],
    }
    validate_metadata_only(result)
    return result
