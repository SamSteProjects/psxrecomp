# Texture runtime acceptance

The 2026-09-10 cold authored run used the existing layout-compatible replacement
for `texture://town01/5/raw/0`. Nonzero palette entries were changed to magenta;
the image payload, transparency/STP treatment and TIM layout were preserved.
Actor overrides were removed from the isolated test project, leaving one TIM
replacement as the only package edit.

The tested executable SHA-256 is
`2be69467c02937d6ccfc86a6030f9380bc5654ea6404694ea3e801a25b716fab`.
The replacement TIM is 33,312 bytes, SHA-256
`827f9152d7dc9a6d5493041c3246e85b3c57cdaf3a318e97514b9fdd85dfa01f`.
The runtime consumed exactly 33,312 overlay bytes across 17 sector applications
with no expected-byte guard failure and no direct memory writes.

A cold New Game reached name entry and the field scene. The captured field
image visibly shows magenta ground beneath Vahn beside the Genesis Tree. No
savestate was loaded. This establishes one source texture's consumption and
visible display in this scene; it does not establish every TIM carrier, palette
animation, blend mode, battle resource or conditional upload path.

A second cold run used the same executable with actor and texture overrides
empty and a zero-overlay package. Its field image restores the original ground
color beneath Vahn; the magenta strip is absent. Neither run used a savestate.
The supporting pixel criterion `R>=80, B>=80, 2*G<min(R,B)` counts 1,141 pixels
in the authored image and zero in the baseline. Camera/animation frames are
not asserted identical; the conclusion also uses independent visual inspection.

The authored run stopped normally with exit code zero. Its full guarded Live
observation rejected a missing required execution witness. That rejection was
retained; no profile was relaxed and no actor-correlation acceptance is claimed.
The visible texture conclusion relies on the identified cold process, guarded
overlay consumption and inspected field capture.

The baseline manually requested all three profile PCs during the opening movie,
before field entry. At the final Village Elder dialogue, all three witnesses
were current with the required backends and the unchanged v2 observer accepted
the scene. This exposed an SDK collection setup gap: negotiation enables
tracking, but exact-PC requests are needed before execution is retained.

Compatible-runtime discovery now prepares every required profile PC, and
Build & Run invokes discovery after verifying the owned process and mod plan.
Initial `missing` replies mean collection is prepared, not that a scene or
instruction was verified. A separate startup-only run tested this automatic
path: all three PCs were reported primed, `scene_verified` remained false, and
the process exited zero. The cold field comparison used manual early requests;
it is not represented as an end-to-end test of the new automatic launch path.

A subsequent independent zero-overlay cold run did pass the full automatic
launch-to-field path, with all three witnesses current and 90 nodes accepted.
See [automatic witness field acceptance](automatic-witness-field-acceptance.md).
That later run used no manual witness requests and exited zero.

No runtime or profile definitions changed. `overlay_capture.c` retains only
requested PCs and has no idle expiry; restore resets retained ownership and
still requires genuine re-execution. Late attachment cannot recover an earlier
unrecorded execution. Cross-scene and restored Live acceptance remain separate.

Private source projects, package files, logs and images remain beneath ignored
`local-output/sdk-20260909/texture-runtime-project` and `texture-runtime-qa`.
The existing authored test project and main editor project were not modified.
