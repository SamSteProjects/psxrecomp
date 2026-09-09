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
PROFILE_FILE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*-v[0-9]+\.json$")
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
    runtime_source = _need(executable, "runtime_source_identity", "$.executable_identity")
    if runtime_source.get("algorithm") != "sha256" or runtime_source.get("scope") != "ps-x-exe-body":
        _fail("$.executable_identity.runtime_source_identity contract is unsupported")
    source_digest = runtime_source.get("sha256")
    if not isinstance(source_digest, str) or not SHA256.fullmatch(source_digest):
        _fail("$.executable_identity.runtime_source_identity.sha256 is invalid")
    if not isinstance(runtime_source.get("length"), int) or runtime_source["length"] < 1:
        _fail("$.executable_identity.runtime_source_identity.length is invalid")
    _address(runtime_source.get("guest_base"), "$.executable_identity.runtime_source_identity.guest_base")
    _confidence(_need(runtime_source, "claim", "$.executable_identity.runtime_source_identity"), "$.executable_identity.runtime_source_identity.claim")

    protocol = _need(result, "supported_runtime_protocol", "$")
    if protocol.get("name") != "psxrecomp-debug":
        _fail("$.supported_runtime_protocol.name is unsupported")
    if protocol.get("required_runtime_implementation") != "psxrecomp":
        _fail("$.supported_runtime_protocol.required_runtime_implementation is unsupported")
    if protocol.get("minimum_major") != 1:
        _fail("$.supported_runtime_protocol.minimum_major must equal 1")
    if not isinstance(protocol.get("minimum_minor"), int) or protocol["minimum_minor"] < 1:
        _fail("$.supported_runtime_protocol.minimum_minor must be positive")
    capabilities = protocol.get("required_capabilities")
    if not isinstance(capabilities, list) or not capabilities or not all(isinstance(item, str) for item in capabilities):
        _fail("$.supported_runtime_protocol.required_capabilities must be nonempty strings")

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

    execution = _need(result, "execution_identity", "$")
    if execution.get("kind") != "field_execution_witness_set":
        _fail("$.execution_identity.kind is unsupported")
    witnesses = execution.get("required_witnesses")
    minimum = execution.get("minimum_required_witnesses")
    if not isinstance(witnesses, list) or len(witnesses) < 2:
        _fail("$.execution_identity.required_witnesses needs at least two witnesses")
    if not isinstance(minimum, int) or minimum < 2 or minimum > len(witnesses):
        _fail("$.execution_identity.minimum_required_witnesses is invalid")
    witness_ids: set[str] = set()
    witness_pcs: set[str] = set()
    for index, witness in enumerate(witnesses):
        path = f"$.execution_identity.required_witnesses[{index}]"
        wid = _need(witness, "id", path)
        pc = _need(witness, "pc", path)
        if not isinstance(wid, str) or not wid or wid in witness_ids:
            _fail(f"{path}.id is empty or duplicated")
        if pc in witness_pcs:
            _fail(f"{path}.pc duplicates execution witness {pc}")
        witness_ids.add(wid); witness_pcs.add(pc)
        pc_value = _address(pc, f"{path}.pc")
        if pc_value & 3:
            _fail(f"{path}.pc is not instruction aligned")
        if witness.get("backend") not in {"static-native", "cached-native", "runtime-native", "interpreter"}:
            _fail(f"{path}.backend is unsupported")
        span = _need(witness, "range", path)
        base = _address(_need(span, "base", f"{path}.range"), f"{path}.range.base")
        if span.get("kind") != "executed-instruction" or span.get("length") != 4 or base != pc_value:
            _fail(f"{path}.range is not the exact executed instruction")
        live_sha = witness.get("live_sha256")
        if not isinstance(live_sha, str) or not SHA256.fullmatch(live_sha):
            _fail(f"{path}.live_sha256 is invalid")
        if witness.get("require_current") is not True or witness.get("require_watched_generation_match") is not True:
            _fail(f"{path} must require current generation-matched evidence")

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
    if not set(epoch_signals).issubset(signal_ids | overlay_ids | {"field_execution_identity", "actor_list_head", "actor_census_base"}):
        _fail("$.scene_epoch references an unknown invalidation signal")

    policy = _need(result, "observation_policy", "$")
    guard = _need(policy, "guard", "$.observation_policy")
    expected_guard = {
        "capability": "observation_guard",
        "token_domain": "psxrecomp-observation-guard-v1",
        "ram_regions_from": "scene_identity.required_signals+actor_pool.linked_list_head",
        "execution_witnesses_from": "execution_identity.required_witnesses",
        "require_witness_currentness": True,
        "require_before_after_stability": True,
        "require_expected_token_match": True,
    }
    if guard != expected_guard:
        _fail("$.observation_policy.guard contract is unsupported")
    if "observation_guard" not in protocol.get("required_capabilities", []):
        _fail("$.supported_runtime_protocol must require observation_guard")
    head_policy = _need(policy, "head_pointer", "$.observation_policy")
    if (head_policy.get("width"), head_policy.get("type"), head_policy.get("endianness")) != (4, "ram_pointer", "little"):
        _fail("$.observation_policy.head_pointer encoding is unsupported")
    if head_policy.get("accepted_segments") != ["kseg0"] or head_policy.get("alignment") != 4:
        _fail("$.observation_policy.head_pointer rules are unsupported")
    traversal = _need(policy, "traversal", "$.observation_policy")
    if traversal.get("prefix_length") != read_size or traversal.get("next_pointer_offset") != 0:
        _fail("$.observation_policy.traversal must use the accepted actor prefix and next pointer")
    maximum_nodes = traversal.get("maximum_nodes")
    aggregate = traversal.get("maximum_aggregate_bytes")
    requests = traversal.get("maximum_requests")
    duration = traversal.get("maximum_duration_ms")
    if not isinstance(maximum_nodes, int) or not 1 <= maximum_nodes <= 4096:
        _fail("$.observation_policy.traversal.maximum_nodes is invalid")
    if not isinstance(aggregate, int) or aggregate < read_size or aggregate < maximum_nodes * read_size:
        _fail("$.observation_policy.traversal.maximum_aggregate_bytes is too small")
    if not isinstance(requests, int) or requests < maximum_nodes or requests > 4096:
        _fail("$.observation_policy.traversal.maximum_requests is invalid")
    if not isinstance(duration, int) or not 1 <= duration <= 60000:
        _fail("$.observation_policy.traversal.maximum_duration_ms is invalid")
    if traversal.get("partial_snapshots") != "reject":
        _fail("$.observation_policy.traversal must reject partial snapshots")
    _confidence(_need(traversal, "claim", "$.observation_policy.traversal"), "$.observation_policy.traversal.claim")
    snapshot = _need(policy, "snapshot", "$.observation_policy")
    if not isinstance(snapshot.get("stability_samples"), int) or snapshot["stability_samples"] < 2:
        _fail("$.observation_policy.snapshot.stability_samples is invalid")
    if not isinstance(snapshot.get("maximum_attempts"), int) or not 1 <= snapshot["maximum_attempts"] <= 10:
        _fail("$.observation_policy.snapshot.maximum_attempts is invalid")
    if snapshot.get("mixed_boundary_policy") != "discard":
        _fail("$.observation_policy.snapshot must discard mixed boundaries")

    _scan_metadata(result)
    try:
        validate_metadata_only(result)
    except Exception as exc:
        raise LayoutProfileError(str(exc)) from exc
    return result


