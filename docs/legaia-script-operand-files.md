# Script operand JSON files

Open an imported actor or partition-two script in the script inspector. In Edit
mode, **Download operand JSON** exports the owner's existing authored numeric
operand entries. An owner without these edits exports an empty components map.
The file is bound to the exact owner and imported scene hash. It contains authored
metadata; dialogue/text files use their existing separate workflow.

**Inspect operand JSON file** verifies the imported source and each supplied
entry through the normal fixed-width authoring contexts. Review shows current
and proposed authored fields for every supplied instruction. **Apply reviewed
operands** re-verifies the file and complete owner state before one atomic
Undo/Redo command. Save/Open persists the ordinary authored components.

Supported components are ScriptMovement, ScriptFlags, ScriptWaits,
ScriptModelSelectors and Transitions. Existing instruction eligibility and
numeric bounds apply. Each supplied entry replaces all authored fields for that
entry; other entries and unrelated components are preserved. This v1 does not
clear omitted entries, transplant to another owner, append instructions, change
control flow or transfer dialogue. A no-op file adds no history entry.

Files use `legaia.script-operand-file.v1`, exact scene/owner/source-import SHA256
and a components map containing only existing `entries` structures. Limit:
64 KiB UTF-8 JSON and256 instruction entries. Duplicate keys, unsupported fields,
nonfinite values, malformed bounds, unknown instructions, owner/source mismatch
and stale reviews reject. Live mode cannot Apply persistent edits. Unknown retail
semantics and actual execution remain unknown; metadata is not runtime authority.

**Script operand JSON workflow (2026-10-01):** The script inspector now
exports authored movement, flag, wait, model-selector and transition operand
metadata. A bounded source/owner-bound file review stages every entry through
existing verified commands; one atomic Apply supports Undo/Redo and Save/Open.
Supplied entries replace their authored fields; other entries/components remain.
Duplicate/nonfinite/extra/oversized files, wrong source/owner and stale reviews
reject without partial edits. No instruction bytes, dialogue, control-flow layout
or runtime state are transferred. Nineteen focused Python checks, all 18 Node
checks and 20 editor syntax checks passed. Retail browser verified export,
read-only review, Apply/Save/Undo/Redo, wrong-owner rejection and restored baseline,
zero page errors. Screenshot inspected. Independent reopen retained all four
NPC drafts; a detached no-draft normal Build matched the complete 45338-byte MAN
with only offset4811 changed for owner0003's selector240→239. Other content
payloads were unchanged. Package SHA256:
`e440d265be2a20a7008801e89c60eb1de8adc586ef3cac470e6ad22dc4aad53e`.
Normal Build still rejects drafts. Private evidence:
`local-output/sdk-20260909/script-operand-files-20261001/`. This postdates the
469-test integrated checkpoint; execution/gameplay remains deferred. No game
launched or disc installed. See [operand files](legaia-script-operand-files.md).


## Advanced retail workflow verification — 2026-10-01

**Script file review refinement (2026-10-01):** File controls now bind to
the script owner's authored-state snapshot. An owner edit observed during review
withdraws Apply in the UI; the server's existing stale-key rejection remains.
Reviews show a readable operand/instruction/current/proposed table, with complete
source-bound details collapsed. All 18 Node checks and 20 editor syntax checks
passed. Final retail browser checked one-command flag/model-selector/move imports,
actual partition-two asset-to-script navigation, P2 Apply/Save/Undo/Redo, stale
review withdrawal and a closed pending response, zero page errors. Baseline
restored; screenshot inspected. Independent Save/Open retained four drafts.
Detached no-draft builds matched the complete 45338-byte MAN: mixed actor edits
changed only4808/4811/4816; the P2 flag changed only28557. Raw record-table/opcode
checks established offsets independently; every other content payload was
unchanged. Private evidence:
`local-output/sdk-20260909/script-operand-files-advanced-20261001/`.
No game launched or disc installed. Gameplay remains deferred; these checks
postdate the integrated469-test checkpoint.

Mixed package SHA256:
`f54beb07d39295ddad40d897ea29113ad1c7cd7b7c52084e31e866a2cfa5a867`.
Partition-two package SHA256:
`fee5c9d3ba1d876d93995f0916ad79f974d399919c8466d836bf4bd823778d92`.
Normal Build still rejects projects containing NPC drafts; this readback used
detached views without drafts and did not change saved draft state. The file
format and supported serializers are unchanged. No opcode execution, story flag
meaning or runtime actor identity is inferred from successful serialization.
