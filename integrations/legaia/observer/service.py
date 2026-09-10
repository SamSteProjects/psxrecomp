"""Read-only Live-mode adapter; imported and authored project data never enter it."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from integrations.legaia.layouts import load_profile

from .client import ProtocolClient
from .correlation import sample_man_bindings
from .errors import ObserverError, ProfileRejected, ProtocolError, SnapshotUnstable
from .profile import LoadedProfile
from .snapshot import RuntimeObserver


LAYOUTS = Path(__file__).resolve().parents[1] / "layouts"
RESTORED_FROM = "28ce54367127e858c8ef2bfbd27ffe64f60e0e93"
ANDREW_REFERENCE = "d6e64c68ede25813d35db20980da82a1a025549b"


class ObserverService:
    """One bounded snapshot per call, serialized for a Python HTTP service.

    `discover()` checks protocol/executable compatibility and requests the
    selected profile's exact-PC witnesses to arm future execution tracking.
    A missing witness is expected at startup; priming never verifies a scene.
    `observe()` defaults to scene-boundary metadata. Actor traversal is an
    explicit option, always behind the same profile, process and epoch guards.
    No result is cached as current live state after an unavailable response.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 4370, *,
                 client_factory: Callable[..., ProtocolClient] = ProtocolClient) -> None:
        self.host, self.port = host, port
        self._factory = client_factory
        self._lock = threading.RLock()
        self._profiles = {
            profile.document["profile_id"]: profile
            for profile in (LoadedProfile.from_document(load_profile(path))
                            for path in sorted(LAYOUTS.glob("scus94254-*-v[0-9]*.json")))
        }
        self._client: ProtocolClient | None = None
        self._observer: RuntimeObserver | None = None
        self._last_epoch: dict[str, Any] | None = None

    def profiles(self) -> list[dict[str, Any]]:
        return [{
            "profile_id": value.document["profile_id"],
            "profile_hash": value.profile_hash,
            "profile_revision": value.document["profile_id"].rsplit("-v", 1)[-1],
            "is_default": value.document["profile_id"] == "legaia-na-scus94254-field-v2",
            "scene": value.document["scene_identity"]["scene_key"],
            "required_protocol": value.document["supported_runtime_protocol"],
            "traversal_bounds": value.document["observation_policy"]["traversal"],
            "andrew_reference_revision": ANDREW_REFERENCE,
            "read_only": True,
        } for value in self._profiles.values()]

    def _select(self, profile_id: str | None) -> LoadedProfile:
        selected = profile_id or "legaia-na-scus94254-field-v2"
        try:
            return self._profiles[selected]
        except KeyError as exc:
            raise ProfileRejected(f"unknown profile: {selected}") from exc

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                self._client.close()
            self._client = self._observer = self._last_epoch = None

    def _session(self, profile: LoadedProfile) -> RuntimeObserver:
        if self._observer is None or self._observer.profile.profile_hash != profile.profile_hash:
            self.close()
            self._client = self._factory(self.host, self.port, connection_timeout=1.0,
                                         request_timeout=2.0, startup_attempts=1)
            self._observer = RuntimeObserver(self._client, profile)
        return self._observer

    def _unavailable(self, exc: Exception) -> dict[str, Any]:
        message = str(exc)
        if isinstance(exc, SnapshotUnstable):
            code = "stale_epoch"
        elif isinstance(exc, ProfileRejected):
            code = "profile_rejected"
        elif isinstance(exc, ProtocolError):
            code = "unsupported_protocol" if "unknown" in message.lower() else "protocol_unavailable"
        else:
            code = "observation_unavailable"
        self.close()
        return {"available": False, "state": "unavailable", "read_only": True,
                "reason": {"code": code, "message": message},
                "profiles": self.profiles(), "observation": None,
                "runtime": None, "ram_writes": 0}

    def discover(self, profile_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            try:
                profile = self._select(profile_id)
                observer = self._session(profile)
                observer.selector.negotiate()
                # The runtime records only requested PCs. Negotiation enables
                # lifecycle tracking but does not arm individual witnesses;
                # request them before a later scene entry can execute once.
                # These replies are collection setup, never profile evidence.
                requested_pcs = []
                initial_statuses = []
                for required in profile.document["execution_identity"]["required_witnesses"]:
                    pc = required["pc"]
                    response = self._client.execution_witness(pc)
                    if not isinstance(response, dict) or response.get("requested_pc") != pc:
                        raise ProtocolError("execution witness priming returned a mismatched PC")
                    status, witness = response.get("status"), response.get("witness")
                    if status not in ("missing", "current", "stale", "ambiguous"):
                        raise ProtocolError("execution witness priming returned an invalid status")
                    if status == "missing":
                        if "witness" not in response or witness is not None:
                            raise ProtocolError("missing execution witness priming response contains evidence")
                    else:
                        expected_range = {"kind": "executed-instruction", "guest_base": pc,
                                          "length": 4, "instruction_count": 1,
                                          "block_range_available": False}
                        observed_range = witness.get("range") if isinstance(witness, dict) else None
                        if (not isinstance(witness, dict) or witness.get("resolved_pc") != pc or
                                not isinstance(observed_range, dict) or any(
                                    observed_range.get(key) != value for key, value in expected_range.items()) or
                                witness.get("observation_current") is not (status == "current")):
                            raise ProtocolError("execution witness priming returned invalid exact-PC evidence")
                    requested_pcs.append(pc)
                    initial_statuses.append({"pc": pc, "status": status})
                return {"available": True, "state": "compatible_runtime",
                        "read_only": True, "reason": None, "profiles": self.profiles(),
                        "runtime": observer.selector.runtime, "observation": None,
                        "scene_verified": False, "ram_writes": 0,
                        "witness_tracking": {"status": "primed", "requested_pcs": requested_pcs,
                                             "initial_statuses": initial_statuses}}
            except (ObserverError, OSError, ValueError) as exc:
                return self._unavailable(exc)

    def observe(self, profile_id: str | None = None, *, expected_epoch_id: str | None = None,
                include_actors: bool = False) -> dict[str, Any]:
        with self._lock:
            try:
                profile = self._select(profile_id)
                observer = self._session(profile)
                if expected_epoch_id is not None:
                    if self._last_epoch is None or self._last_epoch["epoch_id"] != expected_epoch_id:
                        raise SnapshotUnstable("requested epoch is no longer the accepted observation")
                    guard = observer.selector.sample_guard_only(self._last_epoch["observation_guard_token"])
                    frame = guard.get("frame_after")
                    if type(frame) is not int or frame < self._last_epoch["last_validated_frame"]:
                        raise SnapshotUnstable("runtime frame moved backwards since the accepted observation")
                observation = (observer.capture(maximum_attempts=1) if include_actors
                               else observer.capture_boundary(subsequent_samples=1))
                bindings = sample_man_bindings(self._client, profile, observation) if include_actors else None
                self._last_epoch = observation["epoch"]
                return {"available": True, "state": "observed", "read_only": True,
                        "reason": None, "observation": observation,
                        "runtime": observation["runtime"], "ram_writes": 0,
                        "historical_observation": True, "actor_bindings": bindings,
                        "correlation": {"available": False,
                                        "reason": "Runtime node addresses are epoch-scoped; imported actor identity is not established."}}
            except (ObserverError, OSError, ValueError) as exc:
                return self._unavailable(exc)
