"""Bounded logical session for PSXRecomp's one-command TCP transport."""

from __future__ import annotations

import json
import secrets
import socket
import time
from typing import Any

from .errors import ProtocolError


READ_ONLY_COMMANDS = {
    "protocol_info",
    "runtime_identity",
    "read_regions",
    "execution_witness",
    "executable_lifecycle",
}


class ProtocolClient:
    """Persistent logical client over the native server's one-shot sockets.

    The native server closes a TCP connection after each response. This class
    preserves request IDs, negotiated state, timeouts, and process-session
    scope while reconnecting transparently for each command. It never exposes
    a write command.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4370,
        *,
        connection_timeout: float = 3.0,
        request_timeout: float = 5.0,
        maximum_response_bytes: int = 65536,
        startup_attempts: int = 5,
        startup_backoff: float = 0.1,
    ) -> None:
        if maximum_response_bytes < 256:
            raise ValueError("maximum_response_bytes is too small")
        self.host = host
        self.port = port
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout
        self.maximum_response_bytes = maximum_response_bytes
        self.startup_attempts = startup_attempts
        self.startup_backoff = startup_backoff
        self.session_id = f"observer-session-{secrets.token_hex(8)}"
        self._next_id = 1
        self._closed = False
        self.request_count = 0
        self.protocol_info: dict[str, Any] | None = None

    def __enter__(self) -> "ProtocolClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._closed = True

    def _receive_line(self, sock: socket.socket) -> bytes:
        data = bytearray()
        while True:
            try:
                chunk = sock.recv(min(65536, self.maximum_response_bytes + 1 - len(data)))
            except socket.timeout as exc:
                raise ProtocolError("request timed out") from exc
            if not chunk:
                if not data:
                    raise ProtocolError("connection closed before a response")
                break
            data.extend(chunk)
            if len(data) > self.maximum_response_bytes:
                raise ProtocolError("response line exceeds negotiated client bound")
            newline = data.find(b"\n")
            if newline >= 0:
                if data[newline + 1 :].strip():
                    raise ProtocolError("response contains more than one line")
                return bytes(data[:newline])
        return bytes(data)

    def request(self, command: str, *, startup_retry: bool = False, **params: Any) -> dict[str, Any]:
        if self._closed:
            raise ProtocolError("client is closed")
        if command not in READ_ONLY_COMMANDS:
            raise ProtocolError(f"command is not permitted by the read-only client: {command}")
        request_id = self._next_id
        self._next_id += 1
        request = {"id": request_id, "cmd": command, **params}
        encoded = (json.dumps(request, separators=(",", ":")) + "\n").encode("utf-8")
        attempts = self.startup_attempts if startup_retry else 1
        last_error: BaseException | None = None
        for attempt in range(attempts):
            try:
                with socket.create_connection(
                    (self.host, self.port), timeout=self.connection_timeout
                ) as sock:
                    sock.settimeout(self.request_timeout)
                    sock.sendall(encoded)
                    line = self._receive_line(sock)
                break
            except (OSError, ProtocolError) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    if isinstance(exc, ProtocolError):
                        raise
                    raise ProtocolError(f"connection failed: {exc}") from exc
                time.sleep(min(self.startup_backoff * (2**attempt), 1.0))
        else:  # pragma: no cover - loop always breaks or raises
            raise ProtocolError(f"connection failed: {last_error}")
        self.request_count += 1
        try:
            response = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("malformed JSON response") from exc
        if not isinstance(response, dict):
            raise ProtocolError("response is not a JSON object")
        if response.get("id") != request_id:
            raise ProtocolError(
                f"response ID mismatch: expected {request_id}, got {response.get('id')!r}"
            )
        if response.get("ok") is not True:
            raise ProtocolError(str(response.get("error") or response.get("err") or "command failed"))
        return response

    def negotiate(self) -> dict[str, Any]:
        response = self.request("protocol_info", startup_retry=True)
        protocol = response.get("protocol")
        capabilities = response.get("capabilities")
        if not isinstance(protocol, dict) or not isinstance(capabilities, list):
            raise ProtocolError("protocol_info is incomplete")
        if capabilities != sorted(capabilities):
            raise ProtocolError("protocol capabilities are not deterministically ordered")
        limits = response.get("limits")
        if not isinstance(limits, dict):
            raise ProtocolError("protocol limits are missing")
        remote_limit = limits.get("max_response_bytes")
        if isinstance(remote_limit, int):
            self.maximum_response_bytes = min(self.maximum_response_bytes, remote_limit)
        self.protocol_info = response
        return response

    def runtime_identity(self) -> dict[str, Any]:
        return self.request("runtime_identity")

    def read_regions(self, regions: list[dict[str, Any]]) -> dict[str, Any]:
        return self.request("read_regions", regions=regions)

    def execution_witness(self, pc: str) -> dict[str, Any]:
        return self.request("execution_witness", pc=pc)

    def lifecycle_token(self) -> dict[str, Any]:
        return self.request("executable_lifecycle", view="instances", cursor="0", limit=1)
