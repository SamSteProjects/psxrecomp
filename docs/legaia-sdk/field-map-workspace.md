# Field map resources and base collision preview

Source trigger/region cells now connect the hierarchy, shared Inspector and
viewport. See [field source workspace](../legaia-field-source-workspace.md)
for the separate trigger/region quantizers, guarded source picking and P2 links.
These outlines preserve unknown height and do not simulate activation.

Field map discovery follows pinned Andrew reference revision
`d6e64c68ede25813d35db20980da82a1a025549b`. The scene-window entry and its
extended footprint come from `scene/scene_ty.rs` (blob
`073f3c19dca35c4fe1985049084d20a50af7c8ae`). Wall subcell interpretation
comes from `world/field_movement.rs` (blob
`12ce75c6990cfd5df489a28cb17c6fb33a719f26`). Trigger and region semantics
come from `field_regions.rs` (blob
`8f54e88895ecdf0ca3fe1fc5602ce583911c5feb`). All three paths are beneath
`crates/engine-core/src/` in the reference repository.

The derived catalog contains structural collision, trigger and region IDs.
It stores source locations, counts and encoded record fields. Grid payloads
and viewport geometry are private on-demand responses, never project metadata.
Source identity is verified before decoding and again before response delivery.
No raw address, client coordinate array or source path is accepted by preview.

The base wall grid occupies the field MAP carrier's `+0x4000..+0x8000`
region. Its high nibble describes four subcells. The low nibble is not used
to invent world heights. Viewport rectangles follow the pinned biased wall
lookup over its explicitly bounded canonical domain. They are shown at display
Y=0. Actor collision, runtime script paints, wrapping and unresolved boundary
aliases are outside the preview. This is not a playable navigation mesh.

Primary and fallback trigger tables retain distinct source identities and
ordering. Kind 0 is a local coordinate teleport, not a named scene transition.
Kind 1 gate 0 binds an object record; gate 1 references a P2 script. A record
reference does not establish that its script is reachable or resolves to a
particular destination scene. Region rectangles retain immutable encoded source fields. Their four primary
corner bytes have a separate [reviewed authored workflow](../legaia-region-bounds.md);
region type and opaque padding remain read-only. The current P1 actor inspector is not evidence for P2 routes.

The editor consumes SDK metadata and precomputed world rectangles. Collision
and trigger inspection never alters imported or authored state. Source/project
changes or preview failures clear the previous overlay.

The pinned `docs/subsystems/field-locomotion.md` (blob
`220746dd6a415bfd61cc8982f18c9aae691279d4`) establishes table strides
4/4/4/8. All four spans are validated for bounds and overlap, including
unexposed kind 2. Its semantics remain outside this decoder. The later
reference checkout contains an additional MAP detector that is not part of
this pin; it was not imported or used to silently change reference revisions.
