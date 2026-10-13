# PLAYER Art Animation Sources

In Progress — 2026-10-13. The bounded native ME codec and source discovery are implemented. Fresh project APIs, Asset Database registration, explicit archive selection, Retail/Current assembly preview, export/playback/timeline controls and normal browser verification remain pending. This is a source foundation, not a completed editor workflow.

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
