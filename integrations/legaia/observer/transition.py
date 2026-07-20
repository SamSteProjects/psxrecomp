"""Transition-only town01 scene-epoch acceptance state machine."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

from .epoch import establish_scene_epoch, require_compatible
from .errors import ObserverError, ProfileRejected, SnapshotUnstable
from .profile import LoadedProfile, ProfileSelector


class TransitionState(str, Enum):
    WAITING_FOR_INITIAL_TOWN01 = "waiting_for_initial_town01"
    STABILIZING_INITIAL_EPOCH = "stabilizing_initial_epoch"
    INITIAL_EPOCH_STABLE = "initial_epoch_stable"
    WAITING_FOR_EXIT = "waiting_for_exit"
    OLD_EPOCH_INVALIDATED = "old_epoch_invalidated"
    OUTSIDE_TOWN01 = "outside_town01"
    WAITING_FOR_REENTRY = "waiting_for_reentry"
    STABILIZING_NEW_EPOCH = "stabilizing_new_epoch"
    NEW_EPOCH_STABLE = "new_epoch_stable"
    COMPLETED = "completed"
    FAILED = "failed"


class TransitionTimeout(ObserverError):
    """A bounded transition state did not complete before its deadline."""


class Navigator(Protocol):
    mode: str

    def begin(self, phase: str) -> None: ...

    def cleanup(self) -> None: ...


@dataclass
class ManualNavigator:
    """Normal user navigation; the observer performs no input injection."""

    announce: Callable[[str], None] = print
    mode: str = "manual"

    def begin(self, phase: str) -> None:
        if phase == "exit":
            self.announce("Profiled scene epoch established. Navigate out normally.")
        elif phase == "reentry":
            self.announce("Old epoch invalidated. Return to the profiled scene normally.")

    def cleanup(self) -> None:
        return


@dataclass(frozen=True)
class TransitionLimits:
    poll_interval_seconds: float = 0.1
    initial_timeout_seconds: float = 30.0
    exit_timeout_seconds: float = 180.0
    outside_timeout_seconds: float = 30.0
    reentry_timeout_seconds: float = 180.0
    stabilization_timeout_seconds: float = 30.0
    initial_stable_samples: int = 10
    reentry_stable_samples: int = 10
    maximum_outside_samples: int = 32

    def validate(self) -> None:
        if not 0.1 <= self.poll_interval_seconds <= 5.0:
            raise ValueError("poll interval must be between 0.1 and 5 seconds")
        for name in (
            "initial_timeout_seconds", "exit_timeout_seconds", "outside_timeout_seconds",
            "reentry_timeout_seconds", "stabilization_timeout_seconds",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.initial_stable_samples < 10 or self.reentry_stable_samples < 10:
            raise ValueError("transition acceptance requires at least ten stable samples")
        if not 1 <= self.maximum_outside_samples <= 128:
            raise ValueError("maximum_outside_samples must be between 1 and 128")


def _privacy_scan(value: Any) -> None:
    forbidden = {
        "raw_bytes", "payload", "ram_dump", "disc_path", "host_path", "dialogue",
        "executable_bytes", "actor_chain", "actors", "nodes",
    }
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key.lower() in forbidden:
                raise ValueError(f"transition report contains forbidden field: {key}")
            _privacy_scan(child)
    elif isinstance(value, list):
        for child in value:
            _privacy_scan(child)


def _sample_summary(sample: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "frame": sample.get("frame_after", sample.get("frame")),
        "stable_frame": sample.get("stable_frame"),
        "stable_executable_state": sample.get("stable_executable_state"),
        "scene_signals": sample.get("scene_signals"),
        "actor_list_head": sample.get("actor_list_head"),
        "decode_errors": sample.get("decode_errors", {}),
    }


class SceneTransitionWatcher:
    def __init__(
        self,
        selector: ProfileSelector,
        profile: LoadedProfile,
        *,
        limits: TransitionLimits | None = None,
        navigator: Navigator | None = None,
        announce: Callable[[str], None] = print,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.selector = selector
        self.profile = profile
        self.limits = limits or TransitionLimits()
        self.limits.validate()
        self.navigator = navigator or ManualNavigator(announce)
        self.announce = announce
        self.sleep = sleep
        self.clock = clock
        self.state = TransitionState.WAITING_FOR_INITIAL_TOWN01
        self.events: list[dict[str, Any]] = []
        self._epoch_number = 0

    def _set_state(self, state: TransitionState, **evidence: Any) -> None:
        self.state = state
        self.events.append({"state": state.value, **evidence})

    def _deadline(self, seconds: float) -> float:
        return self.clock() + seconds

    def _pause(self) -> None:
        self.sleep(self.limits.poll_interval_seconds)

    def _town01_signals_match(self, sample: Mapping[str, Any]) -> bool:
        observed = sample.get("scene_signals") or {}
        return all(
            observed.get(signal["id"]) == signal["expected"]
            for signal in self.profile.document["scene_identity"]["required_signals"]
        )

    def _runtime_is_current(self) -> bool:
        current = self.selector.client.runtime_identity()
        baseline = self.selector.runtime
        if baseline is None:
            return False
        structural = {key: value for key, value in current.items() if key not in {"id", "frame"}}
        expected = {key: value for key, value in baseline.items() if key not in {"id", "frame"}}
        return structural == expected

    def _establish_epoch(self, stable_samples: int, *, new_epoch: bool) -> tuple[dict[str, Any], dict[str, Any]]:
        timeout_seconds = (
            self.limits.stabilization_timeout_seconds
            if new_epoch
            else self.limits.initial_timeout_seconds
        )
        timeout = self._deadline(timeout_seconds)
        last_error: str | None = None
        while self.clock() < timeout:
            try:
                first = self.selector.sample_boundary()
                token = first["observation_guard_token"]
                second_guard = self.selector.sample_guard_only(token)
                second = dict(first)
                second["frame"] = second_guard["frame_after"]
                require_compatible(first, second)
                for _ in range(stable_samples):
                    guard = self.selector.sample_guard_only(token)
                    if guard["guard_token"] != token:
                        raise SnapshotUnstable("scoped token changed during stabilization")
                final = self.selector.sample_guard_only(token)
                if final["guard_token"] != token:
                    raise SnapshotUnstable("final scoped token changed")
                self._epoch_number += 1
                epoch = establish_scene_epoch(
                    self.profile.document, first, second, self._epoch_number
                ).as_dict()
                epoch["last_validated_frame"] = final["frame_after"]
                result = {
                    "epoch": epoch,
                    "token": token,
                    "scene_signals": first["scene_signals"],
                    "actor_list_head": first["actor_list_head"],
                    "witnesses": first["witness_results"],
                    "stable_sample_count": stable_samples + 3,
                    "first_frame": first["frame"],
                    "last_frame": final["frame_after"],
                    "frames_advanced": final["frame_after"] > first["frame"],
                }
                return result, first
            except (ProfileRejected, SnapshotUnstable) as exc:
                last_error = str(exc)
                self._pause()
        label = "re-entry" if new_epoch else "initial"
        raise TransitionTimeout(f"{label} town01 epoch did not stabilize: {last_error}")

    @staticmethod
    def _classify_invalidation(
        initial: Mapping[str, Any], scene: Mapping[str, Any], guard: Mapping[str, Any]
    ) -> list[str]:
        reasons: list[str] = []
        old_signals = initial.get("scene_signals") or {}
        new_signals = scene.get("scene_signals") or {}
        for key in ("active_scene_name", "active_scene_prot_base", "master_game_mode"):
            if old_signals.get(key) != new_signals.get(key):
                reasons.append(f"{key}_changed")
        if initial.get("actor_list_head") != scene.get("actor_list_head"):
            reasons.append("actor_list_head_changed")
        if not guard.get("runtime_instance_matches", True):
            reasons.append("runtime_instance_changed")
        for witness in guard.get("execution_witnesses") or []:
            pc = witness.get("pc", "unknown")
            if witness.get("status") == "missing":
                reasons.append(f"witness_{pc}_missing")
            elif witness.get("current") is not True:
                reasons.append(f"witness_{pc}_stale")
        if guard.get("stable") is not True:
            reasons.append("guard_before_after_changed")
        if guard.get("expected_token_matched") is not True:
            reasons.append("expected_token_mismatch")
        if not reasons and guard.get("compatible") is not True:
            reasons.append("profile_relevant_guard_incompatibility")
        return reasons

    def run(self) -> dict[str, Any]:
        started = self.clock()
        start_requests = self.selector.client.request_count
        self.limits.validate()
        self.selector.negotiate()
        try:
            self._set_state(TransitionState.STABILIZING_INITIAL_EPOCH)
            initial, initial_boundary = self._establish_epoch(
                self.limits.initial_stable_samples, new_epoch=False
            )
            old_token = initial["token"]
            process_identity = initial["epoch"]["runtime_process_identity"]
            self._set_state(
                TransitionState.INITIAL_EPOCH_STABLE,
                frame=initial["last_frame"], stable_samples=initial["stable_sample_count"],
            )
            self._set_state(TransitionState.WAITING_FOR_EXIT)
            self.navigator.begin("exit")
            exit_deadline = self._deadline(self.limits.exit_timeout_seconds)
            invalidation: dict[str, Any] | None = None
            outside_first: dict[str, Any] | None = None
            while self.clock() < exit_deadline:
                scene = self.selector.sample_scene_signals_unscoped()
                guard = self.selector.sample_guard_diagnostic(old_token)
                if guard["compatible"]:
                    self._pause()
                    continue
                if not guard["stable"]:
                    self._pause()
                    continue
                reasons = self._classify_invalidation(initial_boundary, scene, guard)
                if reasons:
                    invalidation = {
                        "frame": guard["frame_after"],
                        "reasons": reasons,
                        "old_expected_token_rejected": not guard["expected_token_matched"],
                        "guard_valid": guard["valid"],
                        "guard_stable": guard["stable"],
                        "new_token": guard["token_before"],
                        "failure_reason": guard["failure_reason"],
                        "scene": _sample_summary(scene),
                    }
                    outside_first = scene
                    break
                self._pause()
            if invalidation is None or outside_first is None:
                raise TransitionTimeout("town01 did not exit before timeout")
            if not invalidation["old_expected_token_rejected"]:
                raise SnapshotUnstable("old expected token was not rejected after transition")
            self._set_state(
                TransitionState.OLD_EPOCH_INVALIDATED,
                frame=invalidation["frame"], reasons=invalidation["reasons"],
            )
            self.announce("Old epoch invalidated: " + ", ".join(invalidation["reasons"]))

            self._set_state(TransitionState.OUTSIDE_TOWN01)
            outside_samples = [_sample_summary(outside_first)]
            outside_deadline = self._deadline(self.limits.outside_timeout_seconds)
            stable_outside: dict[str, Any] | None = None
            previous = _sample_summary(outside_first)
            while self.clock() < outside_deadline:
                self._pause()
                sample = self.selector.sample_scene_signals_unscoped()
                summary = _sample_summary(sample)
                if len(outside_samples) < self.limits.maximum_outside_samples:
                    outside_samples.append(summary)
                if (
                    summary["stable_frame"] is True
                    and summary["stable_executable_state"] is True
                    and previous["stable_frame"] is True
                    and previous["stable_executable_state"] is True
                    and summary["scene_signals"] == previous["scene_signals"]
                    and (
                    summary["actor_list_head"] == previous["actor_list_head"]
                    )
                ):
                    stable_outside = summary
                    break
                previous = summary
            if stable_outside is None:
                raise TransitionTimeout(
                    "no stable outside-town01 structural state was observed; "
                    f"last_sample={previous}"
                )
            if not self._runtime_is_current():
                raise SnapshotUnstable("runtime or executable identity changed outside town01")

            self._set_state(TransitionState.WAITING_FOR_REENTRY)
            self.navigator.begin("reentry")
            reentry_deadline = self._deadline(self.limits.reentry_timeout_seconds)
            candidate_seen = False
            while self.clock() < reentry_deadline:
                scene = self.selector.sample_scene_signals_unscoped()
                if self._town01_signals_match(scene):
                    candidate_seen = True
                    break
                if len(outside_samples) < self.limits.maximum_outside_samples:
                    outside_samples.append(_sample_summary(scene))
                self._pause()
            if not candidate_seen:
                last = outside_samples[-1] if outside_samples else None
                raise TransitionTimeout(
                    "profiled-scene re-entry was not detected before timeout; "
                    f"last_sample={last}"
                )

            self._set_state(TransitionState.STABILIZING_NEW_EPOCH)
            reentry, _ = self._establish_epoch(
                self.limits.reentry_stable_samples, new_epoch=True
            )
            if reentry["epoch"]["runtime_process_identity"] != process_identity:
                raise SnapshotUnstable("same-process re-entry changed runtime identity")
            if reentry["epoch"]["epoch_id"] == initial["epoch"]["epoch_id"]:
                raise SnapshotUnstable("re-entry reused the observer-owned epoch identity")
            self._set_state(
                TransitionState.NEW_EPOCH_STABLE,
                frame=reentry["last_frame"], stable_samples=reentry["stable_sample_count"],
            )
            self._set_state(TransitionState.COMPLETED)
            report = {
                "schema_version": 1,
                "observation_kind": "town01-scene-transition-acceptance",
                "profile_id": self.profile.document["profile_id"],
                "protocol": self.selector.protocol["protocol"],
                "runtime_identity_summary": {
                    "process_instance_id": process_identity,
                    "implementation": self.selector.runtime["runtime"]["implementation"],
                    "program_serial": self.selector.runtime["main_executable"]["serial"],
                    "source_identity": self.selector.runtime["main_executable"]["source_identity"],
                },
                "navigation_mode": self.navigator.mode,
                "initial_epoch": initial,
                "exit_invalidation": invalidation,
                "outside_scene_samples": outside_samples,
                "stable_outside_state": stable_outside,
                "reentry_epoch": {
                    **reentry,
                    "token_differs_from_initial": reentry["token"] != old_token,
                    "token_reuse_is_state_equivalence": reentry["token"] == old_token,
                    "actor_head_reused": reentry["actor_list_head"] == initial["actor_list_head"],
                },
                "state_transitions": self.events,
                "limits": self.limits.__dict__,
                "metrics": {
                    "request_count": self.selector.client.request_count - start_requests,
                    "duration_ms": round((self.clock() - started) * 1000.0, 3),
                    "actor_node_requests": 0,
                    "actor_bytes_read": 0,
                    "ram_writes": 0,
                },
                "privacy": {"metadata_only": True, "raw_ram_included": False},
                "unresolved": [
                    "No actor-node traversal was performed.",
                    "Imported/runtime actor correlation remains unimplemented.",
                ],
            }
            _privacy_scan(report)
            return report
        except Exception:
            self._set_state(TransitionState.FAILED)
            raise
        finally:
            self.navigator.cleanup()
