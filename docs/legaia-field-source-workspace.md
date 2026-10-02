# Field source workspace

Refresh scene resources to add source Transitions, Triggers, Regions, Collision
and Scripts groups to the hierarchy. Selecting a row uses the shared read-only
Inspector. **Asset details and references** opens the existing Asset Browser
tools; their source-specific editors retain their normal authoring checks.

For a trigger or region, **Frame source cell** loads freshly verified MAP
footprints and frames its X/Z bounds. **Source cells** controls their viewport
outlines; **Pick source cell** enables explicit read-only picking. Clicking
coincident cell centres cycles distinct source rows in source order. Hiding
the overlay exits picking. Ordinary actor/scenery selection restores the
normal Inspector. Scene, project or resource-context changes discard the
source overlay and selected resource.

The two tile lookups use different arithmetic:

| Source | Tile lookup | World interval for tile t |
| --- | --- | --- |
| Kind 0/1 trigger | `world >> 7` | `[128*t, 128*(t+1))` |
| Region | `(world - 64) >> 7` | `[128*t+64, 128*(t+1)+64)` |

Region rectangles retain existing half-open normalization, including reversed
and degenerate source bounds. Display Y=0 is an inspection plane with unknown
height; it is never terrain sampling. Gate 0 object-bind cells are source lookup
keys, not proven contact volumes. Rows outside dispatcher tiles 0..127 remain
source metadata without an activation claim. These outlines and markers do
not identify a destination arrival or prove a script will run.

Gate 1 MAP rows expose `field_trigger_script_reference` in Active/Project asset
references. Qualification requires an exact four-byte trigger row hash and a
unique, non-aliased bounded P2 source record from the same disc/scene. Evidence
retains both hashes, primary/fallback table identity, trigger/P2 indexes and
gate 1. Shared script references preserve separate trigger identities. Gate 0,
unknown gates, missing and aliased P2 records remain unresolved. Runtime
binding is `not_asserted`; reachability is `not_evaluated`.

`POST /api/field-map-preview` now includes `spatial` with schema
`legaia.field-spatial.v1`. `sdk.field_spatial.build_field_spatial` adapts the
existing fresh importer metadata; it does not add a source decoder. The adapter
checks source identities, table spans, record ordering, collision carrier
agreement and trigger payload hashes. The frontend checks bounded identities,
quantizers, geometry/provenance agreement and table overlap before rendering.
Source geometry remains private transient data, outside imported/authored
project documents and Build output.

The reference stays pinned at
`d6e64c68ede25813d35db20980da82a1a025549b`. Trigger quantization is in
`crates/engine-core/src/scene/host/scene_entry.rs`, lines1267-1291, blob
`0cf4e43f69fa6f5a547e2b3fd7696306c340fd0a`. Region quantization and
normalization are in `crates/engine-core/src/field_regions.rs`, blob
`8f54e88895ecdf0ca3fe1fc5602ce583911c5feb`, with the caller in
`crates/engine-core/src/world/field_movement.rs`, blob
`12ce75c6990cfd5df489a28cb17c6fb33a719f26`. The reference is a development
oracle; no dependency or runtime code was copied.

Town01 has 99 trigger cells,14 region bounds and 51 gate 1 references to 22 P2
records. Fallback kind1 row0000 resolves P2[38] and frames X[12416,12544),
Z[1280,1408). Actual browser checks cover hierarchy/Inspector/frame/pick,
coincident rows, script-reference/source navigation, region bias, overlay hide,
actor selection restoration and scene invalidation. Retail HTTP checks prove
source hashes agree with the catalog and inspection leaves authored state,
history, dirty status and Save/Open data unchanged.

Final validation:59 retail-enabled Python tests passed with no skips in84.629s;41 Node checks and39 module syntax checks passed. Actual browser frame/pick, overlapping rows, reference/script navigation, actor restoration and scene invalidation passed with zero page/HTTP errors. The saved baseline/import hashes remained unchanged; no package or game was launched.

Private evidence is in `local-output/sdk-20260909/field-spatial-20261002/`.
Gameplay contact, runtime height and activation remain in the
[deferred verification queue](legaia-gameplay-verification-queue.md).
