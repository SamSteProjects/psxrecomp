"""Derived scene geometry for the editor; never authored or live game state."""
from __future__ import annotations

from copy import deepcopy, copy
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



def preview_project(project, representation='authored'):
    """A read-only layer projection; never clear edits on the live project."""
    if representation not in ('authored', 'retail'):
        raise ProjectError('Scene representation must be authored or retail')
    if representation == 'authored':
        return project
    view = copy(project)
    view.overrides = {}
    view.actor_drafts = {}
    view.model_overrides = {}
    view.texture_overrides = {}
    return view

def source_key(project, *, geometry_only=False) -> str | None:
    document = project.imports.get(project.active_scene)
    if not project.disc_path or not document:
        return None
    path = resolve_disc_path(Path(project.disc_path)).resolve()
    appearances = {actor["semantic_id"]: deepcopy(project.overrides[actor["semantic_id"]]["ActorAppearance"])
                   for actor in document["actors"]
                   if "ActorAppearance" in project.overrides.get(actor["semantic_id"], {})}
    return digest({"project": str(project.root), "scene": project.active_scene,
                   "import": digest(document), "disc_path": str(path),
                   "appearances": appearances, "textures": deepcopy(project.texture_overrides),
                   "model_shapes": deepcopy(project.model_overrides),
                   "actor_drafts": None if geometry_only else {key: deepcopy(value) for key,value in getattr(project,'actor_drafts',{}).items() if value['scene_id']==project.active_scene},
                   "animation_channels": {a["semantic_id"]: deepcopy(project.overrides[a["semantic_id"]]["AnimationChannels"])
                                          for a in document["actors"] if "AnimationChannels" in project.overrides.get(a["semantic_id"], {})},
                   "environment": None if geometry_only else deepcopy(project.overrides.get(project.active_scene, {}).get("Environment")),
                   "collision": None if geometry_only else deepcopy(project.overrides.get(project.active_scene, {}).get("Collision")),
                   "disc_stamp": _disc_stamp(path), "schema": "legaia.scene-preview.v1"})


def environment_effective_transforms(project, metadata: dict) -> dict:
    """Project shared and cell-local edits without changing imported identities."""
    value = project.overrides.get(project.active_scene, {}).get("Environment")
    if not value:
        return {}
    from importer.environment_authoring import patch_environment_overrides
    project._validate_environment(project.active_scene, value)
    if metadata["source_record"]["map_sha256"] != value["source_sha256"]:
        raise ProjectError("Environment preview source differs from authored binding")
    _, changes = patch_environment_overrides(project._environment_source(project.active_scene), value)
    by_record, by_cell = {}, {}
    for change in changes:
        if 'allocation' in change:
            by_cell.setdefault(change['allocation']['cell_index'], []).append(change)
        else:
            by_record.setdefault(change["record_index"], []).append(change)
    result = {}
    for placement in metadata["placements"]:
        grid_offset = placement.get('source_record', {}).get('grid_byte_offset', -1)
        cell = (grid_offset - 0x8000) // 2
        rows = by_record.get(placement["object_record_index"], []) + by_cell.get(cell, [])
        if not rows:
            continue
        transform = deepcopy(placement["imported_transform"])
        for row in rows:
            field, axis = row["field"].split('.')
            if field == 'offset':
                transform["position"][axis] += (row["after_value"] - row["before_value"]) * (-1 if axis == 'z' else 1)
            else:
                transform["rotation_psx"][axis] = row["after_value"]
        result[placement["semantic_id"]] = transform
    return result


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


