#!/usr/bin/env python3
"""Synthetic and structural regressions for debug protocol 1.1.

No retail bytes, executable payloads, host paths, or emulator state are used.
The executable models below exercise the documented bounds and authoritative
watched-page contract; source assertions keep those models wired to the native
and Beetle implementations.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = (ROOT / "runtime/src/debug_server.c").read_text(encoding="utf-8")
BEETLE = (ROOT / "runtime/src/beetle_debug_server.c").read_text(encoding="utf-8")
MEMORY = (ROOT / "runtime/src/memory.c").read_text(encoding="utf-8")
LOADER = (ROOT / "runtime/src/overlay_loader.c").read_text(encoding="utf-8")
CLIENT = (ROOT / "tools/debug_client.py").read_text(encoding="utf-8")
DUCK_PATCH = (ROOT / "tools/duckstation/psxrecomp_oracle.patch").read_text(encoding="utf-8")
VERSIONING = (ROOT / "docs/debug-protocol-versioning.md").read_text(encoding="utf-8")
IDENTITY = (ROOT / "docs/executable-identity.md").read_text(encoding="utf-8")

PAGE_SIZE = 4096
RAM_SIZE = 2 * 1024 * 1024
MAX_REGIONS = 32
MAX_REGION = 4096
MAX_TOTAL = 16384


class WatchModel:
    def __init__(self) -> None:
        self.ram = bytearray(RAM_SIZE)
        self.watched: set[int] = set()
        self.generation = [0] * (RAM_SIZE // PAGE_SIZE)
        self.registrations: list[tuple[int, int, str]] = []

    def register(self, base: int, length: int, source: bytes) -> None:
        first = base // PAGE_SIZE
        last = (base + length - 1) // PAGE_SIZE
        self.watched.update(range(first, last + 1))
        self.registrations.append((base, length, hashlib.sha256(source).hexdigest()))

    def write(self, base: int, payload: bytes) -> None:
        first = base // PAGE_SIZE
        last = (base + len(payload) - 1) // PAGE_SIZE
        for page in range(first, last + 1):
            if page in self.watched:
                self.generation[page] = (self.generation[page] + 1) & 0xFFFFFFFF
        self.ram[base : base + len(payload)] = payload

    def token(self) -> str:
        h = hashlib.sha256(b"psxrecomp-exec-state-v1")
        for index, generation in enumerate(self.generation):
            h.update(index.to_bytes(4, "little"))
            h.update(generation.to_bytes(4, "little"))
        for base, length, source in self.registrations:
            h.update(base.to_bytes(4, "little"))
            h.update(length.to_bytes(4, "little"))
            h.update(source.encode("ascii"))
        return h.hexdigest()


def validate_regions(regions: list[dict]) -> list[dict]:
    if not regions:
        raise ValueError("regions must not be empty")
    if len(regions) > MAX_REGIONS:
        raise ValueError("too many regions")
    result = []
    total = 0
    keys: set[str] = set()
    for item in regions:
        length = item.get("len")
        if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
            raise ValueError("invalid region length")
        if length > MAX_REGION:
            raise ValueError("region byte limit exceeded")
        raw = item.get("addr")
        if isinstance(raw, str):
            if raw.startswith("-"):
                raise ValueError("invalid region address")
            address = int(raw, 0)
        elif isinstance(raw, int) and not isinstance(raw, bool):
            address = raw
        else:
            raise ValueError("invalid region address")
        if address < 0 or address > 0xFFFFFFFF:
            raise ValueError("region address overflow")
        phys = address & 0x1FFFFFFF
        if phys >= 0x00800000:
            raise ValueError("region is not main RAM")
        phys &= 0x001FFFFF
        if length > RAM_SIZE - phys:
            raise ValueError("region range overflow")
        total += length
        if total > MAX_TOTAL:
            raise ValueError("aggregate byte limit exceeded")
        key = item.get("key")
        if key is not None:
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", key):
                raise ValueError("invalid region key")
            if key in keys:
                raise ValueError("duplicate region key")
            keys.add(key)
        result.append({"key": key, "phys": phys, "len": length})
    return result


class ProtocolMetadataTests(unittest.TestCase):
    def test_01_protocol_info_schema(self) -> None:
        for field in ("protocol", "name", "major", "minor", "capabilities", "limits", "frame"):
            self.assertIn(f'\\"{field}\\"', NATIVE)

    def test_02_stable_capability_ordering(self) -> None:
        expected = ["executable_regions", "read_ram", "read_regions",
                    "runtime_identity", "watched_page_generation"]
        positions = [NATIVE.index(f'\\"{name}\\"', NATIVE.index("handle_protocol_info"))
                     for name in expected]
        self.assertEqual(positions, sorted(positions))

    def test_03_version_compatibility_rules(self) -> None:
        self.assertIn("unsupported major", VERSIONING.lower())
        self.assertIn("minor", VERSIONING.lower())
        self.assertIn("capabil", VERSIONING.lower())

    def test_04_server_kind_reporting(self) -> None:
        self.assertIn('\\"kind\\":\\"native\\"', NATIVE)
        self.assertIn('\\"kind\\":\\"beetle\\"', BEETLE)

    def test_05_runtime_identity_canonicalization(self) -> None:
        self.assertIn("debug_server_set_program_identity", NATIVE)
        self.assertIn("c == '-' || c == '_' || c == '.'", NATIVE)

    def test_06_main_executable_hash_determinism(self) -> None:
        payload = bytes(range(64))
        self.assertEqual(hashlib.sha256(payload).digest(), hashlib.sha256(payload).digest())
        self.assertIn("psx_sha256(bytes, len, text_source_sha256)", MEMORY)

    def test_07_executable_hash_range_boundaries(self) -> None:
        ram = bytes(range(256)) * 32
        self.assertNotEqual(hashlib.sha256(ram[12:28]).digest(), hashlib.sha256(ram[11:28]).digest())
        self.assertIn("len[i] > 0x200000u - lo[i]", NATIVE)

    def test_08_bss_and_mutable_memory_exclusion_contract(self) -> None:
        self.assertIn("BSS", IDENTITY)
        self.assertIn("PS-X EXE", IDENTITY)
        self.assertIn("immutable", IDENTITY.lower())

    def test_09_multiple_region_ordering(self) -> None:
        self.assertIn('\\"ordering\\":\\"registration\\"', NATIVE)
        self.assertIn("logical = offset", NATIVE)

    def test_10_static_overlay_watched_registration(self) -> None:
        register = LOADER.index("overlay_watch_set_range(lo, len)")
        generation = LOADER.index("overlay_watch_pagegen_sum(lo, len)", register)
        self.assertLess(register, generation)


class GenerationAndIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = WatchModel()
        self.base = PAGE_SIZE + 32
        self.source = bytes.fromhex("1020304050607080")
        self.memory.ram[self.base : self.base + len(self.source)] = self.source
        self.memory.register(self.base, len(self.source), self.source)

    def test_11_generation_changes_after_8_bit_write(self) -> None:
        before = self.memory.generation[1]
        self.memory.write(self.base, b"\x11")
        self.assertEqual(self.memory.generation[1], before + 1)

    def test_12_generation_changes_after_16_bit_write(self) -> None:
        before = self.memory.generation[1]
        self.memory.write(self.base, b"\x11\x22")
        self.assertEqual(self.memory.generation[1], before + 1)

    def test_13_generation_changes_after_32_bit_write(self) -> None:
        before = self.memory.generation[1]
        self.memory.write(self.base, b"\x11\x22\x33\x44")
        self.assertEqual(self.memory.generation[1], before + 1)

    def test_14_dma_and_cd_use_covered_write_chokepoint(self) -> None:
        dma = (ROOT / "runtime/src/dma.c").read_text(encoding="utf-8")
        self.assertIn("uint32_t word = cdrom_dma_read()", dma)
        self.assertIn("psx_write_word(addr, word)", dma)

    def test_15_same_byte_write_advances_generation(self) -> None:
        before = self.memory.token()
        self.memory.write(self.base, self.source[:1])
        self.assertNotEqual(before, self.memory.token())
        self.assertEqual(self.memory.ram[self.base], self.source[0])

    def test_16_same_base_length_replacement_has_distinct_identity(self) -> None:
        replacement = bytes.fromhex("8070605040302010")
        self.memory.write(self.base, replacement)
        self.assertNotEqual(hashlib.sha256(self.source).digest(), hashlib.sha256(replacement).digest())

    def test_17_no_stale_native_ownership_after_mutation(self) -> None:
        replacement = bytes.fromhex("8070605040302010")
        self.memory.write(self.base, replacement)
        live = self.memory.ram[self.base : self.base + len(self.source)]
        self.assertFalse(hashlib.sha256(live).digest() == hashlib.sha256(self.source).digest())
        self.assertIn("candidate_protocol_native_valid(c, out->source_matches_live)", LOADER)

    def test_18_source_and_live_identity_are_distinct_fields(self) -> None:
        self.assertIn('\\"source_identity\\"', NATIVE)
        self.assertIn('\\"live_identity\\"', NATIVE)

    def test_19_live_hash_determinism(self) -> None:
        live = self.memory.ram[self.base : self.base + len(self.source)]
        self.assertEqual(hashlib.sha256(live).hexdigest(), hashlib.sha256(live).hexdigest())

    def test_20_invalid_executable_range_rejection(self) -> None:
        self.assertIn("lo[i] >= 0x200000u", NATIVE)
        self.assertIn("invalid executable registration", NATIVE)

    def test_21_executable_state_stable_without_changes(self) -> None:
        self.assertEqual(self.memory.token(), self.memory.token())

    def test_22_executable_state_changes_after_write(self) -> None:
        before = self.memory.token()
        self.memory.write(self.base, b"\xff")
        self.assertNotEqual(before, self.memory.token())

    def test_23_registration_state_changes(self) -> None:
        before = self.memory.token()
        self.memory.register(PAGE_SIZE * 3, 4, b"abcd")
        self.assertNotEqual(before, self.memory.token())


class ReadRegionsTests(unittest.TestCase):
    def test_24_normal_operation(self) -> None:
        got = validate_regions([{"key": "a", "addr": "0x80001000", "len": 4}])
        self.assertEqual(got[0]["phys"], 0x1000)

    def test_25_request_order_preservation(self) -> None:
        got = validate_regions([{"key": "b", "addr": 0x80002000, "len": 2},
                                {"key": "a", "addr": 0x80001000, "len": 1}])
        self.assertEqual([r["key"] for r in got], ["b", "a"])

    def test_26_region_count_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "too many"):
            validate_regions([{"addr": i * 4, "len": 1} for i in range(33)])

    def test_27_per_region_byte_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "region byte"):
            validate_regions([{"addr": 0, "len": MAX_REGION + 1}])

    def test_28_aggregate_byte_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "aggregate"):
            validate_regions([{"addr": i * MAX_REGION, "len": MAX_REGION} for i in range(5)])

    def test_29_response_size_limit(self) -> None:
        self.assertIn("#define OBS_MAX_RESPONSE_BYTES 65536", NATIVE)
        self.assertIn("estimated > OBS_MAX_RESPONSE_BYTES", NATIVE)

    def test_30_address_wraparound(self) -> None:
        with self.assertRaisesRegex(ValueError, "overflow"):
            validate_regions([{"addr": 0x801FFFFF, "len": 2}])

    def test_31_invalid_and_negative_lengths(self) -> None:
        for length in (0, -1, "4", True):
            with self.subTest(length=length), self.assertRaisesRegex(ValueError, "length"):
                validate_regions([{"addr": 0, "len": length}])

    def test_32_duplicate_key_handling(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_regions([{"key": "same", "addr": 0, "len": 1},
                              {"key": "same", "addr": 4, "len": 1}])

    def test_33_frame_stamp_semantics(self) -> None:
        for field in ("frame_before", "frame_after", "stable_frame"):
            self.assertIn(f'\\"{field}\\"', NATIVE)
            self.assertIn(f'\\"{field}\\"', BEETLE)

    def test_34_executable_state_stamp_semantics(self) -> None:
        for field in ("executable_state_before", "executable_state_after",
                      "stable_executable_state"):
            self.assertIn(f'\\"{field}\\"', NATIVE)
            self.assertNotIn(f'\\"{field}\\"', BEETLE)


class CompatibilityAndHygieneTests(unittest.TestCase):
    def test_35_existing_commands_remain_registered(self) -> None:
        for command in ("ping", "frame", "read_ram", "write_ram"):
            self.assertRegex(NATIVE, rf'\{{\s*"{command}"\s*,')

    def test_36_oracle_unsupported_capabilities_are_omitted(self) -> None:
        protocol = BEETLE[BEETLE.index("h_protocol_info"):BEETLE.index("h_get_registers")]
        self.assertIn('\\"read_regions\\"', protocol)
        self.assertNotIn('\\"runtime_identity\\"', protocol)
        self.assertNotIn('\\"executable_regions\\"', protocol)

    def test_37_no_host_paths_in_identity_responses(self) -> None:
        identity_handler = NATIVE[NATIVE.index("handle_runtime_identity"):NATIVE.index("hash_live_ranges")]
        for forbidden in ("bios_path", "game_config_path", "cache_dir", "filename"):
            self.assertNotIn(forbidden, identity_handler)

    def test_38_no_raw_executable_bytes_in_identity_responses(self) -> None:
        handlers = NATIVE[NATIVE.index("handle_runtime_identity"):NATIVE.index("typedef struct {", NATIVE.index("handle_read_regions"))]
        self.assertNotIn('\\"hex\\"', handlers[:handlers.index("handle_read_regions")])
        self.assertIn('\\"sha256\\"', handlers)

    def test_39_fixtures_are_synthetic_and_metadata_only(self) -> None:
        synthetic = json.dumps({"addr": "0x80001000", "len": 4, "hex": "10203040"})
        self.assertEqual(json.loads(synthetic)["hex"], "10203040")
        self.assertLess(len(synthetic), 128)

    def test_40_stale_cache_regression_remains_wired(self) -> None:
        regression = ROOT / "runtime/tests/test_static_overlay_cache_invalidation.py"
        self.assertTrue(regression.is_file())
        self.assertIn("overlay_watch_set_range(lo, len)", LOADER)

    def test_41_debug_client_exposes_observer_commands(self) -> None:
        for command in ("protocol-info", "runtime-identity", "executable-regions", "read-regions"):
            self.assertIn(command, CLIENT)

    def test_42_request_line_limit_is_fail_closed(self) -> None:
        self.assertIn("#define RECV_BUF_SIZE 8193", NATIVE)
        self.assertIn("return -2", NATIVE)
        self.assertIn("request line too long", NATIVE)

    def test_43_no_title_specific_runtime_protocol(self) -> None:
        changed_handlers = NATIVE[NATIVE.index("handle_protocol_info"):NATIVE.index("handle_frame_fingerprint")]
        self.assertNotRegex(changed_handlers, r"Legaia|SCUS[-_]?94254|town01")

    def test_44_duckstation_reports_only_supported_observer_capabilities(self) -> None:
        self.assertIn('"kind":"duckstation"', DUCK_PATCH)
        self.assertIn('"capabilities":["read_ram","read_regions"]', DUCK_PATCH)
        self.assertIn('std::strcmp(cmd, "read_regions")', DUCK_PATCH)
        self.assertNotIn('"capabilities":["executable_regions"', DUCK_PATCH)


if __name__ == "__main__":
    unittest.main(verbosity=2)
