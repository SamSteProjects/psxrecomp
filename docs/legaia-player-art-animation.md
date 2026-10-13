# PLAYER Art Animation Sources

In Progress — 2026-10-13. Native source decoding, fresh APIs, client qualification, Asset Database registration and normal read-only inspection/playback/timeline controls are implemented. Pose/clip exports and broader normal browser coverage remain pending. Gameplay, runtime residency and native cadence remain unverified.

The pinned reference `d6e64c68ede25813d35db20980da82a1a025549b` identifies ME archives in PROT 894, separate from the twelve inline PLAYER action records. Each of four characters has a main archive at slot `3*player+1` and a base archive at `3*player+2`, within fixed 0x10800-byte slots. Main counts are 17, 18, 19 and 1; every base archive has eight entries. All 87 retail entries use the channel-delta codec.

The codec walks the ME size table, preserving stored/compressed spans and opaque trailing bytes. It decodes bounded MSB-first selector, high-first nibble and literal-byte streams to native packed nine-byte channel records. All five selector branches, previous-part wrap, first-frame spatial accumulation, subsequent temporal accumulation and 16-bit arithmetic/12-bit emission are covered by a hand-built literal oracle. Source decoding does not establish compression-growth capacity or authoring permission.

Decoded stream part counts are 15, 16, 15 and 17. These differ from assembled object counts; the existing PLAYER equipment assembly's animation-part indices fit the streams and must be used for per-object pose mapping.

PLAYER record0 word +0x58 points to `[count][count × 0xD0 records]`. Discovery retains 109 logical records (33, 35, 32 and 9), including combo/name bytes, stream-source index, staged animation id, attach key and both rate bytes. All four banks contain eight records with alternate rate 0xFF. The source role hint and eligible main/base stream references are explicit, and multiple records may share physical streams. Runtime resident archive selection is separate and unobserved; a preview must select an archive explicitly. Cadence, interpolation, activation and gameplay are not inferred from rate bytes or archive eligibility.

Four focused Python tests pass in 2.050 seconds: codec oracle, malformed header/table/body refusals, all eight archives and assembly part ranges, all 109 art record relationships and corrupted PLAYER source refusal. Metadata-only catalogues preserve disc, PLAYER file/decoded bank, ME slot/body and decoded-stream hashes. No extracted payload is persisted in project metadata.

Private research evidence: `local-output/sdk-20260909/player-art-animation-20261013/archive-proof.json` and `catalog.json`. The native files are `importer/me_archive.py` and `importer/player_art_animation.py`; tests are in `tests/test_me_archive.py`. No game, attachment, recomp compilation, installation, disc export or publication occurred. The full SDK goal remains active.

## Fresh Assembly And Pose API Integration

In Progress — 2026-10-13. `POST /api/player-art-resources` qualifies current project/disc source metadata. `POST /api/player-art-playback` additionally requires model asset/catalog identity, selected equipment, art source key, physical stream id, optional eligible art-record id, Retail/Current geometry layer and the Current file hash (null for Retail). `POST /api/player-art-pose` requires the same fields plus a whole native frame index. Exact field sets, stale archive identity, cross-character streams, art-record eligibility and Current freshness are enforced. A bank source-role hint never silently selects runtime residency.

Playback receipts carry the existing texture-qualified Retail or Current base inspection, complete raw ME slot witness and decoded stream bytes. Poses map each object through assembly animation-part indices, preserve base textures and remove unposed normal-preview data consistently with existing PLAYER poses. Source discovery remains immutable and distinct from authored inline action channels.

Two focused native/HTTP tests pass in 369.947 seconds: every physical stream's first/last frames (174 total) against independently constructed rotation matrices, and original ME channels applied to saved authored Current geometry for all four characters. Project document, Undo and Redo remain unchanged by inspection. Stale Current/archive identities, invalid records/streams/layers and boolean frame indices refuse. Four Python AST checks and whitespace pass.

