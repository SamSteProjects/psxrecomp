from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from integrations.legaia.observer import (
    LoadedProfile,
    ProfileRejected,
    SceneTransitionWatcher,
    TransitionLimits,
    TransitionState,
    TransitionTimeout,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "layouts" / "scus94254-na-field-v1.json"


def profile() -> LoadedProfile:
    return LoadedProfile.from_document(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeClient:
    def __init__(self, selector: "FakeSelector") -> None:
        self.selector = selector
        self.request_count = 0

    def runtime_identity(self) -> dict[str, Any]:
        self.request_count += 1
        return self.selector.runtime


class FakeSelector:
    def __init__(
        self, loaded: LoadedProfile, scenario: str = "normal", *, process_tag: str = "a"
    ) -> None:
        self.profile = loaded
        self.scenario = scenario
        self.phase = "initial"
        self.frame = 100
        self.node_reads = 0
        self.write_commands = 0
        self.runtime_process_identity = "proc-" + process_tag * 64
        self.protocol = {
            "protocol": {"name": "psxrecomp-debug", "major": 1, "minor": 5},
            "server": {"kind": "native"},
            "capabilities": loaded.document["supported_runtime_protocol"]["required_capabilities"],
        }
        source = loaded.document["executable_identity"]["runtime_source_identity"]
        self.runtime = {
            "id": 1,
            "ok": True,
            "runtime": {
                "implementation": "psxrecomp",
                "process_instance_id": self.runtime_process_identity,
            },
            "main_executable": {
                "serial": "SCUS-94254",
                "guest_base": source["guest_base"],
                "canonical_length": source["length"],
                "source_identity": {
                    "algorithm": source["algorithm"],
                    "scope": source["scope"],
                    "sha256": source["sha256"],
                },
            },
            "frame": self.frame,
        }
        self.client = FakeClient(self)

    def negotiate(self) -> None:
        self.client.request_count += 2

    def _token(self) -> str:
        if self.scenario == "token_reuse" and self.phase == "reentry":
            return "1" * 64
        return ("1" if self.phase == "initial" else "2") * 64

    def _signals(self) -> dict[str, Any]:
        if self.phase in {"initial", "reentry"}:
            return {
                "active_scene_name": "town01",
                "active_scene_prot_base": 3,
                "master_game_mode": 3,
            }
        signal = self.scenario
        return {
            "active_scene_name": "map01" if signal != "prot" and signal != "mode" and signal != "head" else "town01",
            "active_scene_prot_base": 4 if signal == "prot" else 3,
            "master_game_mode": 2 if signal == "mode" else 3,
        }

    def _head(self) -> str:
        if self.phase == "initial":
            return "0x80090000"
        if self.phase == "reentry" and self.scenario == "head_reuse":
            return "0x80090000"
        return "0x80090100"

    def _witnesses(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item["id"], "pc": item["pc"], "status": "current",
                "backend": item["backend"],
                "range": {"kind": "executed-instruction", "base": item["pc"], "length": 4},
                "live_sha256": item["live_sha256"], "observation_current": True,
            }
            for item in self.profile.document["execution_identity"]["required_witnesses"]
        ]

    def sample_boundary(self) -> dict[str, Any]:
        self.client.request_count += 2
        self.frame += 1
        if self.scenario == "initial_unstable" and self.phase == "initial":
            raise ProfileRejected("synthetic initial scene mismatch")
        witnesses = self._witnesses()
        return {
            "runtime_process_identity": self.runtime_process_identity,
            "frame": self.frame,
            "scene_signals": self._signals(),
            "actor_list_head": self._head(),
            "actor_list_head_raw": int(self._head(), 16),
            "actor_census_base": "0x801C93C8",
            "field_execution_identity": "field",
            "witness_structural_identities": [
                {key: witness[key] for key in ("pc", "backend", "range", "live_sha256")}
                for witness in witnesses
            ],
            "witness_results": witnesses,
            "observation_guard_token": self._token(),
        }

    def sample_guard_only(self, expected_token: str) -> dict[str, Any]:
        self.client.request_count += 1
        self.frame += 1
        if self.scenario == "unstable_reentry" and self.phase == "reentry":
            raise TransitionTimeout("synthetic unstable re-entry")
        if expected_token != self._token():
            raise AssertionError("unexpected token")
        return {"guard_token": self._token(), "frame_before": self.frame, "frame_after": self.frame}

    def sample_scene_signals_unscoped(self) -> dict[str, Any]:
        self.client.request_count += 1
        self.frame += 1
        return {
            "frame_before": self.frame,
            "frame_after": self.frame,
            "stable_frame": self.scenario != "outside_unstable",
            "stable_executable_state": self.scenario != "outside_unstable",
            "scene_signals": self._signals(),
            "actor_list_head": self._head(),
            "decode_errors": {},
        }

    def sample_guard_diagnostic(self, expected_token: str) -> dict[str, Any]:
        self.client.request_count += 1
        self.frame += 1
        if self.scenario in {"global_only", "frame_only"}:
            return {
                "compatible": True, "stable": True, "valid": True,
                "expected_token_matched": True, "token_before": expected_token,
                "token_after": expected_token, "frame_after": self.frame,
                "runtime_instance_matches": True, "execution_witnesses": [],
            }
        if self.scenario == "temporary_unstable":
            return {
                "compatible": False, "stable": False, "valid": True,
                "expected_token_matched": False, "token_before": "2" * 64,
                "token_after": "3" * 64, "frame_after": self.frame,
                "runtime_instance_matches": True, "execution_witnesses": [],
            }
        witnesses = []
        if self.scenario == "witness_stale":
            witnesses = [{"pc": "0x801CF754", "status": "stale", "current": False}]
        return {
            "compatible": False, "stable": True, "valid": not witnesses,
            "expected_token_matched": False, "token_before": "2" * 64,
            "token_after": "2" * 64, "frame_after": self.frame,
            "runtime_instance_matches": True, "execution_witnesses": witnesses,
            "failure_reason": "required execution witness is stale" if witnesses else "none",
        }


class FakeNavigator:
    mode = "manual"

    def __init__(self, selector: FakeSelector, *, reenter: bool = True, fail: bool = False) -> None:
        self.selector = selector
        self.reenter = reenter
        self.fail = fail
        self.cleaned = False

    def begin(self, phase: str) -> None:
        if self.fail:
            raise RuntimeError("navigation failed")
        if phase == "exit":
            self.selector.phase = "outside"
        elif phase == "reentry" and self.reenter:
            self.selector.phase = "reentry"

    def cleanup(self) -> None:
        self.cleaned = True


class TransitionObserverTests(unittest.TestCase):
    def run_transition(
        self, scenario: str = "normal", *, reenter: bool = True
    ) -> tuple[dict[str, Any], FakeSelector, FakeNavigator]:
        loaded = profile()
        selector = FakeSelector(loaded, scenario)
        navigator = FakeNavigator(selector, reenter=reenter)
        clock = FakeClock()
        limits = TransitionLimits(
            poll_interval_seconds=0.1, initial_timeout_seconds=1,
            exit_timeout_seconds=1, outside_timeout_seconds=1,
            reentry_timeout_seconds=1, stabilization_timeout_seconds=1,
        )
        result = SceneTransitionWatcher(
            selector, loaded, limits=limits, navigator=navigator,
            announce=lambda _: None, sleep=clock.sleep, clock=clock,
        ).run()
        return result, selector, navigator

    def test_01_initial_epoch_established(self):
        result, _, _ = self.run_transition(); self.assertIn("epoch_id", result["initial_epoch"]["epoch"])

    def test_02_scene_name_exit(self):
        result, _, _ = self.run_transition(); self.assertIn("active_scene_name_changed", result["exit_invalidation"]["reasons"])

    def test_03_prot_exit(self):
        result, _, _ = self.run_transition("prot"); self.assertIn("active_scene_prot_base_changed", result["exit_invalidation"]["reasons"])

    def test_04_mode_exit(self):
        result, _, _ = self.run_transition("mode"); self.assertIn("master_game_mode_changed", result["exit_invalidation"]["reasons"])

    def test_05_head_change_is_relevant(self):
        result, _, _ = self.run_transition("head"); self.assertIn("actor_list_head_changed", result["exit_invalidation"]["reasons"])

    def test_06_stale_witness_exit(self):
        result, _, _ = self.run_transition("witness_stale"); self.assertTrue(any("stale" in item for item in result["exit_invalidation"]["reasons"]))

    def test_07_global_only_not_exit(self):
        with self.assertRaises(TransitionTimeout): self.run_transition("global_only")

    def test_08_frame_only_not_exit(self):
        with self.assertRaises(TransitionTimeout): self.run_transition("frame_only")

    def test_09_unstable_sample_not_outside(self):
        with self.assertRaises(TransitionTimeout): self.run_transition("temporary_unstable")

    def test_09b_unstable_unscoped_sample_not_outside(self):
        with self.assertRaises(TransitionTimeout): self.run_transition("outside_unstable")

    def test_10_old_token_rejected(self):
        result, _, _ = self.run_transition(); self.assertTrue(result["exit_invalidation"]["old_expected_token_rejected"])

    def test_11_stable_outside_sample(self):
        result, _, _ = self.run_transition(); self.assertIsNotNone(result["stable_outside_state"])

    def test_12_reentry_recognized(self):
        result, _, _ = self.run_transition(); self.assertEqual(result["reentry_epoch"]["scene_signals"]["active_scene_name"], "town01")

    def test_13_reentry_witnesses_validated(self):
        result, _, _ = self.run_transition(); self.assertEqual(len(result["reentry_epoch"]["witnesses"]), 3)

    def test_14_reentry_head_may_differ(self):
        result, _, _ = self.run_transition(); self.assertFalse(result["reentry_epoch"]["actor_head_reused"])

    def test_15_reentry_head_may_reuse(self):
        result, _, _ = self.run_transition("head_reuse"); self.assertTrue(result["reentry_epoch"]["actor_head_reused"])

    def test_16_two_sample_epoch(self):
        result, _, _ = self.run_transition(); self.assertGreaterEqual(result["reentry_epoch"]["stable_sample_count"], 12)

    def test_17_new_token_differs(self):
        result, _, _ = self.run_transition(); self.assertNotEqual(result["initial_epoch"]["token"], result["reentry_epoch"]["token"])

    def test_17b_reentry_may_restore_same_scoped_state(self):
        result, _, _ = self.run_transition("token_reuse")
        self.assertEqual(result["initial_epoch"]["token"], result["reentry_epoch"]["token"])
        self.assertFalse(result["reentry_epoch"]["token_differs_from_initial"])
        self.assertTrue(result["reentry_epoch"]["token_reuse_is_state_equivalence"])
        self.assertNotEqual(
            result["initial_epoch"]["epoch"]["epoch_id"],
            result["reentry_epoch"]["epoch"]["epoch_id"],
        )

    def test_18_ten_reentry_samples(self):
        result, _, _ = self.run_transition(); self.assertGreaterEqual(result["reentry_epoch"]["stable_sample_count"], 13)

    def test_19_final_guard_verification(self):
        result, _, _ = self.run_transition(); self.assertGreater(result["reentry_epoch"]["last_frame"], result["reentry_epoch"]["first_frame"])

    def test_20_runtime_restart_invalidates_token(self):
        loaded = profile()
        selectors = [FakeSelector(loaded, process_tag=tag) for tag in ("a", "b")]
        reports = []
        for selector in selectors:
            navigator = FakeNavigator(selector)
            clock = FakeClock()
            reports.append(SceneTransitionWatcher(
                selector, loaded, navigator=navigator, announce=lambda _: None,
                sleep=clock.sleep, clock=clock,
            ).run())
        self.assertNotEqual(
            reports[0]["runtime_identity_summary"]["process_instance_id"],
            reports[1]["runtime_identity_summary"]["process_instance_id"],
        )
        self.assertNotEqual(
            reports[0]["initial_epoch"]["epoch"]["epoch_id"],
            reports[1]["initial_epoch"]["epoch"]["epoch_id"],
        )

    def test_21_same_process_reentry(self):
        result, _, _ = self.run_transition(); self.assertEqual(result["initial_epoch"]["epoch"]["runtime_process_identity"], result["reentry_epoch"]["epoch"]["runtime_process_identity"])

    def test_22_second_launch_identity_is_process_local(self):
        loaded = profile()
        first = FakeSelector(loaded, process_tag="a")
        second = FakeSelector(loaded, process_tag="b")
        self.assertNotEqual(first.runtime_process_identity, second.runtime_process_identity)

    def test_23_transition_timeout(self):
        with self.assertRaises(TransitionTimeout): self.run_transition("global_only")

    def test_23b_initial_establishment_timeout(self):
        with self.assertRaisesRegex(TransitionTimeout, "initial town01 epoch"):
            self.run_transition("initial_unstable")

    def test_24_reentry_timeout(self):
        with self.assertRaises(TransitionTimeout): self.run_transition(reenter=False)

    def test_25_navigation_cleanup_after_timeout(self):
        loaded = profile(); selector = FakeSelector(loaded, "global_only"); nav = FakeNavigator(selector); clock = FakeClock()
        watcher = SceneTransitionWatcher(selector, loaded, limits=TransitionLimits(exit_timeout_seconds=.1), navigator=nav, announce=lambda _: None, sleep=clock.sleep, clock=clock)
        with self.assertRaises(TransitionTimeout): watcher.run()
        self.assertTrue(nav.cleaned)

    def test_26_manual_navigation_mode(self):
        result, _, _ = self.run_transition(); self.assertEqual(result["navigation_mode"], "manual")

    def test_27_automated_navigation_failure_cleanup(self):
        loaded = profile(); selector = FakeSelector(loaded); nav = FakeNavigator(selector, fail=True); clock = FakeClock()
        watcher = SceneTransitionWatcher(selector, loaded, navigator=nav, announce=lambda _: None, sleep=clock.sleep, clock=clock)
        with self.assertRaises(RuntimeError): watcher.run()
        self.assertTrue(nav.cleaned)

    def test_28_no_actor_reads(self):
        result, selector, _ = self.run_transition(); self.assertEqual((selector.node_reads, result["metrics"]["actor_node_requests"]), (0, 0))

    def test_29_no_write_commands(self):
        result, selector, _ = self.run_transition(); self.assertEqual((selector.write_commands, result["metrics"]["ram_writes"]), (0, 0))

    def test_30_no_actor_array(self):
        result, _, _ = self.run_transition(); self.assertNotIn("actor_chain", json.dumps(result))

    def test_31_metadata_only_report(self):
        result, _, _ = self.run_transition(); self.assertTrue(result["privacy"]["metadata_only"])

    def test_32_no_absolute_paths(self):
        result, _, _ = self.run_transition(); self.assertNotIn("C:\\", json.dumps(result))

    def test_33_state_machine_completed(self):
        result, _, _ = self.run_transition(); self.assertEqual(result["state_transitions"][-1]["state"], TransitionState.COMPLETED.value)


if __name__ == "__main__":
    unittest.main()
