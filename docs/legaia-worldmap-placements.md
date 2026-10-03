# Inspecting world-map source model placements

The **World ground** inspection can include **Source model placements** alongside the qualified walk-ground surface. Choose a kingdom, inspect its source scene, and enable or disable the placement layer. Use the **World source entity** hierarchy or click a mesh, then **Frame selected**, to inspect a stable source entity and its MAP cell, object record, model slot, raw transform, and source confidence. This is read-only inspection: the current authored field scene, overrides, project history, and Build inputs remain unchanged.

These positions are source placement seeds. Script-managed objects can move to a different resting position or change visibility after initialization. A placed landmark's source transform is not a claim about its current gameplay position. Decorations and placed records remain distinct source families. Unknown model bindings are reported without inventing a mesh or position, and world-map menu pixel coordinates are not used.

## Exact source selection

Each kingdom uses the same MAP, MAN floor table, and texture atlas carrier already qualified for [world walk ground](legaia-worldmap-geometry.md). Slot 1 of the kingdom bundle is a TMD dictionary with a bounded directory of word offsets. The source object record's u16 at `+0x10` selects that dictionary slot directly. The retail actor pool's five-model prefix is a separate runtime address convention and is not added to this dictionary index.

Placed records have object flag `0x4` and require the footprint anchor to stay within the 128 by 128 grid. The source placed-record rule keeps reserved actor record selectors separate. Sparse walk decorations require all of: grid cell `0x1000`, a nonzero object record, a nonzero model slot, record mesh-drawn flag `0x2`, and no placed flag `0x4`. Riverbank/system records without the mesh-drawn flag are excluded. Ground cells are not stamped with a model merely because their record contains another nonzero field.

Source positions use the selected cell and signed record offsets:

```text
X = column * 128 + record.x + 64
Y = -MAN.floor_lut[MAP.floor_tier_at_selected_cell] + record.y
Z = row * 128 - record.z + 64
```

The floor lookup uses the placement cell, not the footprint anchor. Record rotation halfwords at `+0x08`, `+0x0A`, and `+0x0C` remain source PSX X/Y/Z angles. Renderer display conversion is separate from these raw source values. The object record hash and cell/record byte offsets keep inspection anchored to the precise source owner.

## Independent retail qualification

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b`, particularly `crates/asset/src/field_objects.rs`, establishes the placed and decoration gates, source offsets, rotations, and direct dictionary binding. Independent raw retail walking confirms every candidate's position, rotation, floor tier, flags, record hash, and bounded model slot across all three kingdoms:

| Kingdom | Source placed records | Decorations | Total candidates | TMD dictionary slots |
|---|---:|---:|---:|---:|
| map01 | 6 | 295 | 301 | 40 |
| map02 | 33 | 239 | 272 | 36 |
| map03 | 25 | 211 | 236 | 56 |

Every current candidate resolves to an existing qualified model dictionary slot. The raw TMD object tables and primitive references independently reproduce the model decoder's ordered vertices and triangles for all 40, 36, and 56 dictionary entries. Model geometry stays object-local, and source instances supply placement transforms. The existing walk-ground geometry remains a separate source asset. Texture association uses the same kingdom atlas and retains explicit missing or unsupported results; it does not assume current runtime VRAM residency.

The inspected scene graphs use 26, 22, and 26 unique model assets respectively. Model material associations are partial: map01 has 37 matched, 3 missing, and 4 unsupported; map02 has 26 matched, 10 missing, and 2 unsupported; map03 has 43 matched, 5 missing, and 3 unsupported. Independent comparisons reproduce every source entity transform and record hash, every loaded model's ordered topology, and the unchanged ground vertex and triangle hashes. A resolved model reference is separate from a resolved texture association.

Private source hashes, record identities, raw topology comparisons, SDK comparisons, and the saved browser fixture are under `local-output/sdk-20260909/worldmap-placements-20261002/research/`. Retail payloads are not committed fixtures. No game is launched, no disc export is written, and no source reference repository is modified for these proofs.

This extends the source scene inspection with sparse models. It does not reconstruct a complete world-map level, evaluate scripts, predict story visibility, infer resting transforms, animate oceans, or resolve the separate overview pool. Source model placement and exact byte ownership do not establish live gameplay parity; that acceptance remains deferred.

Eleven central Python cases and both Node guard suites passed. Nine integrated
browser checks verified all three scenes, hierarchy and source XYZ, actual GPU
mesh picking, placement toggles, camera controls, 540px fit, source withdrawal,
pending-close cancellation and exact project/Build file hashes. Screenshots and
the combined proof are private under the milestone `parent/` evidence folder.

The inspection now supports [source scene and selected-entity GLB export](legaia-worldmap-export.md) with the same geometry, transforms and confidence limits.

The separate [World placements authoring workspace](legaia-worldmap-placement-authoring.md) now supports reviewed source-record offsets/yaw and normal Build. This inspection and source GLB export retain their retail-source scope.
