from __future__ import annotations

import copy
import hashlib
import json
import socket
import threading
import time
import unittest
from pathlib import Path
from typing import Any

import jsonschema

from integrations.legaia.observer import (
    ChainInvalid,
    LoadedProfile,
    ProfileRejected,
    ProtocolClient,
    ProtocolError,
    RetryExhausted,
    RuntimeObserver,
    canonical_snapshot_json,
    validate_snapshot,
)
from integrations.legaia.observer.actor_nodes import decode_fields, pointer_metadata, traverse_actor_chain
from integrations.legaia.observer.epoch import establish_scene_epoch


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "layouts" / "scus94254-na-field-v1.json"
SCHEMA_PATH = ROOT / "schemas" / "runtime-observation.v1.schema.json"
OBSERVER_TOOL = (ROOT / "tools" / "legaia_observe.py").read_text(encoding="utf-8")


def synthetic_profile() -> dict[str, Any]:
    value = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    value["executable_identity"]["sha256"] = "1" * 64
    value["executable_identity"]["claim"]["value"] = f"SCUS-94254:{'1' * 64}"
    value["executable_identity"]["runtime_source_identity"]["sha256"] = "a" * 64
    value["executable_identity"]["runtime_source_identity"]["claim"]["value"] = f"ps-x-exe-body:{'a' * 64}"
    for index, witness in enumerate(value["execution_identity"]["required_witnesses"], 2):
        witness["live_sha256"] = str(index) * 64
    return value


def make_node(next_pointer: int, *, x: int = 10) -> bytes:
    data = bytearray(156)
    data[0:4] = next_pointer.to_bytes(4, "little")
    data[12:16] = (0x80100000).to_bytes(4, "little")
    data[16:20] = (0x20000).to_bytes(4, "little")
    data[20:22] = x.to_bytes(2, "little", signed=True)
    data[22:24] = (-3).to_bytes(2, "little", signed=True)
    data[24:26] = (20).to_bytes(2, "little", signed=True)
    data[38:40] = (1024).to_bytes(2, "little")
    data[68:72] = (0x800A0000).to_bytes(4, "little")
    data[76:80] = (0x800A1000).to_bytes(4, "little")
    data[80:82] = (7).to_bytes(2, "little")
    data[96] = 4
    data[100:102] = (9).to_bytes(2, "little")
    data[144:148] = (0x800B0000).to_bytes(4, "little")
    data[148:152] = (0x800B0100).to_bytes(4, "little")
    return bytes(data)


