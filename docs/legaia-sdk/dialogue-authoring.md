# Bounded dialogue text authoring

The script inspector can author existing plain-text runs through project commands.
Imported segments remain visible, with authored and effective text shown
separately. This is text editing within established source spans; it does not
relocate scripts, change control codes or evaluate which conversation is active.

## Source evidence

Reference: AndrewAltimit/legend-of-legaia-re at
`d6e64c68ede25813d35db20980da82a1a025549b`, inspected through read-only Git objects.
No reference implementation or retail text is bundled with the SDK.

| Pinned source | Blob | Evidence |
|---|---|---|
| `crates/mes/src/lib.rs` | `72a4cc8f96f079a544a3b7c5eee85df2feeec955` | Bytes 0..0x1E terminate a segment; caret 0x5E is a two-byte spacing alias; substitutions consume their argument, including zero. |
| `crates/engine-core/src/man_field_scripts/records.rs` | `a7f072f56ce4fc836967b95c9cd990cdf18ad3c1` | Actor entry follows one local-count byte, two bytes per local and the four-byte placement header. |
| `crates/engine-core/src/man_field_scripts.rs` | `63a45088c2382e43a7ced22629122dbaf249ae5c` | Record ceilings consider all partition starts, section offsets and MAN length. |
| `crates/engine-core/src/dialog.rs` | `078d6a6ab8fbdc86be8d5d01adba622bae84d566` | Inline MAN segments use the evidenced 0x1F lead. |

## Representation and workflow

`Dialogue.runs` maps stable run IDs to authored strings. For example:

```json
{
  "Dialogue": {
    "runs": {
      "script://fixture/actors/man-p1/0001/dialogue/0010/run/0011": "SDK text"
    }
  }
}
```

PC suffixes are lowercase, four-digit record-relative hexadecimal offsets.
Commands `set_dialogue_text` and `clear_dialogue_text` participate in Undo/Redo,
dirty tracking and Save/Open. Clearing one run preserves other text runs,
transforms and appearance overrides. Project opening checks identifier/text
syntax without requiring the disc; editing and building reverify actual source
membership and capacity. Project metadata stores authored strings, not copies of
the imported dialogue or binary payload.

The script modal exposes each supported run's imported text, authored input,
effective text and source-byte capacity. Shorter input is right-padded with
spaces, including empty input. The padding count is explicit. Caret, control
characters, non-ASCII and over-capacity input are rejected without truncation.
Controls, substitutions and unsupported segments remain read-only.

## Serialization invariants

`importer/dialogue_authoring.py` loads one verified bounded MAN stream. It
rejects aliased actor starts across all partitions, section overlap, conflicting
decode boundaries and unknown instruction stops. Supported runs contain only
contiguous one-byte printable ASCII glyphs, excluding the caret alias. Unvisited
tail bytes remain untouched and are not treated as decoded script.

The patch helper starts from its immutable verified baseline and returns exact
audited spans. It compares decoded instruction/control/token structure after
editing and confirms unchanged MAN placement and record metadata. No-op edits
return identical source bytes. All source spans retain their original length.

Build validates text-run ownership, merges guarded dialogue spans with any
independently validated position/appearance changes, rejects overlap and checks
that no unaudited bytes changed. It serializes the composed buffer within the
original MAN capacity. The existing greedy encoding remains unchanged when it
fits. On overflow, decoded streams up to 256 KiB use an eight-phase minimum-byte
LZS parse, including control-byte costs. References never expand beyond the
declared output length. The fallback is independently decoded and records its
strategy and greedy size in the audit. If it still exceeds capacity, build fails
without relocating data or changing authored text. No-op source bytes stay exact.
Private build audits retain exact byte changes and source hashes.

## Acceptance and remaining scope

The initial town01 source sweep exposed 154 runs across 16 actors. Later decoder
coverage expanded this set; these initial counts are not current capability
limits. Unknown instruction paths still reject authoring. Targeted checks cover
padding, no-ops, malformed strings, alias/conflict rejection, source preservation,
history/persistence and composition with existing edits.

A custom text and placement build reduced a 24,896-byte greedy stream to
24,504 bytes within the original 24,894-byte capacity. A combined appearance,
placement and custom text build also passed exact decoded-span validation.
The refreshed editor passed Apply, Undo/Redo, Save/Open, Clear/Undo, overlong
draft rejection and Build with the saved replacement. Browser errors were empty.

On 2026-09-10 a separate cold run visibly accepted actor 49's 12-byte run
`script://town01/actors/man-p1/0049/dialogue/0050/run/0053`. Replacing
`, I love the` with `SDK VERIFIED` rendered `VahnSDK VERIFIED` and the unchanged
next line `Genesis Tree, too!` when talking to the child beside the tree after
the opening Village Elder conversation. The character-name control token was
preserved; the concatenation reflects the exact authored replacement. Normal
Confirm closed the message and returned to field control.

The package SHA-256 was
`f44a8fc57ee981abd4ce90d7d1a1298fad3c477d6457ca11e0cdcf9971f01bd9`;
the runtime consumed 24,894 overlay bytes across 13 sectors with no disc guard
failure. Runtime and editor exited zero. Private evidence is retained under
`local-output/sdk-20260909/dialogue-navigation-20260910`, especially
`edited-dialogue.png`, `following-dialogue.png`, `acceptance.json`, and the
project build audit. No savestate or guest-memory edit was used. An earlier
failed title/movie-loop attempt remains separately retained; confirming promptly
from a fresh title screenshot resolved navigation without a runtime change.

This establishes one modified message's reachability and visible rendering,
not general font widths, line wrapping, box layout, full script behavior or P2
dialogue gameplay acceptance.
Text growth requiring relocation, control-token editing, rich character encoding
and script authoring remain separate unfinished features.
