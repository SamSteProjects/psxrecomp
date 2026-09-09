# Field-party animation preview evidence

The independent Python decoder is based on reference commit
`d6e64c68ede25813d35db20980da82a1a025549b` of
`AndrewAltimit/legend-of-legaia-re`. No reference implementation or retail payload
is included in the importer or its tracked fixtures.

Relevant reference sources:

- `crates/asset/src/player_anm.rs`: frame-major records, eight-byte rigid
  channels, signed twelve-bit translations and byte angles shifted by four;
  runtime consumer `FUN_8001BE80`.
- `crates/asset/src/character_pack.rs`: PROT extraction entry 874, section 1,
  three seven-record party banks, idle slot 1 and walk slot 0. Ten channels map
  to TMD objects 0–9; objects 10–11 are equipment descriptor templates.
- `crates/engine-core/src/field_anim.rs`: reference playback advances one clip
  frame per 30 Hz field tick. The wire has no rate byte. This is a cited runtime
  interpretation, not a new live trace performed by this importer.
- `crates/tmd/src/mesh/{mod,vram_posed}.rs`: actor-local rigid assembly applies
  `Rz * Ry * Rx`, then translation. The importer uses double-precision analytic
  trigonometry; it does not claim bit-exact GTE rounding.

Supported imported models are global assets F0/F1/F2. Their idle records are
1/8/15 and walk records 0/7/14. Idle clips each have 15 frames; walk clips have
15/10/15 frames. Vahn/Noa/Gala previews contain respectively 270/271/199 vertices
and 496/488/358 triangles after excluding the equipment templates. Channels have
stable skeleton IDs across clips and no invented anatomical parent hierarchy.

Validation on the user's read-only SCUS-94254 disc:

- Nine focused tests cover record bounds, unsupported modes, signed decoding,
  frame order, matrix composition, model provenance and all six retail clips.
- A private Rust control compiled the unchanged pinned `BoneTransform::decode`
  and `rot_zyx` functions. All 20,845 posed-vertex cases from the six clips
  matched translation and rotation integers exactly. Maximum positional
  difference was `0.000015829874723038984` between Python double and reference
  single precision, below the `0.0001` comparison tolerance.
- Private control source, inputs, full previews and `reference-validation.json`
  are ignored under `local-output/sdk-20260909/animation/`.

Run the tracked tests with `LEGAIA_DISC_BIN` set to the user's disc path:
`python -m unittest discover -s integrations/legaia/tests -p test_importer_animation.py`.

Unsupported: live equipment descriptor swaps, scene NPC/scripted and battle
animation associations, and exact GTE arithmetic. Shared party texture uploads
are now supported separately; see `field-party-textures-20260909.md` for their
model-scoped source validation and independent VRAM control. Remaining limits
are reported explicitly in preview metadata. The source disc is never modified.
