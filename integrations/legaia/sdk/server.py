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
        from .run import RunService
        self.runs = RunService()
        self.observer = ObserverService(port=runtime_port)
        self.live_status = {"available": False, "state": "disconnected", "reason": {"message": "Runtime has not been checked"}}
        self.command_lock = threading.RLock()
        self.editor_root = Path(__file__).resolve().parents[1] / "editor"
        super().__init__(address, EditorHandler)

    def state(self) -> dict:
        state = self.project.state()
        state["runtime"] = self.live_status
        state["capabilities"]["live_mode"] = self.live_status.get("available", False)
        state["capabilities"]["runtime_discovery"] = True
        state["capabilities"]["model_preview"] = bool(self.project.disc_path)
        state["capabilities"]["build"] = bool(self.project.disc_path and self.project.overrides)
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

    def model_preview(self, asset: dict) -> dict:
        from importer.assets import load_model_preview
        from importer.textures import associate_material, load_scene_texture_catalog
        project = self.project
        preview = load_model_preview(Path(project.disc_path), asset)
        scene = asset.get("source_record", {}).get("prot_entry_name")
        if scene == "befect_data":
            scene = project.imports.get(project.active_scene, {}).get("scene", {}).get("name")
        if not scene:
            preview["textures"] = []
            return preview
        key = (project.disc_path, scene)
        if key not in self.texture_catalogs:
            if len(self.texture_catalogs) >= 2:
                self.texture_catalogs.clear()
            self.texture_catalogs[key] = load_scene_texture_catalog(project.disc_path, scene)
        catalog = self.texture_catalogs[key]
        preview["texture_catalog"] = catalog.metadata()
        preview["textures"] = []
        budget = 2 * 1024 * 1024
        for index, material in enumerate(preview.get("materials", [])):
            uvs = [uv for triangle_index, material_index in enumerate(preview["triangle_materials"])
                   if material_index == index for uv in (preview["triangle_uvs"][triangle_index] or [])]
            if not uvs or index >= 32:
                preview["textures"].append({"material_index": index, "status": "unsupported", "reason": "Untextured material or bounded preview limit"})
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
                 "/editor.css": ("editor.css", "text/css")}
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
            if not 0 < length <= 32768 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ProjectError("Commands require a JSON object of at most 32768 bytes")
            content = self.rfile.read(length)
            if len(content) != length:
                raise ProjectError("Incomplete command request body")
            body = json.loads(content)
            if not isinstance(body, dict):
                raise ProjectError("Command body must be an object")
            with self.server.command_lock:
                if urlsplit(self.path).path == "/api/preview":
                    from importer.assets import load_model_preview
                    project = self.server.project
                    if not project.disc_path:
                        raise ProjectError("Model preview requires the project's user-owned disc")
                    asset = project.assets.records.get(body.get("asset_id"))
                    if asset is None:
                        raise ProjectError("Unknown model asset")
                    self._json(200, self.server.model_preview(asset))
                    return
                self._command(urlsplit(self.path).path, body)
                self._json(200, self.server.state())
        except (ProjectError, ValueError, KeyError, TypeError, OSError) as exc:
            self._json(400, {"error": str(exc)})

    def _command(self, route: str, body: dict) -> None:
        project = self.server.project
        # Reject malformed field types before they reach filesystem/importer services.
        required_strings = {"/api/project/new": ("path",), "/api/project/open": ("path",),
                            "/api/import": ("disc",), "/api/scene": ("scene_id",),
                            "/api/command": ("entity_id",)}
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
