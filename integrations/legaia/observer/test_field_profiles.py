"""Versioned field execution evidence must never relax byte or epoch guards."""
from copy import deepcopy
from pathlib import Path
import unittest
from integrations.legaia.layouts import load_profile, validate_observation_context, LayoutProfileError

LAYOUTS = Path(__file__).resolve().parents[1] / "layouts"


def context(profile):
    protocol = profile["supported_runtime_protocol"]
    witnesses = []
    for item in profile["execution_identity"]["required_witnesses"]:
        witnesses.append({**deepcopy(item), "status": "current", "observation_current": True,
                          "watched_generation_at_observation": "synthetic-generation",
                          "watched_generation_current": "synthetic-generation"})
    return {"executable_identity": {"serial": "SCUS-94254"},
            "runtime_source_identity": profile["executable_identity"]["runtime_source_identity"],
            "runtime_protocol": {"name": protocol["name"], "major": 1, "minor": 5,
                                 "capabilities": protocol["required_capabilities"]},
            "observation_boundary": {"stable_observation_guard": True},
            "execution_witnesses": witnesses,
            "scene_signals": {s["id"]: s["expected"] for s in profile["scene_identity"]["required_signals"]},
            "actor_count": 0}


class FieldProfileTests(unittest.TestCase):
    def setUp(self):
        self.old = load_profile(LAYOUTS / "scus94254-na-field-v1.json")
        self.current = load_profile(LAYOUTS / "scus94254-na-field-v2.json")

    def test_revision_preserves_instruction_and_scene_identity(self):
        old = self.old["execution_identity"]["required_witnesses"]
        current = self.current["execution_identity"]["required_witnesses"]
        self.assertEqual([(w["pc"], w["range"], w["live_sha256"]) for w in old],
                         [(w["pc"], w["range"], w["live_sha256"]) for w in current])
        self.assertEqual(self.old["scene_identity"], self.current["scene_identity"])
        observed = context(self.current)
        validate_observation_context(self.current, observed)
        with self.assertRaisesRegex(LayoutProfileError, "backend mismatch"):
            validate_observation_context(self.old, observed)

    def test_new_revision_still_rejects_wrong_or_stale_evidence(self):
        for field, value in [("live_sha256", "0" * 64), ("status", "stale"),
                             ("observation_current", False), ("backend", "cached-native"),
                             ("watched_generation_current", "changed-generation")]:
            with self.subTest(field=field):
                observed = context(self.current)
                observed["execution_witnesses"][0][field] = value
                with self.assertRaises(LayoutProfileError):
                    validate_observation_context(self.current, observed)
        for field, value in [("active_scene_name", "opdeene"), ("master_game_mode", 2),
                             ("active_scene_prot_base", 748)]:
            observed = context(self.current)
            observed["scene_signals"][field] = value
            with self.assertRaises(LayoutProfileError):
                validate_observation_context(self.current, observed)


if __name__ == "__main__":
    unittest.main()
