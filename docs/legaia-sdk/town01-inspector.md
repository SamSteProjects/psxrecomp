# Read-only `town01` inspection surface

## Boundary

Legaia Trace is the first visual consumer of `legaia.scene-import.v1`. It lives at `integrations/legaia/inspector` and remains separate from generic PSXRecomp runtime code. It does not open a disc, connect to PSXRecomp, inspect RAM, render retail assets, modify metadata or persist a project.

The surface accepts the deterministic JSON created by `integrations/legaia/tools/legaia_import.py`. The file is read with the browser `File` API and held in React state for the current tab. There is no upload route, connector, storage binding, browser storage or analytics path.

## What it displays

- source/build/schema/reference metadata;
- searchable MAN partition-1 actor records;
- a structural X/Z placement projection with no retail geometry;
- imported X/Y/Z values with unresolved Y shown explicitly;
- rotation/facing as unknown when no claim supports it;
- model pool/index and unresolved asset-record identity;
- PROT/MAN source record and decoded byte span;
- per-property confidence, evidence locators and notes;
- actor-level and import-level unresolved questions.

The built-in preview contains handcrafted synthetic actors only. It exists so the UI can be evaluated without a disc or generated importer output.

## Run and validate

```powershell
cd integrations\legaia\inspector
npm ci --ignore-scripts
npm run dev
```

Use **Open import** or drag a `legaia.scene-import.v1` JSON file onto the drop target. The client rejects other schema versions and scenes.

```powershell
npm test
npm run lint
```

The tests build and server-render the production surface, assert product-specific content, verify the starter preview was removed, and scan the client source for network, storage, runtime-write and editing primitives.

## Data handling

The deployed/static application contains no import snapshot. A user-selected file is not transmitted to the host. Do not add example retail imports, extracted models, textures, dialogue, absolute disc paths or runtime captures to this project.

## Still unresolved

This surface intentionally does not infer facing, vertical position, model asset identity, scripts, dialogue, story flags or runtime actor correlation. It shows unknown and contradictory claims instead of inventing display values.

The next separately approved slice is a read-only PSXRecomp observation bridge and revisioned Legaia layout profile. It must preserve imported/live state separation and must not introduce RAM writes or generic runtime title checks.
