# Scene actor animation associations and poses

The independent `importer/scene_animation.py` reuses the already tested packed
channel decoder and rigid transform composition from `importer/animation.py`.
It adds scene/MAN association and bounded, request-scoped source/model caches.
The unchanged Andrew reference pin is
`d6e64c68ede25813d35db20980da82a1a025549b`.

Exact reference evidence:

- `crates/asset/src/man_section.rs`, `ActorPlacement::anim_id`: the placement
  header seeds the actor animation record ID plus one. Zero means no animation;
  special/global models use a separate bank. Later scripts can change the clip.
- `crates/asset/src/player_anm.rs`: the scene bank is descriptor type `0x05`,
  despite the dispatcher's misleading type/case labels. It has absolute record
  byte offsets and the same frame-major packed rigid transforms already used by
  the party decoder. The renderer requires bone count to equal model object
  count. Town01's bank has 69 records in 96,448 decoded bytes.
- `crates/web-viewer/src/field_npc.rs`: the placement's selected ANM frame
  assembles object-local vertices as `R_bone * vertex + T_bone`. Multi-object
  models with no evidenced clip must not be presented as an assembled actor.
- `crates/tmd/src/mesh/{mod,vram_posed}.rs`: independent object transforms use
  `Rz * Ry * Rx` followed by translation. No skeletal parent hierarchy is needed
  or invented.

The scene factory verifies one fresh import and locates exactly one nonempty
type-5 descriptor in its MAN-bearing scene bundle. It records and bounds the
compressed span before the next descriptor. Actor source locator, model
reference, placement fields and model source locator must equal the verified
import; changing only a plausible ID is not accepted. Each selected record
must satisfy the existing wire decoder and match the actual TMD object count.

Town01's existing importer expresses the ANM carrier as PROT entry 2, table
offset 8192, descriptor 2. Its compressed offset is 187689 relative to entry 2.
The pinned reference calls this logical PROT entry 4. A private read verified
that entry 2 starts at LBA 239, entry 4 at LBA 243, and the table at entry 2+8192
equals entry 4's table byte-for-byte. The new source locator preserves the
importer's existing container coordinate system instead of renumbering it.

APIs:

- `actor_animation_capabilities(actor, asset)` advertises an eligible imported
  header binding. It is a routing hint, not source verification.
- `load_scene_actor_animation_catalog(disc, scene)` creates a private source
  snapshot for one request. Its `capabilities(actor, asset)` verifies the binding
  and wire record without decoding model triangles.
- `catalog.pose_preview(actor, asset, frame_index=0)` returns a model preview
  with one frame baked into its vertex stream, `posed: true`, and provenance in
  `pose`. It does not materialize every posed frame.
- `catalog.animation_preview(actor, asset)` returns the existing animation
  wrapper contract with `geometry`, all `frames`, structural animation/skeleton
  IDs and source evidence. Single-actor convenience wrappers are also provided.

The factory and wrappers compose with the pipeline's request-scoped verified
disc context. One catalog can serve a scene request without repeated scene
imports. Model/record caches are private; callers receive copies. Counts and
payloads use existing bounded decoders, with additional cached geometry and
full-clip posed-vertex budgets of one million each.

Retail proof used the read-only SCUS-94254 disc with SHA-256
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`:

- All 39 nonzero-ID scene actors have matching model/animation channel counts
  and successfully decode first poses. Ten zero-ID actors remain unresolved;
  three global-bank actors remain outside this scene-bank path.
- Independent numerical comparison of all 5,028 first-pose vertices against
  the unchanged pinned Rust transform functions produced exact integer channel
  decoding and maximum position error `3.88902932968449e-05` (tolerance 0.0001).
- Actor 0049 selects scene model 0103 and animation record 14 (header ID 15),
  with ten objects and fifteen frames. An exported first pose was imported and
  rendered in Blender 5.2.1 and visually inspected: coherent upright textured
  girl with brown pigtails and pink dress. This validates assembly, not live
  story state, spawn coordinates or gameplay animation selection.
- Five focused tests cover source/association rejection, zero/global IDs,
  channel mismatch, frame bounds, stable IDs, copy isolation, full-frame/single
  pose agreement and the complete 39-actor retail association set.

Results stay in actor-local PSX Y-down coordinates. World height and facing
remain unknown; the viewport must not apply the object transforms twice or
silently treat this imported pose as runtime state. Scene clip rate and looping
are left unknown: the separately pinned party locomotion cadence is not evidence
for every NPC record. Private proof data and rendered previews remain ignored in
`local-output/sdk-20260909/scene-animation`; no retail bytes are tracked.

## Reusable initial-animation presets — 2026-10-02

No new retail decode rule or reference pin was added. Versioned v2 presets
capture the existing exact ActorAnimation witness/hash, with optional authored
position/appearance. Frozen source proof validates the captured composition or
an imported witness independently of the originating actor's current overrides.
Target review proves the complete proposed model/clip against the existing
fresh MAN assignment options before atomic single/group mutation. An inherited
captured clip normalizes to absence; omitted assignments stay unchanged.

47 focused retail-enabled tests plus8 compatibility checks and37 Node files
pass. Real browser capture/transfer/scene/group/history/Save passes with no
page/unexpected HTTP errors. Independent pure-clip MAN readback changes only9471
14→13, preserving channel ownership; combined actor0049 readback changes only
19122 13→14 and19123 119→150. Record13 SHA-256 is
5f8e8175544512db45f3ec37a9be33ddf414ee0b5a2ddf079ac195b6d5bdd09e.
Reopened combined package SHA-256 is
2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389.
Evidence: local-output/sdk-20260909/animated-presets-20261002/.
No runtime binding, playback timing or gameplay acceptance is asserted.
