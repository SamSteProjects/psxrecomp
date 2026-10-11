# World Placed-Object Animation Preview

The SDK resolves nonzero placed-object MAN header
selectors to kingdom type-5 ANM record `selector-1`, decodes a bounded frame,
and poses the corresponding Current model's vertices. This is a retail source
animation association, not an observed runtime clip. A Current placed-object bind with a nonzero selector exposes frame controls in the Inspector. The browser independently verifies bank/record bytes, channels, posed geometry and normals before the selected instance changes in the viewport. Return to Current, selection changes and dialog closure restore the source scene; export is blocked during the temporary preview.

`POST /api/worldmap-object-animation` requires exactly `scene`, `source_key`,
`entity_id` and integer `frame_index`. Current native placement and model
provenance, retail object bind, same kingdom carrier, slot type, clip bounds
and exact object/channel count are checked. Zero selectors, absent binds,
unsupported records, stale sources and out-of-range frames refuse. Complete
bank and record byte witnesses support the upcoming browser qualification.
The endpoint has a 40 MiB private response limit and changes no project state.

The preview preserves model topology and materials. Vertex poses use the
existing analytic rigid transform decoder, without claiming bit-exact GTE
rounding. Source triangle normals receive rotation only, independently qualified with the shared rigid-normal viewer contract and reported as `normal_pose=rigid_rotation_only`. This is a source-vector diagnostic; retail GTE lighting is not simulated. Playback timing, looping and runtime activation are unresolved.
No registered animation asset identity or authored World ANM edit is invented.

## Evidence — 2026-10-10

Pinned `d6e64c68ede25813d35db20980da82a1a025549b`
`crates/engine-core/src/field_env.rs` documents the nonzero source selector's
scene ANM `selector-1` association and per-object rigid posing. Existing
`scene_animation.py` supplies the type-5 bank contract; `animation.py` owns the
bounded record and channel decoder.

Retail source inspection finds five supported nonzero bindings: one Map01
20-frame/two-channel clip, three Map02 users of a 30-frame/two-channel clip,
and one Map03 15-frame/one-channel clip. Every channel count exactly matches
the Current model object count. First and last vertex poses differ for every
binding; model topology remains unchanged. All five API frame-zero requests
pass, with four malformed/stale HTTP refusals and unchanged project/history.
Four focused Python tests cover two distinct frame poses, immutable models,
zero/absent/out-of-bank selectors, incompatible object counts and frame bounds.
The existing source-bind and schema regression checks also pass (27 Python tests total). Four Python AST, two JS syntax and whitespace checks pass. Ten first/last poses agree with independent browser decoding, with 45 altered source/channel/geometry/scope refusals. The shared source-normal Node suite passes. The initial independent check caught a normal-loop variable overwriting the reported record offset; that is corrected and covered by the normal-rotation/record-span regression. Evidence remains private in
`local-output/sdk-20260909/worldmap-object-animation-20261010/`.

No game launch, native build, runtime attachment, install or disc export was
performed. Gameplay remains deferred; the full SDK goal remains active.

Three final actual kingdom editor workflows pass bind selection, frame controls, independently qualified first/last posed geometry, unchanged placement matrices, export refusal during preview, Return to Current and selection clearing. A separate Map01 run confirms automatic Current restoration when selection changes during a preview. Wide/400-pixel Inspector layouts and first/last viewport captures were visually inspected: the gate panel changes pose while the surrounding scene stays in place. Browser runs report no authoring commands or page errors; private document/history and Save/Open baselines remain unchanged. Source animation identities remain structural record references; this does not register an animation asset or prove live script behavior.
