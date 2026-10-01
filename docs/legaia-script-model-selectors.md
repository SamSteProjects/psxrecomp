# Script model selectors

Open a supported actor or partition-two script Inspector and locate
SET_ACTOR_MODEL. **Open operand editor** focuses its signed script selector.
Retail, Authored and Effective values stay separate; an input draft also shows
the encoded unsigned word and signed high-pool dispatch test. Apply, Clear,
Discard, Undo/Redo and Save/Open use the existing command and history system.
The project stores a ScriptModelSelectors component with source-qualified IDs:
`script://<owner>/model-selector/<four-hex-PC>`.

The supported value is an integer from -32768 through 32767. This is an encoded
script selector, not a resolved Asset Database model ID. The pinned wrapper uses
a signed comparison against 240 to set/clear flag0x01000000. Its primitive writes
model_id, resets move_id, clears draw flag0x1000, and mirrors the ID in world-map
mode. Runtime pool bases, the resulting asset, mesh restaging, animation pairing
and story execution remain unresolved. The viewport does not simulate this opcode.

Only reached, uniquely owned instructions in records without decoder stops are
offered. Writes change the signed16 operand at MENU_CTRL sub-op0x50 and preserve
opcode, sub-op, extended dispatch byte, other operands, branch layout and source
record extent. Build rechecks the exact source, requested value and audited
two-byte span, rejecting overlaps and any unaudited byte. Appended records are
rebound through partition/index and verified instruction preimage.

Descriptor scenes use the ordinary package Build path. Streaming scenes such as
Dolk2 use the experimental Export disc path; ordinary descriptor Build remains
unavailable for their script overrides. Source-compatible append and streaming
composition retain the same selector audit and uncertainty.

## Evidence - 2026-09-30

Thirty-four focused retail-enabled script/project/build/draft tests passed in
35.413s with no skips, including five selector tests with partition-two
ownership/persistence and rebased extended actor-context rejection coverage. Signed boundaries, high-pool
threshold, extended dispatch, no-stop gates, appended rebasing, exact spans,
history/persistence and Build audit rejection are covered. Node bindings and
editor syntax passed. This feature follows the 405-test source checkpoint.

Retail source discovery offered ten Dolk2 actor selectors and three town01 actor
selectors. The Dolk2 actor0002 browser passed source-instruction navigation,
invalid input, negative draft unsigned display, no-write draft, Discard,
241-to240 Apply/Undo/Redo/Clear/Undo/Save and Boolean HTTP rejection. Exact saved
field focus passed; screenshots were visually inspected, with zero page errors.

A reopened town01 actor0003 project built a package whose ZIP overlay independently
decoded to the exact expected MAN: selector241-to240 plus the three retained
menu overrides. Package SHA256:
`228abd8eea3d71114f5401b7897c12109a5d257130474757d51e5b1dfe9ebaac`.
The Dolk2 experimental archive retained the exact expected MAN candidate, found
uniquely in the rebuilt PROT, with other MAN bytes preserved. No disc or package
was installed and no game launched. Gameplay/model restaging remains deferred.

Private evidence is under `local-output/sdk-20260909/`:
`model-selector-project-20260930/model-selector-browser-check.json`,
`model-selector-field-focus.json`, `model-selector-streaming-readback.json`,
`model-selector-final.png`, and
`model-selector-town01-20260930/model-selector-package-readback.json`.

## Reference

Unchanged pin `d6e64c68ede25813d35db20980da82a1a025549b`:
`crates/engine-vm/src/field/step/menu_ctrl/nibble_5_6_7.rs::op_4c_n5` and
`crates/engine-vm/src/field/host.rs::op4c_n5_sub0_set_actor_model`, read through
git show. The serializer is independently implemented over our verified MAN
decoder; reference code is not a shipped runtime dependency.

## Integrated source checkpoint — 2026-09-30

The retail-enabled discovery suite passed 421 tests in 172.966s with no skips
against unchanged `be7a5e42686119b2290643556a9827775cfb21c7`. This includes
this feature's Python service tests and supersedes the earlier 405-test full
checkpoint referenced above. Five Node checks and editor/module syntax passed
separately. Browser/package/rendered evidence and gameplay acceptance remain
separate; no game was launched for this checkpoint.
