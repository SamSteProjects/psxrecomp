# Field overlay 0897 live-identity attempts

Latest validation date: 2026-07-19. Status: **not accepted**.

## Accepted boundary evidence

A freshly rebuilt native runtime was advanced through normal controller input
only. No debugger RAM write, title-specific hook, actor traversal, or
correlation was used. Bounded `read_regions` samples established:

- active scene name `town01`;
- runtime PROT base `3`;
- master game mode `3`;
- equal frame boundaries within each request; and
- equal executable-ownership boundaries within each request.

This accepts the scene boundary, not an overlay identity.

## Generic model correction

Protocol 1.2 now distinguishes image groups, structural ranges, registrations,
and current ownership. Static generated dispatch variants have no
authoritative guest overlay-load object, so they are grouped by exact range set
and expected CRC as `static-overlay-variant`. Their `load_base` remains null;
the separate structural envelope records the bounded range evidence.

The full town01 catalog was retrieved safely:

| View | Records | Pages at limit 8 |
|---|---:|---:|
| Image groups | 116 | 15 |
| Structural ranges | 116 | 15 |
| Registrations | 562 | 71 |

The structural catalog token remained stable. Ownership tokens changed across
some pages because watched generations changed on pages intersecting registered
executable ranges; the client exposed those changes separately. No response
overflowed and no record was silently dropped.

## Registrations covering the field function

The earlier eight records reduced to three structural ranges because duplicate
static matcher cache slots carried the same expected CRC and exact range. They
were duplicate registrations of one structural variant, not three loaded
overlay images.

During the longer renewed run, lazy execution registered two additional copies
of those variants and one additional exact range beginning at `0x801CF740`.
The resulting ten registrations represented four structural variants. Every
registration covering `0x801CF754` reported its exact source/live byte domain,
watched generation, prior validation when one existed, and the first failing
predicate. None was a current active owner. The failures were
`validated-bytes-mismatch`; several also had stale validation generations, but
the byte mismatch was the decisive current guard. Raw bytes and local hashes
are not committed.

The growth from 468 records in the first pass to 562 in the longer pass is
explained by lazy static matcher registration as normal execution reaches more
generated dispatch guards. The stable catalog token within a completed pass
shows that paging itself no longer creates an ambiguous mixed catalog.

## `0x801CE818` classification

No image group had `0x801CE818` as an authoritative load base, and no current
catalog metadata supplied a loaded length or lifecycle event rooted there.
Nearby static structural variants begin at later function/range addresses.
The candidate is therefore **still unresolved**: the available generic evidence
does not establish it as a loaded-image, allocation, data, or relocation base,
and it is not safe to label it incorrect solely from absent static registration
coverage.

## Decision

Overlay 0897 still lacks a repeatable authoritative loaded-image identity or a
deterministic required set of currently owned registrations. Its canonical
base, loaded length, live SHA-256 domain, source relationship, and ownership
gate remain unknown. At that stage, the revisioned layout profile remained
unchanged and fail closed.

The generic catalog prerequisite is accepted; a Legaia observer is not. The
next safe work is evidence collection for the actual overlay load/capture event
or another authoritative generic image lifecycle source. Actor traversal and
imported/runtime correlation remain premature.

## Protocol 1.3 lifecycle result

A later fresh `RelWithDebInfo` run enabled lifecycle tracking during protocol
negotiation and reached the same stable `town01` / PROT `3` / master-mode `3`
boundary through normal controller input. No debugger RAM write was used.

The exact field instruction at `0x801CF754` was observed executing through the
dirty-RAM interpreter. Two fresh runs agreed on the backend. In the final run,
the observation was current at query time, had 3,814 prior hits, and advanced
while repeated queries were made. The record had no native registration ID and
no DMA-image-instance parent. This resolves the execution backend without
promoting any mismatched static registration to native-valid.

The earlier base candidate `0x801CE818` had no exact execution-owner observation
and was not an authoritative DMA capture base containing the observed field
instruction. This narrows the result but does not prove whether the address is
a decompression destination, allocation/data base, or an incorrect prior
interpretation. It remains unresolved.

The first lifecycle run exceeded the initial diagnostic-table capacity during
the long opening sequence. Raising the bounded instance and exact-owner tables
above that observed working set produced `overflowed:false` in the repeat
town01 run. The 4,096-event ring correctly reported older history as truncated;
this is bounded retention, not silent loss.

Overlay 0897 is still **not accepted**. The interpreter backend is repeatable,
but it cannot be linked to a bounded active executable-image instance, source
or capture identity, deterministic child range set, or authoritative base and
length. The layout profile remains unchanged and fail closed.

## Protocol 1.4 terminology decision

The subsequent execution-witness pass did not discover a canonical whole-image
range. Instead, it accepted three independent exact-instruction witnesses as a
repeatable **field execution identity**. The profile now uses that witness set,
plus executable and scene signals, for fail-closed selection. It does not call
the set an overlay hash or resolve `0x801CE818` as an image base.

See `field-execution-identity.md` for the accepted ranges, hashes, backend
stability, field-scene replacement evidence, and profile contract.
