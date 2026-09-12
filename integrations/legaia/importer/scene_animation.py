"""Scene actor poses from the MAN header's actual scene ANM association.

Reference pin: pipeline.REFERENCE_COMMIT, asset/{man_section,player_anm}.rs,
web-viewer/field_npc.rs. A nonzero placement animation byte names scene ANM
record byte-1 for scene models. Zero IDs and global model banks are not guessed.
This is imported spawn-pose evidence, not current runtime script state.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

from .animation import (MAX_POSED_VERTICES, _bounds, animation_record_ranges,
                        decode_animation_record, pose_vertices)
from .assets import load_model_preview
from .core import ImportError, decompress_lzs, find_scene_bundle
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context, import_scene


def actor_animation_capabilities(actor: dict, asset: dict) -> dict:
    """Cheap header association advertisement; catalog loading verifies sources."""
    reason = None
    reference = actor.get("model_reference", {})
    animation_id = actor.get("placement_fields", {}).get("animation_id")
    model_index = reference.get("model_index")
    if reference.get("asset_semantic_id") != asset.get("semantic_id") or asset.get("asset_kind") != "tmd_model":
        reason = "Actor does not resolve to the supplied imported model."
    elif type(model_index) is not int or not 0 <= model_index < 0xF0:
        reason = "Global model banks require their separate evidenced animation association."
    elif type(animation_id) is not int or not 1 <= animation_id <= 255:
        reason = "The MAN placement header has no supported nonzero scene animation ID."
    return {"supported": reason is None,
            "clips": [{"id": "placement", "label": f"Imported animation {animation_id}",
                       "record_index": animation_id - 1}] if reason is None else [],
            "reason": reason, "evidence": "man_header_initial_animation_not_runtime_script_state"}


class SceneActorAnimationCatalog:
    """Private request-scoped verified source snapshot with bounded model caches.

    Create with load_scene_actor_animation_catalog. Reuse across one scene
    viewport request; do not treat this object as a live-disc monitor.
    """
    def __init__(self, disc, scene, document, body, source):
        self._disc, self.scene, self._body, self._source = disc, scene, body, source
        self._actors = {a["semantic_id"]: a for a in document["actors"]}
        self._assets = {a["semantic_id"]: a for a in document["assets"]["models"]}
        self._ranges = animation_record_ranges(body)
        self._decoded = {}
        self._models = {}
        self._cached_vertices = 0
        self._cached_triangles = 0

    def _binding(self, actor, asset):
        support = actor_animation_capabilities(actor, asset)
        if not support["supported"]:
            raise ImportError(support["reason"])
        expected_actor = self._actors.get(actor.get("semantic_id"))
        expected_asset = self._assets.get(asset.get("semantic_id"))
        if (expected_actor is None or expected_asset is None or
                any(actor.get(key) != expected_actor[key] for key in
                    ("source_record", "model_reference", "placement_fields")) or
                asset.get("source_record") != expected_asset["source_record"]):
            raise ImportError("actor/model animation provenance does not match the freshly imported scene")
        index = actor["placement_fields"]["animation_id"] - 1
        if not 0 <= index < len(self._ranges):
            raise ImportError("MAN animation ID is outside the scene ANM record bank")
        if index not in self._decoded:
            start, end = self._ranges[index]
            self._decoded[index] = decode_animation_record(self._body[start:end])
        decoded = self._decoded[index]
        if decoded["bone_count"] != expected_asset["source_record"]["object_count"]:
            raise ImportError("scene animation channel count does not match the actor model's object count")
        return index, decoded

    def source_bank(self) -> tuple[bytes, dict]:
        """Immutable verified bank for other scene consumers, with copied provenance."""
        return self._body, deepcopy(self._source)

    def capabilities(self, actor: dict, asset: dict) -> dict:
        """Validate the binding and wire record without loading triangle geometry."""
        try:
            index, decoded = self._binding(actor, asset)
        except ImportError as exc:
            return dict(supported=False, clips=[], reason=str(exc))
        return dict(supported=True, clips=[dict(id="placement", label=f"Imported animation {index + 1}",
                    record_index=index, frame_count=decoded["frame_count"], bone_count=decoded["bone_count"])],
                    reason=None, evidence="verified_man_header_initial_animation_not_runtime_script_state")

    def referenced_animation_metadata(self) -> dict:
        """Bounded imported MAN bindings, without geometry or decoded frames.

        Resource incompatibilities stay explicit; an unreferenced ANM table
        record is not advertised as a compatible actor animation.
        """
        if len(self._actors) > 512:
            raise ImportError("animation catalog exceeds the 512 actor binding bound")
        bindings, unavailable = [], []
        for identifier, actor in sorted(self._actors.items()):
            asset = self._assets.get(actor.get("model_reference", {}).get("asset_semantic_id"), {})
            try:
                index, decoded = self._binding(actor, asset)
            except ImportError as exc:
                unavailable.append({"actor_semantic_id": identifier, "reason": str(exc)})
                continue
            metadata = self._metadata(actor, asset, index, decoded)
            start, end = self._ranges[index]
            metadata["source_record"]["record_sha256"] = hashlib.sha256(self._body[start:end]).hexdigest()
            bindings.append(metadata)
        return {"scene": self.scene, "source_record": deepcopy(self._source),
                "scene_anm_record_count": len(self._ranges), "actor_count": len(self._actors),
                "bindings": bindings, "unavailable_bindings": unavailable}

    def _geometry(self, asset, decoded):
        identity = asset["semantic_id"]
        if identity not in self._models:
            geometry = load_model_preview(self._disc, asset)
            if len(geometry["objects"]) != decoded["bone_count"]:
                raise ImportError("decoded scene model object count does not match animation channels")
            if (self._cached_vertices + len(geometry["vertices"]) > MAX_POSED_VERTICES or
                    self._cached_triangles + len(geometry["triangles"]) > MAX_POSED_VERTICES):
                raise ImportError("scene model cache exceeds the bounded geometry budget")
            self._cached_vertices += len(geometry["vertices"])
            self._cached_triangles += len(geometry["triangles"])
            self._models[identity] = geometry
        return deepcopy(self._models[identity])

    def _metadata(self, actor, asset, index, decoded):
        start, end = self._ranges[index]
        source = dict(deepcopy(self._source), record_index=index, byte_offset=start, byte_length=end - start,
                      containing_size=len(self._body), byte_coordinate_space=("raw_scene_anm_chunk" if self._source.get('source_kind') == 'raw_streaming_anm' else "decoded_scene_anm_descriptor"))
        skeleton_id = "skeleton://" + asset["semantic_id"].removeprefix("asset://")
        return {
            "schema_version": "legaia.animation-preview.v1",
            "semantic_id": f"animation://{self.scene}/scene-anm/{index:04d}",
            "asset_semantic_id": asset["semantic_id"], "actor_semantic_id": actor["semantic_id"],
            "clip_id": "placement", "label": f"Imported animation {index + 1}",
            "reference_commit": REFERENCE_COMMIT, "source_record": source,
            "frame_count": decoded["frame_count"], "bone_count": decoded["bone_count"],
            "header_a": decoded["header_a"], "header_flags": decoded["header_flags"],
            "coordinate_system": "retail_psx_actor_local_y_down", "looping": None,
            "timing": {"fps": None, "wire_rate": None, "evidence": "unresolved_scene_actor_playback_rate",
                       "note": "This record has no rate byte; a viewer may choose an explicit preview rate."},
            "association": {"kind": "verified_man_header_scene_anm_record_plus_one",
                            "animation_id": index + 1, "actor_source_record": deepcopy(actor["source_record"]),
                            "active_object_indices": list(range(decoded["bone_count"]))},
            "skeleton": {"semantic_id": skeleton_id, "topology": "independent_rigid_objects", "hierarchy": None,
                         "channels": [{"semantic_id": f"{skeleton_id}/channels/{i:02d}",
                                       "object_index": i, "parent_index": None} for i in range(decoded["bone_count"])]},
            "limitations": ["Imported header association; scripts can later change model, clip, location and facing.",
                            "Actor world height and facing are unresolved and are not baked into this local pose.",
                            "Analytic rigid transforms approximate GTE fixed-point rounding.",
                            "No anatomical joint hierarchy or scene actor playback cadence is inferred."],
        }

    def animation_preview(self, actor: dict, asset: dict) -> dict:
        index, decoded = self._binding(actor, asset)
        return self._animation_preview(actor, asset, index, decoded)

    def channel_values(self, actor: dict, asset: dict, frame_index: int, object_index: int,
                       overrides: dict[str, dict] | None = None) -> dict:
        """Return one source channel without loading geometry or expanding poses."""
        index, decoded = self._binding(actor, asset)
        if type(frame_index) is not int or not 0 <= frame_index < decoded["frame_count"]:
            raise ImportError("Animation frame is outside the imported clip")
        if type(object_index) is not int or not 0 <= object_index < decoded["bone_count"]:
            raise ImportError("Animation object is outside the imported clip")
        channel = decoded["frames"][frame_index]["object_transforms"][object_index]
        start, end = self._ranges[index]
        result = {"frame_index": frame_index, "object_index": object_index,
                "source_record_sha256": hashlib.sha256(self._body[start:end]).hexdigest(),
                "retail": {field: dict(zip("xyz", channel[field])) for field in ("translation", "rotation_psx")}}
        result["effective"] = deepcopy(result["retail"])
        result["contributors"] = []
        if overrides:
            bank, _audit = self.authored_bank(overrides)
            effective = decode_animation_record(bank[start:end])["frames"][frame_index]["object_transforms"][object_index]
            result["effective"] = {field: dict(zip("xyz", effective[field])) for field in ("translation", "rotation_psx")}
            result["effective_record_sha256"] = hashlib.sha256(bank[start:end]).hexdigest()
            clip = f"animation://{self.scene}/scene-anm/{index:04d}"
            result["contributors"] = sorted(owner for owner, value in overrides.items()
                                             if value["animation_id"] == clip and any(
                                                 e["frame_index"] == frame_index and e["object_index"] == object_index
                                                 for e in value["edits"]))
        return result

    def authored_bank(self, overrides: dict[str, dict]) -> tuple[bytes, list[dict]]:
        """Compose shared clip edits, rejecting contradictory writes to one axis."""
        from .animation_authoring import patch_animation_channels
        grouped = {}
        for identifier, override in sorted(overrides.items()):
            actor = self._actors[identifier]
            asset = self._assets[actor["model_reference"]["asset_semantic_id"]]
            index, _ = self._binding(actor, asset)
            if override["animation_id"] != f"animation://{self.scene}/scene-anm/{index:04d}":
                raise ImportError("Authored clip differs from the imported actor binding")
            self.authored_animation_record(actor, asset, override["edits"], override["source_record_sha256"])
            group = grouped.setdefault(index, {"axes": {}, "owners": []})
            group["owners"].append(identifier)
            for edit in override["edits"]:
                for field in ("translation", "rotation_psx"):
                    for axis, value in edit.get(field, {}).items():
                        key = (edit["frame_index"], edit["object_index"], field, axis)
                        if key in group["axes"] and group["axes"][key] != value:
                            raise ImportError(
                                f"Conflicting shared animation {index:04d}, frame {key[0]}, object {key[1]}, "
                                f"{field}.{axis}: {identifier} requests {value}; another actor requests {group['axes'][key]}. "
                                "Clear or align that channel contribution before applying.")
                        group["axes"][key] = value
        result, audit = bytearray(self._body), []
        for index, group in sorted(grouped.items()):
            edits = {}
            for (frame, obj, field, axis), value in sorted(group["axes"].items()):
                edit = edits.setdefault((frame, obj), {"frame_index": frame, "object_index": obj})
                edit.setdefault(field, {})[axis] = value
            start, end = self._ranges[index]
            original = self._body[start:end]
            changed, changes = patch_animation_channels(original, hashlib.sha256(original).hexdigest(), list(edits.values()))
            result[start:end] = changed
            for change in changes:
                audit.append({**change, "animation_id": f"animation://{self.scene}/scene-anm/{index:04d}",
                              "animation_record_offset": start, "authored_owners": group["owners"],
                              "scope": "shared-scene-animation-record"})
        allowed = {offset for row in audit for offset in range(
            row["animation_record_offset"] + row["channel_byte_offset"],
            row["animation_record_offset"] + row["channel_byte_offset"] + 8)}
        if len(result) != len(self._body) or any(a != b and i not in allowed
                                               for i, (a, b) in enumerate(zip(self._body, result))):
            raise ImportError("Animation composition changed bytes outside audited channels")
        return bytes(result), audit

    def authored_bank_preview(self, actor: dict, asset: dict, overrides: dict[str, dict]) -> dict:
        """Preview the same composed shared bank that enters the build."""
        index, _ = self._binding(actor, asset)
        changed, audit = self.authored_bank(overrides)
        start, end = self._ranges[index]
        preview = self._animation_preview(actor, asset, index, decode_animation_record(changed[start:end]))
        preview["representation"] = "authored"
        animation_id = f"animation://{self.scene}/scene-anm/{index:04d}"
        preview["authored"] = {"animation_id": animation_id,
                               "source_record_sha256": hashlib.sha256(self._body[start:end]).hexdigest(),
                               "effective_record_sha256": hashlib.sha256(changed[start:end]).hexdigest(),
                               "changes": [row for row in audit if row["animation_id"] == animation_id],
                               "scope": "shared-scene-animation-record"}
        return preview

    def authored_animation_record(self, actor: dict, asset: dict, edits: list[dict],
                                  expected_record_sha256: str) -> tuple[bytes, dict]:
        """Validate a binding and serialize its record without expanding posed meshes.

        Returned bytes are private build material. The metadata contains source
        identity and an audit suitable for project validation or packaging.
        """
        from .animation_authoring import patch_animation_channels
        index, _ = self._binding(actor, asset)
        start, end = self._ranges[index]
        changed, audit = patch_animation_channels(self._body[start:end], expected_record_sha256, edits)
        return changed, {"animation_id": f"animation://{self.scene}/scene-anm/{index:04d}",
                         "source_record_sha256": expected_record_sha256,
                         "effective_record_sha256": hashlib.sha256(changed).hexdigest(),
                         "byte_offset": start, "byte_length": end - start,
                         "byte_coordinate_space": "decoded_scene_anm_descriptor",
                         "changes": audit, "scope": "existing_rigid_channels"}

    def authored_animation_preview(self, actor: dict, asset: dict, edits: list[dict],
                                   expected_record_sha256: str) -> dict:
        """Preview exact authored channels separately from the imported cache.

        The source binding and record hash are checked before applying edits.
        Record identity remains imported; authored metadata identifies the
        effective frames. This is an offline preview, not runtime acceptance.
        """
        index, _ = self._binding(actor, asset)
        changed, metadata = self.authored_animation_record(actor, asset, edits, expected_record_sha256)
        preview = self._animation_preview(actor, asset, index, decode_animation_record(changed))
        preview["representation"] = "authored"
        preview["authored"] = metadata
        return preview

    def _animation_preview(self, actor, asset, index, decoded):
        geometry = self._geometry(asset, decoded)
        if len(geometry["vertices"]) * decoded["frame_count"] > MAX_POSED_VERTICES:
            raise ImportError("scene animation exceeds the bounded posed-vertex budget")
        frames = []
        for frame in decoded["frames"]:
            vertices = pose_vertices(geometry["vertices"], geometry["objects"], frame["object_transforms"])
            frames.append(dict(deepcopy(frame), vertices=vertices, bounds=_bounds(vertices), posed=True,
                               coordinate_system="retail_psx_actor_local_y_down"))
        return dict(self._metadata(actor, asset, index, decoded), geometry=geometry, frames=frames,
                    representation="imported")

    def pose_preview(self, actor: dict, asset: dict, frame_index: int = 0, *, authored_bank: bytes | None = None) -> dict:
        """Bake one actor-local pose without materializing every posed frame."""
        index, decoded = self._binding(actor, asset)
        if authored_bank is not None:
            if len(authored_bank) != len(self._body):
                raise ImportError("Authored pose bank must retain its source length")
            start, end = self._ranges[index]
            decoded = decode_animation_record(authored_bank[start:end])
        if type(frame_index) is not int or not 0 <= frame_index < decoded["frame_count"]:
            raise ImportError("scene animation frame index is outside the decoded clip")
        geometry = self._geometry(asset, decoded)
        frame = decoded["frames"][frame_index]
        vertices = pose_vertices(geometry["vertices"], geometry["objects"], frame["object_transforms"])
        metadata = self._metadata(actor, asset, index, decoded)
        if authored_bank is not None:
            metadata["representation"] = "authored"
            metadata["effective_record_sha256"] = hashlib.sha256(authored_bank[start:end]).hexdigest()
        geometry.update(vertices=vertices, bounds=_bounds(vertices), posed=True,
                        coordinate_system="retail_psx_actor_local_y_down",
                        pose=dict(metadata, frame_index=frame_index,
                                  object_transforms=deepcopy(frame["object_transforms"])))
        return geometry


def load_scene_actor_animation_catalog(disc: Any, scene: str) -> SceneActorAnimationCatalog:
    """Verify the scene once and locate its unique MAN-bearing type-0x05 bank."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        document = import_scene(disc, scene)
        if document["source"]["disc_identity"] != "sha256:" + digest:
            raise ImportError("scene animation source identity changed during verification")
        start, end = _bounded_scene_range(archive, mapping, scene)
        try:
            bundle, raw = find_scene_bundle(archive, start, end)
        except ImportError:
            from .man_source import read_man_source
            from .streaming_man import streaming_chunks
            carrier = read_man_source(archive, start, end, scene)
            if carrier.kind != 'raw_streaming_man':
                raise ImportError('scene animation source changed during streaming resolution')
            entry = archive.entry(carrier.entry_index)
            following = [e.start_lba * archive.SECTOR for e in archive.entries if e.index >= end]
            limit = min(following) if following else archive.node.size
            raw = archive.read_entry(entry, extended=False)[:max(0, limit - entry.start_lba * archive.SECTOR)]
            if raw[carrier.payload_offset:carrier.payload_offset + len(carrier.payload)] != carrier.payload:
                raise ImportError('streaming MAN changed during animation bank resolution')
            chunks, _ = streaming_chunks(raw)
            candidates = [c for c in chunks if c['type_byte'] == 5]
            if len(candidates) != 1:
                raise ImportError('streaming MAN carrier requires one unambiguous type-5 animation bank')
            chunk = candidates[0]
            if chunk['size'] > 4 * 1024 * 1024:
                raise ImportError('streaming scene animation bank exceeds byte bound')
            offset = chunk['header_offset'] + 4
            body = raw[offset:offset + chunk['size']]
            source = {'disc': {'sha256': digest, 'serial': 'SCUS-94254'}, 'iso_file': 'PROT.DAT',
                      'prot_entry_index': carrier.entry_index, 'prot_entry_name': scene,
                      'source_kind': 'raw_streaming_anm', 'compression': 'none',
                      'chunk_header_offset': chunk['header_offset'], 'payload_offset': offset,
                      'payload_byte_length': len(body), 'payload_sha256': hashlib.sha256(body).hexdigest(),
                      'association_evidence': 'type_5_in_verified_man_carrier_with_per_actor_channel_validation'}
            return SceneActorAnimationCatalog(disc, scene, document, body, source)
        candidates = [d for d in bundle.descriptors if d.type_byte == 5 and d.size > 0]
        if len(candidates) != 1:
            raise ImportError("scene requires exactly one evidenced type-0x05 animation descriptor")
        descriptor = candidates[0]
        stream_offset = bundle.table_offset + descriptor.data_offset
        later = [bundle.table_offset + d.data_offset for d in bundle.descriptors
                 if d.data_offset > descriptor.data_offset]
        stream_end = min(later + [len(raw)])
        if not 0 <= stream_offset < stream_end <= len(raw):
            raise ImportError("scene animation compressed stream is outside its container bounds")
        body, consumed = decompress_lzs(raw[stream_offset:stream_end], descriptor.size)
        source = {"disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
                  "prot_entry_index": bundle.entry_index, "prot_entry_name": scene,
                  "scene_table_offset": bundle.table_offset, "descriptor_index": descriptor.index,
                  "descriptor_type": descriptor.type_byte, "compressed_stream_offset": stream_offset,
                  "compressed_bytes_consumed": consumed}
        return SceneActorAnimationCatalog(disc, scene, document, body, source)


def load_actor_animation_preview(disc: Any, scene: str, actor: dict, asset: dict) -> dict:
    with _disc_context(disc):
        return load_scene_actor_animation_catalog(disc, scene).animation_preview(actor, asset)


def load_actor_pose_preview(disc: Any, scene: str, actor: dict, asset: dict, frame_index: int = 0) -> dict:
    with _disc_context(disc):
        return load_scene_actor_animation_catalog(disc, scene).pose_preview(actor, asset, frame_index)
