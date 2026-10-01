# Apply actor presets to a group

Select 2–128 imported actors in one active scene with Ctrl-click or the actor box
tool. Choose **Apply preset to group**, pick a position, appearance or combined
preset, then **Review group preset**. The SDK freshly verifies the source scene,
target scene and every target's existing compatibility rules before returning
any proposed edits. One incompatible target rejects the whole review.

The table shows imported, effective and proposed XYZ and authored/proposed donor
references. Complete authored component changes and Build restrictions remain
inspectable. Saved position axes are absolute for every actor, so applying shared
X/Z axes can overlap a group. Untouched axes and unrelated components stay as
before. Appearance scope changes initial donor pairs only.

After review, **Inspect group preset in scene** opens a read-only assembled
scene comparison. Switch between **Current** and **Proposed**, then **Return to
group preset** to retain the reviewed Apply action. **Restore** discards the
inspection. Closing a pending request or changing group membership also discards
it. The camera remains fixed, and marker coordinates follow the active layer.
Unknown guest Y stays unknown; preview does not write actor components.

**Apply reviewed preset to group** re-verifies the group and reviewed key and
commits one atomic Undo/Redo entry. Save/Open uses the existing authored override
format. An already matching group creates no history entry. Changed membership,
preset, target components, source scene, stale reviews, Live mode and active
proposal inspections prevent application. No NPCs are instantiated, and retail
height, facing, scripts, visibility, collision and runtime behavior remain open.

Validation on 2026-10-01: 11 focused Python tests cover all three scopes,
persistence, source failure, stale keys, no-op groups and failure on the last
target without partial edits. All 15 Node checks and 18 editor syntax checks
passed. Retail-source browser selected actors 0011/0012, reviewed without writes,
applied one changed target, saved, and restored the entire group with one
Undo/Redo; unknown Y stayed unknown and zero page errors occurred. Screenshot
inspected. Independent Save/Open retained all four NPC drafts. A detached normal
Build view without drafts produced a full decoded 45338-byte town01 MAN equal to
its baseline with exactly target 0012 X changed at offset 8498, from 3008 to 2944.
Package SHA256: `a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build still rejects projects containing NPC drafts. Private evidence is
under `local-output/sdk-20260909/preset-batch-20261001/`. No game launched or disc
installed. These additions postdate the integrated 463-test checkpoint.

**Group preset scene inspection (2026-10-01):** The extension adds read-only Current/Proposed comparison in the assembled
3D scene for position, appearance and combined group presets. Return retains the
review for atomic Apply; Restore, changed selection and a closed pending request
discard it. Preview preserves the camera and unknown guest Y, and writes no
actor components. Markers and framing now use the active proposal's display
coordinates, matching its rendered meshes. Twelve focused Python checks, all 16 Node checks and 18 editor module syntax
checks passed. The final scene screenshot was inspected. All three scopes also passed the production
decoder against freshly verified retail-source scene responses. The retail browser
checked two changed actors, Current/Proposed/Return, Restore, late-response and
selection guards, Apply/Save/Undo/Redo, matching marker coordinates and unchanged
camera, with zero page errors. Independent normal Build readback matched the
entire 45338-byte MAN with only five expected donor/position bytes changed; all
other package payloads were preserved. Normal Build proof used a detached view
without drafts; projects containing drafts remain rejected. Private evidence:
`local-output/sdk-20260909/preset-batch-scene-20261001/`. These changes postdate
the integrated 463-test checkpoint. Gameplay and
runtime parity remain pending; no game was launched.
