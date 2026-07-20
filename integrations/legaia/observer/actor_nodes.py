"""Bounded traversal and evidence-backed decoding of field actor candidates."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from .client import ProtocolClient
from .epoch import SceneEpoch
from .errors import ChainInvalid, ProtocolError, SnapshotUnstable


POINTER_TYPES = {"ram_pointer", "code_pointer"}


def _address(value: str) -> int:
    return int(value, 16)


def _format_address(value: int) -> str:
    return f"0x{value:08X}"


def pointer_metadata(
    raw: int, profile: Mapping[str, Any], *, dereferenced: bool = False
) -> dict[str, Any]:
    bounds = profile["safety_bounds"]
    start = _address(bounds["main_ram_start"])
    end = _address(bounds["main_ram_end_exclusive"])
    alignment = profile["observation_policy"]["head_pointer"]["alignment"]
    return {
        "raw_value": raw,
        "value": _format_address(raw),
        "null": raw == 0,
        "aligned": raw == 0 or raw % alignment == 0,
        "in_main_ram": start <= raw < end,
        "accepted_segment": start <= raw < end,
        "in_known_executable_range": None,
        "dereferenced": dereferenced,
    }


def validate_chain_pointer(raw: int, profile: Mapping[str, Any], prefix_length: int) -> None:
    metadata = pointer_metadata(raw, profile)
    if raw == 0:
        return
    if not metadata["aligned"]:
        raise ChainInvalid(f"unaligned actor-node pointer {_format_address(raw)}")
    if not metadata["in_main_ram"] or not metadata["accepted_segment"]:
        raise ChainInvalid(f"actor-node pointer is outside accepted main RAM: {_format_address(raw)}")
    end = _address(profile["safety_bounds"]["main_ram_end_exclusive"])
    if raw + prefix_length < raw or raw + prefix_length > end:
        raise ChainInvalid(f"actor-node prefix overflows main RAM: {_format_address(raw)}")


def _decode_numeric(data: bytes, field: Mapping[str, Any]) -> int:
    start = field["offset"]
    end = start + field["width"]
    if end > len(data):
        raise ChainInvalid(f"field {field['id']} exceeds returned node prefix")
    return int.from_bytes(data[start:end], "little", signed=field["signed"])


def decode_fields(data: bytes, profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for descriptor in profile["actor_fields"]:
        raw = _decode_numeric(data, descriptor)
        claim = descriptor["claim"]
        conditional = descriptor["observation"] != "safe"
        interpreted: Any = raw
        if descriptor["id"] == "heading_yaw":
            interpreted = {"units": raw, "degrees": raw * 360.0 / 4096.0}
        elif descriptor["type"] in POINTER_TYPES:
            interpreted = pointer_metadata(raw, profile)
        elif conditional:
            interpreted = None
        fields.append(
            {
                "property": descriptor["id"],
                "raw_numeric_value": raw,
                "interpreted_value": interpreted,
                "offset": descriptor["offset"],
                "width": descriptor["width"],
                "signedness": "signed" if descriptor["signed"] else "unsigned",
                "representation": descriptor["representation"],
                "confidence": claim["confidence"],
                "evidence": claim["evidence"],
                "notes": claim["notes"],
                "applicability": "unresolved" if conditional else descriptor["owner"],
                "unresolved": conditional or claim["confidence"] in {"unknown", "contradictory"},
                "alternatives": claim.get("alternatives", []),
            }
        )
    return fields


@dataclass
class TraversalResult:
    head: str
    nodes: list[dict[str, Any]]
    termination_reason: str
    request_count: int
    bytes_read: int
    duration_ms: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "head": self.head,
            "node_count": len(self.nodes),
            "traversal_complete": True,
            "termination_reason": self.termination_reason,
            "prefix_length": self.nodes[0]["prefix_length"] if self.nodes else 156,
            "request_count": self.request_count,
            "bytes_read": self.bytes_read,
            "nodes": self.nodes,
        }


def traverse_actor_chain(
    client: ProtocolClient,
    profile: Mapping[str, Any],
    epoch: SceneEpoch,
) -> TraversalResult:
    policy = profile["observation_policy"]["traversal"]
    prefix_length = policy["prefix_length"]
    current = int(epoch.actor_list_head, 16)
    validate_chain_pointer(current, profile, prefix_length)
    if current == 0:
        return TraversalResult(epoch.actor_list_head, [], "null_head", 0, 0, 0.0)
    visited: set[int] = set()
    nodes: list[dict[str, Any]] = []
    request_count = 0
    bytes_read = 0
    started = time.perf_counter()
    while current:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > policy["maximum_duration_ms"]:
            raise ChainInvalid("actor traversal exceeded wall-clock safety limit")
        if current in visited:
            reason = "self-loop" if nodes and int(nodes[-1]["node_address"], 16) == current else "cycle"
            raise ChainInvalid(f"actor chain contains a {reason} at {_format_address(current)}")
        if len(nodes) >= policy["maximum_nodes"]:
            raise ChainInvalid("actor traversal reached node_limit")
        if request_count >= policy["maximum_requests"]:
            raise ChainInvalid("actor traversal reached request_limit")
        if bytes_read + prefix_length > policy["maximum_aggregate_bytes"]:
            raise ChainInvalid("actor traversal reached aggregate_byte_limit")
        validate_chain_pointer(current, profile, prefix_length)
        response = client.read_regions(
            [{"key": "actor_node", "addr": _format_address(current), "len": prefix_length}]
        )
        request_count += 1
        if response.get("stable_frame") is not True or response.get("stable_executable_state") is not True:
            raise SnapshotUnstable("node read crossed a frame or executable-state boundary")
        if response.get("executable_state_before") != epoch.executable_state_token:
            raise SnapshotUnstable("node read belongs to a different executable state")
        records = response.get("regions")
        if not isinstance(records, list) or len(records) != 1:
            raise ProtocolError("node read returned an invalid region count")
        record = records[0]
        if record.get("key") != "actor_node" or record.get("len") != prefix_length:
            raise ProtocolError("node read did not preserve the requested range")
        try:
            data = bytes.fromhex(record["hex"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError("node read returned malformed hex") from exc
        if len(data) != prefix_length:
            raise ChainInvalid("node read was truncated")
        visited.add(current)
        bytes_read += prefix_length
        next_value = int.from_bytes(data[policy["next_pointer_offset"] :][:4], "little")
        validate_chain_pointer(next_value, profile, prefix_length)
        decoded = decode_fields(data, profile)
        nodes.append(
            {
                "epoch_scoped_node_id": f"runtime://{epoch.epoch_id}/field-node/{current:08x}",
                "node_address": _format_address(current),
                "chain_index": len(nodes),
                "source_read_range": {"base": _format_address(current), "length": prefix_length},
                "next_pointer": pointer_metadata(next_value, profile, dereferenced=next_value != 0),
                "prefix_length": prefix_length,
                "decoded_fields": decoded,
                "unresolved_fields": [item["property"] for item in decoded if item["unresolved"]],
                "claims": [
                    {
                        "property": item["property"],
                        "confidence": item["confidence"],
                        "evidence": item["evidence"],
                        "notes": item["notes"],
                    }
                    for item in decoded
                ],
                "diagnostics": [],
            }
        )
        current = next_value
    return TraversalResult(
        epoch.actor_list_head,
        nodes,
        "null",
        request_count,
        bytes_read,
        (time.perf_counter() - started) * 1000.0,
    )
