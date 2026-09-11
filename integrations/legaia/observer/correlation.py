"""Guarded MAN binding evidence and conservative imported/runtime candidates.

A candidate is not a confirmed actor identity: another subclass can reuse +0x90,
and the MAN bank's relocation is not yet independently mapped. No address,
chain index, nearest position or +0x60 MAP object index becomes a content ID.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import time
from typing import Any, Mapping

from .errors import ProtocolError, SnapshotUnstable
from .profile import LoadedProfile, ProfileSelector, build_guard_descriptor

REFERENCE = "d6e64c68ede25813d35db20980da82a1a025549b"
SOURCE_EVIDENCE = [
    {"repository": "AndrewAltimit/legend-of-legaia-re", "revision": REFERENCE,
     "path": "docs/subsystems/script-vm.md", "symbol": "FUN_8003A1E4",
     "claim": "MAN P1 record base at actor+0x90; header follows 1 + 2*N locals."},
    {"repository": "AndrewAltimit/legend-of-legaia-re", "revision": REFERENCE,
     "path": "scripts/pcsx-redux/walk_actor_lists.py", "symbol": "actor+0x44",
     "claim": "Model object table starts with its object count."},
    {"repository": "AndrewAltimit/legend-of-legaia-re", "revision": REFERENCE,
     "path": "crates/web-viewer/src/field_npc.rs", "symbol": "build_npc_catalog_impl",
     "claim": "MAN model selector resolves scene pool or global pool at selector minus 0xF0."},
]
MAX_NODES = 128
BATCH_NODES = 6  # At most 30 read_regions entries, below the protocol cap of 32.
MAX_REQUESTS = 45  # One disc identity and two reads for each six-node batch.
MAX_BYTES = 4096
MAX_DURATION_MS = 4000
MAX_OBJECTS = 256


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _fields(node: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {field["property"]: field for field in node.get("decoded_fields", [])}


def _pointer(value: Any, length: int, *, aligned: bool = True) -> bool:
    return (type(value) is int and 0x80000000 <= value < 0x80200000 and
            (not aligned or value % 4 == 0) and value + length <= 0x80200000)


def _region(key: str, addr: int, length: int) -> dict:
    return {"key": key, "addr": f"0x{addr:08X}", "len": length}


def sample_man_bindings(client: Any, profile: LoadedProfile, observation: Mapping[str, Any]) -> dict:
    """Two bounded reads per six-node batch, under the unchanged field witness guard.

    Before/after pointer words, local count and model count must agree. Only
    five placement-header scalars and object count leave the sampler; no locals,
    scripts, model bytes or dereferenced memory payloads are exported.
    """
    epoch = observation["epoch"]
    chain = observation.get("actor_chain") or {}
    nodes = chain.get("nodes", [])
    if chain.get("traversal_complete") is not True or len(nodes) > 128:
        raise ProtocolError("binding sampling requires a complete bounded actor chain")
    descriptors = {field["id"]: field for field in profile.document["actor_fields"]}
    for name, offset in (("field_script_pointer", 144), ("model_object_table_pointer", 68)):
        field = descriptors.get(name, {})
        if field.get("offset") != offset or field.get("width") != 4:
            raise ProtocolError("profile does not support the pinned MAN binding hypothesis")
    if observation["profile"]["profile_hash"] != profile.profile_hash:
        raise SnapshotUnstable("binding profile differs from the accepted observation")
    result = {"available": True, "complete": True, "epoch_id": epoch["epoch_id"],
              "runtime_process_identity": epoch["runtime_process_identity"],
              "guard_token": epoch["observation_guard_token"], "profile_hash": profile.profile_hash,
              "scene_name": epoch["scene_name"], "first_frame": epoch["last_validated_frame"],
              "last_frame": epoch["last_validated_frame"], "nodes": [], "request_count": 0,
              "bytes_read": 0, "source_evidence": deepcopy(SOURCE_EVIDENCE),
              "bounds": {"nodes": MAX_NODES, "requests": MAX_REQUESTS, "bytes": MAX_BYTES,
                         "duration_ms": MAX_DURATION_MS}, "reason": None}
    started = time.monotonic()
    def budget(regions: list[dict]) -> None:
        if (result["request_count"] >= MAX_REQUESTS or
                result["bytes_read"] + sum(r["len"] for r in regions) > MAX_BYTES or
                (time.monotonic() - started) * 1000 >= MAX_DURATION_MS):
            raise SnapshotUnstable("MAN binding sampling exceeded its request/byte/time budget")
    def read(regions: list[dict]) -> dict[str, bytes]:
        budget(regions)
        response = client.read_regions(regions, guard=build_guard_descriptor(profile.document,
                                                        epoch["observation_guard_token"]))
        result["request_count"] += 1
        result["bytes_read"] += sum(r["len"] for r in regions)
        if (time.monotonic() - started) * 1000 > MAX_DURATION_MS:
            raise SnapshotUnstable("MAN binding sampling exceeded wall-clock budget")
        guard = ProfileSelector._require_guard(response)
        if (guard["token_before"] != epoch["observation_guard_token"] or
                guard.get("evidence", {}).get("runtime_instance_id") != epoch["runtime_process_identity"]):
            raise SnapshotUnstable("MAN binding read belongs to another epoch/session")
        before, after = response.get("frame_before"), response.get("frame_after")
        if type(before) is not int or type(after) is not int or before < result["last_frame"] or after < before:
            raise SnapshotUnstable("MAN binding frame moved backwards")
        result["last_frame"] = after
        records = response.get("regions")
        if response.get("payload_returned") is not True or not isinstance(records, list) or len(records) != len(regions):
            raise ProtocolError("MAN binding payload is unavailable or incomplete")
        decoded = {}
        for expected, record in zip(regions, records):
            if (record.get("key") != expected["key"] or record.get("len") != expected["len"] or
                    record.get("addr", "").lower() != expected["addr"].lower()):
                raise ProtocolError("MAN binding read changed the requested region")
            try:
                value = bytes.fromhex(record["hex"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError("malformed MAN binding payload") from exc
            if len(value) != expected["len"]:
                raise ProtocolError("truncated MAN binding payload")
            decoded[expected["key"]] = value
        return decoded
    # Disc identity is independent from the imported project and the EXE body.
    status = client.request("mod_status")
    result["request_count"] += 1
    budget([])
    identity = status.get("disc_identity", {})
    sha = identity.get("sha256")
    if (identity.get("available") is not True or identity.get("scope") != "committed-source-disc" or
            not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)):
        result.update(available=False, complete=False, reason="Committed runtime disc identity is unavailable")
        return result
    result["disc_identity"] = "sha256:" + sha
    pending = []
    for node in nodes:
        node_id = node["epoch_scoped_node_id"]
        record = {"runtime_node_id": node_id, "available": False, "reason": None}
        result["nodes"].append(record)
        address = int(node["node_address"], 16)
        if not _pointer(address, 148) or node_id != f"runtime://{epoch['epoch_id']}/field-node/{address:08x}":
            raise SnapshotUnstable("runtime node identity is outside the accepted epoch")
        fields = _fields(node)
        script = fields.get("field_script_pointer", {}).get("raw_numeric_value")
        model = fields.get("model_object_table_pointer", {}).get("raw_numeric_value")
        # MAN records are byte packed; nodes and u32 model tables are aligned.
        if not _pointer(script, 1, aligned=False) or not _pointer(model, 4):
            record["reason"] = "MAN record or model table pointer is unavailable/outside accepted RAM"
            continue
        pending.append((address, script, model, record))
    for offset in range(0, len(pending), BATCH_NODES):
        batch = pending[offset:offset + BATCH_NODES]
        regions = []
        for i, (address, script, model, record) in enumerate(batch):
            prefix = f"n{i}."
            regions.extend([_region(prefix + "script_pointer", address + 144, 4),
                            _region(prefix + "model_pointer", address + 68, 4),
                            _region(prefix + "local_count", script, 1),
                            _region(prefix + "object_count", model, 4)])
        before = read(regions)
        valid = []
        after_regions = []
        for i, (address, script, model, record) in enumerate(batch):
            prefix = f"n{i}."
            if (int.from_bytes(before[prefix + "script_pointer"], "little") != script or
                    int.from_bytes(before[prefix + "model_pointer"], "little") != model):
                raise SnapshotUnstable("actor binding pointers changed after actor capture")
            local_count = before[prefix + "local_count"][0]
            header = script + 1 + local_count * 2
            object_count = int.from_bytes(before[prefix + "object_count"], "little")
            if not _pointer(header, 4, aligned=False) or not 1 <= object_count <= MAX_OBJECTS:
                record["reason"] = "MAN header or model object count is outside the proven bounds"
                continue
            after_regions.extend(regions[i * 4:i * 4 + 4])
            after_regions.append(_region(prefix + "placement_header", header, 4))
            valid.append((prefix, local_count, object_count, record))
        if not after_regions:
            continue
        after = read(after_regions)
        for key in after:
            if key in before and before[key] != after[key]:
                raise SnapshotUnstable("actor binding metadata changed during sampling")
        for prefix, local_count, object_count, record in valid:
            model_index, animation_id, tile_x, tile_z = after[prefix + "placement_header"]
            record.update(available=True, local_count=local_count, model_index=model_index,
                          animation_id=animation_id, object_count=object_count,
                          model_pool="global_special" if model_index >= 0xF0 else "scene_tmd",
                          normalized_pool_index=model_index - 0xF0 if model_index >= 0xF0 else model_index,
                          placement_position={"x": (tile_x & 127) * 128 + 64 + (64 if tile_x & 128 else 0),
                                              "z": (tile_z & 127) * 128 + 64 + (64 if tile_z & 128 else 0)},
                          observed_frame=result["last_frame"],
                          unresolved=["MAN bank membership and actor subclass remain unproven"])
    result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
    return result


def unavailable(reason: str) -> dict:
    return {"available": False, "state": "unavailable", "reason": reason,
            "confirmed_match_count": 0, "candidate_count": 0, "entities": {},
            "runtime_nodes": [], "historical_observation": True}


def correlate(imported: Mapping[str, Any] | None, live_status: Mapping[str, Any],
              appearance_donors: Mapping[str, str] | None = None) -> dict:
    """Produce structural candidate groups; never promote unique guesses to identity."""
    if imported is None:
        return unavailable("No imported scene is active")
    observation = live_status.get("observation")
    binding = live_status.get("actor_bindings")
    if live_status.get("available") is not True or not isinstance(observation, Mapping) or not isinstance(binding, Mapping):
        return unavailable("Guarded actor and MAN binding observations are unavailable")
    if binding.get("available") is not True:
        return unavailable(binding.get("reason") or "MAN binding observations are unavailable")
    epoch = observation.get("epoch", {})
    profile = observation.get("profile", {})
    if (not epoch.get("epoch_id") or profile.get("selection", {}).get("accepted") is not True or
            observation.get("snapshot_current_at_capture") is not True or
            observation.get("boundaries", {}).get("stable") is not True or
            observation.get("actor_chain", {}).get("traversal_complete") is not True):
        return unavailable("Actor snapshot did not retain its profile and boundary acceptance")
    for key, wanted in (("epoch_id", epoch.get("epoch_id")),
                        ("runtime_process_identity", epoch.get("runtime_process_identity")),
                        ("guard_token", epoch.get("observation_guard_token")),
                        ("profile_hash", profile.get("profile_hash"))):
        if not wanted or binding.get(key) != wanted:
            return unavailable("Binding evidence belongs to a stale epoch/session/profile")
    if (type(binding.get("first_frame")) is not int or type(binding.get("last_frame")) is not int or
            binding["first_frame"] < epoch["last_validated_frame"] or binding["last_frame"] < binding["first_frame"]):
        return unavailable("Binding evidence has stale frame bounds")
    if imported["scene"]["name"] != epoch["scene_name"] or binding.get("scene_name") != epoch["scene_name"]:
        return unavailable("Observed scene differs from the imported scene")
    if binding.get("disc_identity") != imported["source"]["disc_identity"]:
        return unavailable("Observed disc identity differs from imported evidence")
    refs = imported["source"].get("reference_repositories", [])
    if not any(ref.get("repository") == "AndrewAltimit/legend-of-legaia-re" and ref.get("commit") == REFERENCE for ref in refs):
        return unavailable("Imported evidence does not retain the supported reference revision")
    actors = imported.get("actors", [])
    nodes = observation["actor_chain"].get("nodes", [])
    if len(actors) > 4096 or len(nodes) > 128 or len(binding.get("nodes", [])) > 128:
        return unavailable("Correlation collection bounds exceeded")
    node_lookup = {node["epoch_scoped_node_id"]: node for node in nodes}
    if len(node_lookup) != len(nodes):
        return unavailable("Runtime node identities are duplicated")
    appearance_donors = dict(appearance_donors or {})
    actor_lookup = {actor["semantic_id"]: actor for actor in actors}
    if any(target not in actor_lookup or donor not in actor_lookup
           for target, donor in appearance_donors.items()):
        return unavailable("Appearance donor is outside the imported scene")
    models = {model["semantic_id"]: model for model in imported.get("assets", {}).get("models", [])}
    entries = {actor["semantic_id"]: {"status": "unmatched", "binding_confirmed": False,
                "candidates": [], "reason": "No independently compatible MAN/model evidence"} for actor in actors}
    result = {"available": True, "state": "candidates", "reason": None,
              "confirmed_match_count": 0, "candidate_count": 0, "entities": entries,
              "runtime_nodes": [], "epoch_id": epoch["epoch_id"],
              "runtime_process_identity": epoch["runtime_process_identity"],
              "profile_hash": profile["profile_hash"], "guard_token": epoch["observation_guard_token"],
              "scene_name": epoch["scene_name"], "disc_identity": binding["disc_identity"],
              "import_digest": _digest(imported), "appearance_donors": deepcopy(appearance_donors), "frame": binding["last_frame"],
              "complete": binding.get("complete") is True, "historical_observation": True,
              "source_evidence": deepcopy(SOURCE_EVIDENCE)}
    seen = set()
    for observed in binding.get("nodes", []):
        node_id = observed.get("runtime_node_id")
        if node_id not in node_lookup or node_id in seen:
            return unavailable("Binding evidence contains unknown or duplicate runtime nodes")
        seen.add(node_id)
        node_fields = _fields(node_lookup[node_id])
        runtime_entry = {"runtime_node_id": node_id, "candidate_entity_ids": [],
                         "reason": observed.get("reason"), "binding_confirmed": False,
                         "observed_position": {axis: node_fields.get("position_" + axis, {}).get("interpreted_value") for axis in ("x", "y", "z")},
                         "epoch_id": epoch["epoch_id"], "frame": node_lookup[node_id].get("position_capture_frames", {}).get("after"),
                         "position_capture_frames": deepcopy(node_lookup[node_id].get("position_capture_frames"))}
        result["runtime_nodes"].append(runtime_entry)
        if observed.get("available") is not True:
            continue
        if (any(type(observed.get(key)) is not int or not 0 <= observed[key] <= 255
                for key in ("model_index", "animation_id", "local_count")) or
                type(observed.get("object_count")) is not int or not 1 <= observed["object_count"] <= MAX_OBJECTS):
            return unavailable("Binding evidence contains invalid structural values")
        if (type(observed.get("observed_frame")) is not int or
                not binding["first_frame"] <= observed["observed_frame"] <= binding["last_frame"]):
            return unavailable("Binding evidence contains stale per-node frame bounds")
        runtime_entry["binding_evidence"] = deepcopy(observed)
        for actor in actors:
            actor_id = actor["semantic_id"]
            donor_id = appearance_donors.get(actor_id, actor_id)
            variants = [("imported", actor), ("effective", actor_lookup[donor_id])]
            matching_layers = []
            for layer, appearance_actor in variants:
                ref = appearance_actor["model_reference"]
                asset = models.get(ref.get("asset_semantic_id"), {})
                if (actor.get("source_record", {}).get("record_kind") != "man_partition_1_actor_placement" or
                        ref.get("resolution_status") != "resolved" or
                        ref.get("model_index") != observed.get("model_index") or
                        ref.get("model_pool") != observed.get("model_pool") or
                        ref.get("normalized_pool_index") != observed.get("normalized_pool_index") or
                        actor["placement_fields"].get("local_count") != observed.get("local_count") or
                        appearance_actor["placement_fields"].get("animation_id") != observed.get("animation_id") or
                        asset.get("source_record", {}).get("object_count") != observed.get("object_count")):
                    continue
                matching_layers.append(layer)
            if not matching_layers:
                continue
            position = actor["imported_transform"]["position"]
            placement_agrees = all(position.get(axis) == observed["placement_position"][axis] for axis in ("x", "z"))
            live_fields = _fields(node_lookup[node_id])
            observed_position = {axis: live_fields.get("position_" + axis, {}).get("interpreted_value") for axis in ("x", "y", "z")}
            candidate = {"runtime_node_id": node_id, "confidence": "supported_candidate",
                         "appearance_layers": matching_layers,
                         "effective_donor_id": donor_id if "effective" in matching_layers else None,
                         "epoch_id": epoch["epoch_id"], "frame": observed["observed_frame"],
                         "position_capture_frames": deepcopy(node_lookup[node_id].get("position_capture_frames")),
                         "evidence": ["MAN model selector and pool", "MAN animation selector", "MAN local-count prefix",
                                      "independent runtime model object count"],
                         "placement_header_agrees_with_import": placement_agrees,
                         "placement_position": deepcopy(observed["placement_position"]),
                         "observed_position": observed_position,
                         "unresolved": ["Actor subclass and MAN bank membership are not proven",
                                        "No address or list-order identity is assumed"]}
            entries[actor_id]["candidates"].append(candidate)
            runtime_entry["candidate_entity_ids"].append(actor_id)
            result["candidate_count"] += 1
    # Many-to-many ambiguity is retained even when one side has a single link.
    multiplicity = {item["runtime_node_id"]: len(item["candidate_entity_ids"]) for item in result["runtime_nodes"]}
    for entry in entries.values():
        entry["candidates"].sort(key=lambda item: item["runtime_node_id"])
        if entry["candidates"]:
            ambiguous = len(entry["candidates"]) > 1 or any(multiplicity[item["runtime_node_id"]] > 1 for item in entry["candidates"])
            entry.update(status="ambiguous" if ambiguous else "candidate",
                         reason="Structural compatibility is not a confirmed identity binding")
    result["runtime_nodes"].sort(key=lambda item: item["runtime_node_id"])
    return result
