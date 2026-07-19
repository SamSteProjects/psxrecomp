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

## Source descriptors

Every asset record carries a bounded source descriptor without carrying its
bytes. A raw TMD descriptor may use a PROT-entry byte offset directly. A TMD
found after decompression uses an offset and length in the decoded section's
coordinate space and also identifies the containing PROT entry, container
section or scene-table descriptor, and decoded size.

Global-special descriptors identify PROT entry 874, container section 0, the
decoded pack slot, its bounded decoded offset and length, and the containing
decoded size. They do not claim that a decoded offset is a raw disc offset.

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
