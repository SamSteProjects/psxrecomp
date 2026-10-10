# Global World-Map Source Resource Browser

Open **World ground**, choose a kingdom and **Inspect kingdom**, then **Browse world resources**. Filter by kingdom and geometry or native TIM textures. Metadata shows stable resource identities, native source hashes and spans, geometry bounds, complete source instance membership and material address associations. Expand **Recorded relationships** and select a link to navigate to its owner, texture or consumer.

**Focus representative source instance** re-reads the selected kingdom, verifies the resource source and complete instance membership, enables source model rendering and frames the first canonical source instance on the Retail layer. It does not frame every instance together. The existing field scene remains active. Texture rows have no geometry focus; navigate to a model consumer first.

**Save resource index** downloads the complete metadata graph after a fresh project/source check. It does not extract geometry or image payloads, save project edits or change Undo/Redo.

## SDK Contract and Scope

`POST /api/worldmap-resources` accepts exactly `{source_key}` using the current Edit project's `worldmap_authoring_state_key`. `legaia.worldmap-resources.v1` contains three kingdom roots, model and native TIM records, exact ownership/material relationships, coverage and explicit limitations. It uses a detached project view and checks source identity before and after discovery. Resources carry `scene_id: null`, a separate source kingdom and `runtime_state: not_observed`.

The native input qualified 215 records: three roots, 77 geometry assets (three derived ground surfaces and 74 placed models), 135 TIM textures and 375 relationships. Geometry enumerates verified drawable assets referenced by source walk placements. It does not claim all unplaced TMDs. Ground comes from the MAP/floor heightfield rather than a native primitive pool. Static material/TIM address associations do not establish runtime palette behavior, VRAM residency or gameplay visibility. No standalone TIM pixel viewer or model authoring is added here.

This reusable SDK index is connected to **World ground**. The **Project resources** global browser continues to expose its separate placement ownership graph; unified Project Asset Database integration remains future work.

## Offline Evidence — 2026-10-09

Three focused Python tests cover metadata-only output, unchanged project state, stale/Live refusal and malformed source spans/ownership/bounds. The Node decoder qualifies the actual native report and exact browser-downloaded report and rejects fifteen forged source/membership/reference variants. Two JavaScript syntax checks, three Python AST checks and whitespace checks passed.

The muted editor browser workflow navigates resources and native TIM consumers in all three kingdoms. Fresh viewport focus verifies models with 126, 138 and 109 source instances respectively, selects their first canonical instance on Retail, and preserves the active field scene. Full downloaded JSON matches the fresh SDK graph exactly. Stale source keys and unexpected scene selectors return HTTP 400. Desktop and 400px layouts were visually inspected; no page errors occurred.

Private evidence is retained under `local-output/sdk-20260909/worldmap-resources-20261009/`: native/downloaded indexes, browser proof, unchanged-project proof and screenshots. All fixture files, imported/authored inputs and history remain unchanged. No Apply, Build, game launch or runtime attachment occurred. Offline checks are not user acceptance or gameplay proof; the full SDK goal remains active.
