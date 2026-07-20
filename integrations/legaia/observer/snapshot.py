"""One-shot, two-boundary runtime snapshot orchestration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

import jsonschema

from .actor_nodes import traverse_actor_chain
from .client import ProtocolClient
from .epoch import establish_scene_epoch, require_compatible
from .errors import (
    ChainInvalid,
    ObserverError,
    ProfileRejected,
    ProtocolError,
    RetryExhausted,
    SnapshotUnstable,
)
from .profile import LoadedProfile, ProfileSelector


OBSERVER_VERSION = "1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "runtime-observation.v1.schema.json"


def canonical_snapshot_json(snapshot: Mapping[str, Any]) -> str:
    validate_snapshot(snapshot)
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(dict(snapshot), schema)
    forbidden = {"raw_bytes", "payload", "ram_dump", "disc_path", "host_path", "dialogue", "executable_bytes"}

    def scan(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key.lower() in forbidden:
                    raise ValueError(f"snapshot contains forbidden field: {key}")
                scan(child)
        elif isinstance(value, list):
            for child in value:
                scan(child)

    scan(snapshot)


class RuntimeObserver:
    def __init__(self, client: ProtocolClient, profile: LoadedProfile) -> None:
        self.client = client
        self.profile = profile
        self.selector = ProfileSelector(client, profile)
        self._observer_epoch = 0

    def capture(self, maximum_attempts: int | None = None) -> dict[str, Any]:
        self.selector.negotiate()
        policy_attempts = self.profile.document["observation_policy"]["snapshot"]["maximum_attempts"]
        attempts = policy_attempts if maximum_attempts is None else maximum_attempts
        if not 1 <= attempts <= policy_attempts:
            raise ValueError(f"maximum_attempts must be between 1 and {policy_attempts}")
        failures: list[dict[str, str]] = []
        start_requests = self.client.request_count
        total_started = time.perf_counter()
        for attempt in range(1, attempts + 1):
            try:
                before = self.selector.sample_boundary()
                token = before["observation_guard_token"]
                scoped = self.selector.sample_guard_only(token)
                second = dict(before)
                second["frame"] = scoped["frame_after"]
                second["global_executable_state_before"] = scoped[
                    "global_executable_state_before"
                ]
                second["global_executable_state_after"] = scoped[
                    "global_executable_state_after"
                ]
                second["stable_global_executable_state"] = scoped[
                    "stable_global_executable_state"
                ]
                require_compatible(before, second)
                self._observer_epoch += 1
                epoch = establish_scene_epoch(
                    self.profile.document, before, second, self._observer_epoch
                )
                traversal = traverse_actor_chain(self.client, self.profile.document, epoch)
                final_guard = self.selector.sample_guard_only(token)
                if final_guard["guard_token"] != token:
                    raise SnapshotUnstable("final scoped observation guard changed")
                if final_guard["frame_after"] < epoch.last_validated_frame:
                    raise SnapshotUnstable("snapshot boundary frame moved backwards")
                epoch_dict = epoch.as_dict()
                epoch_dict["last_validated_frame"] = final_guard["frame_after"]
                selection = self.selector.selection_result(before)
                snapshot = {
                    "schema_version": 1,
                    "observer_version": OBSERVER_VERSION,
                    "profile": {
                        "profile_id": self.profile.document["profile_id"],
                        "profile_hash": self.profile.profile_hash,
                        "selection": selection,
                    },
                    "protocol": selection["protocol_identity"],
                    "runtime": selection["runtime_identity"],
                    "epoch": epoch_dict,
                    "scene_signals": before["scene_signals"],
                    "execution_witnesses": before["witness_results"],
                    "actor_chain": traversal.as_dict(),
                    "boundaries": {
                        "before": {
                            key: value for key, value in before.items()
                            if key not in {"witness_results", "actor_list_head_raw"}
                        },
                        "after": final_guard,
                        "stable": True,
                    },
                    "snapshot_current_at_capture": True,
                    "historical_observation": True,
                    "metrics": {
                        "attempt": attempt,
                        "request_count": self.client.request_count - start_requests,
                        "actor_read_requests": traversal.request_count,
                        "actor_bytes_read": traversal.bytes_read,
                        "traversal_duration_ms": round(traversal.duration_ms, 3),
                        "total_duration_ms": round((time.perf_counter() - total_started) * 1000.0, 3),
                    },
                    "diagnostics": failures,
                    "unresolved": [
                        "Live node addresses and chain indices are epoch-scoped, not semantic actor identities.",
                        "Conditional actor subclass applicability is unresolved.",
                        "Imported actor correlation is intentionally absent.",
                    ],
                }
                validate_snapshot(snapshot)
                return snapshot
            except (ProfileRejected, SnapshotUnstable, ChainInvalid) as exc:
                failures.append({"attempt": str(attempt), "classification": type(exc).__name__, "message": str(exc)})
                if attempt == attempts:
                    raise RetryExhausted(
                        f"snapshot retry exhausted after {attempts} attempts: {type(exc).__name__}: {exc}"
                    ) from exc
            except ObserverError:
                raise
        raise RetryExhausted("snapshot retry exhausted")  # pragma: no cover

    def capture_boundary(self, subsequent_samples: int = 10) -> dict[str, Any]:
        """Establish and repeatedly validate a scoped epoch without actor reads."""
        if not 1 <= subsequent_samples <= 100:
            raise ValueError("subsequent_samples must be between 1 and 100")
        self.selector.negotiate()
        started = time.perf_counter()
        start_requests = self.client.request_count
        before = self.selector.sample_boundary()
        token = before["observation_guard_token"]
        samples = [self.selector.sample_guard_only(token)]
        second = dict(before)
        second["frame"] = samples[0]["frame_after"]
        require_compatible(before, second)
        self._observer_epoch += 1
        epoch = establish_scene_epoch(
            self.profile.document, before, second, self._observer_epoch
        )
        for _ in range(subsequent_samples):
            sample = self.selector.sample_guard_only(token)
            if sample["guard_token"] != token:
                raise SnapshotUnstable("scoped observation guard changed")
            samples.append(sample)
        first_frame = before["frame"]
        last_frame = samples[-1]["frame_after"]
        if not isinstance(first_frame, int) or not isinstance(last_frame, int):
            raise ProtocolError("boundary-only frame stamps are unavailable")
        if last_frame < first_frame:
            raise SnapshotUnstable("boundary-only frame moved backwards")
        global_tokens = [before.get("global_executable_state_after")]
        for sample in samples:
            global_tokens.extend(
                [
                    sample.get("global_executable_state_before"),
                    sample.get("global_executable_state_after"),
                ]
            )
        global_changes = sum(
            1 for left, right in zip(global_tokens, global_tokens[1:]) if left != right
        )
        component_changes: dict[str, int] = {}
        for component in ("watched_pages", "registrations", "lifecycle_catalog"):
            values: list[Any] = []
            for sample in samples:
                before_components = sample.get("global_state_components_before") or {}
                after_components = sample.get("global_state_components_after") or {}
                values.extend([before_components.get(component), after_components.get(component)])
            component_changes[component] = sum(
                1 for left, right in zip(values, values[1:]) if left != right
            )
        result = {
            "schema_version": 1,
            "observation_kind": "scoped-scene-epoch-boundary",
            "observer_version": OBSERVER_VERSION,
            "profile": {
                "profile_id": self.profile.document["profile_id"],
                "profile_hash": self.profile.profile_hash,
                "selection": self.selector.selection_result(before),
            },
            "protocol": self.selector.selection_result(before)["protocol_identity"],
            "runtime": self.selector.selection_result(before)["runtime_identity"],
            "epoch": epoch.as_dict(),
            "scene_signals": before["scene_signals"],
            "execution_witnesses": before["witness_results"],
            "guard": {
                "token": token,
                "descriptor": self.selector.guard_descriptor(),
                "initial_evidence": before["guard_evidence"],
                "compatible_sample_count": len(samples) + 1,
                "subsequent_sample_count": subsequent_samples,
            },
            "frames": {
                "first": first_frame,
                "last": last_frame,
                "advanced": last_frame > first_frame,
            },
            "global_executable_state": {
                "changes_observed_between_samples": global_changes,
                "component_changes": component_changes,
                "remains_diagnostic": True,
            },
            "actor_node_reads": 0,
            "actor_bytes_read": 0,
            "ram_writes": 0,
            "metrics": {
                "request_count": self.client.request_count - start_requests,
                "duration_ms": round((time.perf_counter() - started) * 1000.0, 3),
            },
            "historical_observation": True,
            "diagnostics": [],
            "unresolved": [
                "Retail actor traversal remains separately gated.",
                "Imported actor correlation is intentionally absent.",
            ],
        }
        # Reuse the same privacy scan as snapshots without claiming the actor
        # snapshot schema applies to this boundary-only diagnostic.
        forbidden = {
            "raw_bytes", "payload", "ram_dump", "disc_path", "host_path",
            "dialogue", "executable_bytes",
        }

        def scan(value: Any) -> None:
            if isinstance(value, Mapping):
                for key, child in value.items():
                    if key.lower() in forbidden:
                        raise ValueError(f"boundary observation contains forbidden field: {key}")
                    scan(child)
            elif isinstance(value, list):
                for child in value:
                    scan(child)

        scan(result)
        return result
