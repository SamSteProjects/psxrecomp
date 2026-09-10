"""Loopback-only editor service. Commands are serialized; no runtime RAM writes."""
from __future__ import annotations

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import threading
from urllib.parse import urlsplit

from importer.core import ImportError as RetailImportError
from .project import ProjectError, ProjectService


class EditorServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, address: tuple[str, int], project: ProjectService, runtime_port: int = 4370):
        if address[0] not in ("127.0.0.1", "localhost"):
            raise ProjectError("Editor service must bind to loopback")
        from integrations.legaia.observer.service import ObserverService
        self.project = project
        self.last_build = None
        self.texture_catalogs = {}
        from .scene_preview import ScenePreviewService
        self.scene_previews = ScenePreviewService()
        from .run import RunService
        self.runs = RunService()
        self.observer = ObserverService(port=runtime_port)
        self.live_status = {"available": False, "state": "disconnected", "reason": {"message": "Runtime has not been checked"}}
        self.command_lock = threading.RLock()
        self.editor_root = Path(__file__).resolve().parents[1] / "editor"
        super().__init__(address, EditorHandler)

    def state(self) -> dict:
        from importer.animation import animation_capabilities
        state = self.project.state()
        state["runtime"] = self.live_status
        state["capabilities"]["live_mode"] = self.live_status.get("available", False)
        state["capabilities"]["runtime_discovery"] = True
        state["capabilities"]["model_preview"] = bool(self.project.disc_path)
        state["capabilities"]["animation_preview"] = bool(self.project.disc_path)
        from .scene_preview import source_key
        try:
            state["scene_preview_source_key"] = source_key(self.project)
        except (RetailImportError, OSError):
            state["scene_preview_source_key"] = None
        state["capabilities"]["scene_preview"] = bool(state["scene_preview_source_key"])
        for asset in state["assets"]:
            asset["animation_support"] = animation_capabilities(asset)
        from importer.scene_animation import actor_animation_capabilities
        actors = {actor["semantic_id"]: actor for actor in
                  self.project.imports.get(self.project.active_scene, {}).get("actors", [])}
        for entity in state["scene"]["entities"]:
            actor = actors.get(entity["id"])
            if actor is not None and "Animation" in entity["components"]:
                asset = self.project.assets.records.get(actor["model_reference"].get("asset_semantic_id"), {})
                entity["components"]["Animation"]["preview_support"] = actor_animation_capabilities(actor, asset)
        state["capabilities"]["actor_animation_preview"] = bool(self.project.disc_path)
        state["capabilities"]["actor_script_preview"] = bool(self.project.disc_path)
        state["capabilities"]["actor_dialogue_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_appearance"] = bool(self.project.disc_path)
        state["capabilities"]["resource_catalog"] = bool(self.project.disc_path and self.project.active_scene)
        state["capabilities"]["texture_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["texture_replacement"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["field_map_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["build"] = bool(self.project.disc_path and self.project.imports)
        state["build"] = self.last_build
        state["run"] = self.runs.status()
        try:
            state["launch_config"] = self.runs.config(self.project)
        except (ProjectError, ValueError, OSError) as exc:
            state["launch_config"] = {}
            state["diagnostics"].append("Launch configuration: " + str(exc))
        state["capabilities"]["build_and_run"] = state["capabilities"]["build"]
        return state

    def server_close(self) -> None:
        self.observer.close()
        super().server_close()

    def actor_animation_preview(self, entity_id: str) -> dict:
        """Resolve an imported actor; clients cannot supply a model or clip binding."""
        from importer.pipeline import _disc_context
        from importer.scene_animation import load_scene_actor_animation_catalog
        project = self.project
        if not project.disc_path:
            raise ProjectError("Actor animation preview requires the project's user-owned disc")
        document = project.imports.get(project.active_scene)
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == entity_id), None)
        if actor is None:
            raise ProjectError("Actor animation requires an imported actor in the active scene")
        asset = project.assets.records.get(actor["model_reference"].get("asset_semantic_id"))
        if asset is None:
            raise ProjectError("Actor's imported model is unresolved")
        with _disc_context(project.disc_path):
            catalog = load_scene_actor_animation_catalog(project.disc_path, document["scene"]["name"])
            animation = catalog.animation_preview(actor, asset)
            preview = self.model_preview(asset, prepared=animation.pop("geometry"))
            preview["frames"] = animation.pop("frames")
            animation.update(source_clip_id=animation["clip_id"], clip_id="scene-header", entity_id=entity_id)
            preview["animation"] = animation
            preview["animation_support"] = {
                "supported": True, "clips": [{"id": "scene-header", "label": animation["label"]}],
                "evidence": "verified_man_header_initial_animation_not_runtime_script_state"}
        return preview

    def actor_script_preview(self, entity_id: str) -> dict:
        from importer.script_inspection import inspect_actor_script
        from importer.pipeline import _disc_context
        project = self.project
        if not project.disc_path:
            raise ProjectError("Script inspection requires the project's user-owned disc")
        document = project.imports.get(project.active_scene)
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == entity_id), None)
        if actor is None:
            raise ProjectError("Script inspection requires an imported actor in the active scene")
        with _disc_context(project.disc_path):
            report = inspect_actor_script(project.disc_path, document["scene"]["name"], actor)
            try:
                report["dialogue_authoring"] = project.dialogue_options(entity_id)
            except (RetailImportError, ProjectError) as exc:
                report["dialogue_authoring"] = {"supported": False, "reason": str(exc), "runs": [],
                                                "unresolved_overrides": sorted(project.overrides.get(entity_id, {}).get("Dialogue", {}).get("runs", {})),
                                                "limitations": ["Read-only script inspection does not establish text-write safety."]}
            return report

    def actor_appearance_preview(self, entity_id: str) -> dict:
        from importer.pipeline import _disc_context
        if not self.project.overrides.get(entity_id, {}).get("ActorAppearance"):
            raise ProjectError("Actor has no authored appearance override")
        with _disc_context(self.project.disc_path):
            donor = self.project.appearance_source_actor(entity_id, verify_disc=True)
            preview = self.actor_animation_preview(donor["semantic_id"])
            preview["animation"].update(entity_id=entity_id, donor_entity_id=donor["semantic_id"],
                                        clip_id="authored-appearance", layer="authored",
                                        label="Authored initial appearance")
            preview["animation_support"]["clips"] = [{"id": "authored-appearance", "label": "Authored initial appearance"}]
            return preview

    def export_preview(self, preview: dict, frame_index: int | None) -> dict:
        from .build import _guard_output
        from .project import atomic_write
        from importer.export import write_model_export
        output = self.project.root / "Exports"
        _guard_output(output / ".gitignore", self.project.root)
        result = write_model_export(preview, output, frame_index)
        if not (output / ".gitignore").exists():
            atomic_write(output / ".gitignore", b"*\n")
        return result

    def model_preview(self, asset: dict, clip_id: str | None = None, *, prepared: dict | None = None) -> dict:
        from importer.assets import load_model_preview
        from importer.animation import animation_capabilities, load_animation_preview
        from importer.textures import (associate_material, load_asset_texture_catalog,
                                       load_scene_texture_catalog, uses_field_party_textures)
        project = self.project
        if prepared is not None:
            from copy import deepcopy
            preview = deepcopy(prepared)
        elif clip_id is not None:
            animation = load_animation_preview(Path(project.disc_path), asset, clip_id)
            preview = animation.pop("geometry")
            preview["frames"] = animation.pop("frames")
            preview["animation"] = animation
        else:
            preview = load_model_preview(Path(project.disc_path), asset)
        preview["animation_support"] = animation_capabilities(asset)
        scene = asset.get("source_record", {}).get("prot_entry_name")
        if scene == "befect_data":
            scene = project.imports.get(project.active_scene, {}).get("scene", {}).get("name")
        if not scene:
            preview["textures"] = []
            return preview
        from .scene_preview import source_key
        from .resources import apply_texture_overrides
        for binding in project.texture_overrides.values():
            if binding["source_scene_id"] == "scene://" + scene:
                project.read_texture_replacement(binding)
        key = (project.disc_path, scene, source_key(project))
        if key not in self.texture_catalogs:
            if len(self.texture_catalogs) >= 2:
                self.texture_catalogs.clear()
            self.texture_catalogs[key] = apply_texture_overrides(project, load_scene_texture_catalog(project.disc_path, scene))
        # The selected shared bank never replaces or merges into the scene cache.
        catalog = load_asset_texture_catalog(project.disc_path, asset, self.texture_catalogs[key])
        preview["texture_scope"] = "field_party" if uses_field_party_textures(asset) else "scene"
        preview["texture_catalog"] = catalog.metadata()
        preview["textures"] = []
        budget = 2 * 1024 * 1024
        for index, material in enumerate(preview.get("materials", [])):
            if not material.get("textured"):
                preview["textures"].append({"material_index": index, "status": "untextured", "reason": "Material uses vertex colors"})
                continue
            uvs = [uv for triangle_index, material_index in enumerate(preview["triangle_materials"])
                   if material_index == index for uv in (preview["triangle_uvs"][triangle_index] or [])]
            if not uvs or index >= 32:
                preview["textures"].append({"material_index": index, "status": "unsupported", "reason": "Missing texture coordinates or bounded preview limit"})
                continue
            bounds = (min(uv[0] for uv in uvs), min(uv[1] for uv in uvs), max(uv[0] for uv in uvs), max(uv[1] for uv in uvs))
            result = associate_material(catalog, material, bounds)
            rgba = result.pop("rgba", None)
            result.pop("stp", None)
            if rgba is not None:
                if len(rgba) > budget:
                    result = {"status": "unsupported", "reason": "Decoded texture preview byte budget exceeded"}
                else:
                    budget -= len(rgba)
                    result["rgba_base64"] = base64.b64encode(rgba).decode("ascii")
            result["material_index"] = index
            preview["textures"].append(result)
        return preview


