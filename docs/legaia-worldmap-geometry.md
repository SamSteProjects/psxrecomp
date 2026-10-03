# Inspecting source world-map walk ground

The editor's **World ground** button opens the read-only **World-map source scene** dialog. Choose a **World kingdom** (`map01`, `map02`, or `map03`) and select **Inspect kingdom**. The viewport uses the same SceneRenderer as the field editor. Drag to orbit, use the wheel to zoom, and use **Frame ground**, **Top view**, and **Wireframe** to inspect the surface. Expand **Source provenance and limitations** for the qualified source spans and coverage.

This displays the source walk-visible ground heightfield for Drake, Sebucus, and Karisto. It does not import another scene, write authored overrides, change project history, start the game, or replace the current field scene. Source changes withdraw the stale inspection. World-map landmark menu X/Y bytes are not interpreted as 3D positions.

## Qualified geometry source

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b` supplies the world walk carrier selection and ground conventions. The SDK independently reads the user-owned retail disc. Each kingdom uses the complete `0x12000`-byte MAP immediately before its asset bundle, plus slot 2's MAN floor-height lookup table and slot 0's TIM_LIST atlas data.

| Kingdom | MAP PROT entry | Equivalent asset-table views | Visible cells | Vertices | Triangles |
|---|---:|---|---:|---:|---:|
| map01 | 83 | entry 85 + 6144 bytes = entry 86 + 0 | 16,251 | 65,004 | 32,502 |
| map02 | 242 | entry 244 + 2048 bytes = entry 245 + 0 | 16,381 | 65,524 | 32,762 |
| map03 | 389 | entry 391 + 6144 bytes = entry 392 + 0 | 16,374 | 65,496 | 32,748 |

The overlapping PROT views must resolve the same physical table and identical decoded source slots. The bare table view is the canonical locator. Seven descriptors retain their source types and stream boundaries; slot 2 provides the sixteen signed floor heights at MAN bytes 2 through 33. The source MAP has 128 by 128 cells. A cell's `0x1000` bit selects this surface, its low nine bits select the 32-byte object record, and corner height tiers select the MAN floor table. Each displayed cell contributes four vertices and two triangles. Raw geometry uses retail Y-down axes; only the renderer flips Y for display.

Texture selectors come from each selected source object record's atlas tile, page, and CLUT words. TIM_LIST member offsets are word offsets multiplied by four. The SDK qualifies bounded TIM images and their static address associations rather than inventing an atlas. Source material associations are available for 23 of 23 map01 materials, 17 of 18 map02 materials, and 15 of 16 map03 materials. Missing associations remain explicit. Static address agreement does not establish runtime upload order or VRAM residency.

## Independent retail evidence

Private evidence under `local-output/sdk-20260909/worldmap-geometry-20261002/retail/` independently walks all three MAPs and bundle tables. It records disc, MAP, compressed stream, and decoded MAN/TIM_LIST hashes and span boundaries. Independently generated ordered vertices, triangle indices, source UV coordinates, and every visible cell's record/tile/page/CLUT selector match the SDK output exactly. The probe writes metadata and hashes; it does not export an ISO/BIN or extract a broad payload tree.

For map01, the exact MAP SHA256 is `d29209df2b99b54182fdd029515bb89b7ca8fd47ac8bee2e128332608e925ea4`. Its source floor table is `[1,48,96,128,192,240,288,336,384,432,480,528,576,624,672,720]`; source ground bounds are `[0,-576,0]` through `[16384,-1,16256]`.

The current surface is a reference heightfield. It does not reproduce the complete retail ground emitter, per-story object placement, script visibility, collision deformation, ocean animation, special world overlay mesh semantics, or the separate overview resource. Landmark TMDs, decorations, and live actor placement are separate consumers and are not guessed into this viewport. Source geometry inspection does not establish full world-map rendering parity. No game was launched for this evidence; visual gameplay acceptance remains deferred.

Source model seeds now share this viewport. Use **Source model placements**, the
source entity hierarchy and **Frame selected** to inspect their immutable XYZ.
See [sparse placements](legaia-worldmap-placements.md) for provenance, model
texture coverage and the limits on runtime visibility and resting transforms.
