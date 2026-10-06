# NPC-owned branch destination authoring

The native serializer supports independent branch destination words for appended
NPC records. It uses the existing source-qualified branch authoring adapter; it
creates no new instruction families or speculative script semantics. Only
original reached instruction or atomic message starts can become destinations.
Unknown/conflicting paths, opaque/interior boundaries, changed conditions,
selectors, contexts and foreign/aliased allocations reject.

The adapter resolves final record extents after appending all clones. It rebinds a
clone to its immutable donor slot in a private in-memory MAN snapshot for native
qualification, then copies only audited destination words into that clone.
Imported records are untouched. Complete entries qualify together against both
the original source graph and the proposed graph. Source spans are retained even
when changed edges make their instructions unreachable.

Branch serialization should run after the other NPC-owned script families so
those qualified operands remain present even if the final graph skips them.
Runtime branch activation, story reachability and termination are not asserted.

Select an authored NPC and choose **Edit NPC script branches...** in its
Inspector or Asset Details. Check a target to enable an independent override and
enter an original source instruction/message PC from the shared destination list.
Review qualifies the complete branch set against the existing own script edits;
Apply makes one Undo step. Changing inputs withdraws the proposal. Uncheck and
apply to restore the Retail destination. Undo/Redo and Save/Open retain entries.
Normal compressed and streaming Build paths compose branches last. Repetition
qualifies and retains branch entries. Branch-bearing preset capture currently
rejects; portable presets are still pending. Saved-script comparison now qualifies
branch words and retained edits in instructions skipped by changed edges.

Thirteen focused Python checks pass with private retail input enabled. A fresh
Town01 two-clone proof changes SYSFLAG_TEST PC14 to source boundaries11/12 and
preserves appearance, waits, movement, flags, donor, layout, unrelated bytes,
project/history and all file hashes. Evidence:
`local-output/sdk-20260909/npc-branches-native-20261005/proof.json`.
No game launch or full-disc export was used.

## Editor and Build verification

Nineteen focused Python checks with private retail input and the Node contract
suite pass. Actual browser Review/Apply/Clear, input withdrawal, Undo/Redo and
Save/reload pass; the saved 540px dialog top and bottom were visually inspected
without changing project/history/files. A first-probe opener export mismatch was
fixed and added to the Node check.

Town01 normal Build `6e6a47c3f7d988fe` independently reopens target11 at PC14;
only the branch destination word differs from the verified six-family record.
Streaming Rayman Build `0dc504a3a5d7cf6f` reopens two independent targets9/10 at
PC12, changing only their word bytes while retaining all six previous families.
Evidence:
`local-output/sdk-20260909/npc-branches-editor-20261005/proof.json` and
`local-output/sdk-20260909/npc-branches-streaming-20261005/proof.json`.
No game launch or full-disc export was used; runtime acceptance remains deferred.

## Saved NPC branch explanations - 2026-10-05

Saved-build comparison now explains source-qualified NPC branch destination words
alongside appearance, dialogue, waits, movement, facing and flag bits. Native
qualification binds original instruction boundaries and the final graph to the
saved receipt. Browser decoding independently checks all eight supported branch
word families, exact dispatch, targets, original boundaries and held selectors.
Edits retained in instructions skipped by a changed branch still qualify: facing
and flag checks use a private copy with original branch words restored, while the
comparison always displays exact saved bytes. No project data is changed.

Validation: 11 focused Python checks with private retail input and the Node
comparison suite pass, including skipped-body edits and forged receipt rejection.
A fresh saved Town01 Build `6e6a47c3f7d988fe` comparison renders all seven edit
families and accounts for 30 of 33 changed bytes; three stay unexplained. The 540px
comparison was visually inspected. Streaming Build `0dc504a3a5d7cf6f` independently
qualifies both NPC branch spans. Both projects, Undo/Redo history and every project
file hash remain unchanged. Evidence:
`local-output/sdk-20260909/npc-branches-script-comparison-20261005/proof.json`.

Portable branch presets remain pending. No game launch, new Build or full-disc
export occurred; branch activation, story reachability and termination remain
unverified. Manual gameplay acceptance stays deferred and the SDK goal is active.