class EditorHandler(BaseHTTPRequestHandler):
    server: EditorServer

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def _trusted_request(self) -> bool:
        # Block browser-driven cross-origin local commands (including DNS rebinding).
        host = self.headers.get("Host", "")
        valid = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if host not in valid:
            self._json(403, {"error": "Editor accepts only its loopback host"})
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + value for value in valid}:
            self._json(403, {"error": "Cross-origin editor requests are forbidden"})
            return False
        return True

    def _send(self, status: int, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, value: dict) -> None:
        self._send(status, json.dumps(value, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if not self._trusted_request():
            return
        route = urlsplit(self.path).path
        with self.server.command_lock:
            if route == "/api/run/status":
                self._json(200, {"run": self.server.runs.status()})
                return
            if route == "/api/state":
                self._json(200, self.server.state())
                return
        files = {"/": ("index.html", "text/html"), "/editor.js": ("editor.js", "text/javascript"),
                 "/editor.css": ("editor.css", "text/css"),
                 "/scene-renderer.js": ("scene-renderer.js", "text/javascript")}
        if route not in files:
            self._json(404, {"error": "Unknown editor route"})
            return
        name, content_type = files[route]
        path = self.server.editor_root / name
        if not path.is_file():
            self._json(503, {"error": "Editor frontend is not installed"})
            return
        self._send(200, path.read_bytes(), content_type + "; charset=utf-8")

    def do_POST(self) -> None:
        if not self._trusted_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request_limit = 2 * 1024 * 1024 if urlsplit(self.path).path == "/api/texture-replacement" else 32768
            if not 0 < length <= request_limit or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ProjectError(f"Commands require a JSON object of at most {request_limit} bytes")
            content = self.rfile.read(length)
            if len(content) != length:
                raise ProjectError("Incomplete command request body")
            body = json.loads(content)
            if not isinstance(body, dict):
                raise ProjectError("Command body must be an object")
            with self.server.command_lock:
                route = urlsplit(self.path).path
                if route in ("/api/texture-source", "/api/texture-replacement"):
                    expected = {"asset_id", "tim_base64"} if route.endswith("replacement") else {"asset_id"}
                    if set(body) != expected or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Texture requests accept a resource identity and optional authored TIM only")
                    if route.endswith("source"):
                        from .resources import texture_source
                        self._json(200, texture_source(self.server.project, body["asset_id"]))
                    else:
                        encoded = body["tim_base64"]
                        if not isinstance(encoded, str) or len(encoded) > 1398104:
                            raise ProjectError("Authored TIM exceeds the 1 MiB limit")
                        try:
                            content = base64.b64decode(encoded, validate=True)
                        except ValueError as exc:
                            raise ProjectError("Authored TIM requires valid base64") from exc
                        self.server.project.set_texture_replacement(body["asset_id"], content)
                        self._json(200, self.server.state())
                    return
                if route == "/api/resource-catalog":
                    if body:
                        raise ProjectError("Resource discovery takes no client source bindings")
                    from .resources import refresh_resource_catalog
                    self._json(200, refresh_resource_catalog(self.server.project))
                    return
                if route == "/api/field-map-preview":
                    if set(body) != {"asset_id"} or not isinstance(body["asset_id"], str) or not body["asset_id"]:
                        raise ProjectError("Field map preview accepts a catalog identity only; coordinates and paths are source-controlled")
                    from .resources import field_map_preview
                    self._json(200, field_map_preview(self.server.project, body["asset_id"]))
                    return
                if route == "/api/texture-preview":
                    if (not {"asset_id", "palette_index"} <= set(body) or set(body) - {"asset_id", "palette_index", "layer"} or
                            not isinstance(body.get("asset_id"), str) or not body["asset_id"] or
                            type(body.get("palette_index")) is not int or body["palette_index"] < 0):
                        raise ProjectError("Texture preview requires a resource identity and nonnegative palette index only")
                    from .resources import texture_preview
                    self._json(200, texture_preview(self.server.project, body["asset_id"], body["palette_index"], body.get("layer", "effective")))
                    return
                if route in ("/api/actor-appearance-options", "/api/actor-appearance-preview", "/api/export/actor-appearance"):
                    exporting = route == "/api/export/actor-appearance"
                    expected = {"entity_id", "frame_index"} if exporting else {"entity_id"}
                    if set(body) != expected or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Appearance requests accept only an imported entity_id and export frame; source bindings are project-controlled")
                    if not any(a["semantic_id"] == body["entity_id"] for a in self.server.project.imports.get(self.server.project.active_scene, {}).get("actors", [])):
                        raise ProjectError("Appearance request requires an actor in the active scene")
                    if route == "/api/actor-appearance-options":
                        self._json(200, self.server.project.appearance_options(body["entity_id"]))
                        return
                    frame_index = body.get("frame_index")
                    if exporting and (type(frame_index) is not int or frame_index < 0):
                        raise ProjectError("Choose a nonnegative animation frame index to export")
                    preview = self.server.actor_appearance_preview(body["entity_id"])
                    self._json(200, self.server.export_preview(preview, frame_index) if exporting else preview)
                    return
                if route == "/api/actor-script":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Script inspection accepts only an imported entity_id; bytes, addresses and paths are not accepted")
                    self._json(200, self.server.actor_script_preview(body["entity_id"]))
                    return
                if route in ("/api/actor-animation-preview", "/api/export/actor-animation"):
                    exporting = route == "/api/export/actor-animation"
                    allowed = {"entity_id", "frame_index"} if exporting else {"entity_id"}
                    if set(body) - allowed or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Actor animation accepts an imported entity_id and export frame only; source bindings and output paths are project-controlled")
                    frame_index = body.get("frame_index")
                    if exporting and (type(frame_index) is not int or frame_index < 0):
                        raise ProjectError("Choose a nonnegative animation frame index to export")
                    preview = self.server.actor_animation_preview(body["entity_id"])
                    self._json(200, self.server.export_preview(preview, frame_index) if exporting else preview)
                    return
                if route == "/api/scene-preview":
                    if body:
                        raise ProjectError("Scene preview uses the active imported scene; client geometry and paths are not accepted")
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    self._json(200, self.server.scene_previews.preview(
                        self.server.project, self.server.model_preview, load_scene_actor_animation_catalog))
                    return
                if route in ("/api/preview", "/api/animation-preview", "/api/export/model"):
                    project = self.server.project
                    if not project.disc_path:
                        raise ProjectError("Model preview requires the project's user-owned disc")
                    if not isinstance(body.get("asset_id"), str):
                        raise ProjectError("asset_id must be a model asset string")
                    asset = project.assets.records.get(body.get("asset_id"))
                    if asset is None:
                        raise ProjectError("Unknown model asset")
                    clip_id = body.get("clip_id") if route != "/api/preview" else None
                    if (route == "/api/animation-preview" or clip_id is not None) and clip_id not in ("idle", "walk"):
                        raise ProjectError("Choose a supported animation clip: idle or walk")
                    if route == "/api/export/model":
                        if set(body) - {"asset_id", "clip_id", "frame_index"}:
                            raise ProjectError("Export accepts asset, clip and frame only; geometry and output paths are project-controlled")
                        frame_index = body.get("frame_index")
                        if clip_id is None and frame_index is not None:
                            raise ProjectError("A frame export requires a supported animation clip")
                        if clip_id is not None and (type(frame_index) is not int or frame_index < 0):
                            raise ProjectError("Choose a nonnegative animation frame index to export")
                        preview = self.server.model_preview(asset, clip_id)
                        self._json(200, self.server.export_preview(preview, frame_index))
                        return
                    self._json(200, self.server.model_preview(asset, clip_id))
                    return
                self._command(urlsplit(self.path).path, body)
                self._json(200, self.server.state())
        except (RetailImportError, ProjectError, ValueError, KeyError, TypeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _command(self, route: str, body: dict) -> None:
        project = self.server.project
        # Reject malformed field types before they reach filesystem/importer services.
        required_strings = {"/api/project/new": ("path",), "/api/project/open": ("path",),
                            "/api/import": ("disc",), "/api/scene": ("scene_id",)}
        if route == "/api/command" and body.get("type") == "clear_texture_replacement":
            if set(body) != {"type", "asset_id"}:
                raise ProjectError("Texture clear accepts only an asset identity")
            required_strings[route] = ("asset_id",)
        if route == "/api/command" and body.get("type") in (
                "set_transform", "clear_transform", "create_actor_template", "apply_actor_template", "set_actor_appearance", "clear_actor_appearance", "set_dialogue_text", "clear_dialogue_text"):
            required_strings[route] = ("entity_id",)
        if route == "/api/command" and body.get("type") in ("set_actor_appearance", "clear_actor_appearance"):
            allowed = {"type", "entity_id", "donor_entity_id"} if body["type"] == "set_actor_appearance" else {"type", "entity_id"}
            if set(body) != allowed:
                raise ProjectError("Appearance commands accept an entity and donor identity only")
        if route == "/api/command" and body.get("type") in ("set_dialogue_text", "clear_dialogue_text"):
            allowed = {"type", "entity_id", "run_id", "text"} if body["type"] == "set_dialogue_text" else {"type", "entity_id", "run_id"}
            if set(body) != allowed:
                raise ProjectError("Dialogue commands accept only entity/run identities and authored text")
        for key in required_strings.get(route, ()):
            if not isinstance(body.get(key), str) or not body[key].strip():
                raise ProjectError(f"{key} must be a nonempty string")
        for key in ("scene", "profile_id", "expected_epoch_id", "entity_id"):
            if key in body and body[key] is not None and not isinstance(body[key], str):
                raise ProjectError(f"{key} must be a string or null")
        if route in ("/api/project/new", "/api/project/open"):
            if project.dirty and (project.imports or project.overrides):
                raise ProjectError("Save current project before opening or creating another")
            path = Path(body["path"]).expanduser()
            if route.endswith("/open"):
                self.server.project = ProjectService.open(path)
            else:
                if path.exists() and not path.is_dir():
                    raise ProjectError("Project path must be a directory")
                if (path / "project.legaia.json").exists():
                    raise ProjectError("A project already exists at this path; open it instead")
                name = body.get("name", "Legaia project")
                if not isinstance(name, str) or not name.strip() or len(name) > 128:
                    raise ProjectError("Project name must contain 1 to 128 characters")
                self.server.project = ProjectService(path, name.strip())
        elif route == "/api/project/save":
            project.save()
        elif route == "/api/build":
            from .build import build_project
            if project.mode != "edit":
                raise ProjectError("Build requires Edit mode")
            self.server.last_build = None
            self.server.last_build = build_project(project)
        elif route == "/api/run/configure":
            self.server.runs.configure(project, body)
        elif route == "/api/run":
            from .build import build_project
            if project.mode != "edit":
                raise ProjectError("Build & Run requires Edit mode")
            self.server.last_build = build_project(project)
            self.server.runs.start(project, self.server.last_build)
        elif route == "/api/run/stop":
            run = self.server.runs.status()
            self.server.runs.stop()
            if run and self.server.observer.port == run.get("debug_port"):
                self.server.observer.close()
                self.server.live_status = {"available": False, "state": "unavailable", "reason": {"message": "Owned runtime stopped"}}
                project.mode = "edit"
                project.correlate_runtime(self.server.live_status)
        elif route == "/api/run/attach":
            run = self.server.runs.status()
            if not run or not run.get("ready") or run.get("project") != str(project.root):
                raise ProjectError("This project's owned runtime has not passed readiness checks")
            from integrations.legaia.observer.service import ObserverService
            self.server.observer.close()
            self.server.observer = ObserverService(port=run["debug_port"])
            self.server.live_status = self.server.observer.discover(body.get("profile_id"))
            observed = (self.server.live_status.get("runtime") or {}).get("runtime", {})
            expected = run["runtime_identity"]["runtime"]["process_instance_id"]
            if observed.get("process_instance_id") != expected:
                self.server.observer.close()
                self.server.live_status = {"available": False, "state": "unavailable", "reason": {"message": "Runtime identity changed before attach"}}
                project.mode = "edit"
                project.correlate_runtime(self.server.live_status)
                raise ProjectError("Runtime identity changed before attach")
        elif route == "/api/import":
            from importer.pipeline import import_scene
            metadata = import_scene(Path(body["disc"]), body.get("scene", "town01"))
            project.import_metadata(metadata, body["disc"])
        elif route == "/api/selection":
            project.select(body.get("entity_id"))
        elif route == "/api/scene":
            project.set_scene(body["scene_id"])
        elif route == "/api/command":
            project.command(body)
        elif route == "/api/undo":
            project.undo()
        elif route == "/api/redo":
            project.redo()
        elif route == "/api/runtime/discover":
            self.server.live_status = self.server.observer.discover(body.get("profile_id"))
            if not self.server.live_status["available"]:
                project.mode = "edit"
        elif route == "/api/runtime/observe":
            if type(body.get("include_actors", False)) is not bool:
                raise ProjectError("include_actors must be a boolean")
            self.server.live_status = self.server.observer.observe(
                body.get("profile_id"), expected_epoch_id=body.get("expected_epoch_id"),
                include_actors=body.get("include_actors", False))
            if not self.server.live_status["available"]:
                project.mode = "edit"
        elif route == "/api/mode":
            mode = body.get("mode")
            if mode not in ("edit", "live"):
                raise ProjectError("Mode must be edit or live")
            if mode == "live":
                self.server.live_status = self.server.observer.observe(body.get("profile_id"))
                if not self.server.live_status["available"]:
                    project.mode = "edit"
                    project.correlate_runtime(self.server.live_status)
                    raise ProjectError(self.server.live_status["reason"]["message"])
            project.mode = mode
        else:
            raise ProjectError("Unsupported editor command route")
        if route in ("/api/project/new", "/api/project/open", "/api/import", "/api/command", "/api/undo", "/api/redo"):
            self.server.last_build = None
        if route in ("/api/project/new", "/api/project/open", "/api/import"):
            self.server.texture_catalogs.clear()
        if route in ("/api/runtime/discover", "/api/runtime/observe", "/api/run/attach", "/api/mode"):
            project.correlate_runtime(self.server.live_status)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open the local Legaia Trace authoring editor")
    parser.add_argument("--project", type=Path, required=True, help="Project directory; existing projects are reopened")
    parser.add_argument("--port", type=int, default=4388)
    parser.add_argument("--runtime-port", type=int, default=4370)
    args = parser.parse_args(argv)
    project = ProjectService.open(args.project) if (args.project / "project.legaia.json").exists() else ProjectService(args.project)
    with EditorServer(("127.0.0.1", args.port), project, runtime_port=args.runtime_port) as server:
        print(f"Legaia Trace: http://127.0.0.1:{server.server_port} | {project.root}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
