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
   in Blender or another GLB editor. Keep the exported `source_object.object_index`
   custom properties; display names may change. If those properties are omitted,
   preserve the `object-N` names. Keep unit scale, the existing timeline and
   rigid-object arrangement; parent TRS transforms are baked into native poses.
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
static TR values, LINEAR tracks and CUBICSPLINE tracks are supported by the importer;
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
increasing nonnegative timestamps. STEP, LINEAR and CUBICSPLINE channels and mapped static
node TR values are supported. Unsupported interpolation, non-rigid hierarchy,
nonunit scale/animated matrices, ambiguous objects, external/sparse data and unsupported
extensions reject. Mesh-only `KHR_materials_unlit` declarations are ignored.
These interoperability rules follow the primary
[glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).

CUBICSPLINE uses at least two timestamped keys and three output vectors per key:
in-tangent, value and out-tangent. Hermite derivatives scale by each segment's
duration in seconds, including nonuniform key spacing. Rotation derivatives keep
their authored magnitudes and signs; interpolated quaternions are normalized
after evaluating the curve, without LINEAR's shortest-arc sign adjustment.
Exact keys and values outside the key range retain their endpoint values.
Nonfinite data, nonunit rotation keys, a sampled zero quaternion and sampled
translation overflow reject before any project command. This samples into existing
frames at the binding's rate; it does not retain cubic tangents in the native bank.

The focused construction checks in `test_animation_glb_cubic.py` cover derivative
units, coordinate reflection, unequal segment durations, endpoint holds, long-path
rotation, complete quaternion sign reversal, source Euler/opaque-byte preservation
and malformed input. The private-disc workflow check
`test_cubic_http_review_pose_history_reopen_and_exact_build_bank` qualifies actual
Town01 HTTP Review/Pose, stale-file rejection, one-command Apply, Undo/Redo,
Save/Open and exact decompressed bank output from normal Build. These passed on
2026-10-04; gameplay cadence and clip selection remain deferred.

The reusable independent proof helper is
`integrations/legaia/tools/blender_animation_roundtrip.py`. It uses the existing
Blender installation to import an SDK clip, save a baseline scene, edit
object 0/frame 0 translation X by 1 and rotation X by 16 source units, re-export,
and verify every other transform and selected-rate timestamp. Private evidence
stays under `local-output/sdk-20260909/animation-glb-20261002/`.
Offline editor/Build verification does not establish in-game clip selection,
animation timing, actor identity or gameplay acceptance. Those checks remain
deferred alongside the wider unfinished SDK.

## Constant unit-scale tracks - 2026-10-06

Files exported by external editors may include neutral scale channels alongside
translation/rotation. Both imported-channel and retained UUID GLB workflows now
accept STEP, LINEAR and CUBICSPLINE scale tracks that stay exactly `[1,1,1]`.
Review identifies this support. Native records store no scale channels, so
accepted neutral tracks leave the rigid animation content unchanged.

For cubic curves, every key value must be unit scale and participating outgoing
and incoming tangents must be zero. The first incoming and last outgoing tangents
are unused and may contain finite values. The importer checks every segment,
not only native sample times. Scale changes, nonfinite/malformed keys, duplicate
targets and animated matrices reject. Identity ancestors may have neutral scale
tracks; ancestor translation/rotation is now sampled and baked. Static
node scales must also remain unit. These rules follow the primary
[Khronos glTF 2.0 TRS and animation specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html),
including the Hermite interpolation formula in Appendix C.5.

The importer allows at most 256 samplers/channels, covering 64 object TRS triplets
and neutral ancestors. Existing 32 MiB GLB, 65536 keys/accessor, one million
components and 4096 native object-frame budgets remain enforced. No binding or
report schema changed. Ordinary files without scale tracks retain their behavior.

Private evidence in `local-output/sdk-20260909/animation-glb-identity-scale-20261006/`
covers imported and retained no-op/Review/pose/Apply, actual editor preview/Return,
Undo/Redo, Save/Open and exact relocated native ANM readback from normal Build
`3174f674d5c90450`. Gameplay playback/timing and general retargeting remain deferred.

## Numeric rejection stability - 2026-10-06

Oversized JSON integers in node vectors/quaternions and FPS now reject through
normal import/SDK errors. FPS range checks precede float conversion; vector
conversion overflow is rejected; quaternion magnitude is bounded before norm
arithmetic. Existing valid tolerance and native output behavior are preserved.
Both imported and retained HTTP workflows return 400 for these malformed values
without changing project/history or preventing a subsequent valid review.

25 focused checks and a private retail retained upload verified this behavior.
The pinned previous importer reproduced three uncontrolled overflow paths;
`local-output/sdk-20260909/animation-glb-numeric-bounds-20261006/` contains the
comparison and live HTTP evidence. A new native Build was not needed for this
validation-only fix. Gameplay timing/retargeting acceptance remains open.

## Selecting a clip in a multi-animation GLB

