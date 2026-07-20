# Headless runtime observer

Status: implemented and synthetically validated; retail snapshot acceptance is
blocked by cross-request executable-state churn.

The observer lives under `integrations/legaia/observer` and consumes the generic
`psxrecomp-debug` 1.4 protocol externally. It adds no Legaia command or runtime
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
- `legaia_observe.py`: one-shot CLI.

The native server intentionally closes each socket after one response. The
client is therefore a persistent logical session: request sequence, negotiated
state, timeouts, and observer process scope persist while each command uses a
fresh transport connection.

## Fail-closed selection

Selection requires native PSXRecomp, protocol 1.4, every profile capability,
the supported executable source range, all three current witnesses, town01,
PROT base 3, master mode 3, and stable frame/executable/lifecycle stamps.
There is no force or ignore option.

The profile now distinguishes the complete 442,368-byte ISO executable file
identity from the 440,320-byte `ps-x-exe-body` identity reported by the
runtime. Two fresh launches repeated the body SHA-256 recorded in the profile.
Conflating those domains caused the first retail attempt to reject correctly.

## Retail blocker

Three fresh runs reached settled town01 through normal pre-observation input.
No debugger input or RAM write occurred during snapshot collection. After the
identity-domain correction, ten diagnostic samples compared one scene read
with the three witness queries. Every request was internally stable, but no
sample retained one global executable-state token across all four requests.
The token continued changing after town01 settled.

The observer consequently discarded every attempt before actor traversal. It
did not emit retail snapshot JSON, accept an actor-list head, or read a node
prefix. Weakening the token comparison would violate the scene-epoch contract.

The missing prerequisite is a generic way to hold or identify one bounded
multi-request observation epoch, for example an atomic snapshot/read batch or
an authoritative token scoped to the executable regions required by the
profile. That work requires separate approval. Actor correlation remains out
of scope.
