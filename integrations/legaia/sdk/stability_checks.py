"""Fixed synthetic runtime checks, isolated from projects and native game launches."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from .project import ProjectError

ROOT = Path(__file__).resolve().parents[3]
FILES = (
    'integrations/legaia/sdk/stability_checks.py',
    'runtime/src/main.cpp', 'runtime/src/debug_server.c',
    'runtime/src/overlay_loader.c', 'runtime/src/overlay_path_canon.c',
    'runtime/src/overlay_posix.c', 'runtime/src/crc32.c',
    'runtime/psx_static_overlay_parts.cmake', 'tools/compile_overlays.py',
    'tools/tests/test_static_overlay_build.py',
    'runtime/tests/test_overlay_restore_runtime.py',
    'runtime/tests/test_overlay_pair_dedup_runtime.py',
    'runtime/tests/overlay_pair_dedup_fixture.c',
    'runtime/tests/overlay_pair_dedup_harness.c',
    'runtime/tests/test_debug_input_ports.py', 'runtime/tests/test_audio_output_health.py',
)
CHECKS = (
    ('restore', 'Restore Ownership', 'runtime/tests/test_overlay_restore_runtime.py'),
    ('audio', 'Host Audio Reporting', 'runtime/tests/test_audio_output_health.py'),
    ('precompile', 'Precompile Inventory and Multi-Config Builds', 'tools/tests/test_static_overlay_build.py'),
)


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def snapshot(root, destination=None):
    """Bind complete selected source files and every runtime header, not game data."""
    root = Path(root).resolve()
    names = sorted(set(FILES) | {p.relative_to(root).as_posix() for p in (root/'runtime/include').rglob('*.h')})
    if len(names) > 512:
        raise ProjectError('Stability source inventory exceeds its bound')
    rows, total = [], 0
    for name in names:
        path = root/name
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ProjectError('Stability source is missing or outside the SDK: '+name)
        before = path.stat()
        if before.st_size > 4*1024*1024:
            raise ProjectError('Stability source exceeds its file bound: '+name)
        with path.open('rb') as stream:
            payload = stream.read(4*1024*1024+1)
        after = path.stat()
        total += len(payload)
        if len(payload)>4*1024*1024 or total > 32*1024*1024 or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ProjectError('Stability source changed during snapshot or exceeds its budget')
        rows.append(dict(path=name, sha256=sha256(payload).hexdigest(), size=len(payload)))
        if destination is not None:
            target = Path(destination)/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
    return rows


def tool(name):
    found = shutil.which(name)
    fallback = Path('C:/msys64/ucrt64/bin')/(name+'.exe')
    if not found and fallback.is_file():
        found = str(fallback)
    if not found:
        raise ProjectError('Fresh stability checks require '+name)
    return str(Path(found).resolve())


class StabilityCheckService:
    """One bounded worker; the caller can cancel it and download its receipt."""
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.lock = threading.RLock()
        self.cancelled = threading.Event()
        self.worker = None
        self.report = None

    def status(self):
        with self.lock:
            return deepcopy(self.report)

    def start(self):
        with self.lock:
            if self.worker and self.worker.is_alive():
                raise ProjectError('A stability check is already running')
            tools = {name: tool(name) for name in ('gcc', 'g++', 'cmake', 'ninja')}
            self.cancelled.clear()
            self.report = dict(schema_version='legaia.stability-checks.v1', id=str(uuid.uuid4()),
                status='running', started_at=stamp(), finished_at=None,
                scope='synthetic_runtime_fixtures', runtime_binary_verified=False,
                gameplay_verified=False, project_modified=False, source_current=None,
                sources=[], tools={name: dict(path=path,sha256=sha256(Path(path).read_bytes()).hexdigest()) for name,path in {**tools,'python':sys.executable}.items()}, checks=[dict(id=i,title=t,status='pending',exit_code=None,output='') for i,t,_ in CHECKS], error=None)
            self.worker = threading.Thread(target=self._run, args=(tools,), daemon=True)
            self.worker.start()
            return deepcopy(self.report)

    def cancel(self, identity):
        with self.lock:
            if not self.report or identity != self.report['id']:
                raise ProjectError('Stability job identity changed')
            if self.report['status'] == 'running':
                self.cancelled.set()
            return deepcopy(self.report)

    def close(self):
        self.cancelled.set()
        if self.worker:
            self.worker.join(timeout=5)

    @staticmethod
    def _stop(process):
        if process.poll() is not None:
            return
        if os.name == 'nt':
            # Only the worker-owned process tree, including its compiler/fixture.
            try:
                result = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            except (OSError, subprocess.TimeoutExpired) as error:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                raise ProjectError('Fixture stopped, but Windows process-tree cancellation could not be confirmed') from error
            if result.returncode and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
                raise ProjectError('Fixture stopped, but Windows process-tree cancellation could not be confirmed')
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)

    def _execute(self, command, cwd, env):
        with tempfile.TemporaryFile() as log:
            kwargs = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else dict(start_new_session=True)
            process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, **kwargs)
            outcome = None
            deadline = time.monotonic()+180
            try:
                while process.poll() is None:
                    if self.cancelled.wait(.1):
                        outcome = 'cancelled'; break
                    if time.monotonic() >= deadline:
                        outcome = 'timed_out'; break
                    if os.fstat(log.fileno()).st_size > 256*1024:
                        outcome = 'output_limit'; break
            finally:
                self._stop(process)
            log.seek(0)
            output = log.read(256*1024).decode('utf-8', errors='replace')
            if os.fstat(log.fileno()).st_size > 256*1024:
                outcome = outcome or 'output_limit'
            # A zero exit with skipped unittest cases is not fresh qualification.
            if re.search(r'\bskipped\s*=\s*[1-9]', output):
                outcome = outcome or 'skipped'
            return outcome or ('passed' if process.returncode == 0 else 'failed'), process.returncode, output

    def _run(self, tools):
        final = 'failed'
        try:
            with tempfile.TemporaryDirectory(prefix='legaia-stability-') as raw:
                copied = Path(raw)/'sdk'
                rows = snapshot(self.root, copied)
                with self.lock:
                    self.report['sources'] = rows
                env = dict(os.environ)
                for key in ('PYTHONPATH', 'LEGAIA_DISC_BIN', 'CC', 'CXX', 'PSX_TEST_CMAKE_GENERATOR'):
                    env.pop(key, None)
                env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(copied/'tools'),
                    CC=tools['gcc'], CXX=tools['g++'], PSX_TEST_CMAKE_GENERATOR='Ninja Multi-Config',
                    PATH=os.pathsep.join(dict.fromkeys(str(Path(p).parent) for p in tools.values()))+os.pathsep+env.get('PATH',''))
                for index, (identity, title, path) in enumerate(CHECKS):
                    if self.cancelled.is_set():
                        final = 'cancelled'; break
                    with self.lock:
                        self.report['checks'][index]['status'] = 'running'
                    command = [sys.executable, str(copied/path)]
                    if identity == 'restore':
                        command += ['--gcc', tools['gcc']]
                    result, code, output = self._execute(command, copied, env)
                    with self.lock:
                        self.report['checks'][index].update(status=result,exit_code=code,output=output)
                    if result != 'passed':
                        final = result; break
                else:
                    final = 'passed'
                current = snapshot(self.root) == rows
                with self.lock:
                    self.report['source_current'] = current
                if final == 'passed' and not current:
                    final = 'source_changed'
        except Exception as error:
            with self.lock:
                self.report['error'] = str(error)
                for row in self.report['checks']:
                    if row['status'] == 'running':
                        row.update(status='failed', output=str(error)[:4096])
        finally:
            with self.lock:
                if self.cancelled.is_set() and self.report['error'] is None:
                    final = 'cancelled'
                self.report.update(status=final, finished_at=stamp())
