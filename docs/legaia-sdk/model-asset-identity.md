# Model asset identity

Status: implementation design for the read-only `town01` semantic slice.

Reference baseline: `AndrewAltimit/legend-of-legaia-re` at
`d6e64c68ede25813d35db20980da82a1a025549b`.

## Scope

This layer resolves the model selector already imported from each MAN
partition-1 actor record into a stable, metadata-only asset identity. It does
not export TMD data, infer character names, bind animations, observe runtime
slots, or add any runtime or authoring behavior.

## Evidence-backed pool rules

Andrew's `field_npc.rs` and `scene_resources.rs` establish two distinct index
spaces:

- A placement model byte below `0xF0` indexes the scene resource TMD list.
  Field-mode construction scans the scene's CDNAME/PROT entries in entry order,
  then each entry's raw bytes followed by its LZS-decoded sections in descriptor
  and byte-offset order. `scene_tmd_stream` entries are excluded because those
  models belong to the battle loader rather than the field/town pool.
- A placement model byte `0xF0` or above selects global slot
  `model_index - 0xF0`. The confirmed town field pool is the five-entry TMD pack
  in decoded section 0 of PROT entry 874.

The stable identities therefore encode structural pool slots:

```text
asset://town01/models/scene-tmd/0004
asset://legaia/models/global-special/00f0
```

The global identifier retains the encoded placement selector (`00f0` through
`00f4`); `normalized_pool_index` records the corresponding zero-based slot.
Neither namespace contains an inferred actor name.

The pinned reference paths used were:

- `crates/engine-core/src/scene_resources.rs`:
  `SceneResources::build_targeted_with_options` and its
  `parse_scene_tmds_anms` walk;
- `crates/asset/src/tmd_scan.rs`: `scan_entry`, `scan_buffer` and
  `ResolvedTmd`-compatible byte extents;
- `crates/web-viewer/src/field_npc.rs`: `build_npc_catalog_impl`, including
  direct scene indexing and `model_index - 0xF0` normalization;
- `crates/engine-core/src/scene/host/effects.rs`:
  `seed_global_tmd_pool_from_befect_data`;
- `crates/asset/src/character_pack.rs`: `parse`, `PROT_ENTRY_INDEX`,
  `CONTAINER_SECTION` and `SLOT_COUNT`;
- `crates/asset/src/pack.rs`: decoded pack entry ordering and bounds.

The PSXRecomp implementation independently performs the bounded container
decode, TMD structural scan, pack-range walk and metadata projection in
`integrations/legaia/importer`. Andrew remains an optional parity oracle only.

## Source descriptors

Every asset record carries a bounded source descriptor without carrying its
bytes. A raw TMD descriptor may use a PROT-entry byte offset directly. A TMD
found after decompression uses an offset and length in the decoded section's
coordinate space and also identifies the containing PROT entry, container
section or scene-table descriptor, and decoded size.

Global-special descriptors identify PROT entry 874, container section 0, the
decoded pack slot, its bounded decoded offset and length, and the containing
decoded size. They do not claim that a decoded offset is a raw disc offset.

For `town01`, the scene-local pool contains 114 valid TMD records, all in PROT
entry 4's decoded scene-table section and ordered by decoded byte offset. The
global pool contains five valid pack slots. No null, sentinel or aliased pool
entry was observed in either enumerated pool. An actor selector outside these
bounds remains `pool_index_out_of_bounds`; the importer does not manufacture an
asset record. Unused pool entries remain independent asset records, and repeated
actor references retain the same semantic ID.

## Claims and uncertainty

The following claims may be confirmed when all bounds and pool rules validate:

- semantic asset ID;
- model pool and encoded selector;
- normalized global slot;
- source PROT entry and bounded decoded record;
- actor-to-asset reference through the structural pool index.

Agreement with Andrew's implementation is parity evidence, not sufficient by
itself to promote a claim. Character identity, animation binding, texture
binding, runtime pointer identity, and unused-slot purpose remain unresolved.

## Compatibility and schema version

The additive asset catalog and semantic actor reference are emitted as
`legaia.scene-import.v2` with importer version `0.2.0`. The v1 schema remains in
the repository, and Legaia Trace continues to accept v1 documents. V2 retains
the existing actor placement fields while adding `assets.models` and
`model_reference.asset_semantic_id`.

Assets are ordered by pool construction: all scene-local slots in structural
source order, followed by global-special slots in pack order. This is equivalent
to ascending pool index within each scope and is stable across repeated imports.

## Inspector behavior

Legaia Trace accepts v1 and v2 documents. For v2, the selected actor displays
the stable asset semantic ID, encoded and normalized pool indices, resolution
status, PROT entry, bounded source span, coordinate space and unresolved model
questions. V1 documents continue to show their unresolved legacy reference.
The inspector remains local-file-only, read-only, storage-free and runtime-free.

## Validation results

The 2026-07-18 retail pass produced 52 unchanged actor IDs and 119 unique model
asset IDs: 114 scene-local and five global-special. All 52 actor references
resolved; 29 assets were referenced and 90 remained unused. All 119 source
records were bounded and confirmed; none had unknown concrete source identity,
aliases, null entries or invalid indices.

Two v2 imports were byte-identical at SHA-256
`bbdd965831be572d3f19eee1ad33e8dd4a9b650d94c919358889cbf18198e728`.
Schema validation, metadata-only validation and the proprietary-payload/path
scan passed. The accepted v1 actor IDs, sources, transforms, pool/index values
and placement fields were unchanged.

The output contains 959 Confirmed claims and 52 Unknown claims. The Unknown
claims are the still-unresolved actor rotations; no model source is unknown on
the supported image. Strongly Inferred, Tentative and Contradictory counts are
zero.

Andrew's two real-disc tests passed. A temporary metadata-only oracle compared
all 119 pool rows by pool slot, PROT entry, decoded offset and bounded length;
119 matched and none differed. The temporary oracle was removed and the Andrew
checkout returned clean.

The synthetic suite covers deterministic scene/global IDs, pool resolution and
normalization, shared and unused assets, absent aliases, invalid selectors,
truncated TMD structures, deterministic ordering, actor references, claims,
unknown and contradictory sources, metadata enforcement and v2 schema
validation. Legaia Trace's production build and two read-only surface tests
passed. The desktop browser displayed the v2 model identity/source UI, but its
native file chooser stalled when attaching the external retail JSON; therefore
the interactive retail-file load was not re-certified in that browser pass.

## Remaining questions and recommendation

Character/object naming, animation binding, texture/VRAM dependencies, mutable
runtime pointers and equipment-conditioned model state remain intentionally
unresolved. The imported side is sufficiently strong for a separately approved
read-only runtime-layout research pass. That work must begin with a revisioned
layout/profile design and must not assume this model identity is a runtime actor
slot or authorize RAM writes.
