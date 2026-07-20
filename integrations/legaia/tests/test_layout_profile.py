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
    return profile()


def context(value: dict | None = None) -> dict:
    value = value or runnable_profile()
    overlay = value["overlay_requirements"][0]["identity"]
    return {
        "executable_identity": copy.deepcopy(value["executable_identity"]),
        "runtime_source_identity": copy.deepcopy(value["executable_identity"]["runtime_source_identity"]),
        "runtime_protocol": {
            "name": "psxrecomp-debug",
            "major": 1,
            "minor": value["supported_runtime_protocol"]["minimum_minor"],
            "capabilities": copy.deepcopy(value["supported_runtime_protocol"]["required_capabilities"]),
        },
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
        "execution_witnesses": [
            {
                "pc": witness["pc"],
                "status": "current",
                "backend": witness["backend"],
                "range": copy.deepcopy(witness["range"]),
                "live_sha256": witness["live_sha256"],
                "observation_current": True,
                "watched_generation_at_observation": f"generation-{index}",
                "watched_generation_current": f"generation-{index}",
            }
            for index, witness in enumerate(value["execution_identity"]["required_witnesses"])
        ],
        "observation_boundary": {
            "stable_executable_state": True,
            "stable_lifecycle_state": True,
            "stable_observation_guard": True,
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
        observed["runtime_source_identity"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(LayoutProfileError, "executable source identity"):
            validate_observation_context(value, observed)

    def test_05_overlay_mismatch_rejected(self) -> None:
        value = runnable_profile()
        value["overlay_requirements"][0]["required"] = True
        value["overlay_requirements"][0]["identity"]["content_sha256"] = "2" * 64
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
            "field_execution_identity": "witness-set-a",
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
        value["overlay_requirements"][0]["required"] = True
        with self.assertRaisesRegex(LayoutProfileError, "unresolved in profile"):
            validate_observation_context(value, context(value))

    def test_20_required_protocol_capability_fails_closed(self) -> None:
        value = runnable_profile()
        observed = context(value)
        observed["runtime_protocol"]["capabilities"].remove("executable_regions")
        with self.assertRaisesRegex(LayoutProfileError, "capabilities are missing"):
            validate_observation_context(value, observed)

    def test_21_protocol_major_mismatch_fails_closed(self) -> None:
        value = runnable_profile()
        observed = context(value)
        observed["runtime_protocol"]["major"] = 2
        with self.assertRaisesRegex(LayoutProfileError, "major is incompatible"):
            validate_observation_context(value, observed)

    def test_22_required_witness_capability(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["runtime_protocol"]["capabilities"].remove("execution_witness")
        with self.assertRaisesRegex(LayoutProfileError, "capabilities are missing"):
            validate_observation_context(value, observed)

    def test_23_missing_witness(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"].pop()
        with self.assertRaisesRegex(LayoutProfileError, "is missing"):
            validate_observation_context(value, observed)

    def test_24_stale_witness(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["status"] = "stale"
        observed["execution_witnesses"][0]["observation_current"] = False
        with self.assertRaisesRegex(LayoutProfileError, "is stale"):
            validate_observation_context(value, observed)

    def test_25_wrong_backend(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["backend"] = "static-native"
        with self.assertRaisesRegex(LayoutProfileError, "backend mismatch"):
            validate_observation_context(value, observed)

    def test_26_wrong_block_base(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["range"]["base"] = "0x801CF758"
        with self.assertRaisesRegex(LayoutProfileError, "range base mismatch"):
            validate_observation_context(value, observed)

    def test_27_wrong_block_length(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["range"]["length"] = 8
        with self.assertRaisesRegex(LayoutProfileError, "range length mismatch"):
            validate_observation_context(value, observed)

    def test_28_wrong_live_hash(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["live_sha256"] = "0" * 64
        with self.assertRaisesRegex(LayoutProfileError, "live identity mismatch"):
            validate_observation_context(value, observed)

    def test_29_changed_watched_generation(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["watched_generation_current"] = "changed"
        with self.assertRaisesRegex(LayoutProfileError, "watched generation changed"):
            validate_observation_context(value, observed)

    def test_30_global_executable_state_is_diagnostic(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["observation_boundary"]["stable_executable_state"] = False
        validate_observation_context(value, observed)

    def test_31_global_lifecycle_state_is_diagnostic(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["observation_boundary"]["stable_lifecycle_state"] = False
        validate_observation_context(value, observed)

    def test_31b_mixed_observation_guard_rejected(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["observation_boundary"]["stable_observation_guard"] = False
        with self.assertRaisesRegex(LayoutProfileError, "scoped observation guard"):
            validate_observation_context(value, observed)

    def test_32_ambiguous_execution_owner(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][0]["backend"] = "ambiguous"
        observed["execution_witnesses"][0]["status"] = "ambiguous"
        with self.assertRaisesRegex(LayoutProfileError, "ambiguous execution owner"):
            validate_observation_context(value, observed)

    def test_33_multiple_required_witnesses(self) -> None:
        value = runnable_profile(); observed = context(value)
        self.assertEqual(validate_observation_context(value, observed)["actor_count"], 7)
        self.assertEqual(len(value["execution_identity"]["required_witnesses"]), 3)

    def test_34_one_witness_matches_another_fails(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["execution_witnesses"][1]["live_sha256"] = "1" * 64
        with self.assertRaisesRegex(LayoutProfileError, "live identity mismatch"):
            validate_observation_context(value, observed)

    def test_35_witness_profile_serialization_determinism(self) -> None:
        self.assertEqual(canonical_profile_json(profile()), canonical_profile_json(profile()))

    def test_36_protocol_minor_compatibility(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["runtime_protocol"]["minor"] = 6
        self.assertEqual(validate_observation_context(value, observed)["actor_count"], 7)

    def test_37_protocol_minor_too_old(self) -> None:
        value = runnable_profile(); observed = context(value)
        observed["runtime_protocol"]["minor"] = 4
        with self.assertRaisesRegex(LayoutProfileError, "minor is too old"):
            validate_observation_context(value, observed)

    def test_38_no_proprietary_code_bytes(self) -> None:
        serialized = canonical_profile_json(profile())
        self.assertNotIn('"bytes"', serialized)
        self.assertNotIn('"payload"', serialized)

    def test_39_metadata_only_witness_identities(self) -> None:
        for witness in profile()["execution_identity"]["required_witnesses"]:
            self.assertRegex(witness["live_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(witness["range"]["length"], 4)

    def test_40_witness_requirements_are_optional_for_legacy_schema_shape_but_fail_selection(self) -> None:
        value = profile(); del value["execution_identity"]
        with self.assertRaisesRegex(LayoutProfileError, "execution_identity is required"):
            validate_profile(value)

    def test_41_previous_unresolved_overlay_still_fails_when_required(self) -> None:
        value = profile(); value["overlay_requirements"][0]["required"] = True
        with self.assertRaisesRegex(LayoutProfileError, "unresolved in profile"):
            validate_observation_context(value, context(value))


if __name__ == "__main__":
    unittest.main()
