# Town01 live evidence, 2026-09-09

The SDK placement package was consumed by a cold-started Windows recomp, and
the revision-2 town01 profile accepted a bounded field actor traversal. This
is stronger evidence than successful installation or title-screen startup;
it does not establish visible authored placement, animation correctness,
audible continuity, or restored-state performance.

## Runtime and package identity

- Runtime source milestone: `be90a25d1bf77b9e725e878b6fc1b907862c5810`.
- Tested executable SHA-256:
  `bc6cf5b04cfda6fe90c0d6ee6c9e87148a540e9653ef6b39988eb01bda7e5d4a`.
- SCUS body SHA-256:
  `185d3362e57441a6a8328fba376a469341c55a2e7a7ef35c0e64d04601fc0f68`.
- Source disc SHA-256:
  `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.
- Enabled plan fingerprint:
  `c57595e65b9d60cd506eef5562584fa913cfd226a8dd5668ce17e941c0389533`.

The private build reads existing generated game/BIOS sources without running
the sibling checkout's generators. Shipping HLE boot, software rendering,
normal XA speed, separate writable state and disabled dynamic overlay caching
were used. These initial field captures used a CMake Release configuration
whose generic compiler flags were empty. They are functional evidence only.
The later validation build explicitly restores `/O2 /Ob2 /DNDEBUG` and C++
`/EHsc`; do not describe the earlier runs as optimized performance results.

## Streaming overlay consumption

The authored project changes actor `man-p1/0001` X from 9920 to 9984. Only
decoded MAN byte 3601 changes. Its replacement compressed stream occupies the
original 24,894-byte carrier span with preserved trailing bytes.

`mod_status` recorded one enabled overlay, zero direct writes, 13 sector
applications and exactly 24,894 copied bytes, ending at LBA 572. No expected-
byte guard failed. The game rendered the Rim Elm arrival scene, and both
bounded cold runs exited normally through `quit` with exit code zero.

## Revisioned field execution profile

The original `legaia-na-scus94254-field-v1` remains unchanged. The rebuilt
inventory executes the same witnessed instructions through this observed
backend combination:

| PC | v2 backend | SHA-256 of executed instruction |
| --- | --- | --- |
| 0x801CF754 | static-native | bad69a1914bdcaf9db0344c046a9731c78aae2d93bb2b842b5d7123b36fbf4bc |
| 0x801DE840 | static-native | ec4f4d5323b718c7b0c2a96aa7da96280e5e363fa61672bde6a0044ea9a621dd |
| 0x801D79E8 | interpreter | 2ed3561c68bb654f8e2ad2ad487bde2c12f773777e92956e1ff0e7f27ad6b1d9 |

The new profile retains every instruction hash, range, generation-currentness
check, scoped guard and scene constraint. It does not accept arbitrary backend
substitution. Title/intro scenes still reject; town0c is not newly validated.

Normal v2 capture accepted town01, PROT base 3 and master mode 3 at frames
21453–21538. It traversed 90 nodes using 90 exact 0x9C-byte prefix reads
(14,040 bytes); total duration was 1,446.744 ms. This is a guarded historical
observation across one stable scene epoch, not a simultaneous single-frame
snapshot of every moving property.

## Structural actor candidates

Pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`,
`docs/subsystems/script-vm.md`, identifies the MAN record base installed at
actor offset 0x90 by `FUN_8003A1E4`. Bounded guarded header reads combine MAN
model/pool, animation, local count and independent model object-count evidence.
Addresses and traversal order never establish content identity.

The initial live sampler examined 32 of the 90 nodes: 31 valid headers yielded
55 candidate links, including 16 single-candidate entities, 15 ambiguous
entities and 21 unmatched entities. These counts are from that explicitly
partial sample. The final implementation batches up to 128 nodes within 45
requests, 4,096 bytes and four seconds; its full-node retail acceptance remains
separate from the initial sample.

The candidate for actor 0001 contains MAN-header X=9984, agreeing with the
authored override and differing from imported X=9920. Its observed world
position was parked at X/Z=16320. Therefore the evidence proves the authored
header reached live RAM, but does not prove that the selected NPC is visibly
standing at the authored location. Candidate identity remains unconfirmed.

Private evidence is retained under `local-output/sdk-20260909/package-runtime/`:
`runtime-field-acceptance.json`, `runtime-field-research.json`,
`field-v2-live.json`, `man-binding-live.json`, `man-correlation-live.json` and
`authored-man-candidate-live.json`. Runtime captures, screenshots and slot-9
savestate remain ignored and are not repository fixtures.
