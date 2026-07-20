# Observation guard model

An observation guard is a stateless, request-scoped consistency boundary for an
external runtime observer. It answers a narrower question than the global
executable-state token: did the exact RAM signals and execution witnesses named
by this request retain the same identity?

## Why both tokens exist

The global executable-state token remains the authoritative digest of all
registered executable watched pages, dirty-text state, registration ownership,
and executable-image lifecycle state. It is intentionally sensitive to changes
outside one title profile.

That breadth made it unsuitable as the sole boundary for a multi-request scene
observation. During stable town01 execution, unrelated watched pages and
lifecycle-catalog records changed even though the three required execution
witnesses and scene signals did not. Weakening the global token would hide real
runtime changes. The scoped guard instead commits to only the dependencies the
observer declares.

## Canonical inputs

The native runtime canonicalizes and hashes:

- its immutable process-local runtime instance identity;
- main executable source identity, guest base, length, and program serial;
- sorted bounded RAM ranges, including each key, base, length, and current
  SHA-256;
- sorted exact-PC execution witnesses, including backend, reason, exact
  four-byte range, current live SHA-256, watched-generation digest/currentness,
  and relevant lifecycle/registration identity.

The digest domain is `psxrecomp-observation-guard-v1`. Request order does not
affect the token. Duplicate keys, duplicate ranges, duplicate witnesses,
invalid addresses, overflow, stale or ambiguous witnesses, and missing
evidence fail closed.

Frames, request IDs, witness hit counts, first/last execution frames, unrelated
watched pages, unrelated execution owners, and unrelated lifecycle records are
excluded. A same-byte write to a guarded executable page can still change its
watched generation and therefore invalidate the guard.

## Scope and stability

Tokens are process-local and are not stable across runtime restarts. The server
does not store a protocol-only generation counter or observer session. A client
may send an expected token; compatibility is true only when the freshly derived
token matches. Guarded reads return payload data only when the before and after
tokens are valid, equal, and compatible with the expectation.

The process-global executable token and bounded component diagnostics remain in
responses for investigation. They are not substitutes for the scoped token and
do not have to remain unchanged for a profile-scoped read to be accepted.

## Security and data boundary

The guard hashes current guest RAM but returns no guarded RAM or executable
bytes. All ranges use the existing main-RAM bounds and response budgets. The
feature performs no guest writes and includes no title-specific addresses.
