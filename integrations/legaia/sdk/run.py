"""Private Windows runtime launches for validated SDK builds, with owned-process control."""
from __future__ import annotations

from copy import deepcopy
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import struct
import subprocess
import threading
import time
import tomllib
import uuid
import zipfile

from .build import _guard_output
from .project import ProjectError, atomic_write, canonical


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _toml_value(value) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) in (int, float):
        return json.dumps(value, allow_nan=False)
    if isinstance(value, list) and all(not isinstance(item, dict) for item in value):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise ProjectError("Runtime configuration contains an unsupported TOML value")


def _toml_document(document: dict) -> bytes:
    lines = []
    def table(values: dict, prefix: tuple[str, ...] = ()) -> None:
        if prefix:
            lines.append("[" + ".".join(json.dumps(key) for key in prefix) + "]")
        for key, value in values.items():
            if not isinstance(value, dict):
                lines.append(json.dumps(key) + " = " + _toml_value(value))
        lines.append("")
        for key, value in values.items():
            if isinstance(value, dict):
                table(value, prefix + (key,))
    table(document)
    result = ("\n".join(lines) + "\n").encode("utf-8")
    tomllib.loads(result.decode("utf-8"))
    return result


def _listener_pid(port: int) -> int | None:
    """Use Windows' owner-PID table to avoid attaching to a port-racing process."""
    size = ctypes.c_ulong(0)
    get_table = ctypes.windll.iphlpapi.GetExtendedTcpTable
    result = get_table(None, ctypes.byref(size), False, 2, 3, 0)
    if result not in (0, 122) or size.value > 1024 * 1024:
        raise ProjectError("Cannot inspect runtime TCP listener ownership")
    data = ctypes.create_string_buffer(max(size.value, 4))
    if get_table(data, ctypes.byref(size), False, 2, 3, 0) != 0:
        raise ProjectError("Runtime TCP listener table changed; retry readiness")
    count = struct.unpack_from("<I", data.raw)[0]
    if 4 + count * 24 > size.value:
        raise ProjectError("Invalid runtime TCP listener table")
    for index in range(count):
        row = struct.unpack_from("<6I", data.raw, 4 + index * 24)
        if row[0] == 2 and socket.ntohs(row[2] & 0xFFFF) == port:
            return row[5]
    return None


