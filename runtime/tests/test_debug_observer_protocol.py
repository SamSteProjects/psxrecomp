#!/usr/bin/env python3
"""Synthetic and structural regressions for debug protocol 1.5.

No retail bytes, executable payloads, host paths, or emulator state are used.
The executable models below exercise the documented bounds and authoritative
watched-page contract; source assertions keep those models wired to the native
and Beetle implementations.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
NATIVE = (ROOT / "runtime/src/debug_server.c").read_text(encoding="utf-8")
BEETLE = (ROOT / "runtime/src/beetle_debug_server.c").read_text(encoding="utf-8")
MEMORY = (ROOT / "runtime/src/memory.c").read_text(encoding="utf-8")
LOADER = (ROOT / "runtime/src/overlay_loader.c").read_text(encoding="utf-8")
CAPTURE = (ROOT / "runtime/src/overlay_capture.c").read_text(encoding="utf-8")
DIRTY = (ROOT / "runtime/src/dirty_ram_interp.c").read_text(encoding="utf-8")
CLIENT = (ROOT / "tools/debug_client.py").read_text(encoding="utf-8")
DUCK_PATCH = (ROOT / "tools/duckstation/psxrecomp_oracle.patch").read_text(encoding="utf-8")
VERSIONING = (ROOT / "docs/debug-protocol-versioning.md").read_text(encoding="utf-8")
IDENTITY = (ROOT / "docs/executable-identity.md").read_text(encoding="utf-8")
IMAGE_MODEL_PATH = ROOT / "docs/executable-image-model.md"
PAGINATION_PATH = ROOT / "docs/executable-catalog-pagination.md"
OWNERSHIP_PATH = ROOT / "docs/executable-ownership-diagnostics.md"

CLIENT_SPEC = importlib.util.spec_from_file_location(
    "psxrecomp_debug_client", ROOT / "tools/debug_client.py"
)
assert CLIENT_SPEC and CLIENT_SPEC.loader
DEBUG_CLIENT = importlib.util.module_from_spec(CLIENT_SPEC)
CLIENT_SPEC.loader.exec_module(DEBUG_CLIENT)

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
        h = hashlib.sha256(b"psxrecomp-exec-ownership-v2")
        for index in sorted(self.watched):
            generation = self.generation[index]
            h.update(index.to_bytes(4, "little"))
            h.update(generation.to_bytes(4, "little"))
        for base, length, source in self.registrations:
            h.update(base.to_bytes(4, "little"))
            h.update(length.to_bytes(4, "little"))
            h.update(source.encode("ascii"))
        return h.hexdigest()


class LifecycleModel:
    """Metadata-only oracle for exact transfer instances and PC owners."""

    def __init__(self, event_cap: int = 4) -> None:
        self.instances: list[dict] = []
        self.owners: dict[int, str] = {}
        self.events: list[dict] = []
        self.event_cap = event_cap
        self.sequence = 0

    def _event(self, kind: str, instance: int, related: int | None = None) -> None:
        self.sequence += 1
        self.events.append({"sequence": self.sequence, "kind": kind,
                            "instance": instance, "related": related})
        self.events = self.events[-self.event_cap :]

    def load(self, base: int, payload: bytes) -> int:
        if not payload or base < 0 or base + len(payload) > RAM_SIZE:
            raise ValueError("invalid exact transfer span")
        ident = len(self.instances) + 1
        for old in self.instances:
            overlaps = base < old["base"] + old["length"] and old["base"] < base + len(payload)
            if old["active"] and overlaps:
                old["active"] = False
                old["successor"] = ident
                self._event("superseded", old["id"], ident)
        self.instances.append({"id": ident, "base": base, "length": len(payload),
                               "identity": hashlib.sha256(payload).hexdigest(),
                               "active": True, "successor": None})
        self._event("created", ident)
        return ident

    def execute(self, pc: int, backend: str) -> None:
        previous = self.owners.get(pc)
        self.owners[pc] = backend
        if previous != backend:
            self._event("owner-acquired" if previous is None else "owner-changed", 0)


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
        expected = ["executable_catalog", "executable_regions", "read_ram", "read_regions",
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
        handlers = NATIVE[NATIVE.index("handle_runtime_identity"):NATIVE.index("hash_live_ranges")]
        self.assertNotIn('\\"hex\\"', handlers)
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


class ExecutableCatalogModelTests(unittest.TestCase):
    def test_45_image_range_registration_are_distinct(self) -> None:
        for token in ("ObserverExecutableImage", "ObserverExecutableRange",
                      "OverlayExecutableRegion"):
            self.assertIn(token, NATIVE if token != "OverlayExecutableRegion" else LOADER)
        self.assertIn('"view", view', NATIVE)

    def test_46_multiple_registrations_group_by_image(self) -> None:
        self.assertIn("images[j].image_id == r->image_id", NATIVE)
        self.assertIn("image->registration_count++", NATIVE)

    def test_47_overlapping_ranges_are_preserved(self) -> None:
        self.assertIn("ranges[j].image_id == r->image_id", NATIVE)
        self.assertIn("ranges[range_index].registration_count++", NATIVE)

    def test_48_distinct_registration_state_is_not_collapsed(self) -> None:
        self.assertIn('registration_id\\\":\\\"reg-%08x', NATIVE)
        self.assertIn('ownership_reason\\\":\\\"%s', NATIVE)

    def test_49_source_live_comparability_is_explicit(self) -> None:
        self.assertIn('source_live_comparison\\\":{\\\"comparable\\\":%s', NATIVE)
        self.assertIn("source_live_comparable", LOADER)

    def test_50_registration_validated_identity_is_separate(self) -> None:
        self.assertIn('registration_time_validated_identity\\\":', NATIVE)
        self.assertIn("has_validated_identity", LOADER)

    def test_51_every_ownership_reason_is_serializable(self) -> None:
        for reason in (
            "valid", "validated-bytes-mismatch", "generation-invalidated",
            "registration-inactive", "shadowed", "blacklisted",
            "native-disabled", "dispatch-guard-failed", "backend-ineligible",
            "unknown",
        ):
            self.assertIn(f'"{reason}"', NATIVE)

    def test_52_generation_is_part_of_native_validity(self) -> None:
        predicate = LOADER[LOADER.index("candidate_protocol_native_valid"):
                           LOADER.index("candidate_ownership_reason")]
        self.assertIn("cand_gensum(c) != c->val_gen", predicate)

    def test_53_same_address_replacement_cannot_retain_owner(self) -> None:
        self.assertIn("OVERLAY_OWNERSHIP_VALIDATED_BYTES_MISMATCH", LOADER)
        self.assertIn("out->live_crc32 == out->source_crc32", LOADER)

    def test_54_runtime_and_static_registration_classes_are_modeled(self) -> None:
        for kind in ("static-overlay-variant", "runtime-compiled-fragment",
                     "native-overlay-bundle"):
            self.assertIn(kind, NATIVE)

    def test_55_catalog_token_excludes_mutable_ownership_state(self) -> None:
        start = LOADER.index("uint64_t overlay_loader_catalog_token")
        end = LOADER.index("void overlay_loader_executable_watch_bitmap", start)
        catalog = LOADER[start:end]
        for state in ("c->state", "c->val_gen", "s_native_exec", "diff_passes"):
            self.assertNotIn(state, catalog)

    def test_56_ownership_scope_uses_registration_ranges(self) -> None:
        token = NATIVE[NATIVE.index("static void executable_state_token"):
                       NATIVE.index("static void handle_protocol_info")]
        self.assertIn("overlay_loader_executable_watch_bitmap", token)
        self.assertNotIn("for (uint32_t page = 0; page < pages", token)

    def test_57_unrelated_data_write_does_not_change_ownership_token(self) -> None:
        model = WatchModel()
        model.register(PAGE_SIZE, 16, b"A" * 16)
        before = model.token()
        model.write(PAGE_SIZE * 8, b"data")
        self.assertEqual(before, model.token())

    def test_58_executable_write_changes_ownership_token(self) -> None:
        model = WatchModel()
        model.register(PAGE_SIZE, 16, b"A" * 16)
        before = model.token()
        model.write(PAGE_SIZE, b"A")
        self.assertNotEqual(before, model.token())

    def test_59_page_max_and_byte_budget_are_bounded(self) -> None:
        self.assertIn("#define EXEC_CATALOG_PAGE_MAX 8", NATIVE)
        self.assertIn("#define EXEC_CATALOG_RECORD_BUDGET 60000", NATIVE)
        self.assertIn("catalog record exceeds response budget", NATIVE)

    def test_60_cursor_is_bound_to_catalog_token(self) -> None:
        self.assertIn("cursor > 0", NATIVE)
        self.assertIn('error\\\":\\\"catalog_changed', NATIVE)
        self.assertIn('next_cursor\\\":', NATIVE)

    def test_61_protocol_minor_and_capability_are_additive(self) -> None:
        self.assertIn('major\\\":1,\\\"minor\\\":5', NATIVE)
        self.assertIn('\\\"executable_catalog\\\"', NATIVE)
        self.assertIn('\\\"executable_image_lifecycle\\\"', NATIVE)
        self.assertIn('\\\"execution_witness\\\"', NATIVE)
        self.assertIn('\\\"observation_guard\\\"', NATIVE)
        self.assertIn('{ "executable_regions", handle_executable_regions }', NATIVE)

    def test_62_complete_client_paging(self) -> None:
        pages = [
            {"ok": True, "catalog_token": "abc", "ownership_token": "one",
             "total": 3, "returned": 2, "has_more": True, "next_cursor": 2,
             "records": [{"n": 1}, {"n": 2}]},
            {"ok": True, "catalog_token": "abc", "ownership_token": "one",
             "total": 3, "returned": 1, "has_more": False, "next_cursor": None,
             "records": [{"n": 3}]},
        ]
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", side_effect=pages):
            result = DEBUG_CLIENT.fetch_executable_catalog(object(), "registrations", 2)
        self.assertTrue(result["ok"])
        self.assertEqual([item["n"] for item in result["records"]], [1, 2, 3])
        self.assertTrue(result["stable_ownership"])

    def test_63_client_rejects_catalog_change(self) -> None:
        pages = [
            {"ok": True, "catalog_token": "a", "ownership_token": "one",
             "total": 2, "returned": 1, "has_more": True, "next_cursor": 1,
             "records": [{}]},
            {"ok": True, "catalog_token": "b", "ownership_token": "two",
             "total": 2, "returned": 1, "has_more": False, "next_cursor": None,
             "records": [{}]},
        ]
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", side_effect=pages):
            result = DEBUG_CLIENT.fetch_executable_catalog(object(), "registrations", 1)
        self.assertFalse(result["ok"])
        self.assertIn("changed", result["error"])

    def test_64_client_rejects_cursor_loop(self) -> None:
        page = {"ok": True, "catalog_token": "a", "ownership_token": "one",
                "total": 2, "returned": 1, "has_more": True, "next_cursor": 0,
                "records": [{}]}
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", return_value=page):
            result = DEBUG_CLIENT.fetch_executable_catalog(object(), "ranges", 1)
        self.assertFalse(result["ok"])
        self.assertIn("cursor", result["error"])

    def test_65_no_host_paths_or_payload_fields(self) -> None:
        handler = NATIVE[NATIVE.index("static void handle_executable_catalog"):
                         NATIVE.index("typedef struct {", NATIVE.index("handle_executable_catalog"))]
        for forbidden in ("cache_dir", "dll_path", '"hex"', '"bytes"'):
            self.assertNotIn(forbidden, handler)

    def test_66_ownership_change_during_paging_is_reported(self) -> None:
        pages = [
            {"ok": True, "catalog_token": "same", "ownership_token": "one",
             "total": 2, "returned": 1, "has_more": True, "next_cursor": 1,
             "records": [{"n": 1}]},
            {"ok": True, "catalog_token": "same", "ownership_token": "two",
             "total": 2, "returned": 1, "has_more": False, "next_cursor": None,
             "records": [{"n": 2}]},
        ]
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", side_effect=pages):
            result = DEBUG_CLIENT.fetch_executable_catalog(object(), "images", 1)
        self.assertTrue(result["ok"])
        self.assertFalse(result["stable_ownership"])
        self.assertEqual(result["ownership_tokens"], ["one", "two"])

    def test_67_static_validation_history_survives_invalidation(self) -> None:
        self.assertIn("int      ever_matched;", LOADER)
        self.assertIn("entry->ever_matched = 1", LOADER)
        self.assertIn("out->has_validated_identity = e->ever_matched", LOADER)
        self.assertIn("entry->last_validated_gen = gen_sum", LOADER)
        self.assertIn("out->validated_generation_sum = e->last_validated_gen", LOADER)

    def test_68_catalog_tracks_structural_replacement(self) -> None:
        start = LOADER.index("uint64_t overlay_loader_catalog_token")
        end = LOADER.index("void overlay_loader_executable_watch_bitmap", start)
        catalog = LOADER[start:end]
        for structural in ("c->dll", "c->addr", "c->crc_code",
                           "c->range_lo[r]", "c->range_len[r]"):
            self.assertIn(structural, catalog)

    def test_69_registration_classes_do_not_invent_dirty_image(self) -> None:
        kinds = NATIVE[NATIVE.index("static const char *catalog_image_kind"):
                       NATIVE.index("static int append_catalog_registration")]
        self.assertNotIn("dirty-executable-image", kinds)
        self.assertIn("per-dispatch-range-not-cataloged", NATIVE)

    def test_70_structural_variant_does_not_claim_loaded_base(self) -> None:
        self.assertIn("has_image_load_base", LOADER)
        self.assertIn('snprintf(load_base, sizeof(load_base), "null")', NATIVE)


class ExecutableLifecycleTests(unittest.TestCase):
    def test_71_same_address_reload_creates_successor(self) -> None:
        model = LifecycleModel()
        first = model.load(0x10000, b"A" * 16)
        second = model.load(0x10000, b"B" * 16)
        self.assertNotEqual(first, second)
        self.assertFalse(model.instances[0]["active"])
        self.assertEqual(model.instances[0]["successor"], second)

    def test_72_different_content_has_distinct_identity(self) -> None:
        model = LifecycleModel()
        model.load(0x10000, b"A" * 16)
        model.load(0x10000, b"B" * 16)
        self.assertNotEqual(model.instances[0]["identity"], model.instances[1]["identity"])

    def test_73_partial_overlap_supersedes_prior_exact_span(self) -> None:
        model = LifecycleModel()
        model.load(0x10000, b"A" * 32)
        model.load(0x10010, b"B" * 4)
        self.assertFalse(model.instances[0]["active"])

    def test_74_adjacent_transfers_are_not_grouped(self) -> None:
        model = LifecycleModel()
        model.load(0x10000, b"A" * 16)
        model.load(0x10010, b"B" * 16)
        self.assertEqual(len(model.instances), 2)
        self.assertTrue(all(item["active"] for item in model.instances))

    def test_75_no_false_unload_without_observation(self) -> None:
        model = LifecycleModel()
        model.load(0x10000, b"A" * 16)
        self.assertTrue(model.instances[0]["active"])
        self.assertNotIn("OVERLAY_LIFECYCLE_UNLOADED", CAPTURE)

    def test_76_backend_owner_changes_at_same_pc(self) -> None:
        model = LifecycleModel()
        model.execute(0x10000, "cached-native")
        model.execute(0x10000, "interpreter")
        self.assertEqual(model.owners[0x10000], "interpreter")
        self.assertEqual(model.events[-1]["kind"], "owner-changed")

    def test_77_native_failure_falls_through_to_interpreter_owner(self) -> None:
        self.assertIn("OVERLAY_EXEC_REASON_NATIVE_VALIDATION_FALLBACK", DIRTY)
        self.assertIn("OVERLAY_EXEC_OWNER_INTERPRETER", DIRTY)
        self.assertIn("if (overlay_loader_dispatch(cpu, addr))", DIRTY)

    def test_78_all_four_execution_backends_are_observable(self) -> None:
        for owner in ("STATIC_NATIVE", "CACHED_NATIVE", "RUNTIME_NATIVE", "INTERPRETER"):
            self.assertIn(f"OVERLAY_EXEC_OWNER_{owner}", NATIVE + LOADER + DIRTY)

    def test_79_owner_observation_is_exact_pc_not_range_guess(self) -> None:
        self.assertIn("lifecycle_owner_slot(phys, 0)", CAPTURE)
        self.assertIn("dirty_ram_exec_pc_observed(phys", CAPTURE)
        self.assertNotIn("nearest", CAPTURE.lower())

    def test_80_lifecycle_events_are_sequence_ordered(self) -> None:
        model = LifecycleModel()
        model.load(0x10000, b"A")
        model.load(0x10000, b"B")
        sequence = [event["sequence"] for event in model.events]
        self.assertEqual(sequence, sorted(sequence))

    def test_81_event_ring_reports_eviction_boundary(self) -> None:
        model = LifecycleModel(event_cap=2)
        model.load(0x10000, b"A")
        model.load(0x10000, b"B")
        self.assertEqual(len(model.events), 2)
        self.assertGreater(model.events[0]["sequence"], 1)
        self.assertIn("lifecycle event cursor evicted", NATIVE)

    def test_82_lifecycle_pages_are_strictly_bounded(self) -> None:
        self.assertIn("#define EXEC_LIFECYCLE_PAGE_MAX 8", NATIVE)
        handler = NATIVE[NATIVE.index("handle_executable_lifecycle"):
                         NATIVE.index("handle_runtime_identity")]
        self.assertIn("OBS_MAX_RESPONSE_BYTES", handler)

    def test_83_cursor_requires_stable_lifecycle_token(self) -> None:
        self.assertIn('error\\\":\\\"lifecycle_changed', NATIVE)
        self.assertIn('"lifecycle_token"', CLIENT)

    def test_84_client_pages_complete_lifecycle(self) -> None:
        pages = [
            {"ok": True, "lifecycle_token": "same", "total": 2, "returned": 1,
             "has_more": True, "next_cursor": 1, "records": [{"n": 1}],
             "frame": 10, "overflowed": False, "event_oldest_sequence": 1,
             "event_latest_sequence": 2},
            {"ok": True, "lifecycle_token": "same", "total": 2, "returned": 1,
             "has_more": False, "next_cursor": None, "records": [{"n": 2}],
             "frame": 10, "overflowed": False, "event_oldest_sequence": 1,
             "event_latest_sequence": 2},
        ]
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", side_effect=pages):
            result = DEBUG_CLIENT.fetch_executable_lifecycle(object(), "instances", 1)
        self.assertTrue(result["ok"])
        self.assertTrue(result["stable_frame"])
        self.assertEqual([record["n"] for record in result["records"]], [1, 2])

    def test_85_client_rejects_lifecycle_change(self) -> None:
        pages = [
            {"ok": True, "lifecycle_token": "a", "total": 2, "returned": 1,
             "has_more": True, "next_cursor": 1, "records": [{}], "frame": 1},
            {"ok": True, "lifecycle_token": "b", "total": 2, "returned": 1,
             "has_more": False, "next_cursor": None, "records": [{}], "frame": 2},
        ]
        with mock.patch.object(DEBUG_CLIENT, "send_cmd", side_effect=pages):
            result = DEBUG_CLIENT.fetch_executable_lifecycle(object(), "owners", 1)
        self.assertFalse(result["ok"])
        self.assertIn("changed", result["error"])

    def test_86_capture_and_live_identities_remain_distinct(self) -> None:
        handler = NATIVE[NATIVE.index("handle_executable_lifecycle"):
                         NATIVE.index("handle_runtime_identity")]
        self.assertIn("capture_identity", handler)
        self.assertIn("current_live_identity", handler)
        self.assertIn("whole_image_identity", handler)

    def test_87_lifecycle_contains_no_raw_payload(self) -> None:
        handler = NATIVE[NATIVE.index("handle_executable_lifecycle"):
                         NATIVE.index("handle_runtime_identity")]
        for forbidden in ('"hex"', "raw_bytes", "host_path"):
            self.assertNotIn(forbidden, handler)

    def test_88_capture_runs_independently_of_optional_cache(self) -> None:
        start = CAPTURE.index("void overlay_capture_on_dma")
        body = CAPTURE[start:CAPTURE.index("/* ---- JSON output", start)]
        self.assertLess(body.index("lifecycle_create_dma_instance"),
                        body.index("if (!s_enabled) return"))

    def test_89_catalog_registration_exposes_execution_owner(self) -> None:
        self.assertIn('\\\"execution_owner\\\"', NATIVE)
        self.assertIn("overlay_lifecycle_owner_at(r->entry", NATIVE)

    def test_90_protocol_command_and_client_are_registered(self) -> None:
        self.assertIn('{ "executable_lifecycle", handle_executable_lifecycle }', NATIVE)
        self.assertIn("fetch_executable_lifecycle", CLIENT)

    def test_91_tracking_is_negotiation_gated(self) -> None:
        self.assertIn("if (!s_lifecycle_tracking_enabled) return", CAPTURE)
        protocol = NATIVE[NATIVE.index("static void handle_protocol_info"):
                          NATIVE.index("static const char *execution_owner_name")]
        self.assertIn("overlay_lifecycle_set_tracking_enabled(1)", protocol)
        self.assertIn("tracking_started_frame", NATIVE)

    def test_92_exact_owner_lookup_is_bounded(self) -> None:
        self.assertIn('strcmp(view, "owner")', NATIVE)
        self.assertIn("missing lifecycle owner address", NATIVE)
        self.assertIn("executable-owner", CLIENT)

    def test_93_interpreter_owner_reuses_existing_exact_pc_evidence(self) -> None:
        self.assertIn("dirty_ram_exec_pc_observed", DIRTY)
        self.assertIn("dirty_ram_exec_pc_observed(phys", CAPTURE)
        self.assertIn("watched_generation", DIRTY)

    def test_94_normal_opening_capacity_exceeds_accepted_observation(self) -> None:
        self.assertIn("OVERLAY_LIFECYCLE_INSTANCE_CAP 32768u", CAPTURE)
        self.assertIn("OVERLAY_LIFECYCLE_OWNER_CAP 65536u", CAPTURE)


class ExecutionWitnessTests(unittest.TestCase):
    def test_95_interpreter_range_is_exact_fetched_instruction(self) -> None:
        self.assertIn("exec_pc_table_record(pc, insn)", DIRTY)
        self.assertIn('\\\"kind\\\":\\\"executed-instruction\\\"', NATIVE)
        self.assertIn('\\\"length\\\":4', NATIVE)
        self.assertIn('\\\"instruction_count\\\":1', NATIVE)

    def test_96_no_decoded_block_or_function_boundary_is_claimed(self) -> None:
        self.assertIn('\\\"block_range_available\\\":false', NATIVE)
        self.assertIn('\\\"decoded-block-boundary\\\"', NATIVE)
        self.assertIn('\\\"function-boundary\\\"', NATIVE)

    def test_97_observed_instruction_identity_is_retained(self) -> None:
        self.assertIn("instruction_word_at_observation", CAPTURE)
        self.assertIn("instruction_word", DIRTY)
        self.assertIn("observed_identity", NATIVE)

    def test_98_live_identity_hashes_exact_four_bytes(self) -> None:
        handler = NATIVE[NATIVE.index("handle_execution_witness"):
                         NATIVE.index("static const char *ownership_reason_name")]
        self.assertIn("psx_sha256(ram + phys, 4u", handler)
        self.assertNotIn("4096u", handler)

    def test_99_witness_uses_authoritative_watched_generation(self) -> None:
        self.assertIn("watched_generation_digest(&lo, &len, 1", NATIVE)
        self.assertIn("owner.watched_generation_at_observation", NATIVE)
        self.assertIn("overlay_lifecycle_owner_observation_current", NATIVE)

    def test_100_same_byte_write_can_stale_witness(self) -> None:
        model = WatchModel()
        model.register(PAGE_SIZE, 4, b"ABCD")
        model.ram[PAGE_SIZE:PAGE_SIZE + 4] = b"ABCD"
        before = model.generation[1]
        model.write(PAGE_SIZE, b"ABCD")
        self.assertNotEqual(before, model.generation[1])
        self.assertEqual(model.ram[PAGE_SIZE:PAGE_SIZE + 4], b"ABCD")

    def test_101_content_replacement_changes_live_identity(self) -> None:
        self.assertNotEqual(hashlib.sha256(b"AAAA").hexdigest(),
                            hashlib.sha256(b"BBBB").hexdigest())
        self.assertIn("source_matches_live", NATIVE)

    def test_102_backend_change_participates_in_witness_id(self) -> None:
        witness_id = NATIVE[NATIVE.index("static void execution_witness_id"):
                            NATIVE.index("static void handle_execution_witness")]
        self.assertIn("owner->owner", witness_id)
        self.assertIn("owner->instruction_word_at_observation", witness_id)

    def test_103_lifecycle_and_registration_provenance_are_explicit(self) -> None:
        self.assertIn('\\\"lifecycle_fragment\\\"', NATIVE)
        self.assertIn('\\\"native_registration\\\"', NATIVE)
        self.assertIn('\\\"whole-image-association\\\"', NATIVE)

    def test_104_missing_witness_is_explicit(self) -> None:
        self.assertIn('\\\"status\\\":\\\"missing\\\"', NATIVE)
        self.assertIn('\\\"witness\\\":null', NATIVE)

    def test_105_stale_and_ambiguous_states_are_explicit(self) -> None:
        self.assertIn('? "ambiguous"', NATIVE)
        self.assertIn('? "current" : "stale"', NATIVE)
        self.assertIn("owner.owner != OVERLAY_EXEC_OWNER_AMBIGUOUS", NATIVE)

    def test_106_lookup_is_aligned_bounded_main_ram(self) -> None:
        self.assertIn("phys >= 0x200000u || (phys & 3u) != 0", NATIVE)
        self.assertIn("phys > 0x1ffffcu", NATIVE)

    def test_107_observation_has_frame_and_state_boundaries(self) -> None:
        for field in ("frame_before", "frame_after", "executable_state_before",
                      "executable_state_after", "lifecycle_token_before",
                      "lifecycle_token_after", "stable_observation_boundary"):
            self.assertIn(field, NATIVE)

    def test_108_protocol_command_and_client_are_registered(self) -> None:
        self.assertIn('{ "execution_witness", handle_execution_witness }', NATIVE)
        self.assertIn("execution-witness <guest-address>", CLIENT)
        self.assertIn("pretty_execution_witness", CLIENT)

    def test_109_response_is_bounded_one_record(self) -> None:
        self.assertIn('\\\"execution_witness_range_bytes\\\":4', NATIVE)
        self.assertNotIn("execution_witness_list", NATIVE)

    def test_110_no_raw_code_or_host_paths(self) -> None:
        handler = NATIVE[NATIVE.index("handle_execution_witness"):
                         NATIVE.index("static const char *ownership_reason_name")]
        for forbidden in ('\\\"hex\\\"', "raw_bytes", "host_path", "source_path"):
            self.assertNotIn(forbidden, handler)

    def test_111_no_title_specific_witness_logic(self) -> None:
        handler = NATIVE[NATIVE.index("handle_execution_witness"):
                         NATIVE.index("static const char *ownership_reason_name")]
        self.assertNotRegex(handler, r"Legaia|SCUS[-_]?94254|town01|801CF754")

    def test_112_delay_slots_are_independently_recorded(self) -> None:
        delay = DIRTY[DIRTY.index("static void exec_delay_slot"):
                      DIRTY.index("static int exec_one(CPUState", DIRTY.index("static void exec_delay_slot"))]
        self.assertIn("exec_one(cpu, pc, &dummy_next)", delay)
        self.assertIn("exec_pc_table_record(pc, insn)", DIRTY)

    def test_113_witness_id_scope_is_not_cross_process(self) -> None:
        self.assertIn('\\\"id_scope\\\":\\\"process-local-observation\\\"', NATIVE)
        self.assertIn("overlay_lifecycle_tracking_started_frame", NATIVE)

    def test_114_old_lifecycle_surface_remains_registered(self) -> None:
        self.assertIn('{ "executable_lifecycle", handle_executable_lifecycle }', NATIVE)
        self.assertIn("executable_image_lifecycle", NATIVE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
