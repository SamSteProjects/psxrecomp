"""Observer-owned scene epoch construction and comparison."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .errors import SnapshotUnstable


BOUNDARY_KEYS = (
    "runtime_process_identity",
    "scene_signals",
    "actor_list_head",
    "actor_census_base",
    "field_execution_identity",
    "witness_structural_identities",
    "executable_state_token",
    "lifecycle_token",
)


def compatible_boundaries(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    return all(before.get(key) == after.get(key) for key in BOUNDARY_KEYS)


def require_compatible(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    changed = [key for key in BOUNDARY_KEYS if before.get(key) != after.get(key)]
    if changed:
        raise SnapshotUnstable(f"scene epoch boundary changed: {', '.join(changed)}")
    before_frame = before.get("frame")
    after_frame = after.get("frame")
    if not isinstance(before_frame, int) or not isinstance(after_frame, int) or after_frame < before_frame:
        raise SnapshotUnstable("runtime frame moved backwards or is unavailable")


@dataclass(frozen=True)
class SceneEpoch:
    epoch_id: str
    observer_epoch_number: int
    profile_id: str
    runtime_process_identity: str
    scene_name: str
    prot_base: int
    master_mode: int
    actor_list_head: str
    executable_state_token: str
    lifecycle_token: str
    required_witness_structural_identities: list[dict[str, Any]]
    first_stable_frame: int
    last_validated_frame: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "observer_epoch_number": self.observer_epoch_number,
            "profile_id": self.profile_id,
            "runtime_process_identity": self.runtime_process_identity,
            "scene_name": self.scene_name,
            "prot_base": self.prot_base,
            "master_mode": self.master_mode,
            "actor_list_head": self.actor_list_head,
            "executable_state_token": self.executable_state_token,
            "lifecycle_token": self.lifecycle_token,
            "required_witness_structural_identities": self.required_witness_structural_identities,
            "first_stable_frame": self.first_stable_frame,
            "last_validated_frame": self.last_validated_frame,
        }


def establish_scene_epoch(
    profile: Mapping[str, Any],
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    observer_epoch_number: int,
) -> SceneEpoch:
    if observer_epoch_number < 1:
        raise ValueError("observer_epoch_number must be positive")
    require_compatible(first, second)
    signals = second["scene_signals"]
    structural = {
        "profile_id": profile["profile_id"],
        "runtime_process_identity": second["runtime_process_identity"],
        "scene_name": signals["active_scene_name"],
        "prot_base": signals["active_scene_prot_base"],
        "master_mode": signals["master_game_mode"],
        "actor_list_head": second["actor_list_head"],
        "executable_state_token": second["executable_state_token"],
        "lifecycle_token": second["lifecycle_token"],
        "required_witness_structural_identities": second["witness_structural_identities"],
        "observer_epoch_number": observer_epoch_number,
    }
    digest = hashlib.sha256(
        json.dumps(structural, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return SceneEpoch(
        epoch_id=f"epoch-{digest}",
        observer_epoch_number=observer_epoch_number,
        profile_id=profile["profile_id"],
        runtime_process_identity=second["runtime_process_identity"],
        scene_name=signals["active_scene_name"],
        prot_base=signals["active_scene_prot_base"],
        master_mode=signals["master_game_mode"],
        actor_list_head=second["actor_list_head"],
        executable_state_token=second["executable_state_token"],
        lifecycle_token=second["lifecycle_token"],
        required_witness_structural_identities=second["witness_structural_identities"],
        first_stable_frame=first["frame"],
        last_validated_frame=second["frame"],
    )
