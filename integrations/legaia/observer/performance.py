"""Bounded, metadata-only runtime performance comparison support.

This module is deliberately title-neutral.  A title supplies only a small
revisioned benchmark-target document containing scene signals.  It neither
launches a process nor changes guest state, cache configuration, renderer,
timing, input, or RAM.
"""

from __future__ import annotations

import json
import math
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .errors import ProfileRejected, ProtocolError


_HEX32 = re.compile(r"^0x[0-9A-Fa-f]{8}$")
_FORBIDDEN = {"bytes", "payload", "raw_bytes", "ram_dump", "disc_path", "host_path", "cache_dir"}


class ReadOnlyMetricsClient(Protocol):
    request_count: int

    def runtime_identity(self) -> dict[str, Any]: ...
    def read_regions(self, regions: list[dict[str, Any]], *, guard: dict[str, Any] | None = None) -> dict[str, Any]: ...
    def performance_stats(self, command: str, **params: Any) -> dict[str, Any]: ...
    def lifecycle_token(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class BenchmarkSignal:
    key: str
    address: str
    width: int
    kind: str
    expected: str | int


@dataclass(frozen=True)
class BenchmarkTarget:
    target_id: str
    signals: tuple[BenchmarkSignal, ...]


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    target_id: str
    poll_hz: float
    warmup_seconds: float
    measurement_seconds: float
    repetitions: int

    def validate(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.case_id):
            raise ValueError("case_id must be a stable lowercase identifier")
        if self.poll_hz < 0 or self.poll_hz > 10:
            raise ValueError("poll_hz must be between 0 and 10")
        if not 0 <= self.warmup_seconds <= 120 or not 1 <= self.measurement_seconds <= 300:
            raise ValueError("benchmark intervals are outside bounded limits")
        if not 1 <= self.repetitions <= 10:
            raise ValueError("repetitions must be between 1 and 10")


def _metadata_only(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key.lower() in _FORBIDDEN:
                raise ValueError(f"benchmark metadata contains forbidden key: {key}")
            _metadata_only(child)
    elif isinstance(value, list):
        for child in value:
            _metadata_only(child)
    elif isinstance(value, str) and (value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value)):
        raise ValueError("benchmark metadata contains an absolute path")


def load_benchmark_targets(path: str | Path) -> dict[str, BenchmarkTarget]:
    """Load only the title-owned scene signal definitions required to compare runs."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load benchmark targets: {exc}") from exc
    _metadata_only(document)
    if document.get("schema_version") != 1 or not isinstance(document.get("targets"), list):
        raise ValueError("benchmark target document has an unsupported schema")
    result: dict[str, BenchmarkTarget] = {}
    for item in document["targets"]:
        if not isinstance(item, Mapping):
            raise ValueError("benchmark target must be an object")
        target_id = item.get("target_id")
        if not isinstance(target_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", target_id):
            raise ValueError("benchmark target ID is invalid")
        if target_id in result:
            raise ValueError("benchmark target ID is duplicated")
        raw_signals = item.get("required_signals")
        if not isinstance(raw_signals, list) or not raw_signals:
            raise ValueError("benchmark target needs at least one signal")
        signals: list[BenchmarkSignal] = []
        keys: set[str] = set()
        for signal in raw_signals:
            if not isinstance(signal, Mapping):
                raise ValueError("benchmark signal must be an object")
            key, address, width, kind, expected = (
                signal.get("id"), signal.get("address"), signal.get("width"),
                signal.get("type"), signal.get("expected"),
            )
            if not isinstance(key, str) or not key or key in keys:
                raise ValueError("benchmark signal ID is invalid or duplicated")
            if not isinstance(address, str) or not _HEX32.fullmatch(address):
                raise ValueError("benchmark signal address is invalid")
            if kind == "ascii_nul_terminated":
                if width not in {8, 16} or not isinstance(expected, str):
                    raise ValueError("benchmark ASCII signal is invalid")
            elif kind == "u16_le":
                if width != 2 or not isinstance(expected, int):
                    raise ValueError("benchmark u16 signal is invalid")
            else:
                raise ValueError("benchmark signal type is unsupported")
            keys.add(key)
            signals.append(BenchmarkSignal(key, address, width, kind, expected))
        result[target_id] = BenchmarkTarget(target_id, tuple(signals))
    return result


def _decode(signal: BenchmarkSignal, payload: bytes) -> str | int:
    if len(payload) != signal.width:
        raise ProtocolError(f"benchmark signal {signal.key} returned wrong width")
    if signal.kind == "u16_le":
        return int.from_bytes(payload, "little")
    nul = payload.find(b"\0")
    if nul < 0 or any(payload[nul + 1 :]):
        raise ProtocolError(f"benchmark signal {signal.key} is malformed")
    try:
        return payload[:nul].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ProtocolError(f"benchmark signal {signal.key} is not ASCII") from exc


def _numeric(response: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, int]:
    return {field: int(response.get(field, 0)) for field in fields if isinstance(response.get(field), int)}


def _delta(before: Mapping[str, int], after: Mapping[str, int]) -> dict[str, int]:
    return {key: after.get(key, 0) - before.get(key, 0) for key in sorted(set(before) | set(after))}


class PerformanceHarness:
    """Compare equivalent scene intervals without changing runtime behavior."""

    def __init__(self, client: ReadOnlyMetricsClient, targets: Mapping[str, BenchmarkTarget], *,
                 clock: Callable[[], float] = time.perf_counter, sleep: Callable[[float], None] = time.sleep) -> None:
        self.client, self.targets, self.clock, self.sleep = client, dict(targets), clock, sleep

    def sample_target(self, target: BenchmarkTarget) -> dict[str, Any]:
        regions = [{"key": signal.key, "addr": signal.address, "len": signal.width} for signal in target.signals]
        response = self.client.read_regions(regions)
        records = response.get("regions")
        if not isinstance(records, list) or len(records) != len(regions):
            raise ProtocolError("benchmark target sample is incomplete")
        values: dict[str, str | int] = {}
        for expected, record in zip(target.signals, records):
            if record.get("key") != expected.key or record.get("len") != expected.width:
                raise ProtocolError("benchmark target response order changed")
            try:
                payload = bytes.fromhex(record["hex"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError("benchmark target response is malformed") from exc
            values[expected.key] = _decode(expected, payload)
        return {
            "frame_before": response.get("frame_before"), "frame_after": response.get("frame_after"),
            "stable_frame": response.get("stable_frame") is True,
            "signals": values,
            "matches": all(values[item.key] == item.expected for item in target.signals),
        }

    def wait_for_target(self, target_id: str, *, timeout_seconds: float = 120.0) -> dict[str, Any]:
        if target_id not in self.targets:
            raise ValueError(f"unknown benchmark target: {target_id}")
        deadline, last = self.clock() + timeout_seconds, None
        while self.clock() < deadline:
            last = self.sample_target(self.targets[target_id])
            if last["matches"] and last["stable_frame"]:
                return last
            self.sleep(0.25)
        raise ProfileRejected(f"benchmark target {target_id} did not stabilize: {last}")

    def _counters(self) -> dict[str, Any]:
        dispatch = self.client.performance_stats("dispatch_stats")
        dirty = self.client.performance_stats("dirty_ram_stats")
        overlay = self.client.performance_stats("overlay_status")
        lifecycle = self.client.lifecycle_token()
        return {
            "dispatch": _numeric(dispatch, ("static_hits", "miss_total", "miss_unique")),
            "dirty_ram": _numeric(dirty, ("blocks_run", "insns_run", "aborts", "guard_yields", "native_handoffs")),
            "overlay": _numeric(overlay, ("loads", "invalidations", "revalidations", "unregistered_funcs", "dispatch_native", "dispatch_interp_fallback", "stale_blocked", "static_checks", "static_hits", "static_variant_misses", "static_address_misses", "static_rehashes", "static_crc_misses", "gen_fastpath")),
            "lifecycle_latest_sequence": lifecycle.get("event_latest_sequence"),
        }

    def _run_once(self, case: BenchmarkCase) -> dict[str, Any]:
        target = self.targets[case.target_id]
        settled = self.wait_for_target(case.target_id)
        if case.warmup_seconds:
            self.sleep(case.warmup_seconds)
        if not self.sample_target(target)["matches"]:
            raise ProfileRejected("benchmark target changed during warm-up")
        start = self._counters()
        start_sample = self.sample_target(target)
        started = self.clock()
        polls = 0
        next_poll = started
        deadline = started + case.measurement_seconds
        while self.clock() < deadline:
            if case.poll_hz and self.clock() >= next_poll:
                sample = self.sample_target(target)
                polls += 1
                if not sample["matches"] or not sample["stable_frame"]:
                    raise ProfileRejected("benchmark target changed during measurement")
                next_poll += 1.0 / case.poll_hz
            self.sleep(min(0.05, max(0.0, deadline - self.clock())))
        elapsed = self.clock() - started
        end_sample = self.sample_target(target)
        if not end_sample["matches"] or not end_sample["stable_frame"]:
            raise ProfileRejected("benchmark target changed at measurement end")
        end = self._counters()
        frames = int(end_sample["frame_after"]) - int(start_sample["frame_after"])
        phase = self.client.performance_stats("phase_profile", window=max(1, min(60, math.ceil(elapsed))))
        return {
            "target": {"id": target.target_id, "signals": settled["signals"]},
            "wall_duration_ms": round(elapsed * 1000.0, 3),
            "emulated_frames": frames,
            "effective_fps": round(frames / elapsed, 4) if elapsed else None,
            "observer_poll_requests": polls,
            "counter_delta": {
                "dispatch": _delta(start["dispatch"], end["dispatch"]),
                "dirty_ram": _delta(start["dirty_ram"], end["dirty_ram"]),
                "overlay": _delta(start["overlay"], end["overlay"]),
                "lifecycle_events": self._lifecycle_delta(start["lifecycle_latest_sequence"], end["lifecycle_latest_sequence"]),
            },
            "phase_profile": _numeric(phase, ("samples", "interp_samples", "native_samples", "static_samples", "gpu_samples", "other_samples", "exc_samples")),
            "phase_shares": {key: phase.get(key) for key in ("interp_share", "native_share", "static_share", "gpu_share", "other_share", "exc_share") if isinstance(phase.get(key), (float, int))},
            "frame_time_ms": {"mean": round((elapsed * 1000.0) / frames, 4) if frames > 0 else None, "source": "wall-clock divided by emulated-frame delta; per-frame host samples unavailable"},
            "cpu_utilization": None,
            "cpu_utilization_note": "not available through the bounded runtime protocol",
        }

    @staticmethod
    def _lifecycle_delta(before: Any, after: Any) -> int | None:
        return after - before if isinstance(before, int) and isinstance(after, int) else None

    def run_case(self, case: BenchmarkCase) -> dict[str, Any]:
        case.validate()
        if case.target_id not in self.targets:
            raise ValueError(f"unknown benchmark target: {case.target_id}")
        runtime = self.client.runtime_identity()
        runs = [self._run_once(case) for _ in range(case.repetitions)]
        fps = [run["effective_fps"] for run in runs if isinstance(run["effective_fps"], (int, float))]
        report = {
            "schema_version": 1,
            "kind": "read-only-performance-ab",
            "runtime_identity": {
                "process_instance_id": runtime.get("runtime", {}).get("process_instance_id"),
                "implementation": runtime.get("runtime", {}).get("implementation"),
                "program_serial": runtime.get("main_executable", {}).get("serial"),
                "source_identity": runtime.get("main_executable", {}).get("source_identity"),
            },
            "configuration": {"case_id": case.case_id, "target_id": case.target_id, "poll_hz": case.poll_hz, "warmup_seconds": case.warmup_seconds, "measurement_seconds": case.measurement_seconds, "repetitions": case.repetitions},
            "counter_reset": "process-scoped monotonic counters compared as bounded start/end deltas; the harness never resets runtime state",
            "runs": runs,
            "aggregate": {"sample_count": len(runs), "effective_fps_mean": round(statistics.fmean(fps), 4) if fps else None, "effective_fps_stdev": round(statistics.stdev(fps), 4) if len(fps) > 1 else 0.0},
            "metrics": {"protocol_request_count": self.client.request_count, "actor_node_requests": 0, "actor_bytes_read": 0, "ram_writes": 0},
            "privacy": {"metadata_only": True, "raw_ram_included": False},
        }
        _metadata_only(report)
        return report
