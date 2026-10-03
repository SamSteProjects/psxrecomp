# Source-qualified model materials

Model material authoring changes existing CLUT/texture-page fields and a primitive group's GPU semi-transparency-enable bit. It keeps the model's packet layout, vertex/normal tables, face references, UV/RGB bytes, row commands, group flags, footers and source allocation. Texture images and palettes are edited through the separate texture workflow.

## Workflow

The [source-binding picker](legaia-material-binding-picker.md) can fill a draft from another active-scene imported model. Loading is read-only; explicit Copy transfers page/depth/indexed CLUT values to one primitive or all textured primitives in a target group and retains target UVs and blend flags. Group scope/count and whole-batch budget validation are explicit. Review and Apply below remain required.

Open a verified imported model in Edit mode and open its material editor. Select an object, group and primitive. The inspector keeps Retail and Current values separate and identifies the source words behind the decoded controls.

For a textured primitive, edit the page column/row and texture bit depth. CLUT column/row are editable for indexed depth. The source-encoded blend mode is read-only. A group's semi-transparency control applies to **every primitive listed in that group**, rather than only the selected row. Untextured rows have no CLUT or texture-page fields; the group control remains the shared source command property.

Collect drafts, then Review. Review shows retail-to-proposed and current-to-proposed audits, shared group membership, source/current/proposed hashes and limitations. Inspect the Current/Proposed model or scene preview and return to the editor before explicitly applying the reviewed proposal. A change in draft, identity, project, scene, mode or source invalidates that review. A no-op cannot be applied.

Apply uses ordinary model replacement authoring. Undo/Redo, Save/Open and clearing the model replacement retain their existing behavior. Resetting or discarding an editor draft does not commit a project edit. The editor accepts at most 256 batched source identities; it does not allocate new primitive groups or change topology.

Changing a source model affects all of its instances. Changing group ABE affects all source rows in the group, including rows that use different CLUTs. A model or VRAM texture address may have several consumers; a static address match does not establish exclusive ownership or current residency.

## Writable wire fields

| Field | Existing source location | Authored domain | Writable mask |
| --- | --- | --- | --- |
| CLUT column | Texture block +2, low six bits | 0–63, in steps of 16 VRAM words | Combined CLUT mask `0x7FFF` |
| CLUT row | Texture block +2, bits 6–14 | 0–511 VRAM rows | Combined CLUT mask `0x7FFF` |
| Page column | Texture block +6, bits 0–3 | 0–15, in steps of 64 VRAM words | Combined TPage mask `0x019F` |
| Page row | Texture block +6, bit 4 | 0–1, in steps of 256 VRAM rows | Combined TPage mask `0x019F` |
| Texture depth | Texture block +6, bits 7–8 | 4, 8 or 16 bpp; encoded mode 3 unsupported | Combined TPage mask `0x019F` |
| Group ABE | Eight-byte group header +7, bit 1 | Boolean, all qualified group rows | `0x02` |

CLUT bit 15 remains unchanged. TPage bits 5–6 (source-encoded ABR) and bits 9–15 remain unchanged. All other header bits are retained. Direct 16-bpp retains the existing CLUT word; it does not expose an unused CLUT edit. Source-reserved depth remains inspectable without inventing a decoded format.

The texture block begins at packet offset zero for lit textured rows (`flags 0x10–0x17`), at offset four for baked flat textured rows (`0x20–0x23`), and at offset 12/16 for baked gouraud triangles/quads (`0x24–0x27`). Untextured rows carry no texture block. CLUT and TPage are little-endian 16-bit words at block offsets +2 and +6. Group flags determine these layouts; the low flag bit does not change the renderer's row/quad selection and remains source-owned.

The writer rereads and qualifies source packet identities and spans, preserves omitted/reserved bits, reconstructs a complete per-byte audit and requalifies the candidate. Duplicate or foreign identities, stale hashes, unsupported fields and malformed/aliased layouts are rejected. The client supplies object/group/primitive identities and semantic values, not trusted byte offsets.

## ABE ownership and ABR limitation

The retail SCUS renderer at `0x80027480` reads group header byte +7. It masks the mode with `0xF6`, stores the resulting command in its temporary descriptor and can force ABE through a caller condition. The emitter at `0x80027E60–0x80027E68` loads that descriptor's command and overwrites byte +7 of the emitted GPU packet. The sibling renderer follows the same source-command path at `0x80029A84–0x80029A98` and `0x8002A4EC–0x8002A4FC`.

Consequently, a source ABE edit belongs to the group header. Each packet's color-word fourth bytes remain exact; there is no need to rewrite them to match the header. The extra group-footer slot is opaque and remains unchanged. Other caller conditions can force the emitted command, so the source ABE value does not prove a particular live blend result.

