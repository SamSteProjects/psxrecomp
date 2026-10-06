# Raw streamed MAN in normal Build

## Current scope — 2026-10-05

Qualified raw streamed MAN NPC candidates now enter normal **Review Build** and
**Build** through source-bound relocation packages. Compressed NPC candidates
may use fixed-span overlays or qualified capacity-growth relocation. Current
source, allocation, composition and actor-pool bounds still apply; source packaging
support does not establish native spawning or gameplay. See the current
[NPC candidate boundaries](legaia-npc-build-candidates.md) and
[actor-pool evidence](legaia-npc-actor-pool.md).

The initial milestone below predates NPC and MAN growth support. Its fixed-span
restrictions and NPC rejection describe that historical implementation only.
The recorded tests and package hashes remain historical evidence.

## Initial fixed-span milestone — 2026-10-01 (historical)

Normal Build now consumes the same typed MAN source handoff used by retail
import and experimental scene preparation. Descriptor MAN is decoded, edited and
capacity-guarded as LZS. Raw streamed MAN is edited directly and emitted as
`assets/<scene>-man.bin`, with `compression: none` in its audit.

This connects existing source-bound placement/header/script editing to normal
mod packaging for supported raw carriers, including Dolk2. It does not append
records or relocate raw chunks. NPC drafts still block normal Build and remain
part of the separate experimental export workflow.

Raw writes must retain the original word-aligned payload size, unique structural
chunk locator, complete terminated carrier, record offsets/lengths/local counts
and partition counts. The writer reopens the MAN, revalidates chunk boundaries,
preserves surrounding carrier bytes and rejects every changed MAN byte outside
the combined audited spans. Overlapping overlays are still rejected. Imported
provenance is freshly checked before source locators are used. A malformed
preferred descriptor is not permission to substitute another raw source.

The existing compositors retain their source and ownership guards. Retail checks
cover raw placement, same-scene initial donor appearance, fixed-span dialogue,
partition-two transition entry and flag-bit changes, together with a separate raw
ANM bank. Other audited script families use the shared route, but this milestone
does not claim retail normal-Build coverage for every streaming scene or family.
Raw actor positions retain the exact 64-unit retail X/Z grid from64 through16384;
height, facing, arbitrary appearance pairs and script reachability remain outside
this placement claim. Scripts may change initial values after loading.

Raw MAN validation is reported separately as **raw MAN structural round trip**.
It does not claim an LZS check on uncompressed bytes. A mixed package can report
both raw and compressed validation, each applying to the corresponding overlays.
Normal Build review, saved receipts/history and comparison use the same output
audit and require no separate manual packaging step.

The unchanged Andrew pin `d6e64c68ede25813d35db20980da82a1a025549b` was reread
through command-scoped `git show`: `crates/engine-core/src/scene_bundle.rs`
extracts raw MAN bytes at chunk header+4, and `crates/asset/src/man_section.rs`
documents the local-count prefix and actor-header coordinate encoding. This is
reference evidence. Fresh retail bytes, exact package member readback and the
SDK's independent guards establish the offline result; no code was copied and
the reference checkout was not modified.

Validation on 2026-10-01: 27 retail-enabled Python checks passed in79.901 seconds,
including raw placement/no-op/clear, exact overlay offset/span, mixed raw MAN/
ANM composition, donor/script edits, unchanged opaque bytes, bad chunk locator
and unaudited mutation rejection before output creation. The focused set also
covers existing compressed Build, reviewed input identity, baseline package
equality, texture composition and animation packaging. All25 Node files and26
editor syntax checks passed. The initial composition test assumed an explicit
scope on placement rows and raised KeyError after successful packaging; its
expectation was corrected to honor the existing default scope, then the expanded
set passed without loosening the serializer.

A fresh headless editor browser reviewed and built the same mixed Town01/Dolk2
report: ten changes, two overlays,68,930 bytes, both validation families passed.
Dolk2 actor0011 initial X9408→9472 was retained in the uncompressed44036-byte MAN.
Authored entities/assets and saved project metadata stayed unchanged, zero page
errors; screenshot inspected. No Run, Save or authoring command was dispatched
by the browser probe. Owned browser/server stopped, no game launched.

Private evidence: `local-output/sdk-20260909/raw-MAN-normal-build-20261001/` and
`streaming-normal-build-20261001.log`. The mixed package SHA256 is
`1a2effd3c3f17f30efa9a77a6945bb98ba5b2a458e71dc11950430e0b02f8ef1`.
Manual gameplay is deferred in the verification queue. This feature postdates
the integrated498 checkpoint; native runtime behavior, scripted repositioning,
scene visibility and collision acceptance remain open.