Both the imported actor and retained UUID GLB editors list the uploaded file's
animation indices and names. Files with two or more clips require an explicit
selection before Review; the SDK samples only that clip, never a merged set of
channels. Up to 64 clips are accepted within the existing 32 MiB file budget.
Single-clip and static-transform files retain their previous behavior.

The optional HTTP `animation_index` must be an integer in the uploaded file's
range. Review includes `file_animation_index` (inside `analysis` for retained
clips), binding that selection into the review key. Pose and Apply use the same
selection. Changing the dropdown clears Review, even when switching back.
Native records and saved contribution/retained-recipe schemas are unchanged.
This extends existing rigid-object authoring; it does not introduce general
skinned retargeting or establish retail playback acceptance.

## Preserving identity while renaming external objects

Nodes retaining `extras.source_object.object_index` map directly to that native
object. Readable names and absent names are supported, and node order may change
when the GLB scene/channel references change with it. A canonical `object-N`
name still rejects if it contradicts the preserved index. Every native object
must appear exactly once, within the selected scene; malformed, duplicate or
out-of-range source indices reject. Renaming does not authorize a different
object count, skinning or unqualified skeleton retargeting.

The original binding remains qualified against the current source clip and
project. Whole-file hashing and native candidate Review bind the edited file;
Apply never trusts a display name as runtime identity. In external exporters,
enable custom properties/extras or preserve the original `object-N` names.

## Equivalent clips still require their own Review

The imported-actor Review digest includes any explicit selected animation
index, in addition to the binding, whole-file hash, native candidate and authored
contribution. Two clips can quantize to identical native poses; their reviewed
keys still differ. A key reviewed for one index cannot authorize Apply for the
other. Implicit single-clip requests retain the prior digest format. Retained
UUID Review already binds the index through its full analysis report.

## Baking rigid parent transforms

The selected animation is sampled through each source object's ancestor chain.
Static and animated ancestor translation/rotation, including mapped-object
parents, are composed in glTF parent-times-local order. The resulting scene-
space pose is reflected to the native coordinates and quantized once per object.
This follows the [glTF node transformation rules](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).
Parent translations rotate child translations; parent and child rotations are
composed in order. Earlier restrictions on transformed/mapped parents are
superseded by this workflow. Source identity properties or canonical names must
still identify every native object exactly once.

Only the source objects and their ancestors are sampled. A parent-first iterative
traversal avoids recursive depth failures and reuses shared ancestor poses.
Total sampled nodes times native frames may not exceed 65536. Existing file,
node, channel, accessor and native-coordinate bounds still apply. Unrelated
translation/rotation targets, non-unit scale, skinning, non-rigid matrices,
cycles and multiple parents reject. Native output retains independent rigid
channels and its original opaque data; no native skeleton is invented.

## Static rigid matrices

Mapped source nodes and their ancestors may use a static column-major glTF
`matrix` instead of TRS. The importer requires final row `[0,0,0,1]`, an
orthonormal 3x3 basis and determinant +1 within a 1e-5 tolerance for float32
export noise. It extracts translation and a normalized quaternion, then uses
the same scene-space hierarchy baking and native quantization path as TRS.
Shear, scale, reflection, perspective and nonfinite components reject. Matrix
plus any TRS property rejects, and every animated matrix node rejects as
required by glTF. Matrices do not allocate native channels or infer skinning.

## Retained animation import inputs

A changed GLB Apply now retains its immutable uploaded GLB under
`Authored/Animations/Sources/<sha256>.glb`. Optional project `animation_sources`
receipts retain the parsed binding, selected clip index, retained donor-frame
mapping when applicable, reviewed native candidate hash and Review key. The
GLB bytes are exact; binding JSON formatting is regenerated from parsed values.
The native change and receipt are one Undo/Redo step. Save/Open validates receipt
metadata and source hashes, and project copies/export snapshots carry referenced
source files. Missing or modified referenced sources reject recovery and input
snapshotting. Native serializers still consume the existing authored channels
and retained recipes; receipts never authorize replay.

Use **Recover animation sources** or **Recover retained animation sources**
in the corresponding GLB editor. Download the original GLB, parsed binding or
receipt. The dialog identifies historical inputs: later changes can make the
old binding stale, so export a fresh binding and Review before applying again.
Each downloaded GLB is checked against its receipt hash in the browser.

The project allows at most 32 receipts and 64 MiB of distinct source GLBs, within
the existing 32 MiB per-file limit. Identical blobs are shared across receipts;
file verification also deduplicates shared blobs. Old projects with no sources
retain their previous metadata and Build-key shape.

In Edit mode, choose **Review source removal** for a receipt. Review shows the
Current receipt count and registered bytes freed; shared files free no bytes
until their last receipt is removed. **Remove reviewed source receipt** changes
only the source library metadata, closes the stale parent GLB editor and refreshes
the project. Undo restores the receipt; Redo removes it again. A changed target,
source context, collection or native authored state rejects the reviewed action.
Native animation content stays intact. Local GLB files are preserved for Undo,
so removal frees the registered input budget rather than physical disk space.
Save/Open and project copies retain only Current references. Physical cleanup
and project-wide source-library browsing remain follow-up work.