**Source ABR is read-only.** The traced retail paths mask the copied TPage with `0x019F` and OR a descriptor/caller value at `0x8002810C–0x80028124`, `0x8002A3EC–0x8002A3FC` and `0x8002A4B8–0x8002A4CC`. This removes source bits 5–6 before emission. The original encoded value is useful provenance but is not evidence that editing it would select a different runtime blend mode. This workflow preserves those bits and does not invent an authoring location for the caller override.

The source texture's STP bit is separate from ABE. The browser's RGBA/static-texture view does not reconstruct PSX semi-transparent blending, texture windows, live upload order or palette animation.

## Derived previews, composition and Build

Preview material indices are derived from `(textured, CLUT, TPage, source ABE)`. A source edit can split, merge or reorder this material table while leaving every triangle and vertex intact. Candidate previews rebuild the table and triangle-to-material mapping coherently and resolve texture crops again. An old material index cannot safely reuse an old texture association after a source-key change. Missing, ambiguous or unsupported static associations remain explicit.

Material changes use the versioned `tmd-content-v2` binding. Legacy `tmd-content-v1` and shape-only bindings continue to reject material/header edits. Content composition retains existing authored XYZ, face, UV and RGB changes and audits the newly allowed masked fields. Proven object ranges and rigid poses remain unchanged when previewing a material proposal.

Normal Build uses the existing source model carrier, exact preimage guards, member readback and allocation/compressed-span fit checks. It emits source-linked CLUT/TPage/group-command audit rows. Other pack members and opaque neighboring bytes remain unchanged; an edit that cannot fit is rejected. Building a package does not launch the game or verify appearance.

The face editor and source-bound GLB mesh workflow can continue from the effective material state. Export a fresh GLB/binding after a material edit. Fresh GLB profile v6 can edit these same qualified material fields through explicit source attributes while retaining reserved bits, source ABR and opaque bytes. Shader/material assignments and image pixels remain separate. See [material GLB editing](legaia-model-glb-materials.md). See [model GLB workflow](legaia-model-glb.md) and [texture authoring](legaia-sdk/texture-authoring.md).

## Private independent evidence

Retail metadata, source payloads, bounded instruction dumps and proof scripts stay under `local-output/sdk-20260909/model-material-20261002/research/`. The disc SHA-256 is `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`; the unchanged SCUS executable SHA-256 is `292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482`. Instruction windows and exact words are independently checked against that executable in `qualification.py` and recorded in `qualification.json`.

The pinned reference remains `d6e64c68ede25813d35db20980da82a1a025549b`:

| Reference | Pinned blob |
| --- | --- |
| `crates/tmd/src/descriptor.rs` | `7e6afe79b675aaf2c30bf194874686b49f22b4be` |
| `crates/tmd/src/legaia_prims.rs` | `75a3b860484e5142bae6457369b593d0d930898c` |
| `docs/formats/tmd.md` | `ed67864c57ab4653a326ed277303c34b8fbbf90a` |

The retail fixture is Dolk2 actor `0001`'s model `asset://dolk2/models/scene-tmd/0133`: 6,672 bytes, 10 objects, 190 source primitives, SHA-256 `faa56014591a06c2351132e6958b29d35493ffa59fe2f669fb9374b1beede282`.

Object 0/group 4 has 14 baked FT3 rows. Its mode byte is at model offset 1,095. Primitive 36's payload starts at 1,096; CLUT is at 1,102 and TPage at 1,106. The independent combined candidate changes only byte 1,095 from `0x25` to `0x27` and byte 1,102 from `0x4E` to `0x4F`: group ABE and CLUT `0x784E→0x784F`. Candidate SHA-256 is `4e6ba8dfc67e29d667e34b2aeb1db7ef864618b6495ff695ef11ccdfca8124f8`.

All geometry/vector bytes, UV/RGB, row commands, flags, footers and TPage words remain identical. Source primitives 36–49 correspond to triangles 51–64; their source ABE becomes true. The derived material count changes from four to six. The selected packet's 8×6 crop remains a static address match to `texture://dolk2/69/0/19`, with 48 changed RGBA samples after the CLUT switch. A separate page-column probe produces a missing static association rather than an invented match.

The existing GLB exporter/importer independently round-trips that combined effective TMD byte-for-byte with freshly regenerated material/crop metadata. Evidence is in `glb-material-preservation.json` and `qualified-current.glb`; the GLB SHA-256 is `47e9d69e494ad62ec0d1bb8ddcbec0cd1b3a25e22bb77a66e118f8c5f3873eac`. These are offline source/payload proofs. No game was launched, and runtime blending or gameplay appearance remains unverified.
