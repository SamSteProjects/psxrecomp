"""Fail-closed errors raised by the read-only Legaia observer."""


class ObserverError(RuntimeError):
    """Base class for bounded observer failures."""


class ProtocolError(ObserverError):
    """The remote protocol violated its negotiated contract."""


class ProfileRejected(ObserverError):
    """Runtime state did not select the requested layout profile."""


class SnapshotUnstable(ObserverError):
    """A snapshot crossed a frame, executable, lifecycle, or scene boundary."""


class ChainInvalid(ObserverError):
    """The candidate actor chain failed bounded structural validation."""


class RetryExhausted(ObserverError):
    """No complete stable snapshot was obtained within the attempt limit."""
