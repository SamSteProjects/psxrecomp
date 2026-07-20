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
from .errors import ChainInvalid, ObserverError, ProfileRejected, RetryExhausted, SnapshotUnstable
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
                stable_samples = self.profile.document["observation_policy"]["snapshot"]["stability_samples"]
                samples = [self.selector.sample_boundary() for _ in range(stable_samples)]
                for first, second in zip(samples, samples[1:]):
                    require_compatible(first, second)
                self._observer_epoch += 1
                epoch = establish_scene_epoch(
                    self.profile.document, samples[-2], samples[-1], self._observer_epoch
                )
                traversal = traverse_actor_chain(self.client, self.profile.document, epoch)
                after = self.selector.sample_boundary()
                require_compatible(samples[-1], after)
                if after["frame"] < epoch.last_validated_frame:
                    raise SnapshotUnstable("snapshot boundary frame moved backwards")
                epoch_dict = epoch.as_dict()
                epoch_dict["last_validated_frame"] = after["frame"]
                selection = self.selector.selection_result(samples[-1])
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
                    "scene_signals": after["scene_signals"],
                    "execution_witnesses": after["witness_results"],
                    "actor_chain": traversal.as_dict(),
                    "boundaries": {
                        "before": {
                            key: value for key, value in samples[-1].items()
                            if key not in {"witness_results", "actor_list_head_raw"}
                        },
                        "after": {
                            key: value for key, value in after.items()
                            if key not in {"witness_results", "actor_list_head_raw"}
                        },
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
