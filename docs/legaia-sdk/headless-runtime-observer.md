# Headless runtime observer

Status: boundary-only town01 and repeated fresh-process transition-only town0c
retail acceptance passed. One bounded read-only actor traversal is now safe as a
separately approved phase; no traversal has yet been performed.

The observer lives under `integrations/legaia/observer` and consumes the generic
`psxrecomp-debug` 1.5 protocol externally. It adds no Legaia command or runtime
hook and has no write-capable API.

## Architecture

- `client.py`: bounded logical session, monotonically increasing request IDs,
  startup backoff, timeouts, response bounds, JSON/ID validation, and a strict
  read-only command allowlist;
- `profile.py`: revisioned profile loading, executable-source and capability
  selection, scene-signal decoding, witness normalization, and boundary
  sampling;
- `epoch.py`: two-sample stabilization and deterministic observer-owned epoch
  IDs;
- `actor_nodes.py`: KSEG0 pointer checks, bounded linked traversal, and
  profile-driven field decoding;
- `snapshot.py`: whole-attempt retry/discard behavior and schema validation;
- `transition.py`: transition-only state machine, old-token rejection,
  outside-scene sampling, and re-entry stabilization;
- `legaia_observe.py`: one-shot boundary or transition-watch CLI.

The native server intentionally closes each socket after one response. The
client is therefore a persistent logical session: request sequence, negotiated
state, timeouts, and observer process scope persist while each command uses a
fresh transport connection.

## Fail-closed selection

Selection requires native PSXRecomp, protocol 1.5, every profile capability,
the supported executable source range, all three current witnesses, town01,
PROT base 3, master mode 3, and a stable profile-scoped observation guard.
There is no force or ignore option.

The profile now distinguishes the complete 442,368-byte ISO executable file
identity from the 440,320-byte `ps-x-exe-body` identity reported by the
runtime. Two fresh launches repeated the body SHA-256 recorded in the profile.
Conflating those domains caused the first retail attempt to reject correctly.

## Retail boundary acceptance

Fresh native runs reached settled town01 through normal pre-observation input.
An initial guarded scene read, stabilization sample, and ten subsequent guard
samples retained one scoped token while frames advanced. The broad global token
continued changing because unrelated watched pages and lifecycle records remain
in its domain. Boundary-only passes used 13 requests, read zero actor-node
bytes, performed zero RAM writes, and took approximately 154–333 ms.

The CLI requires either `--boundary-only` or `--transition-watch`; retail actor
traversal is deliberately disabled. Transition-watch uses manual normal-game
navigation, explicit old-token rejection, stable outside-scene samples, and a
two-sample plus ten-sample re-entry gate. Retail testing established the real
`town01 -> map01 -> town0c` lifecycle and completed a same-process
`town0c -> map01 -> town0c` round trip with zero actor reads and writes. The
revisioned town0c profile now exists. Fresh-process acceptance, world-map A/B,
and the formal readiness review have passed. See
`scene-transition-acceptance.md`. Actor traversal remains absent from this phase,
and actor correlation remains out of scope.
