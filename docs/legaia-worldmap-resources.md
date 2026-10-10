# Global World-Map Source Resource Browser

Open **World ground**, choose a kingdom and **Inspect kingdom**, then **Browse world resources**. Filter by kingdom and geometry or native TIM textures. Metadata shows stable resource identities, native source hashes and spans, geometry bounds, complete source instance membership and material address associations. Expand **Recorded relationships** and select a link to navigate to its owner, texture or consumer.

**Focus representative source instance** re-reads the selected kingdom, verifies the resource source and complete instance membership, enables source model rendering and frames the first canonical source instance on the Retail layer. It does not frame every instance together. The existing field scene remains active. Texture rows have no geometry focus; navigate to a model consumer first.

**Save resource index** downloads the complete metadata graph after a fresh project/source check. It does not extract geometry or image payloads, save project edits or change Undo/Redo.

## SDK Contract and Scope

`POST /api/worldmap-resources` accepts exactly `{source_key}` using the current Edit project's `worldmap_authoring_state_key`. `legaia.worldmap-resources.v1` contains three kingdom roots, model and native TIM records, exact ownership/material relationships, coverage and explicit limitations. It uses a detached project view and checks source identity before and after discovery. Resources carry `scene_id: null`, a separate source kingdom and `runtime_state: not_observed`.

The native input qualified 215 records: three roots, 77 geometry assets (three derived ground surfaces and 74 placed models), 135 TIM textures and 375 relationships. Geometry enumerates verified drawable assets referenced by source walk placements. It does not claim all unplaced TMDs. Ground comes from the MAP/floor heightfield rather than a native primitive pool. Static material/TIM address associations do not establish runtime palette behavior, VRAM residency or gameplay visibility. No standalone TIM pixel viewer or model authoring is added here.

This reusable SDK index is connected to **World ground** and the main **Project resources** browser. The placement ownership graph remains a distinct global source graph; the browser combines their records without adding imported field memberships.

## Offline Evidence — 2026-10-09

Three focused Python tests cover metadata-only output, unchanged project state, stale/Live refusal and malformed source spans/ownership/bounds. The Node decoder qualifies the actual native report and exact browser-downloaded report and rejects fifteen forged source/membership/reference variants. Two JavaScript syntax checks, three Python AST checks and whitespace checks passed.

The muted editor browser workflow navigates resources and native TIM consumers in all three kingdoms. Fresh viewport focus verifies models with 126, 138 and 109 source instances respectively, selects their first canonical instance on Retail, and preserves the active field scene. Full downloaded JSON matches the fresh SDK graph exactly. Stale source keys and unexpected scene selectors return HTTP 400. Desktop and 400px layouts were visually inspected; no page errors occurred.

Private evidence is retained under `local-output/sdk-20260909/worldmap-resources-20261009/`: native/downloaded indexes, browser proof, unchanged-project proof and screenshots. All fixture files, imported/authored inputs and history remain unchanged. No Apply, Build, game launch or runtime attachment occurred. Offline checks are not user acceptance or gameplay proof; the full SDK goal remains active.

## Project Resource Integration — 2026-10-09

Choose **Project resources** in **Asset database scope**, then **Global world-map sources** in the source filter. The combined global inventory contains 1,141 identities: 926 placement ownership identities and 215 geometry/TIM/resource-root records. **Models**, **Textures** and **World-map assets** retain their existing category meanings. Search works by stable ID, type, source kingdom and recorded provenance. Imported scene filters and Active scene resources exclude these global records. Discovery currently requires at least one imported scene and an available source disc.

Geometry cards open World ground directly and focus one freshly qualified Retail source instance. **Details** opens source metadata, resource relationships and **Save world resource index**. Texture cards open Details; their geometry focus is disabled. Follow a consumer link to geometry or an owner link to its resource root. Back retains at most 32 prior resource selections. Field model assignment, donor NPC creation and field editable-instance actions are not offered for global geometry.

The UI qualifies both the navigation-independent Project resources source key and the world geometry source key, which includes active scene context. Discovery withdraws stale combined results, rejects conflicting identities and enforces a combined 32 MiB metadata budget. Viewport handoff re-reads the native kingdom, matches model provenance and complete source membership, and leaves the active imported field scene unchanged. Pending world-map drafts must be resolved before navigation.

Two focused Node suites cover existing project discovery/membership behavior and all 215 native resource adapters, separate source keys, search/filter isolation and nine malformed/stale handoffs. Four JavaScript syntax checks and the server AST check passed. Actual editor workflows cover all three kingdoms, source Details and exact full-index download readback, native TIM consumers, Back and representative viewport focus. Desktop and 400px layouts were inspected with zero page errors. All fixture files, imported/authored inputs and history remain unchanged. Evidence is private under `local-output/sdk-20260909/project-world-resources-20261009/`. No Build, game or runtime attachment occurred; gameplay verification remains deferred.
