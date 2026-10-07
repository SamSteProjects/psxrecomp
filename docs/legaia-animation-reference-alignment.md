# Native Reference Pose Alignment

The imported-actor and retained-clip GLB editors can anchor explicitly mapped external rigid motion to a native reference pose. This is opt-in; existing bindings and direct-pose imports keep their behavior.

1. Load a current exported binding and the edited GLB. Enter **External rigid object mapping** in native object order. Select a joint skin only when importing joint tracks.
2. Enable **Align external motion to a native reference pose**. Choose the zero-based **Native reference frame** and **External reference pose seconds** in the selected GLB clip.
3. Select the clip and existing sampling controls, then Review. The report names the reference values. Preview the proposed native poses, Return, and Apply the current Review.

The reference frame belongs to the proposed native output. For imported actors that is the existing effective clip. For retained clips it is the reconstructed output captured-frame mapping, with current edits retained when that mapping is unchanged. Changing the output mapping can therefore change the native reference pose. Reference time is sampled directly as float32 seconds with endpoint hold; repeat/ping-pong settings affect output sampling, not the reference-time lookup.

For each explicitly mapped rigid object, the importer samples its external reference pose in scene space and obtains the selected native reference pose. It computes:

```text
aligned_pose = native_reference * inverse(external_reference) * sampled_external
```

For example, external X positions 500→503 with an identity reference orientation can become native X positions 10→13. Reference orientations also rotate the motion into the native reference axes. This replaces sampled motion rather than adding the existing per-frame native motion. It does not infer anatomical correspondence, bone rest poses, scale ratios, mesh deformation, or gameplay timing. Inverse-bind matrices remain validated but are not used as alignment references.

References use the same Y-reflected interchange basis as the existing rigid importer. Native signed12 translations, source-biased byte-angle quantization, finite rigid transforms, explicit mapping ownership, unchanged object counts/geometry, opaque source bytes, shared-axis composition, and native Build capacity checks remain. The extra reference sample participates in the existing hierarchy-sample budget.

Both references and the `native_reference_local` mode are retained in `binding.external_pose_alignment`. They participate in Review identity and source-receipt validation. Changing any reference or toggling alignment withdraws Preview/Apply until a fresh Review. Original GLB/binding recovery preserves this recipe; imported/retained Undo/Redo and Save/Open continue through normal commands. Native project and Build formats are unchanged.

## Offline Verification

Eight focused synthetic cases cover exact unchanged native bytes despite a displaced external pose, native-axis translation, relative rotation, selected frame/time, reverse sampling, separate object references, malformed configuration, missing explicit mapping, signed12 overflow, independent noncommuting matrix composition, and hierarchy budgeting. Existing sparse, rig, hierarchy, matrix, sampling, and numerical cases exercise compatibility. Strict Node alignment and existing GLB validators cover mismatched report/reference refusal.

All 50 focused Python checks passed with no skips; five Node suites, JS syntax and Python AST checks passed. Actual private imported and retained editor workflows at 1400/400 px used a translated/rotated rig and sparse tracks. Direct imports exposed the external offset, while aligned unchanged clips reproduced native bytes exactly. The edited clip passed Review/Preview/Return/Apply, alignment/clip changes withdrew Apply, stale-reference Apply refused, and original GLB/binding recipes recovered exactly. Each Apply used one history step; Undo/Redo, Save/Open, and a reopened project copy passed. Normal Build `f1878ecf240eadbb` delivered exact composed native animation-bank readback, SHA-256 `b478a4e572459b837ae2be01b1eb94c160cec9aad4b1952c602e1123a356009d`. No page errors or Run requests occurred; the reference project stayed unchanged and owned helpers terminated. No game, install, or disc export occurred. Evidence is retained under `local-output/sdk-20260909/animation-glb-alignment-20261007/final/`. Gameplay verification and general native skinning/retargeting remain outstanding.
