# NPC-owned named transition arrivals

## NPC-owned transition arrival serialization foundation - 2026-10-06

A native serializer now supports independently owned arrival bytes for qualified
SCENE_CHANGE instructions in appended NPC records. It uses the existing transition
adapter and the shared final-allocation guard, which now accepts the adapter's
transition target collection. Typed partial/full requests alter only encoded
entry X, Z and direction bytes. Destination names, full opcode/context/argument
preimages, untouched arrival bytes and layout remain bound to the retail donor,
even for no-op requests. Branch composition must follow operand serialization.

Validation: 24 focused native transition and NPC selector/branch/wait/flag checks
pass. Coverage includes ordinary/extended dispatch, two independent final clones,
partial/full byte edits, retained waits, no-op preimages, malformed values, changed
names/arguments/context, foreign ownership and forged allocation rejection.

Retail eligibility remains unresolved: a fresh source-qualified scan found no
eligible actor-owned named transitions in Town01, Dolk2, Town0b or map01. This does
not establish absence of runtime transitions. The first Town01 clone-proof attempt
stopped at that eligibility assertion; no retail clone proof is claimed. The scan
preserved project documents, histories and all file hashes. Evidence:
`local-output/sdk-20260909/npc-transitions-native-20261006/discovery.json`.

This is a native foundation with synthetic ownership/composition evidence, not a
completed retail editor workflow. Project review, editor, Build, presets and saved
comparison remain pending; a qualified actor donor or supported script-binding
extension is needed before a retail vertical workflow can be proven. No game
launch or full-disc export occurred. Gameplay acceptance is deferred and the full
SDK goal remains active; other offline SDK work remains available.
