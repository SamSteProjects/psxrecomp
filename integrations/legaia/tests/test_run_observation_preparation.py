"""Owned launches arm observation after identity verification, not as acceptance."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.run import RunService


class RunPreparationTests(unittest.TestCase):
    def run_ready(self, valid=True, prepared=True):
        service = RunService()
        process = SimpleNamespace(pid=42, poll=lambda: None)
        service._process = process
        service._status = {"debug_port": 4391, "expected_text_sha256": "text",
                           "expected_bios_sha256": "bios", "expected_disc_sha256": "disc",
                           "expected_overlay_count": 0}
        identity = {"runtime": {"implementation": "psxrecomp"},
                    "main_executable": {"source_identity": {"sha256": "text" if valid else "wrong"}},
                    "bios": {"sha256": "bios"}}
        mods = {"disc_identity": {"sha256": "disc"}, "active_overlay_count": 0,
                "active_write_count": 0, "plan_committed": True, "disc_enabled": True,
                "disc_guard_failed": False}
        client = Mock()
        client.runtime_identity.return_value = identity
        client.request.return_value = mods
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        cancel = Mock()
        cancel.wait.side_effect = [False, True]
        cancel.is_set.return_value = False
        observer = Mock()
        observer.discover.return_value = {"available": prepared,
            "state": "compatible_runtime" if prepared else "unavailable", "scene_verified": False,
            "witness_tracking": {"status": "primed", "requested_pcs": ["0x801CF754"]} if prepared else None,
            "reason": None if prepared else {"message": "unsupported observation"}}
        with patch("sdk.run._listener_pid", return_value=42), \
             patch("integrations.legaia.observer.client.ProtocolClient", return_value=client), \
             patch("integrations.legaia.observer.service.ObserverService", return_value=observer) as factory, \
             patch.object(service, "_persist"):
            service._await_ready(process, cancel)
        return service._status, factory, observer

    def test_verified_launch_primes_but_does_not_claim_scene_acceptance(self):
        result, factory, observer = self.run_ready()
        factory.assert_called_once_with(port=4391)
        observer.discover.assert_called_once_with()
        observer.close.assert_called_once_with()
        self.assertTrue(result["ready"])
        self.assertFalse(result["observation_preparation"]["scene_verified"])
        self.assertEqual(result["observation_preparation"]["witness_tracking"]["status"], "primed")

    def test_wrong_identity_never_arms_and_observer_rejection_stays_explicit(self):
        result, factory, _ = self.run_ready(valid=False)
        factory.assert_not_called()
        self.assertFalse(result["ready"])
        result, _, observer = self.run_ready(prepared=False)
        self.assertTrue(result["ready"])
        self.assertFalse(result["observation_preparation"]["available"])
        observer.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