class RunService:
    """One owned child; readiness proves identity/plan, never gameplay success."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._process: subprocess.Popen | None = None
        self._status: dict | None = None
        self._cancel = threading.Event()

    def config(self, project) -> dict:
        path = project.root / "Local" / "launch.json"
        _guard_output(path, project.root)
        if not path.exists():
            return {"runtime_executable": "", "bios": "", "game_config": "", "debug_port": 4391, "renderer": "software"}
        if path.stat().st_size > 16384:
            raise ProjectError("Launch configuration exceeds 16 KiB")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ProjectError("Invalid launch configuration")
        return value

    def configure(self, project, values: dict) -> dict:
        config = self._validate_config(values)
        path = project.root / "Local" / "launch.json"
        _guard_output(path, project.root)
        atomic_write(path.parent / ".gitignore", b"*\n")
        atomic_write(path, canonical(config))
        return config

    @staticmethod
    def _validate_config(values: dict) -> dict:
        result = {}
        for key in ("runtime_executable", "bios", "game_config"):
            if not isinstance(values.get(key), str) or not values[key].strip():
                raise ProjectError(f"Configure {key.replace('_', ' ')} before running")
            path = Path(values[key]).expanduser().resolve(strict=True)
            if not path.is_file():
                raise ProjectError(f"{key} must be a regular file")
            result[key] = str(path)
        if Path(result["runtime_executable"]).suffix.lower() != ".exe":
            raise ProjectError("Choose a Windows runtime .exe")
        if Path(result["runtime_executable"]).stat().st_size > 256 * 1024 * 1024:
            raise ProjectError("Runtime executable exceeds the 256 MiB private-copy bound")
        if Path(result["bios"]).stat().st_size != 524288:
            raise ProjectError("BIOS must be a 512 KiB image")
        port = values.get("debug_port", 4391)
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ProjectError("Debug port must be an integer from 1024 to 65535")
        result["debug_port"] = port
        renderer = values.get("renderer", "software")
        if renderer not in ("software", "opengl", "vulkan"):
            raise ProjectError("Renderer must be software, opengl or vulkan")
        result["renderer"] = renderer
        return result

    def status(self) -> dict | None:
        with self._lock:
            if self._status is not None:
                self._status["running"] = self._process is not None and self._process.poll() is None
            if self._status is not None and self._process is not None:
                code = self._process.poll()
                if code is not None and self._status["state"] not in ("stopped", "exited", "failed"):
                    self._status.update(state="exited", exit_code=code, ready=False)
                    self._persist()
            return deepcopy(self._status)

    def _persist(self) -> None:
        if self._status is not None:
            path = Path(self._status["directory"]) / "run.json"
            _guard_output(path, Path(self._status["project"]))
            atomic_write(path, canonical(self._status))

    def start(self, project, build: dict) -> dict:
        if os.name != "nt":
            raise ProjectError("Build & Run currently supports Windows runtimes")
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                raise ProjectError("Stop this editor's current run before launching another")
            config = self._validate_config(self.config(project))
            port = config["debug_port"]
            if _listener_pid(port) is not None:
                raise ProjectError(f"Debug port {port} is already in use; choose another port")
            cfg_path = Path(config["game_config"])
            if cfg_path.stat().st_size > 1024 * 1024:
                raise ProjectError("Runtime game configuration exceeds 1 MiB")
            game_config = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
            if not isinstance(game_config.get("game"), dict) or game_config["game"].get("id") != "SCUS-94254":
                raise ProjectError("Choose a game configuration for SCUS-94254")
            guest_exe = Path(game_config["game"]["exe"])
            if not guest_exe.is_absolute():
                guest_exe = cfg_path.parent / guest_exe
            guest_exe = guest_exe.resolve(strict=True)
            if guest_exe.stat().st_size > 16 * 1024 * 1024:
                raise ProjectError("Configured PS-X EXE exceeds 16 MiB")
            image = guest_exe.read_bytes()
            if len(image) < 2048 or image[:8] != b"PS-X EXE":
                raise ProjectError("Configured game EXE is not a PS-X EXE")
            body_size = struct.unpack_from("<I", image, 0x1C)[0]
            if not 0 < body_size <= len(image) - 2048:
                raise ProjectError("Configured game EXE has invalid text bounds")
            expected_text = hashlib.sha256(image[2048:2048 + body_size]).hexdigest()
            profile_path = Path(__file__).resolve().parents[1] / "layouts" / "scus94254-na-field-v1.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))["executable_identity"]
            if (hashlib.sha256(image).hexdigest() != profile["sha256"] or
                    expected_text != profile["runtime_source_identity"]["sha256"] or
                    body_size != profile["runtime_source_identity"]["length"]):
                raise ProjectError("Configured game EXE does not match the confirmed retail SCUS-94254 identity")
            archive_path = Path(build["path"]).resolve(strict=True)
            _guard_output(archive_path, project.root)
            if _sha(archive_path) != build["sha256"]:
                raise ProjectError("Build package was modified before launch")
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
            runs = project.root / "Runs"
            run = runs / run_id
            _guard_output(run, project.root)
            run.mkdir(parents=True, exist_ok=False)
            atomic_write(runs / ".gitignore", b"*\n")
            self._status = {"schema_version": "legaia.run.v1", "state": "preparing", "ready": False,
                            "directory": str(run), "project": str(project.root), "debug_port": port,
                            "package_id": build["package_id"], "package_version": build["version"],
                            "package_sha256": build["sha256"], "expected_text_sha256": expected_text,
                            "expected_bios_sha256": _sha(Path(config["bios"])), "gameplay_verified": False,
                            "configuration": config, "runtime_identity": None, "mod_status": None}
            self._persist()
            try:
                self._install_build(run, archive_path, build)
                expected_disc = "sha256:" + self._status["expected_disc_sha256"]
                if not project.imports or any(document["source"]["disc_identity"] != expected_disc for document in project.imports.values()):
                    raise ProjectError("Launch package disc identity differs from the imported project")
                source_exe = Path(config["runtime_executable"])
                dependencies = list(source_exe.parent.glob("*.dll"))
                if len(dependencies) > 64 or sum(p.stat().st_size for p in dependencies) > 512 * 1024 * 1024:
                    raise ProjectError("Runtime dependency folder exceeds the private-copy bound")
                copied_exe = run / source_exe.name
                shutil.copyfile(source_exe, copied_exe)
                for dependency in dependencies:
                    shutil.copyfile(dependency, run / dependency.name)
                self._status["runtime_executable_sha256"] = _sha(copied_exe)
                game_config["game"]["exe"] = str(guest_exe)
                game_config["game"]["disc"] = project.disc_path
                game_config.setdefault("runtime", {}).update(overlay_cache=False, memcard_dir=str(run / "saves"))
                private_config = run / "game.toml"
                atomic_write(private_config, _toml_document(game_config))
                command = [str(copied_exe), "--no-launcher", "--game", str(private_config),
                           "--bios", config["bios"], "--disc", project.disc_path,
                           "--memcard-dir", str(run / "saves"), "--debug-port", str(port),
                           "--renderer", config["renderer"]]
                environment = os.environ.copy()
                # A separate run must not inherit a previous experiment's forced timing mode.
                for key in tuple(environment):
                    if key.startswith("PSX_"):
                        environment.pop(key)
                with (run / "stdout.log").open("wb") as stdout, (run / "stderr.log").open("wb") as stderr:
                    self._process = subprocess.Popen(command, cwd=run, env=environment, stdin=subprocess.DEVNULL,
                                                     stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
                self._cancel = threading.Event()
                self._status.update(state="starting", pid=self._process.pid, command=command)
                self._persist()
                threading.Thread(target=self._await_ready, args=(self._process, self._cancel), daemon=True).start()
                return deepcopy(self._status)
            except Exception as exc:
                self._status.update(state="failed", reason=str(exc), ready=False)
                self._persist()
                raise

    def _install_build(self, run: Path, archive_path: Path, build: dict) -> None:
        # Only this SDK build schema is installed here. The runtime's full ModManager
        # independently validates the resulting manifest, stock guards and payloads.
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if len(infos) > 256 or sum(item.file_size for item in infos) > 64 * 1024 * 1024:
                raise ProjectError("Build package exceeds the private install bound")
            names = [item.filename for item in infos]
            if len(names) != len(set(names)) or "manifest.toml" not in names:
                raise ProjectError("Build package has duplicate entries or no manifest")
            manifest = tomllib.loads(archive.read("manifest.toml").decode("utf-8"))
            if manifest.get("id") != build["package_id"] or manifest.get("version") != build["version"]:
                raise ProjectError("Build identity disagrees with its manifest")
            for value in (build["package_id"], build["version"]):
                if not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in value) or value in (".", ".."):
                    raise ProjectError("Unsafe build package identity")
            overlays = manifest.get("overlay", [])
            if len(overlays) != build["overlay_count"] or any(item.get("target") != "disc_user" for item in overlays):
                raise ProjectError("Build package does not match its overlay audit")
            allowed = {"manifest.toml", *(item["file"] for item in overlays)}
            if set(names) != allowed:
                raise ProjectError("Build package contains unexpected files")
            # The whole run directory is new and no process can read it until
            # start() completes this validation. Install directly into its final
            # private location: renaming a freshly written directory can fail
            # under Windows file-indexer sharing locks (including OneDrive).
            staging = run / "mods" / "installed" / build["package_id"] / build["version"]
            _guard_output(staging, run)
            staging.mkdir(parents=True, exist_ok=False)
            for item in infos:
                relative = PurePosixPath(item.filename)
                if relative.is_absolute() or ".." in relative.parts or "\\" in item.filename or ":" in item.filename:
                    raise ProjectError("Unsafe package member path")
                data = archive.read(item)
                expected = next((entry["sha256"] for entry in overlays if entry["file"] == item.filename), None)
                if expected is not None and hashlib.sha256(data).hexdigest() != expected:
                    raise ProjectError("Build overlay hash mismatch")
                target = staging.joinpath(*relative.parts)
                atomic_write(target, data)
            targets = manifest.get("target", [])
            if len(targets) != 1 or targets[0].get("game_id") != "SCUS-94254":
                raise ProjectError("Build target is not SCUS-94254")
            self._status["expected_disc_sha256"] = targets[0]["disc_sha256"]
            self._status["expected_overlay_count"] = len(overlays)
            state = ("format_version = 2\n\n[[package]]\nid = " + json.dumps(build["package_id"]) +
                     "\nversion = " + json.dumps(build["version"]) + "\n\n[[feature]]\npackage_id = " +
                     json.dumps(build["package_id"]) + "\nid = " + json.dumps(build["feature_id"]) + "\nenabled = true\n")
            atomic_write(run / "mods" / "state.toml", state.encode("utf-8"))

    def _await_ready(self, process: subprocess.Popen, cancel: threading.Event) -> None:
        from integrations.legaia.observer.client import ProtocolClient
        deadline = time.monotonic() + 90
        reason = "Waiting for the runtime debug server"
        while time.monotonic() < deadline and not cancel.wait(1):
            if process.poll() is not None:
                self.status()
                return
            try:
                with self._lock:
                    port = self._status["debug_port"]
                owner = _listener_pid(port)
                if owner is None:
                    continue
                if owner != process.pid:
                    raise ProjectError("Debug port belongs to another process; refusing to attach")
                with ProtocolClient(port=port, connection_timeout=.5, request_timeout=2, startup_attempts=1) as client:
                    identity = client.runtime_identity()
                    mods = client.request("mod_status")
                with self._lock:
                    if cancel.is_set() or process is not self._process:
                        return
                    guest = identity.get("main_executable") or {}
                    valid = (identity.get("runtime", {}).get("implementation") == "psxrecomp" and
                             guest.get("source_identity", {}).get("sha256") == self._status["expected_text_sha256"] and
                             identity.get("bios", {}).get("sha256") == self._status["expected_bios_sha256"] and
                             mods.get("disc_identity", {}).get("sha256") == self._status["expected_disc_sha256"] and
                             mods.get("active_overlay_count") == self._status["expected_overlay_count"] and
                             mods.get("active_write_count") == 0 and mods.get("plan_committed") is True and
                             mods.get("disc_enabled") is True and mods.get("disc_guard_failed") is False)
                    self._status.update(runtime_identity=identity, mod_status=mods)
                    if valid:
                        # Arm the selected profile's exact PCs before field entry.
                        # Preparation is observational setup, not Live acceptance.
                        from integrations.legaia.observer.service import ObserverService
                        observer = ObserverService(port=port)
                        try:
                            preparation = observer.discover()
                            self._status["observation_preparation"] = {
                                key: deepcopy(preparation[key]) for key in
                                ("available", "state", "reason", "scene_verified", "witness_tracking")
                                if key in preparation}
                        finally:
                            observer.close()
                        self._status.update(state="ready", ready=True,
                                            reason="Runtime identity and enabled mod plan verified; gameplay not yet verified")
                        self._persist()
                        return
                    reason = "Runtime has not established the expected game identity and enabled mod plan"
            except Exception as exc:
                reason = str(exc)
        with self._lock:
            if process is self._process and not cancel.is_set():
                self._status.update(state="unverified", ready=False, reason=reason)
                self._persist()

    def stop(self) -> dict | None:
        with self._lock:
            self._cancel.set()
            if self._process is not None and self._process.poll() is None:
                try:
                    if _listener_pid(self._status["debug_port"]) == self._process.pid:
                        with socket.create_connection(("127.0.0.1", self._status["debug_port"]), timeout=1) as sock:
                            sock.settimeout(1)
                            sock.sendall(b'{"id":1,"cmd":"quit"}\n')
                            sock.recv(4096)
                        self._process.wait(timeout=3)
                except (OSError, ProjectError, subprocess.TimeoutExpired):
                    pass
                # Popen retains the exact Windows process handle; no PID search/kill.
                if self._process.poll() is None:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                self._status.update(state="stopped", ready=False, exit_code=self._process.returncode)
                self._persist()
            return self.status()