The independent JavaScript codec reproduces all eight archives/87 streams and 469,245 decoded bytes exactly, with 285 malformed source refusals. Receipt/model/texture qualification, normal Asset Database/inspector controls, exports, cached playback, channel timelines and actual browser verification remain pending. No complete workflow or gameplay acceptance is claimed.

Private evidence: `local-output/sdk-20260909/player-art-animation-20261013/workflow-python.log`, `codec-cases.json`, archive proof and catalogue. No game, attachment, recomp compilation, installation, disc export or publication occurred.

## Client Receipt And Cached Frame Qualification

In Progress — 2026-10-13. Client catalogue admission validates all archive/stream/art record identities, bounded physical spans, source hashes, eligible relationships and model-file/disc provenance. Playback qualification replays the complete ME slot through the independent JavaScript codec, compares the stored and decoded stream hashes/bytes, and verifies the existing Retail or Current model/texture inspection. The receipt now additionally carries a complete assembled TMD witness. Native TMD replay checks base vertices, primitives, normals, materials, object metadata and bounds before sampling, closing the missing literal geometry proof in the older Retail preview envelope.

Cached samplers own copies of decoded bytes, geometry and part mappings; caller mutation cannot corrupt subsequent frames. Pose qualification checks object transforms, finite vertices/bounds, preserved textures and the complete expected posed geometry. Source rate bytes remain metadata; no native cadence or resident phase is inferred.

Sixteen explicit archive fixtures cover all four characters, main/base archives and Retail/authored Current geometry, with 32 first/last pose checks and 352 changed source, model, texture, mapping, record and pose refusals. The fixture generator finished successfully; TMD witnesses were added from the original/current qualified assemblies, and separate fresh API checks confirm the new witness field for both layers. The original eight-archive codec suite still matches 469,245 bytes and refuses 285 malformed cases. JavaScript syntax, Python AST and whitespace checks pass.

Evidence: `local-output/sdk-20260909/player-art-animation-20261013/playback-cases.json`, `make_playback_cases.py`, codec cases and `tests/test_player_art_animation.mjs`. Normal inspector controls/registration, export, playback UI, native channel timelines and actual browser verification remain unfinished. No full workflow acceptance is claimed.


## Normal Inspector And Channel Timeline

Offline checks passed — 2026-10-13. Global battle discovery now includes 196 separate animation identities: 109 logical bank records and 87 physical ME streams. The normal inspector selects a same-character eligible archive explicitly, five equipment sections and Retail or Current geometry. Inspection qualifies the fresh model/source receipt before retaining a local sampler. Frame scrubbing, one-pass display playback, object selection, orbit and zoom reuse that sampler and GPU renderer. Display FPS remains an independent whole-number control, not native cadence.

The source channel timeline exposes all native parts and six translation/rotation axes. It displays discrete packed values, including signed translations and PSX rotation units. Click or Left/Right/Home/End changes the same preview frame; the original ME channels apply to both geometry layers. Invalid frame drafts, busy operations and changed project/source identity disable timeline navigation. No project channels are authored by these controls.

Sixteen Retail/Current fixtures validate all mapped part axes against 32 independently qualified first/last poses. All 196 normalized identities are unique. Existing 352 source/model/pose refusals and Asset Database regressions still pass. Actual muted Edge verifies Retail-to-Current reinspection, cached playback without additional pose requests, object selection, timeline End/Home and axis/part controls, invalid frame/busy/source withdrawal, unchanged document/history and wide/400-pixel layouts. Repeated sideband inspection also passes its full existing filter/palette/queued-close/Save/Open workflow after a shared WebGL lifecycle fix: clearing a selection now retains the canvas context; final close disposes it.

Private evidence is in `local-output/sdk-20260909/player-art-inspector-20261013/`, including browser scripts, proof and captures, and its `sideband-regression/` child. Broader art browser checks for archive/equipment changes, authored Current geometry, Save/Open and pending-close races remain queued alongside pose/full-clip exports. Native authored Current coverage exists separately. This is a bounded offline milestone, not complete art workflow or gameplay acceptance.
