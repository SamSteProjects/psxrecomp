"""Headless, read-only Legend of Legaia runtime observation."""

from .client import ProtocolClient
from .errors import (
    ChainInvalid,
    ObserverError,
    ProfileRejected,
    ProtocolError,
    RetryExhausted,
    SnapshotUnstable,
)
from .profile import LoadedProfile, ProfileSelector
from .snapshot import RuntimeObserver, canonical_snapshot_json, validate_snapshot
from .transition import (
    ManualNavigator,
    SceneTransitionWatcher,
    TransitionLimits,
    TransitionState,
    TransitionTimeout,
)

__all__ = [
    "ChainInvalid",
    "LoadedProfile",
    "ManualNavigator",
    "ObserverError",
    "ProfileRejected",
    "ProfileSelector",
    "ProtocolClient",
    "ProtocolError",
    "RetryExhausted",
    "RuntimeObserver",
    "SnapshotUnstable",
    "SceneTransitionWatcher",
    "TransitionLimits",
    "TransitionState",
    "TransitionTimeout",
    "canonical_snapshot_json",
    "validate_snapshot",
]
