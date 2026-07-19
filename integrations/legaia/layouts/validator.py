"""Fail-closed validation for metadata-only Legaia runtime layout profiles.

This module deliberately contains no TCP client and performs no guest-memory
access. It validates profile documents and already-collected synthetic runtime
contexts so a later observer can share the same selection and bounds contract.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Mapping

from integrations.legaia.importer.core import validate_metadata_only


class LayoutProfileError(ValueError):
    """A profile or runtime context failed a fail-closed check."""


CONFIDENCE = {"confirmed", "strongly_inferred", "tentative", "unknown", "contradictory"}
HEX32 = re.compile(r"^0x[0-9A-Fa-f]{8}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*-v[0-9]+$")
FORBIDDEN_PROFILE_KEYS = {
    "bytes",
    "dialogue",
    "disc_path",
    "executable_bytes",
    "payload",
    "ram_dump",
    "raw_bytes",
    "save_state",
    "sectors",
}


def _fail(message: str) -> None:
    raise LayoutProfileError(message)


def _need(mapping: Mapping[str, Any], key: str, path: str) -> Any:
    if key not in mapping:
        _fail(f"{path}.{key} is required")
    return mapping[key]


def _address(value: Any, path: str) -> int:
    if not isinstance(value, str) or not HEX32.fullmatch(value):
        _fail(f"{path} must be an eight-digit hexadecimal address")
    return int(value, 16)


def _confidence(claim: Mapping[str, Any], path: str) -> str:
    value = _need(claim, "confidence", path)
    if value not in CONFIDENCE:
        _fail(f"{path}.confidence is invalid")
    if value == "unknown" and claim.get("value") is not None:
        _fail(f"{path} marks a non-null value unknown")
    if value == "contradictory" and len(claim.get("alternatives", [])) < 2:
        _fail(f"{path} contradictory claim needs at least two alternatives")
    return value


def _scan_metadata(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_PROFILE_KEYS:
                _fail(f"metadata-only profile contains forbidden field {path}.{key}")
            _scan_metadata(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_metadata(child, f"{path}[{index}]")


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a defensive copy of a profile document."""
    if not isinstance(profile, Mapping):
        _fail("profile must be an object")
    result = copy.deepcopy(dict(profile))
    if result.get("schema_version") != 1:
        _fail("$.schema_version must equal 1")
    profile_id = _need(result, "profile_id", "$")
    if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
        _fail("$.profile_id is not a stable versioned identifier")

    executable = _need(result, "executable_identity", "$")
    if executable.get("serial") != "SCUS-94254":
        _fail("$.executable_identity.serial is unsupported")
    digest = executable.get("sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        _fail("$.executable_identity.sha256 must be a lowercase SHA-256")

    protocol = _need(result, "supported_runtime_protocol", "$")
    if protocol.get("name") != "psxrecomp-json-tcp":
        _fail("$.supported_runtime_protocol.name is unsupported")
    if not isinstance(protocol.get("minimum_version"), int) or protocol["minimum_version"] < 1:
        _fail("$.supported_runtime_protocol.minimum_version must be positive")

    bounds = _need(result, "safety_bounds", "$")
    ram_start = _address(_need(bounds, "main_ram_start", "$.safety_bounds"), "$.safety_bounds.main_ram_start")
    ram_end = _address(_need(bounds, "main_ram_end_exclusive", "$.safety_bounds"), "$.safety_bounds.main_ram_end_exclusive")
    if ram_start >= ram_end:
        _fail("$.safety_bounds main RAM range is empty")
    max_read = bounds.get("maximum_read_bytes")
    if not isinstance(max_read, int) or not 1 <= max_read <= ram_end - ram_start:
        _fail("$.safety_bounds.maximum_read_bytes is invalid")

    overlays = _need(result, "overlay_requirements", "$")
    if not isinstance(overlays, list) or not overlays:
        _fail("$.overlay_requirements must be nonempty")
    overlay_ids: set[str] = set()
    for index, overlay in enumerate(overlays):
        path = f"$.overlay_requirements[{index}]"
        identity = _need(overlay, "identity", path)
        oid = _need(identity, "id", f"{path}.identity")
        if oid in overlay_ids:
            _fail(f"{path} duplicates overlay identity {oid}")
        overlay_ids.add(oid)
        _address(_need(identity, "load_address", f"{path}.identity"), f"{path}.identity.load_address")
        sha = identity.get("content_sha256")
        if sha is not None and (not isinstance(sha, str) or not SHA256.fullmatch(sha)):
            _fail(f"{path}.identity.content_sha256 is invalid")
        _confidence(_need(overlay, "claim", path), f"{path}.claim")

    scene = _need(result, "scene_identity", "$")
    signals = _need(scene, "required_signals", "$.scene_identity")
    if not isinstance(signals, list) or not signals:
        _fail("$.scene_identity.required_signals must be nonempty")
    signal_ids: set[str] = set()
    for index, signal in enumerate(signals):
        path = f"$.scene_identity.required_signals[{index}]"
        sid = _need(signal, "id", path)
        if sid in signal_ids:
            _fail(f"{path} duplicates scene signal {sid}")
        signal_ids.add(sid)
        _address(_need(signal, "address", path), f"{path}.address")
        if signal.get("width") not in {1, 2, 4, 8, 16}:
            _fail(f"{path}.width is invalid")
        _confidence(_need(signal, "claim", path), f"{path}.claim")

    pool = _need(result, "actor_pool", "$")
    if pool.get("storage_kind") != "linked_nodes_with_pointer_census":
        _fail("$.actor_pool.storage_kind is unsupported")
    census = _need(pool, "pointer_census", "$.actor_pool")
    census_base = _address(_need(census, "base_address", "$.actor_pool.pointer_census"), "$.actor_pool.pointer_census.base_address")
    pointer_stride = census.get("entry_stride")
    maximum_slots = census.get("maximum_slots")
    if pointer_stride != 4:
        _fail("$.actor_pool.pointer_census.entry_stride must be 4")
    if not isinstance(maximum_slots, int) or not 1 <= maximum_slots <= 4096:
        _fail("$.actor_pool.pointer_census.maximum_slots is invalid")
    census_end = census_base + pointer_stride * maximum_slots
    if census_base < ram_start or census_end > 0x1_0000_0000 or census_end > ram_end:
        _fail("$.actor_pool pointer census overflows address space or RAM")
    count = _need(census, "count", "$.actor_pool.pointer_census")
    _address(_need(count, "address", "$.actor_pool.pointer_census.count"), "$.actor_pool.pointer_census.count.address")
    if count.get("width") not in {1, 2, 4}:
        _fail("$.actor_pool.pointer_census.count.width is invalid")
    list_head = _need(pool, "linked_list_head", "$.actor_pool")
    _address(_need(list_head, "address", "$.actor_pool.linked_list_head"), "$.actor_pool.linked_list_head.address")

    record = _need(pool, "actor_record", "$.actor_pool")
    read_size = record.get("bounded_read_size")
    if not isinstance(read_size, int) or not 1 <= read_size <= max_read:
        _fail("$.actor_pool.actor_record.bounded_read_size is invalid")
    if record.get("contiguous_stride") is not None:
        _fail("$.actor_pool.actor_record.contiguous_stride must remain null for linked nodes")

    fields = _need(result, "actor_fields", "$")
    if not isinstance(fields, list) or not fields:
        _fail("$.actor_fields must be nonempty")
    field_ids: set[str] = set()
    field_offsets: set[int] = set()
    for index, field in enumerate(fields):
        path = f"$.actor_fields[{index}]"
        fid = _need(field, "id", path)
        if fid in field_ids:
            _fail(f"{path} duplicates field id {fid}")
        field_ids.add(fid)
        offset = field.get("offset")
        width = field.get("width")
        if not isinstance(offset, int) or offset < 0:
            _fail(f"{path}.offset is invalid")
        if offset in field_offsets:
            _fail(f"{path}.offset duplicates 0x{offset:X}")
        field_offsets.add(offset)
        if width not in {1, 2, 4} or offset + width > read_size:
            _fail(f"{path} falls outside the bounded actor prefix")
        _confidence(_need(field, "claim", path), f"{path}.claim")

    epoch = _need(result, "scene_epoch", "$")
    epoch_signals = epoch.get("invalidation_signals")
    if not isinstance(epoch_signals, list) or not epoch_signals:
        _fail("$.scene_epoch.invalidation_signals must be nonempty")
    if not set(epoch_signals).issubset(signal_ids | overlay_ids | {"actor_list_head", "actor_census_base"}):
        _fail("$.scene_epoch references an unknown invalidation signal")

    _scan_metadata(result)
    try:
        validate_metadata_only(result)
    except Exception as exc:
        raise LayoutProfileError(str(exc)) from exc
    return result


def load_profile(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LayoutProfileError(f"cannot load layout profile: {exc}") from exc
    return validate_profile(value)


def canonical_profile_json(profile: Mapping[str, Any]) -> str:
    validated = validate_profile(profile)
    return json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def profile_identity(profile: Mapping[str, Any]) -> str:
    return validate_profile(profile)["profile_id"]


def _parse_version(value: Any, path: str) -> int:
    if not isinstance(value, int) or value < 1:
        _fail(f"{path} must be a positive integer")
    return value


def validate_observation_context(profile: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, int]:
    """Select a profile and validate one already-collected snapshot context.

    The function refuses profiles with unresolved required overlay identity.
    It returns only bounded addresses/counts; it never reads memory itself.
    """
    p = validate_profile(profile)
    exe = context.get("executable_identity", {})
    if exe.get("serial") != p["executable_identity"]["serial"] or exe.get("sha256") != p["executable_identity"]["sha256"]:
        _fail("runtime executable identity does not match profile")
    protocol = context.get("runtime_protocol", {})
    wanted = p["supported_runtime_protocol"]
    if protocol.get("name") != wanted["name"]:
        _fail("runtime protocol name does not match profile")
    if _parse_version(protocol.get("version"), "$.runtime_protocol.version") < wanted["minimum_version"]:
        _fail("runtime protocol version is too old")

    observed_overlays = {item.get("id"): item for item in context.get("overlays", [])}
    for requirement in p["overlay_requirements"]:
        identity = requirement["identity"]
        if not requirement.get("required", True):
            continue
        if identity.get("content_sha256") is None:
            _fail(f"required overlay identity {identity['id']} is unresolved in profile")
        observed = observed_overlays.get(identity["id"])
        if observed is None:
            _fail(f"required overlay {identity['id']} is absent")
        for key in ("load_address", "content_sha256"):
            if observed.get(key) != identity.get(key):
                _fail(f"required overlay {identity['id']} {key} mismatch")

    observed_signals = context.get("scene_signals", {})
    for signal in p["scene_identity"]["required_signals"]:
        if signal["id"] not in observed_signals:
            _fail(f"required scene signal {signal['id']} is missing")
        if observed_signals[signal["id"]] != signal.get("expected"):
            _fail(f"required scene signal {signal['id']} does not identify the profiled scene")

    pool = p["actor_pool"]["pointer_census"]
    base = _address(pool["base_address"], "$.actor_pool.pointer_census.base_address")
    count = context.get("actor_count")
    if not isinstance(count, int) or count < 0 or count > pool["maximum_slots"]:
        _fail("actor count is outside the profiled maximum")
    stride = pool["entry_stride"]
    end = base + count * stride
    bounds = p["safety_bounds"]
    ram_start = _address(bounds["main_ram_start"], "$.safety_bounds.main_ram_start")
    ram_end = _address(bounds["main_ram_end_exclusive"], "$.safety_bounds.main_ram_end_exclusive")
    if base < ram_start or end < base or end > ram_end:
        _fail("actor pointer census is outside main RAM")
    return {"actor_census_base": base, "actor_count": count, "actor_pointer_bytes": count * stride}


def establish_epoch(profile: Mapping[str, Any], before: Mapping[str, Any], after: Mapping[str, Any], observer_epoch: int) -> dict[str, Any]:
    """Create an observer-side epoch only when two boundary samples agree."""
    p = validate_profile(profile)
    if not isinstance(observer_epoch, int) or observer_epoch < 1:
        _fail("observer epoch must be a positive integer")
    keys = p["scene_epoch"]["invalidation_signals"]
    for key in keys:
        if key not in before or key not in after:
            _fail(f"scene epoch signal {key} is missing")
        if before[key] != after[key]:
            _fail(f"mixed scene epoch: {key} changed during snapshot")
    return {
        "observer_epoch": observer_epoch,
        "profile_id": p["profile_id"],
        "first_stable_frame": after.get("frame"),
        "signals": {key: after[key] for key in keys},
    }
