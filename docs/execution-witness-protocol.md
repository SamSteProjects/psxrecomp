# Execution witness protocol

`psxrecomp-debug` 1.4 adds the native capability `execution_witness` and one
bounded command:

```json
{"cmd":"execution_witness","pc":"0x80010000"}
```

The address must be four-byte aligned main RAM. The response contains at most
one witness. Missing evidence returns `ok: true`, `status: "missing"`, and a
null witness. Other statuses are `current`, `stale`, and `ambiguous`.

A present witness includes:

- requested and resolved PC;
- backend and acquisition reason;
- exact four-byte executed-instruction range;
- observed and current-live SHA-256;
- authoritative watched-page generation digest and observed/current legacy
  generation values;
- first/last frame and hit count;
- currentness;
- lifecycle-fragment and native-registration identifiers when known; and
- explicit unresolved block/function/whole-image relationships.

Frame, executable-state, and lifecycle tokens are sampled before and after the
query. `stable_observation_boundary` requires all three boundaries to agree.
Handlers run on the emulation thread, but consumers must still check these
explicit stamps.

The command returns no code bytes, RAM payloads, host paths, source paths, or
title-specific interpretation. Protocol 1.3 clients remain compatible because
1.4 is additive. DuckStation and Beetle do not advertise this capability unless
they can supply the same ownership and generation semantics.
