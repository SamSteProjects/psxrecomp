# Retail text glyph preview

Open an imported actor's script Inspector with the project retail disc available.
Supported dialogue and menu-label forms show separate Retail and Effective
glyph runs. Typing a replacement adds an unapplied Draft after Apply preview,
including the spaces required to retain the source byte capacity. Discard hides
that draft. These previews do not change project state or send authoring commands.

The importer decodes the pinned retail font TIM and executable width table.
The service verifies the actor's imported MAN and returns the font with its
source hashes. The editor rejects mismatched owners, MAN identities, dimensions
and payload sizes. A response from a closed or superseded Inspector cannot attach
to its replacement.

This is a source glyph stencil: transparent background, white fill and dark
shadow. Each run starts at zero and uses the retail byte advance plus one pixel.
Controls, substitutions, wrapping, dialogue boxes, pager behavior, runtime tint
and the preceding run's placement are not simulated. Unsupported or over-capacity
drafts have no glyph preview. Drawing is bounded to128 characters and4096 pixels;
the displayed total advance still accounts for the complete supported run.

## Evidence — 2026-09-30

Nine focused font/project/text-file Python tests passed, plus pure JavaScript
font shape, source identity, coordinate, advance, control and clipping checks.
A retail town01 actor0001 browser rendered all30 supported label forms. Retail,
effective and padded draft canvas readback matched decoded atlas pixels and
advances. Invalid drafts, Discard, a held response delivered after close/reopen,
and malformed request rejection passed. Project state stayed unchanged, with
zero authoring requests and page errors. The screenshot was visually inspected.

Private evidence is under
`local-output/sdk-20260909/text-json-project-20260930/font-browser-check.json`
and `font-preview.png`; font pixels and retail text are not tracked. The397-test
checkpoint predates this feature. No game was launched. Runtime dialogue/menu
appearance and reachability remain deferred.

## Source provenance

Reference pin: `d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/font/src/lib.rs` and `docs/formats/dialog-font.md`. This is an independent
decoder, with no reference runtime dependency. Retail source: PROT.DAT offset
0x7F40, bounded0x8100-byte read, 4-bpp TIM page at(896,0), 64 words by256 rows,
CLUT at(0,510). The SCUS_942.54 width table is256 bytes at RAM0x80073F1C,
translated through the executable load header. Source cells are16x16, cropped
to14x15 and packed into a224x210 atlas. Index0 is transparent, index14 is shadow.

Observed retail TIM SHA256:
`f4d822bab3ffe9e262317da3dabfcd8e56b1c0f5381978d772f00422927c4d9c`.
Width-table SHA256:
`d4b26b8ed89674c22562ed9def33cb9308656624cfbd76d8767bcea08b1a1d0f`.

## Accumulated source checkpoint - 2026-09-30

The405-test retail-enabled SDK discovery run passed in165.295s with no skips
at unchanged source `cc41ded01fd8b14fee9c9795c9d780aa43a1f82e`. This supersedes
the397-test checkpoint referenced in the original feature evidence above and
includes this service and its focused tests. Font/operand/texture/runtime-review
Node checks and editor syntax passed separately. Browser evidence and deferred
gameplay acceptance remain separate. Exact private log and command/source/hash
metadata: `local-output/sdk-20260909/sdk-regression-20260930-text-discovery.log/.json`.
