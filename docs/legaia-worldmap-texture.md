# Native World TIM Pixel Preview

Open a native texture record from **Project resources** → **Global world-map sources** → **Textures**, or use **World ground** → **Browse world resources** and select a native TIM. **Preview native TIM** independently reads the native member and its local palette. It works before importing a field scene when the project has its source disc configured.

**Local palette index** is explicit. Indexed TIMs expose their complete local 16-color or 256-color palette blocks; direct-color TIMs accept only index zero. Each local palette colors the entire TIM image. This is not a reconstruction of all per-material CLUT selectors or a statement about the palette used in gameplay. Indexed TIMs without a complete local CLUT show an unsupported reason; cross-TIM and runtime palette behavior is not guessed.

Use **Native TIM pixel view** to choose **Color**, **Transparent-zero alpha** or **PSX STP mask**. Color uses nearest pixel display over a checkerboard. Alpha shows transparent-zero alpha as grayscale. STP shows the separate PSX semitransparency bit as a binary mask; it does not simulate the GPU blend mode. Palette and pixel views do not modify the resource, project or authored state.

## Source Contract

`POST /api/worldmap-texture` accepts exactly `texture_id`, `source_key`, `member_sha256` and `palette_index`. The canonical native identity determines its kingdom and pack slot. The SDK requires the current Edit project/world source key, verified supported disc, pinned kingdom carrier table, bounded decompressed texture pack and exact requested TIM member hash. It returns `legaia.worldmap-texture.v1` with the index's exact native TIM source record, disc/bundle/texture-pack provenance, dimensions, palette coverage, RGBA/STP byte hashes and read-only flags. The metadata index remains payload-free; pixel bytes are a separate private preview response.

The native reader loads only the selected source TIM, without generating the terrain/model graph. Preview is bounded to 2,097,152 pixels and the existing source-pack limits; frontend responses are bounded to 32 MiB. The browser qualifies complete source metadata, palette/dimensions, exact byte counts, SHA-256 hashes and binary STP values before drawing. Closing or navigating away disposes/aborts the preview; stale responses are not published. The same preview controls serve both source browser entry points.

## Offline Evidence — 2026-10-09

Three focused Python tests cover exact local palette colors, transparent zero, independent STP, direct color, missing local CLUTs, bounded palette requests, canonical IDs, stale/Live refusal and unchanged empty project/history. The Node decoder qualifies six native reports and rejects twelve forged source/palette/dimension/payload/flag variants for each. Three JavaScript syntax and four Python AST checks pass.

The actual empty-project browser workflow covers all three kingdoms and both entry points. Each selected TIM is 256×256, 4 bpp and has 16 complete local palettes. Palettes zero and one render; Color, Alpha and STP canvas bytes match the exact returned arrays. A separate native word/palette decoder matches all six returned RGBA/STP arrays byte-for-byte. Wrong source/member hashes and out-of-range palettes return HTTP 400. Relationships, Back, resource index downloads and representative model focus remain intact. Desktop and 400px layouts were visually inspected; zero page errors occurred.

Private evidence is retained under `local-output/sdk-20260909/worldmap-tim-preview-20261009/`. Native decoded pixels and screenshots remain private outputs; no source payload was committed. All fixture files, project metadata, imports, authored inputs, selection and history remain unchanged. No Apply, Build, game launch or runtime attachment occurred. Palette preview does not prove runtime appearance, blending or residency; gameplay verification remains deferred and the full SDK goal remains active.
