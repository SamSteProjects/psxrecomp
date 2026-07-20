# Scene epoch observation contract

A scene epoch is observer-owned. It never writes state into guest RAM and never
makes a node address permanent.

## Stabilization

The profile requires two consecutive compatible boundary samples before an
epoch becomes active. Each boundary contains:

- observer-session-scoped runtime identity;
- profile ID;
- scene name, PROT base, and master mode;
- actor-list head and census base;
- structural identity of every required execution witness;
- profile-scoped observation-guard token; and
- frame number.

Frames may advance, but they may not move backwards. Every other structural
field must agree. Global executable-state and lifecycle tokens remain diagnostic
and are not scoped epoch inputs. The epoch ID is SHA-256 over those inputs plus the positive
observer epoch sequence.

## Snapshot boundary

The observer samples boundary A, reads only validated node prefixes, then
samples boundary B. Every node read must carry boundary A's expected
observation-guard token. Any changed scene signal,
head, witness, token, runtime identity, or profile identity discards the whole
attempt. Partial results are never merged.

An accepted snapshot would be current only at capture. Node addresses can be
reused, list order can change, and an epoch ending makes every captured node ID
stale.

## Current acceptance status

Synthetic transitions prove scene, head, required witness, runtime, and relevant
lifecycle changes all invalidate an epoch. Repeated retail town01 boundary-only
runs established a stable scoped epoch while the broader global token changed.
No actor bytes were read. Normal bounded navigation did not reach a scene exit,
so exit invalidation and re-entry remain the live acceptance blocker.
