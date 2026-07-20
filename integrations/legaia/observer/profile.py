"""Profile-driven runtime selection and boundary sampling."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from integrations.legaia.layouts import (
    LayoutProfileError,
    canonical_profile_json,
    validate_observation_context,
    validate_profile,
)

from .client import ProtocolClient
from .errors import ProfileRejected, ProtocolError, SnapshotUnstable


def _sha(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hex_address(value: int) -> str:
    return f"0x{value:08X}"


def build_guard_descriptor(
    profile: Mapping[str, Any], expected_token: str | None = None
) -> dict[str, Any]:
    signals = profile["scene_identity"]["required_signals"]
    head = profile["actor_pool"]["linked_list_head"]
    ram_regions = [
        {"key": signal["id"], "addr": signal["address"], "len": signal["width"]}
        for signal in signals
    ]
    ram_regions.append(
        {
            "key": "actor_list_head",
            "addr": head["address"],
            "len": profile["observation_policy"]["head_pointer"]["width"],
        }
    )
    descriptor: dict[str, Any] = {
        "ram_regions": ram_regions,
        "execution_witnesses": [
            {"pc": witness["pc"], "require_current": True}
            for witness in profile["execution_identity"]["required_witnesses"]
        ],
    }
    if expected_token is not None:
        descriptor["expected_token"] = expected_token
    return descriptor


def _decode_signal(signal: Mapping[str, Any], payload: bytes) -> Any:
    width = signal["width"]
    if len(payload) != width:
        raise ProfileRejected(f"scene signal {signal['id']} returned the wrong width")
    kind = signal["type"]
    if kind == "ascii_nul_terminated":
        nul = payload.find(b"\0")
        if nul < 0:
            raise ProfileRejected(f"scene signal {signal['id']} is not NUL terminated")
        if any(payload[nul + 1 :]):
            raise ProfileRejected(f"scene signal {signal['id']} has malformed padding")
        try:
            return payload[:nul].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ProfileRejected(f"scene signal {signal['id']} is not ASCII") from exc
    if kind in {"u8", "u16_le", "u32_le"}:
        expected_width = {"u8": 1, "u16_le": 2, "u32_le": 4}[kind]
        if width != expected_width:
            raise ProfileRejected(f"scene signal {signal['id']} encoding width conflicts")
        return int.from_bytes(payload, "little", signed=False)
    raise ProfileRejected(f"unsupported scene signal encoding: {kind}")


@dataclass(frozen=True)
class LoadedProfile:
    document: dict[str, Any]
    profile_hash: str

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "LoadedProfile":
        validated = validate_profile(document)
        canonical = canonical_profile_json(validated).encode("utf-8")
        return cls(validated, hashlib.sha256(canonical).hexdigest())


class ProfileSelector:
    def __init__(self, client: ProtocolClient, profile: LoadedProfile) -> None:
        self.client = client
        self.profile = profile
        self.protocol: dict[str, Any] | None = None
        self.runtime: dict[str, Any] | None = None
        self.runtime_process_identity: str | None = None

    def negotiate(self) -> None:
        self.protocol = self.client.negotiate()
        wanted = self.profile.document["supported_runtime_protocol"]
        protocol = self.protocol["protocol"]
        if protocol.get("name") != wanted["name"]:
            raise ProfileRejected("protocol name does not match profile")
        if protocol.get("major") != wanted["minimum_major"]:
            raise ProfileRejected("protocol major version does not match profile")
        if not isinstance(protocol.get("minor"), int) or protocol["minor"] < wanted["minimum_minor"]:
            raise ProfileRejected("protocol minor version is too old")
        missing = sorted(set(wanted["required_capabilities"]) - set(self.protocol["capabilities"]))
        if missing:
            raise ProfileRejected(f"required capabilities are missing: {', '.join(missing)}")
        if self.protocol.get("server", {}).get("kind") != "native":
            raise ProfileRejected("profile requires the native PSXRecomp server")
        self.runtime = self.client.runtime_identity()
        implementation = self.runtime.get("runtime", {}).get("implementation")
        if implementation != wanted["required_runtime_implementation"]:
            raise ProfileRejected("runtime implementation does not match profile")
        main = self.runtime.get("main_executable")
        expected = self.profile.document["executable_identity"]
        if not isinstance(main, dict):
            raise ProfileRejected("main executable identity is missing")
        if main.get("serial") != expected["serial"]:
            raise ProfileRejected("main executable serial does not match profile")
        source = main.get("source_identity", {})
        expected_source = expected["runtime_source_identity"]
        if source.get("algorithm") != expected_source["algorithm"] or source.get("scope") != expected_source["scope"]:
            raise ProfileRejected("main executable source scope does not match profile")
        if source.get("sha256") != expected_source["sha256"]:
            raise ProfileRejected("main executable source identity does not match profile")
        if main.get("canonical_length") != expected_source["length"] or main.get("guest_base") != expected_source["guest_base"]:
            raise ProfileRejected("main executable source range does not match profile")
        process_identity = self.runtime.get("runtime", {}).get("process_instance_id")
        if not isinstance(process_identity, str) or not process_identity.startswith("proc-"):
            raise ProfileRejected("runtime process instance identity is missing")
        self.runtime_process_identity = process_identity

    def guard_descriptor(self, expected_token: str | None = None) -> dict[str, Any]:
        return build_guard_descriptor(self.profile.document, expected_token)

    @staticmethod
    def _require_guard(response: Mapping[str, Any]) -> Mapping[str, Any]:
        guard = response.get("guard")
        if not isinstance(guard, Mapping):
            raise ProtocolError("observation guard result is missing")
        if guard.get("valid") is not True:
            evidence = guard.get("evidence") or {}
            raise ProfileRejected(
                f"observation guard is invalid: {evidence.get('failure_reason', 'unknown')}"
            )
        if guard.get("stable") is not True:
            raise SnapshotUnstable("observation guard changed during one request")
        if guard.get("expected_token_matched") is not True:
            raise SnapshotUnstable("observation guard does not match the accepted epoch token")
        if guard.get("compatible") is not True:
            raise SnapshotUnstable("observation guard is not compatible")
        token = guard.get("token_before")
        if not isinstance(token, str) or token != guard.get("token_after"):
            raise ProtocolError("observation guard token is malformed")
        return guard

    def _scene_and_head(
        self, expected_token: str | None = None
    ) -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any]]:
        profile = self.profile.document
        signals = profile["scene_identity"]["required_signals"]
        head = profile["actor_pool"]["linked_list_head"]
        regions = self.guard_descriptor()["ram_regions"]
        response = self.client.read_regions(
            regions,
            guard=self.guard_descriptor(expected_token),
        )
        guard = self._require_guard(response)
        if response.get("payload_returned") is not True:
            raise SnapshotUnstable("guarded scene-signal payload was withheld")
        records = response.get("regions")
        if not isinstance(records, list) or len(records) != len(regions):
            raise ProtocolError("read_regions returned an incomplete scene sample")
        by_key: dict[str, bytes] = {}
        for expected_region, record in zip(regions, records):
            if record.get("key") != expected_region["key"] or record.get("len") != expected_region["len"]:
                raise ProtocolError("read_regions did not preserve requested scene region order")
            try:
                data = bytes.fromhex(record["hex"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError("read_regions returned malformed hex") from exc
            if len(data) != expected_region["len"]:
                raise ProtocolError("read_regions returned a truncated scene region")
            by_key[expected_region["key"]] = data
        decoded = {signal["id"]: _decode_signal(signal, by_key[signal["id"]]) for signal in signals}
        head_value = int.from_bytes(by_key["actor_list_head"], "little")
        return decoded, {
            "value": _hex_address(head_value),
            "raw_value": head_value,
            "response": response,
        }, guard

    def _normalize_guard_witnesses(self, guard: Mapping[str, Any]) -> list[dict[str, Any]]:
        evidence = guard.get("evidence")
        if not isinstance(evidence, Mapping):
            raise ProtocolError("observation guard evidence is missing")
        wire_witnesses = evidence.get("execution_witnesses")
        if not isinstance(wire_witnesses, list):
            raise ProtocolError("observation guard witness evidence is missing")
        by_pc = {item.get("pc"): item for item in wire_witnesses if isinstance(item, Mapping)}
        observed: list[dict[str, Any]] = []
        for required in self.profile.document["execution_identity"]["required_witnesses"]:
            witness = by_pc.get(required["pc"])
            if not isinstance(witness, Mapping):
                raise ProfileRejected(f"required witness {required['pc']} is missing from guard")
            generation = witness.get("watched_generation_digest")
            normalized = {
                "id": required["id"],
                "pc": witness.get("pc"),
                "status": witness.get("status"),
                "backend": witness.get("backend"),
                "range": {
                    "kind": "executed-instruction",
                    "base": witness.get("range", {}).get("guest_base"),
                    "length": witness.get("range", {}).get("length"),
                },
                "live_sha256": witness.get("live_sha256"),
                "observation_current": witness.get("current"),
                "watched_generation_digest": generation,
                "watched_generation_at_observation": f"digest:{generation}",
                "watched_generation_current": f"digest:{generation}",
                "image_instance_id": witness.get("image_instance_id"),
                "lifecycle_generation": witness.get("lifecycle_generation"),
                "native_registration_id": witness.get("native_registration_id"),
                "reason": witness.get("reason"),
            }
            observed.append(normalized)
        return observed

    def sample_guard_only(self, expected_token: str) -> dict[str, Any]:
        response = self.client.observation_guard(self.guard_descriptor(expected_token))
        guard = self._require_guard(response)
        evidence = guard.get("evidence") or {}
        if evidence.get("runtime_instance_id") != self.runtime_process_identity:
            raise SnapshotUnstable("runtime process identity changed during guard sampling")
        return {
            "frame_before": response.get("frame_before"),
            "frame_after": response.get("frame_after"),
            "guard_token": guard["token_before"],
            "global_executable_state_before": response.get("executable_state_before"),
            "global_executable_state_after": response.get("executable_state_after"),
            "stable_global_executable_state": response.get("stable_executable_state"),
            "global_state_components_before": response.get(
                "global_state_components_before"
            ),
            "global_state_components_after": response.get(
                "global_state_components_after"
            ),
            "guard_evidence": evidence,
        }

    def sample_guard_diagnostic(self, expected_token: str) -> dict[str, Any]:
        """Return bounded mismatch evidence without promoting it to a valid profile."""
        if self.runtime_process_identity is None:
            raise ProfileRejected("profile negotiation has not completed")
        response = self.client.observation_guard(self.guard_descriptor(expected_token))
        guard = response.get("guard")
        if not isinstance(guard, Mapping):
            raise ProtocolError("observation guard result is missing")
        evidence = guard.get("evidence")
        if not isinstance(evidence, Mapping):
            raise ProtocolError("observation guard evidence is missing")
        runtime_instance = evidence.get("runtime_instance_id")
        return {
            "frame_before": response.get("frame_before"),
            "frame_after": response.get("frame_after"),
            "stable": guard.get("stable") is True,
            "valid": guard.get("valid") is True,
            "compatible": guard.get("compatible") is True,
            "expected_token_matched": guard.get("expected_token_matched") is True,
            "token_before": guard.get("token_before"),
            "token_after": guard.get("token_after"),
            "runtime_instance_id": runtime_instance,
            "runtime_instance_matches": runtime_instance == self.runtime_process_identity,
            "failure_reason": evidence.get("failure_reason"),
            "ram_regions": evidence.get("ram_regions", []),
            "execution_witnesses": evidence.get("execution_witnesses", []),
            "global_executable_state_before": response.get("executable_state_before"),
            "global_executable_state_after": response.get("executable_state_after"),
        }

    def sample_scene_signals_unscoped(self) -> dict[str, Any]:
        """Read only profile-declared scene signals while town01 is not selected."""
        if self.runtime_process_identity is None:
            raise ProfileRejected("profile negotiation has not completed")
        regions = self.guard_descriptor()["ram_regions"]
        response = self.client.read_regions(regions)
        records = response.get("regions")
        if not isinstance(records, list) or len(records) != len(regions):
            raise ProtocolError("read_regions returned an incomplete scene sample")
        by_key: dict[str, bytes] = {}
        for expected_region, record in zip(regions, records):
            if record.get("key") != expected_region["key"] or record.get("len") != expected_region["len"]:
                raise ProtocolError("read_regions did not preserve requested scene region order")
            try:
                payload = bytes.fromhex(record["hex"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError("read_regions returned malformed scene hex") from exc
            if len(payload) != expected_region["len"]:
                raise ProtocolError("read_regions returned a truncated scene region")
            by_key[expected_region["key"]] = payload
        decoded: dict[str, Any] = {}
        decode_errors: dict[str, str] = {}
        for signal in self.profile.document["scene_identity"]["required_signals"]:
            try:
                decoded[signal["id"]] = _decode_signal(signal, by_key[signal["id"]])
            except ProfileRejected as exc:
                decoded[signal["id"]] = None
                decode_errors[signal["id"]] = str(exc)
        head_value = int.from_bytes(by_key["actor_list_head"], "little", signed=False)
        return {
            "frame_before": response.get("frame_before"),
            "frame_after": response.get("frame_after"),
            "stable_frame": response.get("stable_frame"),
            "stable_executable_state": (
                response.get("executable_state_before")
                == response.get("executable_state_after")
            ),
            "scene_signals": decoded,
            "actor_list_head": _hex_address(head_value),
            "actor_list_head_raw": head_value,
            "decode_errors": decode_errors,
            "global_executable_state_before": response.get("executable_state_before"),
            "global_executable_state_after": response.get("executable_state_after"),
        }

    def sample_boundary(self, expected_token: str | None = None) -> dict[str, Any]:
        if self.protocol is None or self.runtime is None or self.runtime_process_identity is None:
            raise ProfileRejected("profile negotiation has not completed")
        runtime = self.client.runtime_identity()
        structural = {key: value for key, value in runtime.items() if key not in {"id", "frame"}}
        expected_structural = {key: value for key, value in self.runtime.items() if key not in {"id", "frame"}}
        if structural != expected_structural:
            raise SnapshotUnstable("runtime identity changed during observation")
        signals, head, guard = self._scene_and_head(expected_token)
        witnesses = self._normalize_guard_witnesses(guard)
        read_response = head.pop("response")
        context = {
            "executable_identity": {
                "serial": runtime["main_executable"]["serial"],
            },
            "runtime_source_identity": {
                **runtime["main_executable"]["source_identity"],
                "length": runtime["main_executable"]["canonical_length"],
                "guest_base": runtime["main_executable"]["guest_base"],
            },
            "runtime_protocol": {
                **self.protocol["protocol"],
                "capabilities": self.protocol["capabilities"],
            },
            "overlays": [],
            "scene_signals": signals,
            "execution_witnesses": witnesses,
            "observation_boundary": {
                "stable_executable_state": read_response.get("stable_executable_state"),
                "stable_lifecycle_state": None,
                "stable_observation_guard": True,
            },
            "actor_count": 0,
        }
        try:
            validate_observation_context(self.profile.document, context)
        except LayoutProfileError as exc:
            raise ProfileRejected(str(exc)) from exc
        witness_structural = [
            {
                "pc": item["pc"],
                "backend": item["backend"],
                "range": item["range"],
                "live_sha256": item["live_sha256"],
            }
            for item in witnesses
        ]
        return {
            "runtime_process_identity": self.runtime_process_identity,
            "runtime_frame": runtime.get("frame"),
            "frame": read_response.get("frame_after"),
            "scene_signals": signals,
            "actor_list_head": head["value"],
            "actor_list_head_raw": head["raw_value"],
            "actor_census_base": self.profile.document["actor_pool"]["pointer_census"]["base_address"],
            "field_execution_identity": _sha(witness_structural),
            "witness_structural_identities": witness_structural,
            "witness_results": witnesses,
            "observation_guard_token": guard["token_before"],
            "guard_evidence": guard.get("evidence"),
            "global_executable_state_before": read_response.get("executable_state_before"),
            "global_executable_state_after": read_response.get("executable_state_after"),
            "stable_global_executable_state": read_response.get("stable_executable_state"),
            "stable_frame": read_response.get("stable_frame"),
            "stable_observation_guard": True,
        }

    def selection_result(self, boundary: Mapping[str, Any]) -> dict[str, Any]:
        assert self.protocol is not None and self.runtime is not None
        return {
            "accepted": True,
            "rejected_reasons": [],
            "profile_id": self.profile.document["profile_id"],
            "profile_hash": self.profile.profile_hash,
            "runtime_identity": {key: value for key, value in self.runtime.items() if key != "id"},
            "protocol_identity": {
                "protocol": self.protocol["protocol"],
                "server": self.protocol["server"],
                "capabilities": self.protocol["capabilities"],
            },
            "witness_results": boundary["witness_results"],
            "scene_signal_results": boundary["scene_signals"],
            "confidence": "confirmed",
            "evidence": ["revisioned-layout-profile", "protocol-1.5-observation-guard"],
        }