class SyntheticServer:
    def __init__(self, profile: dict[str, Any], scenario: str = "stable") -> None:
        self.profile = profile
        self.scenario = scenario
        self.frame = 100
        self.boundary_reads = 0
        self.node_reads = 0
        self.runtime_reads = 0
        self.witness_reads = 0
        self.guard_reads = 0
        self._stop = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.sock.settimeout(0.1)
        self.host, self.port = self.sock.getsockname()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self._stop.set()
        self.sock.close()
        self.thread.join(timeout=1)

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                connection, _ = self.sock.accept()
            except (OSError, socket.timeout):
                continue
            with connection:
                data = bytearray()
                while b"\n" not in data:
                    chunk = connection.recv(65536)
                    if not chunk:
                        break
                    data.extend(chunk)
                if not data:
                    continue
                request = json.loads(bytes(data).split(b"\n", 1)[0])
                if self.scenario == "connection_loss":
                    continue
                if self.scenario == "request_timeout":
                    time.sleep(0.2)
                response = self._response(request)
                if self.scenario == "malformed_json":
                    connection.sendall(b"{not-json}\n")
                else:
                    if self.scenario == "id_mismatch":
                        response["id"] = request["id"] + 1
                    try:
                        connection.sendall((json.dumps(response) + "\n").encode())
                    except OSError:
                        pass

    def _response(self, request: dict[str, Any]) -> dict[str, Any]:
        self.frame += 1
        command = request["cmd"]
        result: dict[str, Any] = {"id": request["id"], "ok": True}
        if command == "protocol_info":
            result.update({
                "protocol": {"name": "psxrecomp-debug", "major": 1, "minor": 5},
                "server": {"kind": "native"},
                "capabilities": sorted(self.profile["supported_runtime_protocol"]["required_capabilities"]),
                "limits": {"max_response_bytes": 65536},
                "frame": self.frame,
            })
        elif command == "runtime_identity":
            self.runtime_reads += 1
            digest = self.profile["executable_identity"]["runtime_source_identity"]["sha256"]
            if self.scenario == "process_change" and self.runtime_reads >= 3:
                digest = "f" * 64
            result.update({
                "runtime": {
                    "implementation": "psxrecomp",
                    "build_revision": "synthetic",
                    "process_instance_id": "proc-" + "b" * 64,
                },
                "server": {"kind": "native"},
                "guest_architecture": "mips-r3000a",
                "bios": {"algorithm": "sha256", "sha256": "a" * 64, "length": 524288},
                "main_executable": {
                    "serial": "WRONG" if self.scenario == "profile_rejection" else "SCUS-94254",
                    "guest_base": "0x80010000",
                    "canonical_length": 440320,
                    "source_identity": {"algorithm": "sha256", "sha256": digest, "scope": "ps-x-exe-body"},
                },
                "frame": self.frame,
            })
        elif command == "execution_witness":
            self.witness_reads += 1
            required = next(item for item in self.profile["execution_identity"]["required_witnesses"] if item["pc"] == request["pc"])
            stale = self.scenario == "witness_stale" or (
                self.scenario == "retry_then_stable" and self.witness_reads <= 3
            )
            live_hash = "f" * 64 if self.scenario == "witness_hash" else required["live_sha256"]
            exec_token = "exec-b" if self.scenario == "executable_change" and self.boundary_reads >= 2 else "exec-a"
            life_token = "life-b" if self.scenario == "lifecycle_change" and self.boundary_reads >= 2 else "life-a"
            result.update({
                "status": "stale" if stale else "current",
                "requested_pc": required["pc"],
                "witness": {
                    "backend": required["backend"], "reason": "synthetic",
                    "range": {"kind": "executed-instruction", "guest_base": required["pc"], "length": 4},
                    "observed_identity": {"sha256": live_hash},
                    "current_live_identity": {"sha256": live_hash},
                    "watched_generation": {"digest": "d" * 64, "observed_legacy_sum": 1, "current_legacy_sum": 1},
                    "observation_current": not stale,
                    "first_observed_frame": 1, "last_observed_frame": self.frame, "hit_count": self.frame,
                    "memory_provenance": {"lifecycle_fragment": None, "native_registration": None},
                },
                "frame_before": self.frame, "frame_after": self.frame,
                "executable_state_before": exec_token, "executable_state_after": exec_token,
                "lifecycle_token_before": life_token, "lifecycle_token_after": life_token,
                "stable_observation_boundary": True,
            })
        elif command == "executable_lifecycle":
            life_token = "life-b" if self.scenario == "lifecycle_change" and self.boundary_reads >= 2 else "life-a"
            result.update({"lifecycle_token": life_token, "records": [], "total": 0, "returned": 0, "has_more": False, "frame": self.frame})
        elif command == "observation_guard":
            guard, global_token = self._guard_result(request["guard"])
            result.update({
                "frame_before": self.frame,
                "frame_after": self.frame,
                "stable_frame": True,
                "executable_state_before": global_token,
                "executable_state_after": global_token,
                "stable_executable_state": True,
                "guard": guard,
            })
        elif command == "read_regions":
            is_node = request["regions"][0].get("key") == "actor_node"
            if is_node:
                self.node_reads += 1
            else:
                self.boundary_reads += 1
            exec_token = "exec-b" if self.scenario == "executable_change" and self.boundary_reads >= 2 else "exec-a"
            guard = None
            if "guard" in request:
                guard, exec_token = self._guard_result(request["guard"])
            records = []
            for region in request["regions"]:
                key = region.get("key")
                length = region["len"]
                if key == "active_scene_name":
                    scene = b"town01\0\0"
                    if self.scenario == "scene_before" and self.boundary_reads == 2:
                        scene = b"map01\0\0\0"
                    if self.scenario == "scene_after" and self.boundary_reads >= 3:
                        scene = b"map01\0\0\0"
                    payload = scene
                elif key == "active_scene_prot_base":
                    payload = (3).to_bytes(2, "little")
                elif key == "master_game_mode":
                    payload = (3).to_bytes(2, "little")
                elif key == "actor_list_head":
                    head = 0 if self.scenario == "null_head" else 0x80090000
                    if self.scenario == "invalid_head": head = 0x90000000
                    if self.scenario == "unaligned_head": head = 0x80090002
                    if self.scenario == "head_change" and self.boundary_reads >= 3: head = 0x80090100
                    payload = head.to_bytes(4, "little")
                else:
                    address = int(region["addr"], 16)
                    next_map = {0x80090000: 0x80090100, 0x80090100: 0x80090200, 0x80090200: 0}
                    if self.scenario == "self_loop": next_map[0x80090000] = 0x80090000
                    if self.scenario == "cycle": next_map[0x80090200] = 0x80090100
                    if self.scenario == "unaligned_pointer": next_map[0x80090000] = 0x80090102
                    if self.scenario == "out_of_range_pointer": next_map[0x80090000] = 0x90000000
                    payload = make_node(next_map.get(address, 0), x=10 + self.node_reads)
                    if self.scenario == "truncated_node": payload = payload[:-1]
                records.append({"key": key, "addr": region["addr"], "len": length, "hex": payload.hex()})
            compatible = guard is None or guard["compatible"]
            if not compatible:
                records = []
            result.update({
                "frame_before": self.frame, "frame_after": self.frame, "stable_frame": True,
                "executable_state_before": exec_token, "executable_state_after": exec_token,
                "stable_executable_state": True, "regions": records,
                "payload_returned": compatible,
            })
            if guard is not None:
                result["guard"] = guard
        return result

    def _guard_result(self, descriptor: dict[str, Any]) -> tuple[dict[str, Any], str]:
        self.guard_reads += 1
        process_id = "proc-" + "b" * 64
        if self.scenario == "process_change" and self.guard_reads >= 2:
            process_id = "proc-" + "c" * 64
        ram_evidence = []
        token_ram = []
        for region in sorted(descriptor["ram_regions"], key=lambda item: (int(item["addr"], 16), item["len"], item["key"])):
            key = region["key"]
            if key == "active_scene_name":
                payload = b"town01\0\0"
                if self.scenario == "scene_before" and self.guard_reads >= 2:
                    payload = b"map01\0\0\0"
                if self.scenario == "scene_after" and self.node_reads > 0:
                    payload = b"map01\0\0\0"
            elif key == "active_scene_prot_base":
                value = 4 if self.scenario == "prot_change" and self.guard_reads >= 2 else 3
                payload = value.to_bytes(2, "little")
            elif key == "master_game_mode":
                value = 2 if self.scenario == "mode_change" and self.guard_reads >= 2 else 3
                payload = value.to_bytes(2, "little")
            else:
                head = 0 if self.scenario == "null_head" else 0x80090000
                if self.scenario == "invalid_head": head = 0x90000000
                if self.scenario == "unaligned_head": head = 0x80090002
                if self.scenario == "head_change" and self.guard_reads >= 2: head = 0x80090100
                payload = head.to_bytes(4, "little")
            digest = hashlib.sha256(payload).hexdigest()
            ram_evidence.append({
                "key": key,
                "addr": region["addr"],
                "len": region["len"],
                "sha256": digest,
            })
            token_ram.append((int(region["addr"], 16), region["len"], key, digest))
        witness_evidence = []
        token_witnesses = []
        for requested in sorted(descriptor["execution_witnesses"], key=lambda item: int(item["pc"], 16)):
            required = next(
                item for item in self.profile["execution_identity"]["required_witnesses"]
                if item["pc"] == requested["pc"]
            )
            stale = self.scenario == "witness_stale" or (
                self.scenario == "retry_then_stable" and self.guard_reads == 1
            )
            live_hash = "f" * 64 if self.scenario == "witness_hash" else required["live_sha256"]
            generation = "e" * 64 if self.scenario == "witness_generation" and self.guard_reads >= 2 else "d" * 64
            backend = "interpreter" if self.scenario == "witness_backend" and self.guard_reads >= 2 else required["backend"]
            lifecycle_generation = 2 if self.scenario == "relevant_lifecycle_change" and self.guard_reads >= 2 else 1
            status = "stale" if stale else "current"
            item = {
                "pc": required["pc"], "status": status, "current": not stale,
                "backend": backend, "reason": "synthetic",
                "range": {"guest_base": required["pc"], "length": 4},
                "live_sha256": live_hash,
                "watched_generation_digest": generation,
                "image_instance_id": "life-0000000000000001",
                "lifecycle_generation": lifecycle_generation,
                "native_registration_id": None,
            }
            witness_evidence.append(item)
            token_witnesses.append((required["pc"], backend, live_hash, generation, not stale, lifecycle_generation))
        valid = all(item["current"] for item in witness_evidence)
        state = {
            "domain": "psxrecomp-observation-guard-v1",
            "process": process_id,
            "source": self.profile["executable_identity"]["runtime_source_identity"]["sha256"],
            "ram": token_ram,
            "witnesses": token_witnesses,
        }
        token = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        token_after = "9" * 64 if self.scenario == "guard_unstable" else token
        expected = descriptor.get("expected_token")
        expected_match = expected is None or expected == token
        stable = token == token_after
        evidence = {
            "token": token,
            "valid": valid,
            "failure_reason": "none" if valid else "required execution witness is stale",
            "runtime_instance_id": process_id,
            "ram_regions": ram_evidence,
            "execution_witnesses": witness_evidence,
            "ram_region_count": len(ram_evidence),
            "execution_witness_count": len(witness_evidence),
        }
        guard = {
            "token_before": token,
            "token_after": token_after,
            "expected_token_matched": expected_match,
            "stable": stable,
            "valid": valid,
            "compatible": valid and stable and expected_match,
            "evidence": evidence,
        }
        global_token = "exec-b" if self.scenario in {"executable_change", "lifecycle_change"} and self.guard_reads >= 2 else "exec-a"
        return guard, global_token


class ObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile_document = synthetic_profile()
        self.profile = LoadedProfile.from_document(self.profile_document)

    def capture(self, scenario: str = "stable", *, attempts: int | None = None) -> dict[str, Any]:
        server = SyntheticServer(self.profile_document, scenario)
        try:
            with ProtocolClient(server.host, server.port, request_timeout=0.05, startup_attempts=2) as client:
                return RuntimeObserver(client, self.profile).capture(attempts)
        finally:
            server.close()

    def boundary(self, scenario: str = "stable", *, samples: int = 10) -> tuple[dict[str, Any], int]:
        server = SyntheticServer(self.profile_document, scenario)
        try:
            with ProtocolClient(server.host, server.port) as client:
                result = RuntimeObserver(client, self.profile).capture_boundary(samples)
            return result, server.node_reads
        finally:
            server.close()

    def test_01_valid_three_node_chain(self) -> None:
        snapshot = self.capture()
        self.assertEqual(snapshot["actor_chain"]["node_count"], 3)
        self.assertEqual(snapshot["actor_chain"]["termination_reason"], "null")

    def test_02_null_head(self) -> None:
        self.assertEqual(self.capture("null_head")["actor_chain"]["termination_reason"], "null_head")

    def test_03_invalid_head(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("invalid_head")

    def test_04_self_loop(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("self_loop")

    def test_05_multi_node_cycle(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("cycle")

    def test_06_unaligned_pointer(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("unaligned_pointer")

    def test_07_out_of_range_pointer(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("out_of_range_pointer")

    def test_08_truncated_node_read(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("truncated_node")

    def test_09_node_limit_exceeded(self) -> None:
        profile = copy.deepcopy(self.profile_document); profile["observation_policy"]["traversal"]["maximum_nodes"] = 2
        profile["observation_policy"]["traversal"]["maximum_requests"] = 2
        profile["observation_policy"]["traversal"]["maximum_aggregate_bytes"] = 312
        server = SyntheticServer(profile)
        try:
            with ProtocolClient(server.host, server.port) as client:
                with self.assertRaises(RetryExhausted): RuntimeObserver(client, LoadedProfile.from_document(profile)).capture(1)
        finally: server.close()

    def test_10_aggregate_byte_limit_profile_rejected(self) -> None:
        profile = copy.deepcopy(self.profile_document); profile["observation_policy"]["traversal"]["maximum_aggregate_bytes"] = 155
        with self.assertRaises(Exception): LoadedProfile.from_document(profile)

    def test_11_scene_changes_before_traversal(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("scene_before", attempts=1)

    def test_12_scene_changes_after_traversal(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("scene_after", attempts=1)

    def test_13_executable_state_change(self) -> None:
        self.assertEqual(self.capture("executable_change", attempts=1)["actor_chain"]["node_count"], 3)

    def test_14_lifecycle_token_change(self) -> None:
        self.assertEqual(self.capture("lifecycle_change", attempts=1)["actor_chain"]["node_count"], 3)

    def test_15_witness_becomes_stale(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("witness_stale", attempts=1)

    def test_16_witness_hash_changes(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("witness_hash", attempts=1)

    def test_17_runtime_process_identity_changes(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("process_change", attempts=1)

    def test_18_actor_list_head_changes(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("head_change", attempts=1)

    def test_19_stable_chain_with_moving_coordinates(self) -> None:
        snapshot = self.capture()
        x = next(field for field in snapshot["actor_chain"]["nodes"][0]["decoded_fields"] if field["property"] == "position_x")
        self.assertGreater(x["raw_numeric_value"], 10)

    def test_20_conditional_applicability_unknown(self) -> None:
        fields = decode_fields(make_node(0), self.profile_document)
        field = next(item for item in fields if item["property"] == "map_object_record_index")
        self.assertTrue(field["unresolved"]); self.assertEqual(field["applicability"], "unresolved")

    def test_21_contradictory_field_claim(self) -> None:
        field = next(item for item in decode_fields(make_node(0), self.profile_document) if item["property"] == "field_0x94")
        self.assertEqual(field["confidence"], "contradictory"); self.assertGreaterEqual(len(field["alternatives"]), 2)

    def test_22_request_timeout(self) -> None:
        server = SyntheticServer(self.profile_document, "request_timeout")
        try:
            with ProtocolClient(server.host, server.port, request_timeout=0.01, startup_attempts=1) as client:
                with self.assertRaises(ProtocolError): client.negotiate()
        finally: server.close()

    def test_23_connection_loss(self) -> None:
        server = SyntheticServer(self.profile_document, "connection_loss")
        try:
            with ProtocolClient(server.host, server.port, request_timeout=0.05, startup_attempts=1) as client:
                with self.assertRaises(ProtocolError): client.negotiate()
        finally: server.close()

    def test_24_response_id_mismatch(self) -> None:
        server = SyntheticServer(self.profile_document, "id_mismatch")
        try:
            with ProtocolClient(server.host, server.port, startup_attempts=1) as client:
                with self.assertRaisesRegex(ProtocolError, "ID mismatch"): client.negotiate()
        finally: server.close()

    def test_25_malformed_json_response(self) -> None:
        server = SyntheticServer(self.profile_document, "malformed_json")
        try:
            with ProtocolClient(server.host, server.port, startup_attempts=1) as client:
                with self.assertRaisesRegex(ProtocolError, "malformed JSON"): client.negotiate()
        finally: server.close()

    def test_26_profile_rejection(self) -> None:
        with self.assertRaises(ProfileRejected): self.capture("profile_rejection")

    def test_27_retry_succeeds_later(self) -> None:
        self.assertEqual(self.capture("retry_then_stable")["metrics"]["attempt"], 2)

    def test_28_retry_exhaustion(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("witness_stale", attempts=2)

    def test_29_snapshot_schema_validation(self) -> None:
        snapshot = self.capture(); validate_snapshot(snapshot)
        jsonschema.validate(snapshot, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))

    def test_30_metadata_only_output_scan(self) -> None:
        text = canonical_snapshot_json(self.capture())
        for forbidden in ('"raw_bytes"', '"payload"', '"ram_dump"', '"disc_path"', '"executable_bytes"'):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("C:\\", text)

    def test_31_unaligned_head(self) -> None:
        with self.assertRaises(RetryExhausted): self.capture("unaligned_head", attempts=1)

    def test_32_pointer_fields_are_not_dereferenced(self) -> None:
        pointer = pointer_metadata(0x800A0000, self.profile_document)
        self.assertFalse(pointer["dereferenced"])

    def test_33_client_rejects_write_commands(self) -> None:
        client = ProtocolClient();
        with self.assertRaisesRegex(ProtocolError, "not permitted"): client.request("write_ram")

    def test_34_boundary_only_two_sample_stabilization(self) -> None:
        result, _ = self.boundary(samples=1)
        self.assertEqual(result["guard"]["compatible_sample_count"], 3)

    def test_35_boundary_only_ten_subsequent_samples(self) -> None:
        result, _ = self.boundary(samples=10)
        self.assertEqual(result["guard"]["subsequent_sample_count"], 10)
        self.assertEqual(result["guard"]["compatible_sample_count"], 12)

    def test_36_boundary_only_reads_no_actor_nodes(self) -> None:
        result, node_reads = self.boundary()
        self.assertEqual(node_reads, 0)
        self.assertEqual(result["actor_node_reads"], 0)
        self.assertEqual(result["actor_bytes_read"], 0)

    def test_37_global_churn_does_not_invalidate_scoped_epoch(self) -> None:
        result, _ = self.boundary("executable_change")
        self.assertGreater(result["global_executable_state"]["changes_observed_between_samples"], 0)

    def test_38_scene_change_invalidates_boundary_only(self) -> None:
        server = SyntheticServer(self.profile_document, "scene_before")
        try:
            with ProtocolClient(server.host, server.port) as client:
                with self.assertRaises(Exception):
                    RuntimeObserver(client, self.profile).capture_boundary(1)
        finally:
            server.close()

    def test_39_relevant_lifecycle_invalidates_boundary_only(self) -> None:
        server = SyntheticServer(self.profile_document, "relevant_lifecycle_change")
        try:
            with ProtocolClient(server.host, server.port) as client:
                with self.assertRaises(Exception):
                    RuntimeObserver(client, self.profile).capture_boundary(1)
        finally:
            server.close()

    def test_40_boundary_first_last_frame_metadata(self) -> None:
        result, _ = self.boundary()
        self.assertLessEqual(result["frames"]["first"], result["frames"]["last"])

    def test_41_guard_descriptor_is_profile_derived(self) -> None:
        server = SyntheticServer(self.profile_document)
        try:
            with ProtocolClient(server.host, server.port) as client:
                observer = RuntimeObserver(client, self.profile)
                observer.selector.negotiate()
                guard = observer.selector.guard_descriptor()
            expected = [item["id"] for item in self.profile_document["scene_identity"]["required_signals"]]
            self.assertEqual([item["key"] for item in guard["ram_regions"][:-1]], expected)
            self.assertEqual(len(guard["execution_witnesses"]), 3)
        finally:
            server.close()

    def test_42_boundary_only_cli_gates_actor_traversal(self) -> None:
        self.assertIn("--boundary-only", OBSERVER_TOOL)
        self.assertIn("retail actor traversal remains gated", OBSERVER_TOOL)


if __name__ == "__main__":
    unittest.main()
