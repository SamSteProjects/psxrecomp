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
        structural_runtime = {key: value for key, value in self.runtime.items() if key not in {"id", "frame"}}
        self.runtime_process_identity = _sha(
            {"observer_session": self.client.session_id, "runtime": structural_runtime}
        )

    def _scene_and_head(self) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile.document
        signals = profile["scene_identity"]["required_signals"]
        head = profile["actor_pool"]["linked_list_head"]
        regions = [
            {"key": signal["id"], "addr": signal["address"], "len": signal["width"]}
            for signal in signals
        ]
        regions.append(
            {
                "key": "actor_list_head",
                "addr": head["address"],
                "len": profile["observation_policy"]["head_pointer"]["width"],
            }
        )
        response = self.client.read_regions(regions)
        if response.get("stable_frame") is not True or response.get("stable_executable_state") is not True:
            raise SnapshotUnstable("scene-signal read crossed a frame or executable boundary")
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
        }

    def _witnesses(self) -> tuple[list[dict[str, Any]], str, str]:
        observed: list[dict[str, Any]] = []
        executable_tokens: set[str] = set()
        lifecycle_tokens: set[str] = set()
        for required in self.profile.document["execution_identity"]["required_witnesses"]:
            response = self.client.execution_witness(required["pc"])
            if response.get("stable_observation_boundary") is not True:
                raise SnapshotUnstable(f"witness {required['pc']} crossed an observation boundary")
            witness = response.get("witness")
            if not isinstance(witness, dict):
                raise ProfileRejected(f"required witness {required['pc']} is missing")
            generation = witness.get("watched_generation", {})
            observed_generation = generation.get("observed_legacy_sum")
            current_generation = generation.get("current_legacy_sum")
            normalized = {
                "id": required["id"],
                "pc": response.get("requested_pc"),
                "status": response.get("status"),
                "backend": witness.get("backend"),
                "range": {
                    "kind": witness.get("range", {}).get("kind"),
                    "base": witness.get("range", {}).get("guest_base"),
                    "length": witness.get("range", {}).get("length"),
                },
                "live_sha256": witness.get("current_live_identity", {}).get("sha256"),
                "observed_sha256": witness.get("observed_identity", {}).get("sha256"),
                "observation_current": witness.get("observation_current"),
                "watched_generation_digest": generation.get("digest"),
                "watched_generation_at_observation": f"legacy:{observed_generation}",
                "watched_generation_current": f"legacy:{current_generation}",
                "first_observed_frame": witness.get("first_observed_frame"),
                "last_observed_frame": witness.get("last_observed_frame"),
                "hit_count": witness.get("hit_count"),
                "memory_provenance": witness.get("memory_provenance"),
            }
            observed.append(normalized)
            executable_tokens.update(
                [response.get("executable_state_before"), response.get("executable_state_after")]
            )
            lifecycle_tokens.update(
                [response.get("lifecycle_token_before"), response.get("lifecycle_token_after")]
            )
        if None in executable_tokens or len(executable_tokens) != 1:
            raise SnapshotUnstable("execution witness set crossed an executable-state boundary")
        if None in lifecycle_tokens or len(lifecycle_tokens) != 1:
            raise SnapshotUnstable("execution witness set crossed a lifecycle boundary")
        return observed, executable_tokens.pop(), lifecycle_tokens.pop()

    def sample_boundary(self) -> dict[str, Any]:
        if self.protocol is None or self.runtime is None or self.runtime_process_identity is None:
            raise ProfileRejected("profile negotiation has not completed")
        runtime = self.client.runtime_identity()
        structural = {key: value for key, value in runtime.items() if key not in {"id", "frame"}}
        expected_structural = {key: value for key, value in self.runtime.items() if key not in {"id", "frame"}}
        if structural != expected_structural:
            raise SnapshotUnstable("runtime identity changed during observation")
        signals, head = self._scene_and_head()
        witnesses, witness_exec, witness_lifecycle = self._witnesses()
        lifecycle = self.client.lifecycle_token()
        lifecycle_token = lifecycle.get("lifecycle_token")
        read_response = head.pop("response")
        read_exec_before = read_response.get("executable_state_before")
        read_exec_after = read_response.get("executable_state_after")
        if read_exec_before != read_exec_after or read_exec_before != witness_exec:
            raise SnapshotUnstable("scene and witness samples disagree on executable state")
        if lifecycle_token != witness_lifecycle:
            raise SnapshotUnstable("scene and witness samples disagree on lifecycle state")
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
                "stable_executable_state": True,
                "stable_lifecycle_state": True,
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
            "executable_state_token": witness_exec,
            "lifecycle_token": witness_lifecycle,
            "stable_frame": True,
            "stable_executable_state": True,
            "stable_lifecycle_state": True,
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
            "evidence": ["revisioned-layout-profile", "protocol-1.4-live-boundary"],
        }
