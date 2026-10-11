# World Script Branch Authoring

## Record Composition Foundation — 2026-10-11

World P0 branch authoring is in progress. The record-level foundation now provides `branch_record_options(record, entry)` and `patch_branch_record(original, entry, edits, operand_record=..., base_offset=...)`. The source caller owns qualified MAN/P0 provenance. These functions reuse the existing branch decoder, target-word arithmetic, original-boundary checks and retained dormant-source graph qualification; they do not execute a VM or modify project state.

Branch destinations must be original reached instruction or atomic MES starts between the source entry and PC32767. Interiors, opaque bytes, header addresses, new boundaries and out-of-record targets refuse. All edits use one immutable Retail record and preserve its complete length. Target words are encoded relative to their owned word offset with sixteen-bit wrap, retaining opcode, context, conditions and all other bytes. Normal SYSFLAG selector composition preserves its operation nibble. Extended system addressing remains unsupported.

Branch words compose after the caller's independently qualified fixed operands. Header and opaque bytes remain exact, and even an unrequested branch word cannot be changed in the supplied operand baseline. Source branch preimages and disjoint destination ownership are required. The complete candidate is redecoded against every original anchor, including instructions made unreachable by a changed edge. The result retains `unreachable_source_pcs`, `unvisited_instructions` and `unvisited_dialogues`; authored values in dormant instructions remain present rather than being erased or misrepresented as executed.

Thirty focused Python checks pass with the user-owned retail input enabled and no skips, covering the new record interface, existing branch serializers, fixed-operand composer and World argument workflow. New cases prove normal selector and MOVE_TO coauthors survive becoming unreachable, mixed branch edits are order independent, no-ops preserve bytes, and malformed domains/source entries/headers/opaque bytes/unaudited branch words refuse.

The real source qualification uses the existing World MAN context over the private project containing all six fixed argument families. Fifty-seven source records expose 165 writable original branch words: 122 `JMP_REL`, 42 normal `SYSFLAG_TEST` and one `BBOX_TEST`. Each is independently retargeted to its own original instruction start. All 165 complete candidates match literal byte construction and have no decoder stops; 41 candidates retain dormant source anchors. Project document/history remain unchanged. This verifies encoding and ownership, not runtime termination, story activation, bank validity or gameplay. Private evidence: `local-output/sdk-20260909/world-script-branches-20261011/`.

## Remaining Integration

The record foundation is not yet a published World branch authoring workflow. Project binding validation, Review/Apply commands, Undo/Redo and persistence, branch-last composition with existing World data-package Build, fresh-source HTTP qualification, and editor destination controls remain unfinished. Retail/Current graph inspection must also represent reached and retained dormant source anchors after intentional edge changes; its present fixed-operand shape guard must not simply be disabled.

The existing World instruction inspector continues to offer read-only static branch navigation. It does not yet apply branch edits. No new package Build, native recomp compile, game, runtime attachment, installation or disc export ran for this foundation. Gameplay remains deferred and the full SDK goal stays active, with implementation continuing solo.
