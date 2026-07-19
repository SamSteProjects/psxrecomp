from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema

from integrations.legaia.layouts import (
    LayoutProfileError,
    canonical_profile_json,
    establish_epoch,
    load_profile,
    profile_identity,
    validate_observation_context,
    validate_profile,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "layouts" / "scus94254-na-field-v1.json"
SCHEMA_PATH = ROOT / "schemas" / "runtime-layout-profile.v1.schema.json"


def profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def runnable_profile() -> dict:
    value = profile()
    overlay = value["overlay_requirements"][0]["identity"]
    overlay["content_sha256"] = overlay["source_entry_sha256"]
    return value


def context(value: dict | None = None) -> dict:
    value = value or runnable_profile()
    overlay = value["overlay_requirements"][0]["identity"]
    return {
        "executable_identity": copy.deepcopy(value["executable_identity"]),
        "runtime_protocol": {"name": "psxrecomp-json-tcp", "version": 1},
        "overlays": [
            {
                "id": overlay["id"],
                "load_address": overlay["load_address"],
                "content_sha256": overlay["content_sha256"],
            }
        ],
        "scene_signals": {
            signal["id"]: signal["expected"]
            for signal in value["scene_identity"]["required_signals"]
        },
        "actor_count": 7,
    }


class RuntimeLayoutProfileTests(unittest.TestCase):
    def test_01_profile_schema_validation(self) -> None:
        value = validate_profile(profile())
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(value, schema)

    def test_02_stable_profile_identity(self) -> None:
        self.assertEqual(profile_identity(profile()), "legaia-na-scus94254-field-v1")
        self.assertEqual(load_profile(PROFILE_PATH)["profile_id"], profile_identity(profile()))

    def test_03_supported_executable_identity(self) -> None:
        value = runnable_profile()
        bounded = validate_observation_context(value, context(value))
        self.assertEqual(bounded["actor_count"], 7)
        self.assertEqual(bounded["actor_pointer_bytes"], 28)

    def test_04_unsupported_executable_rejected(self) -> None:
        value = runnable_profile()
        observed = context(value)
        observed["executable_identity"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(LayoutProfileError, "executable identity"):
            validate_observation_context(value, observed)

    def test_05_overlay_mismatch_rejected(self) -> None:
        value = runnable_profile()
        observed = context(value)
        observed["overlays"][0]["content_sha256"] = "1" * 64
        with self.assertRaisesRegex(LayoutProfileError, "content_sha256 mismatch"):
            validate_observation_context(value, observed)

    def test_06_missing_scene_signal_rejected(self) -> None:
        value = runnable_profile()
        observed = context(value)
        del observed["scene_signals"]["active_scene_name"]
        with self.assertRaisesRegex(LayoutProfileError, "scene signal active_scene_name is missing"):
            validate_observation_context(value, observed)

    def test_07_actor_base_bounds_validation(self) -> None:
        value = profile()
        value["actor_pool"]["pointer_census"]["base_address"] = "0x7FFFFFFC"
        with self.assertRaisesRegex(LayoutProfileError, "outside main RAM|overflows"):
            validate_profile(value)

    def test_08_actor_stride_validation(self) -> None:
        value = profile()
        value["actor_pool"]["pointer_census"]["entry_stride"] = 8
        with self.assertRaisesRegex(LayoutProfileError, "entry_stride"):
            validate_profile(value)

    def test_09_slot_count_overflow_rejected(self) -> None:
        value = runnable_profile()
        observed = context(value)
        observed["actor_count"] = 33
        with self.assertRaisesRegex(LayoutProfileError, "actor count"):
            validate_observation_context(value, observed)

    def test_10_address_wraparound_rejected(self) -> None:
        value = profile()
        value["safety_bounds"]["main_ram_end_exclusive"] = "0xFFFFFFFF"
        value["actor_pool"]["pointer_census"]["base_address"] = "0xFFFFFFF0"
        with self.assertRaisesRegex(LayoutProfileError, "overflows"):
            validate_profile(value)

    def test_11_field_offset_within_bounded_prefix(self) -> None:
        value = profile()
        value["actor_fields"][0]["offset"] = 155
        value["actor_fields"][0]["width"] = 4
        with self.assertRaisesRegex(LayoutProfileError, "outside the bounded actor prefix"):
            validate_profile(value)

    def test_12_duplicate_field_offsets_rejected(self) -> None:
        value = profile()
        value["actor_fields"][1]["offset"] = value["actor_fields"][0]["offset"]
        with self.assertRaisesRegex(LayoutProfileError, "duplicates"):
            validate_profile(value)

    def test_13_contradictory_claim_needs_alternatives(self) -> None:
        value = profile()
        claim = value["actor_fields"][0]["claim"]
        claim["confidence"] = "contradictory"
        with self.assertRaisesRegex(LayoutProfileError, "at least two alternatives"):
            validate_profile(value)

    def test_14_unknown_field_remains_representable(self) -> None:
        value = profile()
        claim = value["actor_fields"][0]["claim"]
        claim["confidence"] = "unknown"
        claim["value"] = None
        self.assertEqual(validate_profile(value)["actor_fields"][0]["claim"]["confidence"], "unknown")

    def test_15_scene_epoch_invalidation(self) -> None:
        value = profile()
        stable = {
            "active_scene_name": "town01",
            "active_scene_prot_base": 3,
            "master_game_mode": 3,
            "field-overlay-0897": "hash-a",
            "actor_list_head": "0x80083000",
            "actor_census_base": "0x801C93C8",
            "frame": 100,
        }
        changed = dict(stable, master_game_mode=2, frame=101)
        with self.assertRaisesRegex(LayoutProfileError, "mixed scene epoch"):
            establish_epoch(value, stable, changed, 1)
        token = establish_epoch(value, stable, dict(stable, frame=101), 1)
        self.assertEqual(token["observer_epoch"], 1)

    def test_16_mixed_overlay_profile_rejected(self) -> None:
        value = profile()
        value["overlay_requirements"].append(copy.deepcopy(value["overlay_requirements"][0]))
        with self.assertRaisesRegex(LayoutProfileError, "duplicates overlay identity"):
            validate_profile(value)

    def test_17_deterministic_serialization(self) -> None:
        first = canonical_profile_json(profile())
        second_value = json.loads(json.dumps(profile(), sort_keys=True))
        second = canonical_profile_json(second_value)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))

    def test_18_no_proprietary_payload_validation(self) -> None:
        value = profile()
        value["payload"] = "retail bytes would be forbidden here"
        with self.assertRaisesRegex(LayoutProfileError, "forbidden field"):
            validate_profile(value)

    def test_19_unresolved_overlay_identity_fails_closed(self) -> None:
        value = profile()
        with self.assertRaisesRegex(LayoutProfileError, "unresolved in profile"):
            validate_observation_context(value, context(runnable_profile()))


if __name__ == "__main__":
    unittest.main()
