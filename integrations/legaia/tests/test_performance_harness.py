from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from integrations.legaia.observer.performance import BenchmarkCase, PerformanceHarness, load_benchmark_targets


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "benchmarks" / "scus94254-na-world-map-v1.json"


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeClient:
    def __init__(self, scene: str = "town0c") -> None:
        self.scene, self.frame, self.request_count = scene, 100, 0
        self.performance_commands: list[str] = []

    def runtime_identity(self) -> dict[str, Any]:
        self.request_count += 1
        return {"runtime": {"process_instance_id": "proc-" + "a" * 64, "implementation": "psxrecomp"}, "main_executable": {"serial": "SCUS-94254", "source_identity": {"algorithm": "sha256", "scope": "ps-x-exe-body", "sha256": "1" * 64}}}

    def read_regions(self, regions: list[dict[str, Any]], *, guard: dict[str, Any] | None = None) -> dict[str, Any]:
        self.request_count += 1; self.frame += 1
        records = []
        for region in regions:
            if region["key"] == "active_scene_name":
                data = self.scene.encode("ascii") + b"\0" * (region["len"] - len(self.scene))
            else:
                data = (3).to_bytes(region["len"], "little")
            records.append({"key": region["key"], "len": region["len"], "hex": data.hex()})
        return {"regions": records, "frame_before": self.frame - 1, "frame_after": self.frame, "stable_frame": True}

    def performance_stats(self, command: str, **params: Any) -> dict[str, Any]:
        self.request_count += 1
        self.performance_commands.append(command)
        scale = self.frame
        if command == "dispatch_stats": return {"static_hits": scale * 3, "miss_total": scale, "miss_unique": 2}
        if command == "dirty_ram_stats": return {"blocks_run": scale * 2, "insns_run": scale * 8, "aborts": 0, "guard_yields": 0, "native_handoffs": scale}
        if command == "overlay_loader_status": return {"loads": 1, "invalidations": 0, "revalidations": 0, "unregistered_funcs": 0, "dispatch_native": scale, "dispatch_interp_fallback": scale * 2, "stale_blocked": 0, "cache_dir": "C:\\not-exported"}
        if command == "phase_profile": return {"samples": 10, "interp_samples": 6, "native_samples": 1, "static_samples": 2, "gpu_samples": 0, "other_samples": 1, "exc_samples": 0, "interp_share": .6, "native_share": .1, "static_share": .2, "gpu_share": 0.0, "other_share": .1, "exc_share": 0.0}
        raise AssertionError(command)

    def lifecycle_token(self) -> dict[str, Any]:
        self.request_count += 1
        return {"event_latest_sequence": self.frame}


class PerformanceHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = load_benchmark_targets(TARGETS_PATH)

    def test_01_target_document_is_deterministic_and_metadata_only(self) -> None:
        self.assertEqual(sorted(self.targets), ["map01-world-map", "town0c-field-control"])
        self.assertEqual(self.targets["map01-world-map"].signals[0].expected, "map01")

    def test_02_case_requires_bounded_intervals_and_polling(self) -> None:
        with self.assertRaises(ValueError): BenchmarkCase("bad", "town0c-field-control", 11, 0, 1, 1).validate()
        with self.assertRaises(ValueError): BenchmarkCase("bad", "town0c-field-control", 0, 0, 0, 1).validate()

    def test_03_control_run_is_metadata_only_and_has_no_actor_or_write_actions(self) -> None:
        clock, client = FakeClock(), FakeClient()
        report = PerformanceHarness(client, self.targets, clock=clock, sleep=clock.sleep).run_case(
            BenchmarkCase("control-idle", "town0c-field-control", 0, 0, 1, 2)
        )
        self.assertEqual(report["aggregate"]["sample_count"], 2)
        self.assertEqual(report["metrics"]["actor_node_requests"], 0)
        self.assertEqual(report["metrics"]["actor_bytes_read"], 0)
        self.assertEqual(report["metrics"]["ram_writes"], 0)
        encoded = json.dumps(report)
        self.assertNotIn("cache_dir", encoded)
        self.assertNotIn("C:\\", encoded)

    def test_04_modest_polling_is_recorded_and_scene_mismatch_rejected(self) -> None:
        clock, client = FakeClock(), FakeClient()
        report = PerformanceHarness(client, self.targets, clock=clock, sleep=clock.sleep).run_case(
            BenchmarkCase("control-poll", "town0c-field-control", 2, 0, 1, 1)
        )
        self.assertGreater(report["runs"][0]["observer_poll_requests"], 0)
        clock, client = FakeClock(), FakeClient("town0c")
        with self.assertRaises(Exception):
            PerformanceHarness(client, self.targets, clock=clock, sleep=clock.sleep).run_case(
                BenchmarkCase("wrong-target", "map01-world-map", 0, 0, 1, 1)
            )

    def test_05_counter_deltas_and_variance_are_reported(self) -> None:
        clock, client = FakeClock(), FakeClient("map01")
        report = PerformanceHarness(client, self.targets, clock=clock, sleep=clock.sleep).run_case(
            BenchmarkCase("map-idle", "map01-world-map", 0, 0, 1, 3)
        )
        self.assertIn("dirty_ram", report["runs"][0]["counter_delta"])
        self.assertIn("effective_fps_stdev", report["aggregate"])
        self.assertEqual(report["runs"][0]["target"]["id"], "map01-world-map")
        self.assertIn("overlay_loader_status", client.performance_commands)
        self.assertNotIn("overlay_status", client.performance_commands)


if __name__ == "__main__":
    unittest.main()