def load_profile(path: str | Path) -> dict[str, Any]:
    """Load one metadata-only profile, resolving a single local base profile.

    A derived profile may change only scene-specific selection metadata and
    provenance.  The base reference is a filename, not an arbitrary path, so
    profile loading remains deterministic and cannot escape the layouts
    directory.  The returned document is always fully resolved and validated.
    """
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LayoutProfileError(f"cannot load layout profile: {exc}") from exc
    if not isinstance(value, Mapping) or "extends" not in value:
        return validate_profile(value)

    extension = value.get("extends")
    if not isinstance(extension, Mapping):
        _fail("$.extends must be an object")
    file_name = extension.get("file_name")
    base_id = extension.get("profile_id")
    if not isinstance(file_name, str) or not PROFILE_FILE_NAME.fullmatch(file_name):
        _fail("$.extends.file_name must be a safe revisioned profile filename")
    if not isinstance(base_id, str) or not PROFILE_ID.fullmatch(base_id):
        _fail("$.extends.profile_id is invalid")
    overrides = value.get("overrides")
    if not isinstance(overrides, Mapping):
        _fail("$.overrides must be an object")
    allowed = {"schema_version", "profile_id", "extends", "overrides"}
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        _fail("derived profile contains unsupported top-level fields: " + ", ".join(unexpected))

    base_path = source.parent / file_name
    try:
        base = json.loads(base_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LayoutProfileError(f"cannot load base layout profile: {exc}") from exc
    if not isinstance(base, Mapping) or "extends" in base:
        _fail("derived profile base must be one complete non-derived profile")
    base_validated = validate_profile(base)
    if base_validated["profile_id"] != base_id:
        _fail("derived profile base ID does not match the referenced profile")
    if value.get("schema_version") != base_validated["schema_version"]:
        _fail("derived profile schema version does not match its base")
    derived_id = value.get("profile_id")
    if not isinstance(derived_id, str) or not PROFILE_ID.fullmatch(derived_id):
        _fail("derived profile ID is not a stable versioned identifier")
    if derived_id == base_id:
        _fail("derived profile ID must differ from its base")
    if set(overrides) != {"scene_identity", "evidence", "unresolved"}:
        _fail("derived profile overrides must contain exactly scene_identity, evidence, unresolved")
    resolved = copy.deepcopy(base_validated)
    resolved["profile_id"] = derived_id
    resolved["scene_identity"] = copy.deepcopy(overrides["scene_identity"])
    resolved["evidence"] = copy.deepcopy(overrides["evidence"])
    resolved["unresolved"] = copy.deepcopy(overrides["unresolved"])
    return validate_profile(resolved)


def canonical_profile_json(profile: Mapping[str, Any]) -> str:
    validated = validate_profile(profile)
    return json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def profile_identity(profile: Mapping[str, Any]) -> str:
    return validate_profile(profile)["profile_id"]


def validate_observation_context(profile: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, int]:
    """Select a profile and validate one already-collected snapshot context.

    The function refuses profiles with unresolved required overlay identity.
    It returns only bounded addresses/counts; it never reads memory itself.
    """
    p = validate_profile(profile)
    exe = context.get("executable_identity", {})
    if exe.get("serial") != p["executable_identity"]["serial"]:
        _fail("runtime executable identity does not match profile")
    runtime_source = context.get("runtime_source_identity", {})
    expected_source = p["executable_identity"]["runtime_source_identity"]
    for key in ("algorithm", "scope", "length", "guest_base", "sha256"):
        if runtime_source.get(key) != expected_source.get(key):
            _fail("runtime executable source identity does not match profile")
    protocol = context.get("runtime_protocol", {})
    wanted = p["supported_runtime_protocol"]
    if protocol.get("name") != wanted["name"]:
        _fail("runtime protocol name does not match profile")
    major = protocol.get("major")
    minor = protocol.get("minor")
    if major != wanted["minimum_major"]:
        _fail("runtime protocol major is incompatible")
    if not isinstance(minor, int) or minor < wanted["minimum_minor"]:
        _fail("runtime protocol minor is too old")
    available = protocol.get("capabilities")
    if not isinstance(available, list):
        _fail("runtime protocol capabilities are missing")
    missing = sorted(set(wanted["required_capabilities"]) - set(available))
    if missing:
        _fail(f"runtime protocol capabilities are missing: {', '.join(missing)}")

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

    execution = p["execution_identity"]
    boundary = context.get("observation_boundary", {})
    if execution.get("require_stable_executable_state") and boundary.get("stable_executable_state") is not True:
        _fail("execution witness selection crossed an executable-state boundary")
    if execution.get("require_stable_lifecycle_state") and boundary.get("stable_lifecycle_state") is not True:
        _fail("execution witness selection crossed a lifecycle boundary")
    if execution.get("require_stable_observation_guard") and boundary.get("stable_observation_guard") is not True:
        _fail("execution witness selection crossed a scoped observation guard")
    observed_witnesses = {
        item.get("pc"): item for item in context.get("execution_witnesses", [])
        if isinstance(item, Mapping)
    }
    matched = 0
    for required in execution["required_witnesses"]:
        observed = observed_witnesses.get(required["pc"])
        if observed is None:
            _fail(f"required execution witness {required['pc']} is missing")
        if observed.get("status") == "ambiguous" or observed.get("backend") == "ambiguous":
            _fail(f"required execution witness {required['pc']} has ambiguous execution owner")
        if observed.get("observation_current") is not True or observed.get("status") != "current":
            _fail(f"required execution witness {required['pc']} is stale")
        if observed.get("backend") != required["backend"]:
            _fail(f"required execution witness {required['pc']} backend mismatch")
        observed_range = observed.get("range", {})
        required_range = required["range"]
        for key in ("kind", "base", "length"):
            if observed_range.get(key) != required_range.get(key):
                _fail(f"required execution witness {required['pc']} range {key} mismatch")
        if observed.get("live_sha256") != required["live_sha256"]:
            _fail(f"required execution witness {required['pc']} live identity mismatch")
        observed_generation = observed.get("watched_generation_at_observation")
        current_generation = observed.get("watched_generation_current")
        if not isinstance(observed_generation, str) or not observed_generation or observed_generation != current_generation:
            _fail(f"required execution witness {required['pc']} watched generation changed")
        matched += 1
    if matched < execution["minimum_required_witnesses"]:
        _fail("execution witness set is incomplete")

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
