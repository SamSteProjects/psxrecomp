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
- executable-state token;
- lifecycle token; and
- frame number.

Frames may advance, but they may not move backwards. Every other structural
field must agree. The epoch ID is SHA-256 over those inputs plus the positive
observer epoch sequence.

## Snapshot boundary

The observer samples boundary A, reads only validated node prefixes, then
samples boundary B. Every node read must be internally frame/executable stable
and must carry boundary A's executable-state token. Any changed scene signal,
head, witness, token, runtime identity, or profile identity discards the whole
attempt. Partial results are never merged.

An accepted snapshot would be current only at capture. Node addresses can be
reused, list order can change, and an epoch ending makes every captured node ID
stale.

## Current acceptance status

Synthetic transitions prove scene, head, witness, runtime, executable, and
lifecycle changes all invalidate an epoch. Retail town01 has not established an
epoch because the process-global executable-state token changes between the
required one-command connections even though each command is internally
stable. Scene exit and re-entry therefore were not tested by the observer; the
retail stop condition was reached first.