def environment_matrix(transform: dict) -> list:
    """Row-major source-local rotation, followed by the editor Y reflection."""
    from importer.animation import pose_vertices
    angles = transform["rotation_psx"]
    basis = pose_vertices([[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                          [{"object_index": 0, "vertex_start": 0, "vertex_count": 3}],
                          [{"object_index": 0, "translation": [0, 0, 0],
                            "rotation_psx": [angles[axis] & 4095 for axis in "xyz"]}])
    position = _display_position(transform["position"])
    return [basis[0][0], basis[1][0], basis[2][0], position["x"],
            -basis[0][1], -basis[1][1], -basis[2][1], position["y"],
            basis[0][2], basis[1][2], basis[2][2], position["z"], 0, 0, 0, 1]


def sample_preview_ground(ground, x, z):
    """Interpolate the displayed source triangles, not runtime collision height."""
    import math
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (x, z)):
        return None
    col, row = math.floor(x / 128), math.floor(z / 128)
    if not (0 <= col < 128 and 0 <= row < 128):
        return None
    cell = next((c for c in ground.get("cells", []) if c["cell_index"] == row * 128 + col), None)
    if cell is None:
        return None
    start = cell["vertex_start"]
    points = ground["vertices"][start:start + 4]
    if len(points) != 4:
        return None
    u, v = x / 128 - col, z / 128 - row
    a, b, c, d = (p[1] for p in points)
    height = a + u * (b - a) + v * (c - a) if u + v <= 1 else d + (1 - v) * (b - d) + (1 - u) * (c - d)
    return {"y": height, "cell_index": cell["cell_index"], "evidence": "source_preview_triangle_interpolation"}


class ScenePreviewService:
    """Two-entry geometry cache; each entry obeys the scene decoding budgets."""

    def __init__(self):
        self.clear()

    def _reset_active(self):
        self._key = None
        self._assets = []
        self._bindings = {}
        self._metrics = {}
        self._environment = []
        self._environment_metadata = None

    def clear(self):
        self._cache = {}
        self._reset_active()

    def _remember_active(self):
        self._cache[self._key] = (self._assets, self._bindings, self._metrics,
                                  self._environment, self._environment_metadata)
        while len(self._cache) > 2:
            del self._cache[next(iter(self._cache))]

    def preview(self, project, model_loader, pose_loader_factory=None, environment_loader_factory=None, terrain_loader=None) -> dict:
        # Cached geometry must not hide missing or modified authored files.
        for asset_id, binding in project.model_overrides.items():
            project.read_model_replacement(asset_id, binding)
        for binding in project.texture_overrides.values():
            if binding["source_scene_id"] == project.active_scene:
                project.read_texture_replacement(binding)
        key = source_key(project)
        if key is None:
            raise ProjectError("Scene preview requires an imported scene and its user-owned disc")
        geometry_key = source_key(project, geometry_only=True)
        if geometry_key != self._key:
            # Failed regeneration must not expose the previous scene's geometry.
            self._reset_active()
            cached = self._cache.pop(geometry_key, None)
            if cached is not None:
                (self._assets, self._bindings, self._metrics,
                 self._environment, self._environment_metadata) = cached
                self._key = geometry_key
            else:
                # Leave room before decoding so a third full scene is never retained.
                if len(self._cache) >= 2:
                    del self._cache[next(iter(self._cache))]
                try:
                    self._build(project, geometry_key, model_loader, pose_loader_factory, environment_loader_factory, terrain_loader)
                except Exception:
                    self.clear()
                    raise
            self._remember_active()
        projected = project.state()["scene"]
        instances = []
        ground = next((asset["preview"] for asset in self._assets if asset.get("pose_kind") == "source_heightfield"), {})
        for entity in projected["entities"]:
            transform = entity["components"]["Transform"]
            position = deepcopy(transform["effective"]["position"])
            preview_position = deepcopy(position)
            ground_sample = sample_preview_ground(ground, position.get("x"), position.get("z")) if position.get("y") is None else None
            if ground_sample is not None:
                preview_position["y"] = ground_sample["y"]
            displayed = _display_position(preview_position)
            matrix = list(POSITION_TO_DISPLAY)
            matrix[3], matrix[7], matrix[11] = displayed["x"], displayed["y"], displayed["z"]
            binding = self._bindings[entity["id"]]
            instances.append({"entity_id": entity["id"], **deepcopy(binding),
                              "position": position, "preview_position": preview_position, "preview_ground_sample": ground_sample, "display_position": displayed,
                              "preview_height_status": "explicit" if position.get("y") is not None else "source_surface" if ground_sample is not None else "unresolved_no_source_surface",
                              "model_to_scene": matrix,
                              "retail_position": deepcopy(transform["imported"]["position"]),
                              "authored_position": deepcopy(transform["authored"].get("position", {})),
                              "evidence": {"position": "imported placement plus authored overrides",
                                           "height": "source terrain preview only; runtime elevation unverified" if ground_sample is not None else "ground-plane preview only" if position.get("y") is None else "authored value",
                                           "heading": "unknown; identity orientation is a display convention",
                                           "scale": "source units retained; physical scale is unknown"}})
        by_id = {instance['entity_id']: instance for instance in instances}
        for identifier, draft in getattr(project,'actor_drafts',{}).items():
            if draft['scene_id'] != project.active_scene:
                continue
            project._validate_actor_draft(identifier,draft)
            donor = by_id.get(draft['donor_entity_id'])
            if donor is None:
                raise ProjectError('Draft preview donor is unavailable')
            instance = deepcopy(donor)
            retail_binding = self._bindings.get(draft['donor_entity_id'] + '/retail-draft-source')
            if retail_binding is not None:
                instance.update(deepcopy(retail_binding))
            position = {**draft['position'], 'y':None}
            sample = sample_preview_ground(ground,position['x'],position['z'])
            preview_position = {**position,'y':sample['y'] if sample else None}
            display = _display_position(preview_position)
            matrix = list(POSITION_TO_DISPLAY)
            matrix[3],matrix[7],matrix[11] = display['x'],display['y'],display['z']
            instance.update(entity_id=identifier,kind='actor_draft',name=draft['name'],
                            donor_entity_id=draft['donor_entity_id'],position=position,
                            preview_position=preview_position,display_position=display,
                            preview_ground_sample=sample,model_to_scene=matrix,
                            retail_position=None,authored_position=deepcopy(draft['position']),
                            preview_height_status='source_surface' if sample else 'unresolved_no_source_surface',
                            evidence={'position':'authored NPC draft',
                                      'appearance':'retail donor assignment; shared authored asset edits may affect preview',
                                      'runtime':'not spawned or gameplay verified'})
            instances.append(instance)
        environment = deepcopy(self._environment)
        effective = (environment_effective_transforms(project, self._environment_metadata)
                     if self._environment_metadata is not None else {})
        for instance in environment:
            transform = effective.get(instance['entity_id'])
            if transform is not None:
                instance.update(position=deepcopy(transform['position']),
                                display_position=_display_position(transform['position']),
                                model_to_scene=environment_matrix(transform),
                                effective_transform=deepcopy(transform), authored_transform=True)
        instances.extend(environment)
        if len(instances)>MAX_ENTITIES:
            raise ProjectError('Scene preview including drafts exceeds entity limit')
        if source_key(project) != key:
            raise ProjectError("Scene preview source changed during transform projection")
        actors = [instance for instance in instances if instance.get('kind') != 'environment']
        metrics = dict(self._metrics)
        metrics.update(entity_count=len(actors),
                       renderable_count=sum(bool(item['renderable']) for item in actors),
                       draft_count=sum(item.get('kind')=='actor_draft' for item in actors),
                       total_entity_count=len(instances),
                       total_renderable_count=sum(bool(item['renderable']) for item in instances))
        return {"schema": "legaia.scene-preview.v1", "source_key": key,
                "scene_id": projected["id"], "coordinate_system": "editor_field_y_up_source_units",
                "position_to_display": list(POSITION_TO_DISPLAY),
                "environment_authoring": deepcopy(project.overrides.get(project.active_scene, {}).get("Environment")),
                "assets": deepcopy(self._assets), "entities": instances, "metrics": metrics,
                "limits": ["Authored placement reference, not scripted runtime placement or visibility",
                           "Unknown heights use source terrain where available, otherwise a display ground plane; unknown heading uses identity",
                           "Unsupported multipart poses remain markers; no fabricated object assembly",
                           "Static reference poses; no live equipment, animated palettes or exact PSX blending"]}

    def _build(self, project, key, model_loader, pose_loader_factory, environment_loader_factory=None, terrain_loader=None):
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
            catalog, animation_error = None, None
            if pose_loader_factory:
                try:
                    catalog = pose_loader_factory(project.disc_path, document["scene"]["name"])
                except RetailImportError as exc:
                    animation_error = str(exc)
            animation_overrides = {a["semantic_id"]: project.overrides[a["semantic_id"]]["AnimationChannels"]
                                   for a in actors if "AnimationChannels" in project.overrides.get(a["semantic_id"], {})}
            if animation_overrides and catalog is None:
                raise ProjectError("Authored animation preview requires the verified scene animation catalog")
            authored_bank = catalog.authored_bank(animation_overrides)[0] if animation_overrides else None
            authored_clips = {v["animation_id"] for v in animation_overrides.values()}
            actor_views = [(actor, False) for actor in actors]
            actor_views += [(actor, True) for actor in actors
                            if 'ActorAppearance' in project.overrides.get(actor['semantic_id'], {})]
            for actor, retail_draft_source in actor_views:
                identifier = actor["semantic_id"]
                resolver = getattr(project, "appearance_source_actor", None)
                appearance = None if retail_draft_source else project.overrides.get(identifier, {}).get("ActorAppearance")
                if resolver is None and appearance is not None:
                    raise ProjectError("Scene appearance override requires a verified source resolver")
                source_actor = resolver(identifier, verify_disc=True) if resolver and not retail_draft_source else actor
                if retail_draft_source:
                    identifier += '/retail-draft-source'
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
                        preview = model_loader(asset, support["clips"][0]["id"])
                        frame = preview["frames"][0]
                        preview["vertices"] = frame["vertices"] if isinstance(frame, dict) else frame
                        preview.pop("frames", None)
                        pose_kind = "reference_party_idle" if support["clips"][0]["id"] == "idle" else "reference_global_loop"
                    elif animation_id and catalog is not None:
                        clip_id = f"animation://{document['scene']['name']}/scene-anm/{animation_id - 1:04d}"
                        changed_clip = clip_id in authored_clips
                        preview = (catalog.pose_preview(source_actor, asset, 0, authored_bank=authored_bank)
                                   if changed_clip else catalog.pose_preview(source_actor, asset, 0))
                        # Texture association remains owned by the server adapter.
                        preview = model_loader(asset, prepared=preview)
                        pose_kind = "authored_scene_animation_frame0" if changed_clip else "imported_scene_animation_frame0"
                    elif animation_id and animation_error:
                        raise RetailImportError(f"Scene animation unavailable: {animation_error}")
                    else:
                        preview = model_loader(asset)
                        if len(preview.get("objects", [])) != 1:
                            if animation_id:
                                raise RetailImportError("Multipart model has no supported placement pose")
                            # Pinned field_npc.rs play catalog includes clipless multipart
                            # actors: draw kind 5 uses one actor transform for all objects.
                            # Do not apply this to an unresolved nonzero animation ID.
                            from importer.animation_catalog import REFERENCE_COMMIT
                            pose_kind = "reference_clipless_multipart_static"
                            preview["pose_evidence"] = {
                                "kind": pose_kind, "reference_commit": REFERENCE_COMMIT,
                                "reference_path": "crates/web-viewer/src/field_npc.rs",
                                "initial_animation_id": 0,
                                "object_transform": "shared_actor_transform_raw_object_vertices",
                                "runtime_state": "not_observed",
                            }
                        else:
                            pose_kind = "single_object_static"
                    count = len(preview.get("triangles", []))
                    bytes_used = sum((len(t.get("rgba_base64", "")) + len(t.get("stp_base64", ""))) * 3 // 4 for t in preview.get("textures", []))
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
            environment = []
            environment_metadata = None
            environment_error = None
            if environment_loader_factory:
                try:
                    env = environment_loader_factory(project.disc_path, document["scene"]["name"])
                    placements = env.metadata["placements"]
                    environment_metadata = deepcopy(env.metadata)
                    if len(placements) + len(actors) > MAX_ENTITIES:
                        raise RetailImportError("Scene environment entity budget exceeded")
                    for placement in placements:
                        transform = placement["imported_transform"]
                        asset_id = placement.get("model_asset_id")
                        instance = {"entity_id": placement["semantic_id"], "kind": "environment",
                                    "name": placement["name"], "asset_id": asset_id,
                                    "renderable": False, "geometry_key": None,
                                    "position": deepcopy(transform["position"]),
                                    "display_position": _display_position(transform["position"]),
                                    "model_to_scene": environment_matrix(transform),
                                    "effective_transform": deepcopy(transform),
                                    "authored_transform": False,
                                    "source_record": deepcopy(placement),
                                    "evidence": {"placement": "imported_MAP_and_MAN_floor_LUT",
                                                 "mesh_pool": deepcopy(env.metadata["mesh_pool"]),
                                                 "pose": "source_reference_frame_zero_not_script_execution"}}
                        environment.append(instance)
                        geometry_key = digest({"environment_asset": asset_id, "animation_id": placement.get("animation_id")})
                        try:
                            if geometry_key not in decoded:
                                asset = project.assets.records.get(asset_id)
                                if asset is None:
                                    raise RetailImportError("Environment mesh is not in the imported asset database")
                                geometry = env.pose_preview(placement["semantic_id"])
                                preview = model_loader(asset, prepared=geometry)
                                count = len(preview.get("triangles", []))
                                bytes_used = sum((len(t.get("rgba_base64", "")) + len(t.get("stp_base64", ""))) * 3 // 4 for t in preview.get("textures", []))
                                if len(assets) >= MAX_GEOMETRIES or triangle_count + count > MAX_TRIANGLES or texture_bytes + bytes_used > MAX_TEXTURE_BYTES:
                                    raise RetailImportError("Scene geometry or texture preview budget exceeded")
                                assets.append({"asset_id": asset_id, "geometry_key": geometry_key, "preview": preview,
                                               "pose_kind": geometry["pose"]["kind"], "bounds": preview["bounds"]})
                                triangle_count += count
                                texture_bytes += bytes_used
                                decoded[geometry_key] = {"geometry_key": geometry_key, "renderable": True,
                                                         "pose_kind": geometry["pose"]["kind"], "reason": None}
                            instance.update(decoded[geometry_key])
                        except RetailImportError as exc:
                            instance["reason"] = str(exc)
                except RetailImportError as exc:
                    environment_error = str(exc)
            terrain_error = None
            terrain_cells = 0
            if terrain_loader:
                try:
                    ground = terrain_loader(project)
                    count = len(ground["triangles"])
                    bytes_used = sum((len(t.get("rgba_base64", "")) + len(t.get("stp_base64", ""))) * 3 // 4 for t in ground["textures"])
                    if len(assets) >= MAX_GEOMETRIES or triangle_count + count > MAX_TRIANGLES or texture_bytes + bytes_used > MAX_TEXTURE_BYTES:
                        raise RetailImportError("Combined terrain geometry or texture budget exceeded")
                    if count:
                        ground_key = digest({"terrain": ground["source_record"], "source_key": key})
                        ground_id = f"environment://{document['scene']['name']}/field-map/ground"
                        bounds = {"min": [min(p[a] for p in ground["vertices"]) for a in range(3)],
                                  "max": [max(p[a] for p in ground["vertices"]) for a in range(3)]}
                        assets.append({"asset_id": ground_id, "geometry_key": ground_key,
                                       "preview": ground, "bounds": bounds, "pose_kind": "source_heightfield"})
                        transform = {"position": {"x": 0, "y": 0, "z": 0}, "rotation_psx": {"x": 0, "y": 0, "z": 0}}
                        environment.append({"entity_id": ground_id, "kind": "environment", "name": "Ground surface",
                                            "asset_id": ground_id, "renderable": True, "geometry_key": ground_key,
                                            "pose_kind": "source_heightfield", "position": transform["position"],
                                            "display_position": transform["position"], "model_to_scene": list(POSITION_TO_DISPLAY),
                                            "source_record": {"imported_transform": transform, "source": ground["source_record"]},
                                            "evidence": {"limits": ground["limitations"], "cell_count": len(ground["cells"])}})
                        triangle_count += count
                        texture_bytes += bytes_used
                        terrain_cells = len(ground["cells"])
                except RetailImportError as exc:
                    terrain_error = str(exc)
        if source_key(project, geometry_only=True) != key:
            raise ProjectError("Scene preview source changed during decoding")
        self._assets, self._bindings, self._key = assets, bindings, key
        self._environment = environment
        self._environment_metadata = environment_metadata
        self._metrics = {"entity_count": len(bindings), "renderable_count": sum(b["renderable"] for b in bindings.values()),
                         "geometry_count": len(assets), "triangle_count": triangle_count,
                         "texture_bytes": texture_bytes, "decode_seconds": round(time.monotonic() - started, 3)}
        self._metrics.update(environment_count=len(environment),
                             environment_renderable_count=sum(e["renderable"] for e in environment),
                             environment_error=environment_error)
        self._metrics.update(terrain_cell_count=terrain_cells, terrain_error=terrain_error,
                             animation_error=animation_error)
