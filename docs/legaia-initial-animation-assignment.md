# Initial animation assignment — 2026-10-02

The actor Inspector now separates the appearance's default model/clip pair,
an authored initial clip, and channel edits on the imported shared clip.
This edits an existing actor's initial MAN header. Scripts can replace it later;
timing, looping and gameplay suitability remain unknown.

## Editor workflow

1. In Edit mode, select an imported actor and choose **Initial animation
   assignment → Choose initial animation…**.
2. Choose an observed clip for its inherited model, then **Review selected
   animation**. Review shows imported, appearance default, current and proposed
   bindings, counts, witness actor and the record digest.
3. **Preview verified witness clip** inspects the imported source witness and is
   labelled with the proposed target and “not applied.” It cannot redirect the
   scene pose to that witness. **Apply reviewed animation** authors one change.
4. The Inspector and authored scene display the assigned clip at the target's
   existing position. **Preview assigned initial animation** and GLB export use
   the target identity and the verified witness. Channel edits affecting that
   chosen shared record are included in this applied preview.
5. Undo/Redo and Save/Open preserve the assignment. Review **Inherit appearance
   default** to clear it. Build emits the final model/animation pair once.

Compatible appearance changes retain a qualified animation witness. Appearance,
group/preset or component-revert changes that invalidate it reject atomically.
Existing position/appearance templates do not capture this separate component.

## Supported evidence and limits

Choices require a freshly verified imported scene, the exact local TMD model
source, an observed scene ANM binding, identical active/excluded object mapping,
and the existing MAN writer's non-aliased equal-count compatibility checks.
Global-bank actors, zero-animation sources, unknown pairings, partial mappings
and newly created clips are not enabled by this workflow. The reference remains
Andrew's existing pinned commit; no reference code or retail payload is added
to the repository.

`ActorAnimation` stores only `donor_entity_id`, `animation_asset_id` and
`source_record_sha256`. Apply re-verifies the requested source and review key.
The assignment never retargets `AnimationChannels`: those keep their imported
clip identity and shared-user semantics. Normal, descriptor draft and raw
streaming builders compose one final header patch; appended NPC drafts keep
their retail donor's header. Effective asset-reference edges use the selected
clip witness separately from the appearance donor. Live candidate correlation
does likewise, invalidates old observations when assignments change, and still
does not confirm runtime actor identity.

The HTTP entry points are `/api/actor-animation-options`,
`/api/actor-animation-review`, `/api/actor-initial-animation-preview` and
`/api/export/actor-initial-animation`. Apply uses the existing `/api/command`
with `set_actor_animation`, actor/clip identities, source key and review key.
Invalid request shapes and stale proofs fail without changing history.

## Verified retail fixture

Town0b actor `scene://town0b/actors/man-p1/0019` and witness
`scene://town0b/actors/man-p1/0049` share model
`asset://town0b/models/scene-tmd/0102` with six rigid objects. The target's
imported MAN animation byte14 references record13/15frames; the chosen byte13
references record12/30frames. Record12 SHA256 is
`73928a7ee13e997b6b53a06919419c0efa985a9f6bbc9d5a61e8a27f506da654`.
Independent normal-package decoding changes only MAN offset9471,14→13.
Model, position, source imports and saved project bytes stay unchanged by Build.

The saved private fixture is
`local-output/sdk-20260909/actor-animation-assignment-20261002/project/`.
Package:
`Builds/initial-animation-verification/legaia.sdk.0f096fa3c17d-0.1.0-1ee1fc4c87dcc868.psxmod`.
SHA256: `8352ed3e3d0cb287091e657b344d0ebfa036ec85f266c2f83649ca78bb52e9cc`.
Private evidence includes `retail-check.json`, `browser-check.json`,
`http-guards.json`, `dialog-layout-check.json`, screenshots and check receipts.

39 focused retail-enabled Python checks passed in55.598s; a separate22-check
appearance/Build/preview compatibility pass took21.572s. All34 Node test files
and35 editor syntax checks passed. Seven raw MAN/appearance compatibility checks
also passed in47.334s without skips. Actual browser Review/Preview/Apply/Clear,
assigned frame GLB export, scene position preservation, Undo/Redo/Save and
initial/effective reference navigation passed without page errors. Final dialog
controls fit within their bounds and the screenshot was inspected. Draft
preparation independently verifies the assigned existing actor and the appended
retail clone, with the header offset correctly rebased9471→9474.

No game was launched or package installed. Later manual acceptance must establish
the actual Town0b scene and actor/script branch, check whether scripts replace
the initial clip, inspect visual suitability and interaction/progression, and
check scene entry/exit. The historical565-test checkpoint predates this feature;
the full modern SDK and runtime parity objective remains incomplete.
