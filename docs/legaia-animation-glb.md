# Source-bound animation GLB authoring

The SDK can export an existing imported actor's effective rigid animation to
GLB, review a GLB edited in an external application, and apply only its changed
source axes through normal animation commands. The accompanying binding JSON
identifies the owner, model, clip, source record, effective record, scene state,
existing frame/object counts and selected interchange rate.

## Workflow

1. Select an imported actor, open its animation channel editor, and choose
   **Edit animation through GLB**.
2. Choose an explicit rate from 1 to 120 fps and export the GLB and binding JSON.
   Both files are also retained in the project's private `Exports` directory.
3. Edit the independent `object-0`, `object-1`, etc. translation/rotation channels
   in Blender or another GLB editor. Keep object names, source object indices,
   unit scale, existing timeline and rigid-object arrangement.
4. Export a self-contained GLB. Select that GLB and the original binding JSON
   in the SDK, then **Review selected files**. Inspect the exact source-axis changes,
   quantization error and shared ownership, and inspect the proposed animation.
5. Apply the matching reviewed proposal. Undo/Redo, Save/Open and normal Build
   use the existing `AnimationChannels` component. Build can reject a candidate
   that exceeds its original compressed bank capacity.

Blender drops the SDK's top-level GLB extras, which is why the binding travels
separately. The verified Blender 5.2.2 profile exports glTF Binary with custom
properties/extras enabled, Actions enabled, forced sampling disabled, animation
size optimization disabled, and the imported frame range retained. At 15 fps,
the verified 30-frame clip has keys at frames 0 through30; frame 30 holds the last
source pose. STEP channels retain the source's discrete samples. Optimized
static TR values and ordinary LINEAR tracks are also supported by the importer;
the SDK samples the existing source frames at the binding's explicit rate.

## Source and ownership rules

The scene source key includes individual animation contributions. Even adding
another owner with an equal value invalidates an old export. Import regenerates
the exact binding against fresh retail metadata before decoding changes. A
review also binds the uploaded GLB hash and quantized candidate hash; Apply
recomputes that review before issuing a command.

The candidate is compared with the effective exported clip. Unchanged axes keep
their existing ownership. Changed axes update the binding's clip-owner contribution; values
returned to retail remove that owner's entry. Other actors' entries remain
unchanged. Shared-bank composition must reproduce the candidate exactly, so a
conflicting edit or a requested clear masked by another contributor rejects.
A no-op GLB creates no history entry and cannot silently clear existing edits.

Translations use `[x,-y,z]` between retail and glTF and round to signed twelve-bit
source integers. Raw values outside -2048 through2047 reject. Source rotations
use rigid `Rz*Ry*Rx` and an eight-bit angle lattice, represented as PSX values 0
through 4080 in steps of 16. Equivalent normalized quaternions, including sign
flips and float32 round-trip noise, retain the exact effective Euler bytes.
Changed orientations choose a deterministic source-nearest equivalent branch;
singular orientations use the source to resolve their Euler ambiguity. Review
reports translation and angular error; unsupported or excessive error rejects.

## Qualified scope and limitations

This imports existing rigid-object translation/rotation channels. It does not
import mesh/material changes, anatomical skinning, arbitrary retargeting, new
object counts, record allocation or new frame counts. Qualified initial appearance
and animation assignments now use [v2 witness bindings](legaia-assigned-animation-glb.md),
with the shared clip owner explicit before Apply. Unassigned actors retain v1
bindings. The selected interchange rate is not verified retail cadence.

Input is bounded to a 32 MiB GLB, 128 KiB binding JSON, 4096 source channels,
64 rigid objects and one million decoded animation components.
The importer validates self-contained GLB 2 chunks, tightly packed FLOAT
animation accessors, explicit object mapping, finite TR values and strictly
increasing nonnegative timestamps. STEP and LINEAR channels and mapped static
node TR values are supported. Unsupported interpolation, transformed hierarchy,
scale/matrix animation, ambiguous objects, external/sparse data and unsupported
extensions reject. Mesh-only `KHR_materials_unlit` declarations are ignored.
These interoperability rules follow the primary
[glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).

The reusable independent proof helper is
`integrations/legaia/tools/blender_animation_roundtrip.py`. It uses the existing
Blender installation to import an SDK clip, save a baseline scene, edit
object 0/frame 0 translation X by 1 and rotation X by 16 source units, re-export,
and verify every other transform and selected-rate timestamp. Private evidence
stays under `local-output/sdk-20260909/animation-glb-20261002/`.
Offline editor/Build verification does not establish in-game clip selection,
animation timing, actor identity or gameplay acceptance. Those checks remain
deferred alongside the wider unfinished SDK.
