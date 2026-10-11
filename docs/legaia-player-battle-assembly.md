# PLAYER Battle Equipment Assembly

Offline checks passed for source-only equipment assembly and editor inspection — 2026-10-11. Four ordinary PLAYER source models are registered beside the default pack resources. These are distinct asset identities and assembly paths. Poses from PROT 1203 are not assigned to the assembled models.

The unchanged Andrew reference pin is `d6e64c68ede25813d35db20980da82a1a025549b`. Evidence was read from `crates/asset/src/battle_data_pack.rs`, `battle_char_assembly.rs`, `battle_char_assembly/assembly.rs` and its selection tests. The SDK independently implements bounded descriptor traversal, five-section selection, loader-frame extraction, object-pool relocation and retail selection-sort ordering. No reference checkout was modified and no reference binary/build is a runtime dependency.

## Source Boundaries

The legacy advertised TOC windows overlap neighbors: entries 865/866 can expose roughly 16 MB while their real descriptor allocations end at 454,656/96,256 bytes. The new reader uses the adjacent physical PROT start and independently requires the descriptor chain to end at exactly the same boundary. It does not change generic archive reading or consume adjacent files.

| PLAYER Source | PROT Index | Qualified Bytes | Descriptors | Default Objects |
|---|---:|---:|---:|---:|
| Model 0 | 863 | 692224 | 54 | 17 |
| Model 1 | 864 | 620544 | 50 | 18 |
| Model 2 | 865 | 454656 | 43 | 17 |
| Model 3 | 866 | 96256 | 5 | 19 |

Headers, canonical terminator, sector-aligned contiguous allocations and five default boundaries are checked. Each selected LZS stream is bounded to its own descriptor allocation. Loader offsets must match the attach-record header, and copied TMD pools remain within the declared body end. A 24-slot output object-table reservation preserves native offsets. Object entries and opaque words are preserved, offsets relocated, and bone tags sorted with the retail permutation. Equipment extras retain separate attachment/channel mappings. Swing/upload header fields are retained as metadata, without implementing their behavior.

Stable IDs are `asset://legaia/models/player-battle/NNNN`. Metadata retains disc/file/physical boundary hashes, descriptors, default assembly provenance and counts. The catalog source key binds all four bounded files. Preview additionally reports selected compressed/decoded hashes, source object mappings, bone tags, attachment channels and assembled TMD digest. No proprietary payload is persisted in discovery metadata.

## Editor Workflow

In Project resources, discover global battle sources and open a PLAYER Battle Model. The five Equipment Section selectors expose native item IDs and defaults without invented item names. Inspect PLAYER Assembly displays source-only object-local geometry through the shared WebGL renderer. Drag to orbit and scroll to zoom. Selection changes withdraw old geometry until freshly inspected. Assembly Provenance shows the requested/selected sections, fallback states and source mappings.

Selection is not an authored equipment change, scene placement or runtime observation. The source-only APIs `/api/player-battle-resources` and `/api/player-battle-preview` require exact current project/source fields. They reject stale/foreign sources and malformed equipment bytes. Missing item IDs follow the evidenced default fallback; UI choices expose existing descriptors only. No project document/history mutation or imported scene membership is created.

## Verification And Remaining Work

Two focused native tests pass all 152 individual descriptor selections, comparing assembled objects against independently decoded original sections: vertices, triangle relationships, UVs, baked colors and material words. All four defaults, fallback behavior, boundary/chain corruption and stale/foreign/boolean selection refusals pass. Actual HTTP source/preview checks preserve the project document and history.

Client checks pass four catalog records and eight default/selected preview receipts, with 64 altered previews and five altered catalog refusals. Existing Project discovery/navigation contracts pass. The actual editor discovers 46 combined battle resources and passes all four PLAYER inspectors, eight native previews, selection withdrawal, orbit/zoom, wide/400-pixel layout and unchanged document/history/empty field scene. Captures were inspected; no commands, scene navigation or page errors occur. Private evidence lives in `local-output/sdk-20260909/player-battle-assembly-20261011/`, including `client-cases.json` and `browser-proof.json`. Extracted geometry/pixels are not committed.

Texture upload/palette assembly, registration-time texture relocation, nine-byte PLAYER action poses, swing/art behavior and native authoring/build/runtime verification remain incomplete. Object-local geometry can overlap before its own action transforms are applied; this is explicitly unposed inspection. No Build, native compilation, game, runtime attachment, installation or disc export ran. Full SDK goal active; gameplay deferred.
