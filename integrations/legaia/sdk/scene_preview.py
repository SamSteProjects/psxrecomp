"""Derived scene geometry for the editor; never authored or live game state."""
from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import time

from importer.core import ImportError as RetailImportError, resolve_disc_path
from importer.pipeline import _disc_context, _disc_stamp, import_scene
from .project import ProjectError, digest


POSITION_TO_DISPLAY = [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
MAX_ENTITIES = 512
MAX_GEOMETRIES = 128
MAX_TRIANGLES = 200_000
MAX_TEXTURE_BYTES = 16 * 1024 * 1024


def source_key(project) -> str | None:
    document = project.imports.get(project.active_scene)
    if not project.disc_path or not document:
        return None
    path = resolve_disc_path(Path(project.disc_path)).resolve()
    appearances = {actor["semantic_id"]: deepcopy(project.overrides[actor["semantic_id"]]["ActorAppearance"])
                   for actor in document["actors"]
                   if "ActorAppearance" in project.overrides.get(actor["semantic_id"], {})}
    return digest({"project": str(project.root), "scene": project.active_scene,
                   "import": digest(document), "disc_path": str(path),
                   "appearances": appearances,
                   "disc_stamp": _disc_stamp(path), "schema": "legaia.scene-preview.v1"})


def _display_position(position: dict) -> dict:
    values = {}
    for axis in ("x", "y", "z"):
        value = position.get(axis)
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
            raise ProjectError("Scene preview requires finite placement coordinates")
        if value is None and axis != "y":
            raise ProjectError("Scene preview requires evidenced X/Z placement")
        values[axis] = (-value if axis == "y" else value) if value is not None else 0
    return values


class ScenePreviewService:
    """One bounded geometry cache. Transform edits never invalidate asset bytes."""

    def __init__(self):
        self._key = None
        self._assets = []
        self._bindings = {}
        self._metrics = {}

    def clear(self):
        self._key = None
        self._assets = []
        self._bindings = {}
        self._metrics = {}

    def preview(self, project, model_loader, pose_loader_factory=None) -> dict:
        key = source_key(project)
        if key is None:
            raise ProjectError("Scene preview requires an imported scene and its user-owned disc")
        if key != self._key:
            # Failed regeneration must not expose the previous scene's geometry.
            self.clear()
            self._build(project, key, model_loader, pose_loader_factory)
        projected = project.state()["scene"]
        instances = []
        for entity in projected["entities"]:
            transform = entity["components"]["Transform"]
            position = deepcopy(transform["effective"]["position"])
            displayed = _display_position(position)
            matrix = list(POSITION_TO_DISPLAY)
            matrix[3], matrix[7], matrix[11] = displayed["x"], displayed["y"], displayed["z"]
            binding = self._bindings[entity["id"]]
            instances.append({"entity_id": entity["id"], **deepcopy(binding),
                              "position": position, "display_position": displayed,
                              "model_to_scene": matrix,
                              "retail_position": deepcopy(transform["imported"]["position"]),
                              "authored_position": deepcopy(transform["authored"].get("position", {})),
                              "evidence": {"position": "imported placement plus authored overrides",
                                           "height": "ground-plane preview only" if position.get("y") is None else "authored value",
                                           "heading": "unknown; identity orientation is a display convention",
                                           "scale": "source units retained; physical scale is unknown"}})
        return {"schema": "legaia.scene-preview.v1", "source_key": key,
                "scene_id": projected["id"], "coordinate_system": "editor_field_y_up_source_units",
                "position_to_display": list(POSITION_TO_DISPLAY),
                "assets": deepcopy(self._assets), "entities": instances, "metrics": dict(self._metrics),
                "limits": ["Authored placement reference, not scripted runtime placement or visibility",
                           "Unknown heights use a display ground plane and unknown heading uses identity",
                           "Unsupported multipart poses remain markers; no fabricated object assembly",
                           "Static reference poses; no live equipment, animated palettes or exact PSX blending"]}

    def _build(self, project, key, model_loader, pose_loader_factory):
        started = time.monotonic()
        document = project.imports[project.active_scene]
        actors = document["actors"]
        if len(actors) > MAX_ENTITIES:
            raise ProjectError("Scene preview entity budget exceeded")
        assets, bindings, decoded = [], {}, {}
        triangle_count = texture_bytes = 0
        with _disc_context(project.disc_path):
            fresh = import_scene(project.disc_path, document["scene"]["name"])
            if fresh != document:
                raise ProjectError("Imported scene evidence differs from the verified retail source")
            catalog = pose_loader_factory(project.disc_path, document["scene"]["name"]) if pose_loader_factory else None
            for actor in actors:
                identifier = actor["semantic_id"]
                resolver = getattr(project, "appearance_source_actor", None)
                appearance = project.overrides.get(identifier, {}).get("ActorAppearance")
                if resolver is None and appearance is not None:
                    raise ProjectError("Scene appearance override requires a verified source resolver")
                source_actor = resolver(identifier, verify_disc=True) if resolver else actor
                # Never let a resolver fabricate geometry provenance or cross scene boundaries.
                if source_actor not in actors:
                    raise ProjectError("Scene appearance source differs from verified scene evidence")
                asset_id = source_actor["model_reference"].get("asset_semantic_id")
                asset = project.assets.records.get(asset_id)
                binding = {"asset_id": asset_id, "geometry_key": None, "renderable": False,
                           "source_actor_id": source_actor["semantic_id"],
                           "source_record": deepcopy(source_actor.get("source_record")),
                           "model_reference": deepcopy(source_actor["model_reference"]),
                           "appearance_authored": appearance is not None,
                           "pose_kind": "unavailable", "reason": "Imported model reference is unresolved"}
                bindings[identifier] = binding
                if asset is None:
                    continue
                animation_id = source_actor.get("placement_fields", {}).get("animation_id", 0)
                geometry_key = digest({"asset": asset_id, "animation_id": animation_id})
                if geometry_key in decoded:
                    binding.update(decoded[geometry_key])
                    continue
                result = {"geometry_key": None, "renderable": False, "pose_kind": "unavailable"}
                try:
                    from importer.animation import animation_capabilities
                    support = animation_capabilities(asset)
                    if support.get("supported"):
                        preview = model_loader(asset, "idle")
                        frame = preview["frames"][0]
                        preview["vertices"] = frame["vertices"] if isinstance(frame, dict) else frame
                        preview.pop("frames", None)
                        pose_kind = "reference_party_idle"
                    elif animation_id and catalog is not None:
                        preview = catalog.pose_preview(source_actor, asset, 0)
                        # Texture association remains owned by the server adapter.
                        preview = model_loader(asset, prepared=preview)
                        pose_kind = "imported_scene_animation_frame0"
                    else:
                        preview = model_loader(asset)
                        if len(preview.get("objects", [])) != 1:
                            raise RetailImportError("Multipart model has no supported placement pose")
                        pose_kind = "single_object_static"
                    count = len(preview.get("triangles", []))
                    bytes_used = sum(len(t.get("rgba_base64", "")) * 3 // 4 for t in preview.get("textures", []))
                    if len(assets) >= MAX_GEOMETRIES or triangle_count + count > MAX_TRIANGLES or texture_bytes + bytes_used > MAX_TEXTURE_BYTES:
                        raise RetailImportError("Scene geometry or texture preview budget exceeded")
                    preview["coordinate_system"] = "actor_local_y_down_source_units"
                    preview["bounds"] = {"min": [min(p[a] for p in preview["vertices"]) for a in range(3)],
                                         "max": [max(p[a] for p in preview["vertices"]) for a in range(3)]}
                    assets.append({"asset_id": asset_id, "geometry_key": geometry_key, "preview": preview,
                                   "pose_kind": pose_kind, "bounds": preview["bounds"]})
                    triangle_count += count
                    texture_bytes += bytes_used
                    result.update(geometry_key=geometry_key, renderable=True, pose_kind=pose_kind, reason=None)
                except RetailImportError as exc:
                    result["reason"] = str(exc)
                decoded[geometry_key] = result
                binding.update(result)
        if source_key(project) != key:
            raise ProjectError("Scene preview source changed during decoding")
        self._assets, self._bindings, self._key = assets, bindings, key
        self._metrics = {"entity_count": len(bindings), "renderable_count": sum(b["renderable"] for b in bindings.values()),
                         "geometry_count": len(assets), "triangle_count": triangle_count,
                         "texture_bytes": texture_bytes, "decode_seconds": round(time.monotonic() - started, 3)}
