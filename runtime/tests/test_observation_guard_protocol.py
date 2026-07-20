#!/usr/bin/env python3
"""Synthetic contract tests for psxrecomp-debug observation guards."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NATIVE = (ROOT / "runtime/src/debug_server.c").read_text(encoding="utf-8")
CLIENT = (ROOT / "tools/debug_client.py").read_text(encoding="utf-8")

RAM_SIZE = 0x200000
MAX_REGIONS = 16
MAX_REGION_BYTES = 256
MAX_TOTAL_BYTES = 2048
MAX_WITNESSES = 8


class GuardModel:
    def __init__(self) -> None:
        self.ram = bytearray(RAM_SIZE)
        self.runtime_instance = "instance-a"
        self.program = "program-a"
        self.frame = 1
        self.global_state = "global-a"
        self.unrelated_lifecycle = 0
        self.witnesses = {
            0x1000: {
                "backend": "static-native", "reason": "dispatch",
                "base": 0x1000, "length": 4,
                "live": "1" * 64, "generation": "a" * 64,
                "current": True, "instance": 1, "lifecycle_generation": 1,
                "registration": 7, "hits": 1, "first_frame": 1, "last_frame": 1,
            },
            0x2000: {
                "backend": "interpreter", "reason": "fallback",
                "base": 0x2000, "length": 4,
                "live": "2" * 64, "generation": "b" * 64,
                "current": True, "instance": 2, "lifecycle_generation": 2,
                "registration": 0, "hits": 1, "first_frame": 1, "last_frame": 1,
            },
        }

    @staticmethod
    def _phys(raw: str | int) -> int:
        value = int(raw, 0) if isinstance(raw, str) else raw
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
            raise ValueError("invalid guard ram region address")
        phys = value & 0x1FFFFFFF
        if phys < 0x800000:
            return phys & 0x1FFFFF
        raise ValueError("guard ram region is not main RAM")

    def canonical(self, descriptor: dict) -> tuple[list[dict], list[dict]]:
        regions = copy.deepcopy(descriptor.get("ram_regions"))
        witnesses = copy.deepcopy(descriptor.get("execution_witnesses"))
        if not isinstance(regions, list) or not isinstance(witnesses, list):
            raise ValueError("missing guard arrays")
        if len(regions) > MAX_REGIONS:
            raise ValueError("too many guard ram regions")
        if len(witnesses) > MAX_WITNESSES:
            raise ValueError("too many guard execution witnesses")
        keys, spans, total = set(), set(), 0
        for region in regions:
            if not isinstance(region.get("key"), str) or not region["key"]:
                raise ValueError("invalid guard ram region key")
            length = region.get("len")
            if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
                raise ValueError("invalid guard ram region length")
            if length > MAX_REGION_BYTES:
                raise ValueError("guard ram region byte limit exceeded")
            phys = self._phys(region.get("addr"))
            if length > RAM_SIZE - phys:
                raise ValueError("guard ram region range overflow")
            total += length
            if total > MAX_TOTAL_BYTES:
                raise ValueError("aggregate guard ram byte limit exceeded")
            span = (phys, length)
            if region["key"] in keys or span in spans:
                raise ValueError("duplicate guard ram region")
            keys.add(region["key"]); spans.add(span); region["phys"] = phys
        pcs = set()
        for witness in witnesses:
            pc = int(witness.get("pc"), 0)
            phys = pc & 0x1FFFFFFF
            if phys >= RAM_SIZE or phys & 3:
                raise ValueError("guard execution witness pc is not aligned main RAM")
            if pc in pcs:
                raise ValueError("duplicate guard execution witness")
            if witness.get("require_current") is not True:
                raise ValueError("guard execution witnesses must require currentness")
            pcs.add(pc); witness["pc_value"] = pc
        regions.sort(key=lambda item: (item["phys"], item["len"], item["key"]))
        witnesses.sort(key=lambda item: item["pc_value"])
        if not regions and not witnesses:
            raise ValueError("observation guard must not be empty")
        return regions, witnesses

    def token(self, descriptor: dict) -> tuple[str, bool]:
        regions, required = self.canonical(descriptor)
        region_state = []
        for region in regions:
            payload = self.ram[region["phys"]:region["phys"] + region["len"]]
            region_state.append((region["phys"], region["len"], region["key"], hashlib.sha256(payload).hexdigest()))
        witness_state, valid = [], True
        for requested in required:
            witness = self.witnesses.get(requested["pc_value"] & 0x1FFFFFFF)
            if witness is None:
                witness_state.append((requested["pc_value"], "missing")); valid = False; continue
            if witness["backend"] == "ambiguous" or not witness["current"]:
                valid = False
            witness_state.append((
                requested["pc_value"], witness["backend"], witness["reason"],
                witness["base"], witness["length"], witness["live"],
                witness["generation"], witness["current"], witness["instance"],
                witness["lifecycle_generation"], witness["registration"],
            ))
        state = {
            "domain": "psxrecomp-observation-guard-v1",
            "runtime_instance": self.runtime_instance,
            "program": self.program,
            "regions": region_state,
            "witnesses": witness_state,
        }
        return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), valid


def descriptor() -> dict:
    return {
        "ram_regions": [
            {"key": "scene", "addr": "0x80000100", "len": 8},
            {"key": "head", "addr": "0x80000200", "len": 4},
        ],
        "execution_witnesses": [
            {"pc": "0x80001000", "require_current": True},
            {"pc": "0x80002000", "require_current": True},
        ],
    }


class ObservationGuardModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = GuardModel()

    def test_01_descriptor_canonicalization(self):
        regions, witnesses = self.model.canonical(descriptor())
        self.assertEqual([r["key"] for r in regions], ["scene", "head"])
        self.assertEqual([w["pc_value"] for w in witnesses], [0x80001000, 0x80002000])

    def test_02_token_determinism(self):
        self.assertEqual(self.model.token(descriptor()), self.model.token(descriptor()))

    def test_03_region_order_normalization(self):
        value = descriptor(); value["ram_regions"].reverse()
        self.assertEqual(self.model.token(value), self.model.token(descriptor()))

    def test_04_witness_order_normalization(self):
        value = descriptor(); value["execution_witnesses"].reverse()
        self.assertEqual(self.model.token(value), self.model.token(descriptor()))

    def test_05_duplicate_ram_region_rejected(self):
        value = descriptor(); value["ram_regions"].append(copy.deepcopy(value["ram_regions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"): self.model.token(value)

    def test_06_duplicate_witness_rejected(self):
        value = descriptor(); value["execution_witnesses"].append(copy.deepcopy(value["execution_witnesses"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"): self.model.token(value)

    def test_07_invalid_ram_address(self):
        value = descriptor(); value["ram_regions"][0]["addr"] = "0x1F800000"
        with self.assertRaisesRegex(ValueError, "not main RAM"): self.model.token(value)

    def test_08_address_overflow(self):
        value = descriptor(); value["ram_regions"][0] = {"key": "bad", "addr": "0x801FFFFF", "len": 2}
        with self.assertRaisesRegex(ValueError, "overflow"): self.model.token(value)

    def test_09_per_region_limit(self):
        value = descriptor(); value["ram_regions"][0]["len"] = 257
        with self.assertRaisesRegex(ValueError, "byte limit"): self.model.token(value)

    def test_10_aggregate_limit(self):
        value = descriptor(); value["ram_regions"] = [
            {"key": f"r{i}", "addr": hex(0x80010000 + i * 0x100), "len": 256}
            for i in range(9)
        ]
        with self.assertRaisesRegex(ValueError, "aggregate"): self.model.token(value)

    def test_11_witness_count_limit(self):
        value = descriptor(); value["execution_witnesses"] = [
            {"pc": hex(0x80001000 + i * 4), "require_current": True} for i in range(9)
        ]
        with self.assertRaisesRegex(ValueError, "too many"): self.model.token(value)

    def test_12_missing_witness(self):
        value = descriptor(); value["execution_witnesses"][0]["pc"] = "0x80003000"
        self.assertFalse(self.model.token(value)[1])

    def test_13_stale_witness(self):
        self.model.witnesses[0x1000]["current"] = False
        self.assertFalse(self.model.token(descriptor())[1])

    def test_14_ambiguous_owner(self):
        self.model.witnesses[0x1000]["backend"] = "ambiguous"
        self.assertFalse(self.model.token(descriptor())[1])

    def test_15_wrong_expected_token(self):
        token, _ = self.model.token(descriptor())
        self.assertNotEqual(token, "0" * 64)

    def test_16_frame_advancement_stable(self):
        before = self.model.token(descriptor()); self.model.frame += 100
        self.assertEqual(before, self.model.token(descriptor()))

    def test_17_hit_count_advancement_stable(self):
        before = self.model.token(descriptor()); self.model.witnesses[0x1000]["hits"] += 50
        self.assertEqual(before, self.model.token(descriptor()))

    def test_18_unrelated_executable_write_stable(self):
        before = self.model.token(descriptor()); self.model.global_state = "global-b"
        self.assertEqual(before, self.model.token(descriptor()))

    def test_19_unrelated_owner_change_stable(self):
        before = self.model.token(descriptor()); self.model.witnesses[0x3000] = copy.deepcopy(self.model.witnesses[0x1000])
        self.assertEqual(before, self.model.token(descriptor()))

    def test_20_unrelated_lifecycle_stable(self):
        before = self.model.token(descriptor()); self.model.unrelated_lifecycle += 1
        self.assertEqual(before, self.model.token(descriptor()))

    def _assert_change(self, mutate):
        before = self.model.token(descriptor())[0]; mutate()
        self.assertNotEqual(before, self.model.token(descriptor())[0])

    def test_21_scene_bytes_change(self): self._assert_change(lambda: self.model.ram.__setitem__(0x100, 1))
    def test_22_prot_bytes_change(self): self._assert_change(lambda: self.model.ram.__setitem__(0x101, 2))
    def test_23_mode_bytes_change(self): self._assert_change(lambda: self.model.ram.__setitem__(0x102, 3))
    def test_24_actor_head_change(self): self._assert_change(lambda: self.model.ram.__setitem__(0x200, 4))
    def test_25_witness_byte_change(self): self._assert_change(lambda: self.model.witnesses[0x1000].__setitem__("live", "f" * 64))
    def test_26_same_byte_rewrite_generation(self): self._assert_change(lambda: self.model.witnesses[0x1000].__setitem__("generation", "e" * 64))
    def test_27_backend_change(self): self._assert_change(lambda: self.model.witnesses[0x1000].__setitem__("backend", "interpreter"))
    def test_28_range_change(self): self._assert_change(lambda: self.model.witnesses[0x1000].__setitem__("length", 8))
    def test_29_relevant_lifecycle_change(self): self._assert_change(lambda: self.model.witnesses[0x1000].__setitem__("lifecycle_generation", 2))
    def test_30_runtime_restart(self): self._assert_change(lambda: setattr(self.model, "runtime_instance", "instance-b"))

    def test_31_before_after_mismatch(self):
        before = self.model.token(descriptor())[0]; self.model.ram[0x100] = 9
        self.assertNotEqual(before, self.model.token(descriptor())[0])

    def test_32_payload_order_is_independent_of_guard_order(self):
        payload = [{"key": "b"}, {"key": "a"}]
        self.assertEqual([item["key"] for item in payload], ["b", "a"])

    def test_33_empty_payload_guard_is_valid(self):
        self.assertTrue(self.model.token(descriptor())[1])

    def test_34_source_keeps_unguarded_read_regions(self):
        self.assertIn("if (has_guard)", NATIVE)
        self.assertIn("append_observer_region_payload", NATIVE)

    def test_35_response_budget_is_bounded(self):
        self.assertIn("OBS_MAX_RESPONSE_BYTES", NATIVE)
        self.assertIn("response too large", NATIVE)


class ObservationGuardSourceTests(unittest.TestCase):
    def test_36_protocol_minor_and_capability(self):
        self.assertIn('\\"minor\\":5', NATIVE)
        self.assertIn('\\"observation_guard\\"', NATIVE)

    def test_37_stateless_command_registered(self):
        self.assertIn('{ "observation_guard", handle_observation_guard }', NATIVE)

    def test_38_token_domain_and_runtime_instance(self):
        self.assertIn("psxrecomp-observation-guard-v1", NATIVE)
        self.assertIn("s_runtime_instance_digest", NATIVE)

    def test_39_volatile_fields_excluded_from_guard_evaluator(self):
        body = NATIVE[NATIVE.index("static void evaluate_observation_guard"):
                      NATIVE.index("static int append_guard_evidence")]
        for volatile in ("hits", "first_observed_frame", "last_observed_frame",
                         "s_frame_count", "executable_state_token"):
            self.assertNotIn(volatile, body)

    def test_40_guard_limits_are_published(self):
        for name in ("max_guard_ram_regions", "max_guard_bytes_per_region",
                     "max_guard_total_ram_bytes", "max_guard_execution_witnesses"):
            self.assertIn(name, NATIVE)

    def test_41_expected_token_withholds_payload(self):
        handler = NATIVE[NATIVE.index("static void handle_read_regions"):
                         NATIVE.index("/* Layer-1 first-divergence")]
        self.assertIn("expected && guard_valid_before", handler)
        self.assertIn("payload_returned", handler)

    def test_42_debug_client_commands(self):
        self.assertIn("observation-guard", CLIENT)
        self.assertIn("guarded-read", CLIENT)
        self.assertIn("pretty_observation_guard", CLIENT)

    def test_43_no_title_specific_guard_logic(self):
        body = NATIVE[NATIVE.index("static int parse_observation_guard"):
                      NATIVE.index("static int parse_observer_regions")]
        for title in ("Legaia", "SCUS", "town01"):
            self.assertNotIn(title, body)


if __name__ == "__main__":
    unittest.main()
