# SCUS-94254 field execution identity

Status: accepted metadata-only field-engine identity for the supported North
American build. This replaces the profile's previously required whole-overlay
identity; it does not claim that overlay 0897 is one canonical live range.

## Accepted witness set

| PC | Backend | Exact range | Live SHA-256 | Runtime role |
|---|---|---:|---|---|
| `0x801CF754` | interpreter | 4 bytes | `bad69a1914bdcaf9db0344c046a9731c78aae2d93bb2b842b5d7123b36fbf4bc` | collision/interaction census rebuild |
| `0x801DE840` | static-native | 4 bytes | `ec4f4d5323b718c7b0c2a96aa7da96280e5e363fa61672bde6a0044ea9a621dd` | field VM dispatcher |
| `0x801D79E8` | static-native | 4 bytes | `2ed3561c68bb654f8e2ad2ad487bde2c12f773777e92956e1ff0e7f27ad6b1d9` | field actor helper |

The hashes identify only the listed instruction spans. They are approved
metadata, not executable payloads or whole-image substitutes.

## Acceptance evidence

Fresh RelWithDebInfo runs used normal controller input and no debugger writes.
All three witnesses were current with stable frame, executable-state, and
lifecycle boundaries. Their backends, ranges, and hashes repeated:

- across fresh launches;
- across the natural `opdeene` -> `opstati` -> `opurud` -> `map01` -> `town01`
  field-scene replacement chain;
- through the town01 field-init (mode 2) to field-run (mode 3) handoff; and
- over repeated settled-town01 queries with advancing hit counts for the three
  selected active witnesses.

`0x801CF9F4` was missing and `0x801CFC40` was stale with a fixed hit count, so
neither is part of the identity. One-shot entries were also excluded.

Five-query town01 samples averaged approximately 9-19 ms per end-to-end Python
CLI request. Frames continued to advance. Full witness negotiation should occur
at startup and scene epochs, not at high frequency.

## Profile contract

The profile requires the supported executable identity, protocol 1.4 and
`execution_witness`, all three current witnesses, matching exact ranges,
backends and hashes, matching observed/current watched generations, stable
executable/lifecycle boundaries, and the existing town01 scene signals.

This establishes **field execution identity**, not canonical overlay-image
identity. The `0x801CE818` image-base hypothesis and whole overlay range/hash
remain unresolved research facts. Actor traversal and correlation remain
separate, unimplemented phases.
