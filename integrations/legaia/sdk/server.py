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


def _transition_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.transition_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "transitions": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("Transitions", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish transition-write safety."]}


def _movement_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.movement_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptMovement", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish movement-write safety."]}


def _flag_authoring_report(project, identifier):
    """Unsupported authoring must not suppress the read-only script report."""
    try:
        return project.flag_options(identifier)
    except (RetailImportError, ProjectError) as exc:
        return {"supported": False, "reason": str(exc), "targets": [],
                "unresolved_overrides": sorted(project.overrides.get(identifier, {}).get("ScriptFlags", {}).get("entries", {})),
                "limitations": ["Read-only inspection does not establish flag-write safety."]}


def _animation_export_choice(body):
    """Exactly one export representation, before expensive source decoding."""
    import math
    if 'clip_fps' in body:
        fps = body['clip_fps']
        if 'frame_index' in body or type(fps) not in (int, float) or not math.isfinite(fps) or not 1 <= fps <= 120:
            raise ProjectError('Choose either a frame index or an explicit clip rate from 1 to 120 fps')
        return None, fps
    frame = body.get('frame_index')
    if type(frame) is not int or frame < 0:
        raise ProjectError('Choose a nonnegative animation frame index to export')
    return frame, None


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
        state["capabilities"]["model_shape_authoring"] = bool(self.project.disc_path)
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
        state["capabilities"]["actor_candidate_inspection"] = bool(self.project.disc_path)
        state["capabilities"]["actor_dialogue_authoring"] = bool(self.project.disc_path)
        state["capabilities"]["actor_appearance"] = bool(self.project.disc_path)
        state["capabilities"]["resource_catalog"] = bool(self.project.disc_path and self.project.active_scene)
        state["capabilities"]["scene_transitions"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["scene_flags"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["texture_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["texture_replacement"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["field_map_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["trigger_script_preview"] = state["capabilities"]["resource_catalog"]
        state["capabilities"]["build"] = bool(self.project.disc_path and self.project.imports)
        if self.last_build is None:
            state["build"] = None
        else:
            from .build import authored_state_key
            from copy import deepcopy
            state["build"] = deepcopy(self.last_build)
            state["build"]["current"] = self.last_build.get("authored_state_key") == authored_state_key(self.project)
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

    def actor_animation_preview(self, entity_id: str, representation: str = "imported") -> dict:
        """Resolve an imported actor; clients cannot supply a model or clip binding."""
        from importer.pipeline import _disc_context
        from importer.scene_animation import load_scene_actor_animation_catalog
        project = self.project
        if representation not in ("imported", "authored"):
            raise ProjectError("Animation representation must be imported or authored")
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
            overrides = {a["semantic_id"]: project.overrides[a["semantic_id"]]["AnimationChannels"]
                         for a in document["actors"] if "AnimationChannels" in project.overrides.get(a["semantic_id"], {})}
            initial_id = actor["placement_fields"].get("animation_id")
            clip_id = f"animation://{document['scene']['name']}/scene-anm/{initial_id - 1:04d}" if type(initial_id) is int and initial_id > 0 else None
            affected = any(value["animation_id"] == clip_id for value in overrides.values())
            if representation == "authored":
                if not affected:
                    raise ProjectError("Actor's imported clip has no authored animation channels")
                animation = catalog.authored_bank_preview(actor, asset, overrides)
            else:
                animation = catalog.animation_preview(actor, asset)
            preview = self.model_preview(asset, prepared=animation.pop("geometry"))
            preview["frames"] = animation.pop("frames")
            animation.update(source_clip_id=animation["clip_id"], clip_id="authored-channels" if representation == "authored" else "scene-header", entity_id=entity_id, representation=representation)
            preview["animation"] = animation
            preview["animation_support"] = {
                "supported": True, "clips": [{"id": "scene-header", "label": "Imported scene animation"}],
                "evidence": "verified_man_header_initial_animation_not_runtime_script_state"}
            if affected:
                preview["animation_support"]["clips"].append({"id": "authored-channels", "label": "Authored channel overrides"})
        return preview

    def export_actor_drafts(self, entity_id: str | None = None) -> dict:
        from uuid import uuid4
        from .draft_build import export_draft_disc
        project = self.project
        if project.mode != 'edit':
            raise ProjectError('Draft export requires Edit mode')
        draft = project.actor_drafts.get(entity_id)
        if entity_id is not None and (draft is None or draft['scene_id'] != project.active_scene):
            raise ProjectError('Draft export requires a draft in the active scene')
        directory = (project.root / 'Builds' / ('experimental-drafts-' + uuid4().hex)).resolve()
        if not directory.is_relative_to(project.root.resolve()):
            raise ProjectError('Draft export directory escapes the project root')
        report = export_draft_disc(project, entity_id, directory)
        return dict(report_path=str(directory / 'report.json'),
                    input_project_path=str(directory / 'Inputs' / 'project.legaia.json'),
                    disc_path=report['disc']['output_path'],
                    output_sha256=report['disc']['output_sha256'],
                    gameplay_verified=False, experimental=True)

    def actor_candidate_inspection(self, entity_id: str) -> dict:
        from importer.actor_candidate_inspection import inspect_actor_candidate
        project = self.project
        if not project.disc_path:
            raise ProjectError("Actor candidate inspection requires the project's disc")
        document = project.imports.get(project.active_scene)
        draft = getattr(project, 'actor_drafts', {}).get(entity_id)
        if draft:
            project._validate_actor_draft(entity_id,draft)
            if draft['scene_id'] != project.active_scene:
                raise ProjectError('Actor draft is outside the active scene')
        donor_id = draft['donor_entity_id'] if draft else entity_id
        actor = next((item for item in (document or {}).get("actors", [])
                      if item["semantic_id"] == donor_id), None)
        if actor is None:
            raise ProjectError("Actor candidate requires an imported actor in the active scene")
        overrides = project.overrides.get(entity_id, {})
        authored = draft['position'] if draft else overrides.get("Transform", {}).get("position", {})
        position = {axis: authored[axis] for axis in ("x", "z") if axis in authored}
        report = inspect_actor_candidate(project.disc_path, document["scene"]["name"],
                                         actor["source_record"]["record_index"], position=position or None)
        report["entity_id"] = entity_id
        report["donor_entity_id"] = donor_id
        report["representation"] = "positioned_retail_donor_candidate" if position else "retail_donor_candidate"
        report["includes_project_overrides"] = bool(position)
        report["included_overrides"] = {"Transform": {"position": position}} if position else {}
        report["excluded_override_components"] = sorted(key for key in overrides if key != "Transform")
        report["excluded_transform_axes"] = sorted(set(authored)-set(position))
        if draft:
            report['representation'] = 'authored_npc_draft_candidate'
        return report

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
            report["movement_authoring"] = _movement_authoring_report(project, entity_id)
            report["flag_authoring"] = _flag_authoring_report(project, entity_id)
            try:
                report["dialogue_authoring"] = project.dialogue_options(entity_id)
                report["transition_authoring"] = _transition_authoring_report(project, entity_id)
            except (RetailImportError, ProjectError) as exc:
                reason = ("Read-only streaming script inspection. Text and transition authoring are not yet supported for this scene."
                          if report.get("man_source", {}).get("source_kind") == "raw_streaming_man" else str(exc))
                report["dialogue_authoring"] = {"supported": False, "reason": reason, "runs": [],
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

    def export_preview(self, preview: dict, frame_index: int | None, clip_fps: float | None = None) -> dict:
        from .build import _guard_output
        from .project import atomic_write
        from importer.export import write_model_export
        output = self.project.root / "Exports"
        _guard_output(output / ".gitignore", self.project.root)
        result = write_model_export(preview, output, frame_index, clip_fps=clip_fps)
        if not (output / ".gitignore").exists():
            atomic_write(output / ".gitignore", b"*\n")
        return result

    def model_preview(self, asset: dict, clip_id: str | None = None, *, prepared: dict | None = None, effective_shape: bool = False, project_view=None) -> dict:
        from importer.assets import load_model_preview
        from importer.animation import animation_capabilities, load_animation_preview
        from importer.textures import (associate_material, load_asset_texture_catalog,
                                       load_scene_texture_catalog, uses_field_party_textures)
        project = self.project if project_view is None else project_view
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
        if effective_shape and asset['semantic_id'] in project.model_overrides:
            from importer.model_authoring import preview_model_shape
            binding = project.model_overrides[asset['semantic_id']]
            preview = preview_model_shape(preview, project.read_model_replacement(asset['semantic_id'], binding), binding)
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
            material['blend'] = {
                'enabled': bool(material.get('semi_transparent')),
                'mode': ((material['tpage'] >> 5) & 3) if material.get('textured') else 0,
                'texel_gate': 'stp_bit' if material.get('textured') else 'all_fragments',
                'evidence': 'decoded_primitive_ABE_and_tpage_ABR; untextured_ABR0_reference_default',
            }
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
            stp = result.pop("stp", None)
            if rgba is not None:
                if stp is None or len(stp) * 4 != len(rgba) or any(bit not in (0, 1) for bit in stp):
                    raise ProjectError('Texture transparency mask does not match decoded pixels')
                if len(rgba) + len(stp) > budget:
                    result = {"status": "unsupported", "reason": "Decoded texture preview byte budget exceeded"}
                else:
                    budget -= len(rgba) + len(stp)
                    result["rgba_base64"] = base64.b64encode(rgba).decode("ascii")
                    result["stp_base64"] = base64.b64encode(stp).decode("ascii")
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
        try:
            self._write_response(status, content, content_type)
        except (ConnectionError, TimeoutError):
            # The client may close a tab while a scene preview is computing.
            # A failed socket write cannot be repaired with another response.
            self.close_connection = True

    def _write_response(self, status: int, content: bytes, content_type: str) -> None:
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
                 "/scene-renderer.js": ("scene-renderer.js", "text/javascript"),
                 "/script-paths.js": ("script-paths.js", "text/javascript"),
                 "/texture-usage.js": ("texture-usage.js", "text/javascript")}
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
            if urlsplit(self.path).path in ('/api/model-shape-replacement', '/api/animation-record-replacement', '/api/animation-record-preview', '/api/animation-file-pose-preview'):
                request_limit = 6 * 1024 * 1024
            if urlsplit(self.path).path in ('/api/model-obj-replacement', '/api/model-json-replacement', '/api/model-file-preview', '/api/texture-json-replacement', '/api/texture-file-preview'):
                request_limit = 24 * 1024 * 1024
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
                if route == '/api/scene-catalog':
                    if set(body) != {'disc', 'offset', 'prefix'} or not isinstance(body['disc'], str) or not body['disc'].strip() or type(body['offset']) is not int or not 0 <= body['offset'] <= 65536 or not isinstance(body['prefix'], str) or len(body['prefix']) > 64:
                        raise ProjectError('Scene catalog requires a disc path, bounded integer offset and name prefix')
                    from importer.pipeline import list_scenes
                    self._json(200, list_scenes(body['disc'], offset=body['offset'], limit=16, prefix=body['prefix']))
                    return
                if route == '/api/texture-file-preview':
                    if set(body) != {'asset_id','format','palette_index','content_base64'} or not isinstance(body['asset_id'],str) or not isinstance(body['content_base64'],str) or len(body['content_base64']) > 22369624:
                        raise ProjectError('Texture preview requires identity, format, palette and bounded file bytes')
                    try:
                        content = base64.b64decode(body['content_base64'],validate=True)
                    except ValueError as exc:
                        raise ProjectError('Texture preview requires valid base64') from exc
                    self._json(200,self.server.project.preview_texture_file(body['asset_id'],content,body['format'],body['palette_index']))
                    return
                if route == '/api/texture-json-source':
                    if set(body) != {'asset_id','layer'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Texture JSON download requires texture identity and layer')
                    self._json(200,self.server.project.texture_json_source(body['asset_id'],body['layer']))
                    return
                if route == '/api/texture-json-replacement':
                    if set(body) != {'asset_id','json_base64'} or not isinstance(body['asset_id'],str) or not isinstance(body['json_base64'],str) or len(body['json_base64']) > 22369624:
                        raise ProjectError('Texture JSON import requires identity and at most 16 MiB of JSON')
                    try:
                        content = base64.b64decode(body['json_base64'],validate=True)
                    except ValueError as exc:
                        raise ProjectError('Texture JSON requires valid base64') from exc
                    self.server.project.set_texture_json(body['asset_id'],content)
                    self._json(200,self.server.state())
                    return
                if route == '/api/texture-pixel-source':
                    if set(body) != {'asset_id','palette_index','x','y'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Pixel inspection requires texture, palette and pixel coordinates')
                    self._json(200, self.server.project.texture_pixel_source(body['asset_id'], body['palette_index'], body['x'], body['y']))
                    return
                if route == '/api/texture-pixel-index':
                    if set(body) != {'asset_id','x','y','palette_entry','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Pixel authoring requires texture, coordinates, palette entry and inspected hash')
                    self.server.project.set_texture_pixel_index(body['asset_id'], body['x'], body['y'], body['palette_entry'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/texture-index-rectangle':
                    if set(body) != {'asset_id','x','y','width','height','palette_entry','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Rectangle fill requires texture, image bounds, index and inspected hash')
                    self.server.project.set_texture_index_rectangle(body['asset_id'],body['x'],body['y'],body['width'],body['height'],body['palette_entry'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/texture-palette-source':
                    if set(body) != {'asset_id','palette_index'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Palette inspection requires texture identity and palette index')
                    self._json(200, self.server.project.texture_palette_source(body['asset_id'], body['palette_index']))
                    return
                if route == '/api/texture-palette-word':
                    if set(body) != {'asset_id','palette_index','entry_index','word','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Palette authoring requires texture, palette/entry, word and inspected hash')
                    self.server.project.set_texture_palette_word(body['asset_id'], body['palette_index'], body['entry_index'], body['word'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-object-rotation':
                    if set(body) != {'asset_id','object_index','axis','quarter_turns','expected_sha256'} or not isinstance(body['asset_id'],str):
                        raise ProjectError('Object rotation requires model, object, axis, quarter turns and inspected hash')
                    self.server.project.rotate_model_object(body['asset_id'],body['object_index'],body['axis'],body['quarter_turns'],body['expected_sha256'])
                    self._json(200,self.server.state())
                    return
                if route == '/api/model-object-translation':
                    if set(body) != {'asset_id','object_index','offset','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Object translation requires asset, object, XYZ offset and inspected hash')
                    self.server.project.translate_model_object(body['asset_id'], body['object_index'],
                                                               body['offset'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-vector':
                    if set(body) != {'asset_id','object_index','kind','vector_index','values','expected_sha256'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model vector editing requires asset, object/kind/vector, XYZ and inspected hash')
                    self.server.project.set_model_vector(body['asset_id'], body['object_index'], body['kind'],
                                                         body['vector_index'], body['values'], body['expected_sha256'])
                    self._json(200, self.server.state())
                    return
                if route == '/api/model-file-preview':
                    if set(body) != {'asset_id', 'format', 'content_base64'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model preview requires asset identity, format and content_base64')
                    encoded = body['content_base64']
                    if not isinstance(encoded, str) or len(encoded) > 22369624:
                        raise ProjectError('Model preview exceeds the 16 MiB file limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model preview requires valid base64') from exc
                    self._json(200, self.server.project.preview_model_file(body['asset_id'], payload, body['format']))
                    return
                if route in ('/api/model-shape-replacement', '/api/model-obj-replacement', '/api/model-json-replacement'):
                    json_upload = route == '/api/model-json-replacement'
                    obj_upload = route == '/api/model-obj-replacement'
                    payload_key = 'json_base64' if json_upload else 'obj_base64' if obj_upload else 'tmd_base64'
                    if set(body) != {'asset_id',payload_key} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Model shape upload requires asset_id and the selected format payload only')
                    encoded = body[payload_key]
                    if not isinstance(encoded, str) or len(encoded) > (22369624 if obj_upload or json_upload else 5592408):
                        raise ProjectError('Model shape exceeds the format size limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Model shape requires valid base64') from exc
                    if json_upload:
                        self.server.project.set_model_json(body['asset_id'], payload)
                    elif obj_upload:
                        self.server.project.set_model_obj(body['asset_id'], payload)
                    else:
                        self.server.project.set_model_replacement(body['asset_id'], payload)
                    self._json(200, self.server.state())
                    return
                if route in ('/api/model-shape-preview', '/api/export/model-shape'):
                    if set(body) != {'asset_id'} or not isinstance(body['asset_id'], str):
                        raise ProjectError('Authored model preview accepts an asset identity only')
                    from importer.assets import decode_tmd
                    project = self.server.project
                    binding = project.model_overrides.get(body['asset_id'])
                    if binding is None or binding['source_scene_id'] != project.active_scene:
                        raise ProjectError('No authored model shape in the active scene')
                    asset = project.assets.records.get(body['asset_id'])
                    if asset is None:
                        raise ProjectError('Unknown model asset')
                    content = project.read_model_replacement(body['asset_id'], binding)
                    preview = decode_tmd(content)
                    preview.update(semantic_id=body['asset_id'], source_record=asset['source_record'],
                                   representation='authored-shape', authored_shape=dict(binding))
                    preview = self.server.model_preview(asset, prepared=preview)
                    self._json(200, self.server.export_preview(preview, None) if route.endswith('model-shape') else preview)
                    return
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
                if route == "/api/worldmap-menu":
                    if body or not self.server.project.disc_path:
                        raise ProjectError('World-map inspection requires the project disc and no supplied source data')
                    from importer.worldmap_menu import load_worldmap_menu
                    self._json(200, load_worldmap_menu(self.server.project.disc_path))
                    return
                if route == '/api/project-flags':
                    if body:
                        raise ProjectError('Project flag discovery uses imported sources only')
                    from .resources import project_flag_index
                    self._json(200,project_flag_index(self.server.project))
                    return
                if route == "/api/scene-flags":
                    if body:
                        raise ProjectError("Flag discovery uses the active scene; no client source bindings are accepted")
                    from .resources import scene_flag_index
                    from .flags import observed_node_flags
                    result = scene_flag_index(self.server.project)
                    result["runtime_snapshot"] = observed_node_flags(self.server.live_status, result["scene_id"])
                    self._json(200, result)
                    return
                if route == "/api/scene-transitions":
                    if body:
                        raise ProjectError("Transition discovery uses the active scene; no client source bindings are accepted")
                    from .resources import scene_transition_graph
                    self._json(200, scene_transition_graph(self.server.project))
                    return
                if route == "/api/resource-catalog":
                    if body:
                        raise ProjectError("Resource discovery takes no client source bindings")
                    from .resources import refresh_resource_catalog
                    self._json(200, refresh_resource_catalog(self.server.project))
                    return
                if route == "/api/partition-two-script":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Partition-two inspection accepts a structural entity_id only")
                    from .resources import partition_two_script_preview
                    report = partition_two_script_preview(self.server.project, body["entity_id"])
                    report["dialogue_authoring"] = self.server.project.dialogue_options(body["entity_id"])
                    report["transition_authoring"] = _transition_authoring_report(self.server.project, body["entity_id"])
                    report["movement_authoring"] = _movement_authoring_report(self.server.project, body["entity_id"])
                    report["flag_authoring"] = _flag_authoring_report(self.server.project, body["entity_id"])
                    self._json(200, report)
                    return
                if route == "/api/trigger-script":
                    if set(body) != {"asset_id"} or not isinstance(body["asset_id"], str) or not body["asset_id"]:
                        raise ProjectError("Trigger script inspection accepts a catalog identity only; partition and source spans are source-controlled")
                    from .resources import trigger_script_preview
                    report = trigger_script_preview(self.server.project, body["asset_id"])
                    identifier = "scene://" + report["script_id"].removeprefix("script://")
                    report["dialogue_authoring"] = self.server.project.dialogue_options(identifier)
                    report["transition_authoring"] = _transition_authoring_report(self.server.project, identifier)
                    report["movement_authoring"] = _movement_authoring_report(self.server.project, identifier)
                    report["flag_authoring"] = _flag_authoring_report(self.server.project, identifier)
                    self._json(200, report)
                    return
                if route == "/api/model-shape-source":
                    if set(body) - {"asset_id", "format", "layer"} or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Model source accepts a catalog identity only")
                    from .resources import model_shape_source
                    self._json(200, model_shape_source(self.server.project, body["asset_id"], body.get('format','tmd'), body.get('layer','imported')))
                    return
                if route == "/api/field-map-preview":
                    if set(body) - {"asset_id", "layer"} or not isinstance(body.get("asset_id"), str) or not body["asset_id"]:
                        raise ProjectError("Field map preview accepts a catalog identity only; coordinates and paths are source-controlled")
                    from .resources import field_map_preview
                    self._json(200, field_map_preview(self.server.project, body["asset_id"], body.get("layer", "imported")))
                    return
                if route == "/api/texture-preview":
                    if (not {"asset_id", "palette_index"} <= set(body) or set(body) - {"asset_id", "palette_index", "layer"} or
                            not isinstance(body.get("asset_id"), str) or not body["asset_id"] or
                            type(body.get("palette_index")) is not int or body["palette_index"] < 0):
                        raise ProjectError("Texture preview requires a resource identity and nonnegative palette index only")
                    from .resources import texture_preview
                    self._json(200, texture_preview(self.server.project, body["asset_id"], body["palette_index"], body.get("layer", "effective")))
                    return
                if route == '/api/animation-record-source':
                    if set(body) - {'entity_id', 'layer', 'format'} or not isinstance(body.get('entity_id'), str) or not body['entity_id'].strip():
                        raise ProjectError('Animation source requires actor identity and optional layer and format only')
                    payload, binding = self.server.project.animation_record_source(body['entity_id'], body.get('layer', 'retail'), body.get('format', 'record'))
                    self._json(200, {'entity_id': body['entity_id'], 'binding': binding,
                                     'representation': body.get('layer', 'retail'), 'byte_length': len(payload),
                                     'record_base64': base64.b64encode(payload).decode('ascii')})
                    return
                if route in ('/api/animation-record-replacement', '/api/animation-record-preview', '/api/animation-file-pose-preview'):
                    if not {'entity_id', 'record_base64'} <= set(body) or set(body) - {'entity_id', 'record_base64', 'format'} or not isinstance(body['entity_id'], str) or not body['entity_id'].strip():
                        raise ProjectError('Animation upload requires actor identity and record_base64 and optional format')
                    encoded = body['record_base64']
                    if not isinstance(encoded, str) or len(encoded) > 5592408:
                        raise ProjectError('Animation record exceeds the 4 MiB limit')
                    try:
                        payload = base64.b64decode(encoded, validate=True)
                    except ValueError as exc:
                        raise ProjectError('Animation record requires valid base64') from exc
                    if route == '/api/animation-file-pose-preview':
                        animation, asset = self.server.project.animation_file_pose_preview(body['entity_id'], payload, body.get('format', 'record'))
                        preview = self.server.model_preview(asset, prepared=animation.pop('geometry'))
                        preview['frames'] = animation.pop('frames')
                        animation.update(source_clip_id=animation['clip_id'], clip_id='file-preview', entity_id=body['entity_id'])
                        preview['animation'] = animation
                        preview['animation_support'] = {'supported': True, 'clips': [], 'evidence': 'proposed_file_not_applied_or_runtime_verified'}
                        self._json(200, preview)
                        return
                    if route == '/api/animation-record-preview':
                        self._json(200, self.server.project.preview_animation_record(body['entity_id'], payload, body.get('format', 'record')))
                        return
                    self.server.project.import_animation_record(body['entity_id'], payload, body.get('format', 'record'))
                    self._json(200, self.server.state())
                    return
                if route == "/api/animation-channel-values":
                    if set(body) != {"entity_id", "frame_index", "object_index"} or not isinstance(body.get("entity_id"), str):
                        raise ProjectError("Channel inspection requires an actor, frame and object index only")
                    self._json(200, self.server.project.animation_channel_values(body["entity_id"], body["frame_index"], body["object_index"]))
                    return
                if route == "/api/animation-authoring-options":
                    if set(body) != {"entity_id"} or not isinstance(body.get("entity_id"), str):
                        raise ProjectError("Animation options require an actor identity only")
                    self._json(200, self.server.project.animation_authoring_options(body["entity_id"]))
                    return
                if route in ("/api/actor-appearance-options", "/api/actor-appearance-preview", "/api/export/actor-appearance"):
                    exporting = route == "/api/export/actor-appearance"
                    expected = {"entity_id", "clip_fps" if "clip_fps" in body else "frame_index"} if exporting else {"entity_id"}
                    if set(body) != expected or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Appearance requests accept only an imported entity_id and export frame or clip rate; source bindings are project-controlled")
                    if not any(a["semantic_id"] == body["entity_id"] for a in self.server.project.imports.get(self.server.project.active_scene, {}).get("actors", [])):
                        raise ProjectError("Appearance request requires an actor in the active scene")
                    if route == "/api/actor-appearance-options":
                        self._json(200, self.server.project.appearance_options(body["entity_id"]))
                        return
                    frame_index = body.get("frame_index")
                    clip_fps = None
                    if exporting:
                        frame_index, clip_fps = _animation_export_choice(body)
                    preview = self.server.actor_appearance_preview(body["entity_id"])
                    self._json(200, self.server.export_preview(preview, frame_index, clip_fps) if exporting else preview)
                    return
                if route == "/api/export/actor-drafts":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Draft export accepts only a draft entity_id")
                    self._json(200, self.server.export_actor_drafts(body["entity_id"]))
                    return
                if route == '/api/export/project':
                    if body:
                        raise ProjectError('Project export accepts no fields')
                    self._json(200, self.server.export_actor_drafts())
                    return
                if route in ('/api/exports', '/api/exports/verify'):
                    from .export_history import list_exports, verify_export
                    if route == '/api/exports':
                        if body:
                            raise ProjectError('Export history accepts no fields')
                        result = list_exports(self.server.project)
                    else:
                        if set(body) != {'id'}:
                            raise ProjectError('Export verification requires an export id')
                        result = verify_export(self.server.project, body['id'])
                    self._json(200, result)
                    return
                if route == '/api/exports/open-copy':
                    from .export_history import copy_export_inputs
                    if set(body)!={'id'}:
                        raise ProjectError('Open export copy requires an export id')
                    if self.server.project.mode!='edit' or self.server.project.dirty:
                        raise ProjectError('Save the current project in Edit mode before opening an export copy')
                    destination=copy_export_inputs(self.server.project,body['id'])
                    self._command('/api/project/open',{'path':str(destination)})
                    self._json(200,self.server.state())
                    return
                if route == "/api/actor-candidate-inspection":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Actor candidate inspection accepts only an imported entity_id")
                    self._json(200, self.server.actor_candidate_inspection(body["entity_id"]))
                    return
                if route == "/api/actor-script":
                    if set(body) != {"entity_id"} or not isinstance(body["entity_id"], str) or not body["entity_id"]:
                        raise ProjectError("Script inspection accepts only an imported entity_id; bytes, addresses and paths are not accepted")
                    self._json(200, self.server.actor_script_preview(body["entity_id"]))
                    return
                if route in ("/api/actor-animation-preview", "/api/export/actor-animation"):
                    exporting = route == "/api/export/actor-animation"
                    allowed = {"entity_id", "representation", "frame_index", "clip_fps"} if exporting else {"entity_id", "representation"}
                    if set(body) - allowed or not isinstance(body.get("entity_id"), str) or not body["entity_id"]:
                        raise ProjectError("Actor animation accepts an imported entity_id and export frame or clip rate only; source bindings and output paths are project-controlled")
                    frame_index = body.get("frame_index")
                    clip_fps = None
                    if exporting:
                        frame_index, clip_fps = _animation_export_choice(body)
                    preview = self.server.actor_animation_preview(body["entity_id"], body.get("representation", "imported"))
                    self._json(200, self.server.export_preview(preview, frame_index, clip_fps) if exporting else preview)
                    return
                if route in ("/api/scene-preview", "/api/export/scene"):
                    exporting = route == "/api/export/scene"
                    if set(body) - ({'representation', 'source_key', 'entity_id'} if exporting else {'representation'}):
                        raise ProjectError("Scene preview uses the active imported scene; client geometry and paths are not accepted")
                    from .scene_preview import preview_project, source_key
                    from importer.scene_animation import load_scene_actor_animation_catalog
                    from importer.environment import load_environment_preview_catalog
                    from .terrain_preview import terrain_preview
                    representation = body.get('representation', 'authored')
                    original_key = source_key(self.server.project)
                    if exporting and (not original_key or body.get("source_key") != original_key):
                        raise ProjectError("Scene export source changed; refresh the scene before exporting")
                    view = preview_project(self.server.project, representation)
                    preview = self.server.scene_previews.preview(
                        view, lambda asset, *args, **kwargs: self.server.model_preview(asset, *args, effective_shape=True, project_view=view, **kwargs),
                        load_scene_actor_animation_catalog, load_environment_preview_catalog, terrain_preview)
                    if source_key(self.server.project) != original_key:
                        raise ProjectError('Project changed during scene comparison preview')
                    preview['representation'] = representation
                    preview['project_source_key'] = original_key
                    if exporting:
                        from importer.scene_export import encode_scene_glb, select_scene_export_instance
                        if "entity_id" in body:
                            preview = select_scene_export_instance(preview, body["entity_id"])
                        from importer.export import write_encoded_glb
                        data, audit = encode_scene_glb(preview)
                        if source_key(self.server.project) != original_key:
                            raise ProjectError('Scene changed during export; refresh and retry')
                        self._json(200, write_encoded_glb(data, audit, self.server.project.root / 'Exports', 'scene'))
                    else:
                        self._json(200, preview)
                    return
                if route == '/api/terrain-point':
                    from .scene_preview import source_key, sample_preview_ground
                    from .terrain_preview import terrain_preview
                    import math
                    if (set(body)!={'x','z','source_key'} or any(type(body[a]) not in (int,float) or not math.isfinite(body[a]) or not 0<=body[a]<=16384 for a in ('x','z'))):
                        raise ProjectError('Terrain point requires bounded X/Z and a preview source key')
                    key=source_key(self.server.project)
                    if not key or body['source_key']!=key:
                        raise ProjectError('Terrain point source changed; refresh the scene')
                    sample=sample_preview_ground(terrain_preview(self.server.project),body['x'],body['z'])
                    if source_key(self.server.project)!=key:
                        raise ProjectError('Terrain source changed during sampling')
                    self._json(200,dict(source_key=key,scene_id=self.server.project.active_scene,
                        position=dict(x=body['x'],y=sample['y'] if sample else None,z=body['z']),
                        sample=sample,evidence='source terrain preview; runtime elevation unverified'))
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
                    if route == "/api/animation-preview" or clip_id is not None:
                        from importer.animation import animation_capabilities
                        clips = [clip['id'] for clip in animation_capabilities(asset)['clips']]
                        if not clips:
                            raise ProjectError("This model does not support animation preview with a verified clip")
                        if clip_id not in clips:
                            raise ProjectError("Choose a supported animation clip for this model: " + ", ".join(clips))
                    if route == "/api/export/model":
                        if set(body) - {"asset_id", "clip_id", "frame_index", "clip_fps"}:
                            raise ProjectError("Export accepts asset, clip and frame or clip rate only; geometry and output paths are project-controlled")
                        frame_index = body.get("frame_index")
                        if clip_id is None and (frame_index is not None or "clip_fps" in body):
                            raise ProjectError("A frame export requires a supported animation clip")
                        clip_fps = None
                        if clip_id is not None:
                            frame_index, clip_fps = _animation_export_choice(body)
                        preview = self.server.model_preview(asset, clip_id)
                        self._json(200, self.server.export_preview(preview, frame_index, clip_fps))
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
        if route == "/api/command" and body.get("type") in ("set_movement_target", "clear_movement_target"):
            allowed = {"type", "entity_id", "movement_id"}
            if body["type"] == "set_movement_target":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Movement commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "movement_id")
        if route == "/api/command" and body.get("type") in ("set_flag_bit", "clear_flag_bit"):
            allowed = {"type", "entity_id", "flag_id"}
            if body["type"] == "set_flag_bit":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Flag commands accept only owner/target identities and supported operand values")
            required_strings[route] = ("entity_id", "flag_id")
        if route == "/api/command" and body.get("type") in ("set_transition_entry", "clear_transition_entry"):
            allowed = {"type", "entity_id", "transition_id"}
            if body["type"] == "set_transition_entry":
                allowed.add("values")
            if set(body) != allowed:
                raise ProjectError("Transition commands accept only owner/transition identities and encoded values")
            required_strings[route] = ("entity_id", "transition_id")
        if route == "/api/command" and body.get("type") == "set_transition_arrival":
            if set(body) != {"type", "entity_id", "transition_id", "arrival"}:
                raise ProjectError("Arrival commands accept only owner/transition identities and arrival fields")
            required_strings[route] = ("entity_id", "transition_id")
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
        if route in ("/api/project/new", "/api/project/open"):
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
