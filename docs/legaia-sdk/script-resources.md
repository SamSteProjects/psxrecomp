# Script and dialogue resources

The central asset database discovers scripts and inline dialogue from supported
MAN actor records. The browser opens the owning actor's existing script/dialogue
inspector, keeping inspection and supported text authoring in one workflow.

Script identities retain the actor's structural source identity. Dialogue
identities append their record-relative segment PC. Resource metadata contains
source spans, hashes, counts and references; retail text and raw script bytes
remain in the private inspector response. Resource discovery does not alter
immutable imported documents, authored overrides, history or saved projects.

The catalog uses the existing bounded decoder. Unknown instructions stop a
path, conflicting boundaries remain unavailable, and unvisited bytes are not
searched for apparent messages. Partial inspection is visible in each script.
The inventory is limited to imported partition-1 actor records; it is not a
complete inventory of every field VM channel or standalone MES resource.

## Flag and transition evidence

Andrew's unchanged reference pin is
`d6e64c68ede25813d35db20980da82a1a025549b`.
`crates/engine-vm/src/field/step.rs`, blob
`9c7801d1626c6f6eb8bd48f9f7c3e5851379e674`, supplies the flag operations,
extended context dispatch and named scene-change structure. Existing decoder
provenance is recorded in `integrations/legaia/provenance/script-inspection-20260909.md`.
The named-label gate comes from `crates/asset/src/field_disasm/render.rs`, blob
`5b144b1f10358c832a7107974dcfd60807fa678b`: one to twelve lowercase letters or
digits. Other encodings retain an unresolved destination.

Flag references preserve their instruction PC, encoded selector and context
qualification. Local/context flags are not silently joined across actors;
extended dispatch can address another VM context. The reference's local-bank
width and encoded-index discrepancy remains explicit. No current flag value,
story name, persistent save location or runtime actor identity is inferred.

Named scene changes are encoded destination references. They do not establish
that the instruction executes, that the destination is importable, or that a
route is playable. Entry coordinates and direction remain encoded fields.
Unresolved destinations remain unresolved. No transitions or flags are writable
through this catalog.

## Acceptance scope

The verified town01 catalog contains 52 scripts and 344 dialogue segments,
including 49 partial scripts and 380 flag references. No named scene changes
were found on those decoded paths; this is not evidence that the scene has no
exits. Combined with textures/animations and the original project records, the
asset browser contains 678 records. Refresh preserves the existing authored
placement and imported/project file hashes.

Browser checks passed script filtering, readable flag references, actor
selection, dialogue filtering, parent-script navigation and exact segment focus
at the existing edit controls. Switching projects removed all 506 derived
records until explicit refresh. Browser errors were empty. Four catalog tests,
three resource workflow tests and three existing HTTP tests passed; synthetic
scene-change fixtures establish encoding only, not retail route acceptance.

Verify discovery, category/search filtering, source inspection, actor selection
and dialogue-segment focus as a single editor workflow. Confirm resource refresh
preserves saved authored state and clears stale catalogs on source/project change.
Gameplay routes, flag values and text display require separate runtime evidence.
