# Global World-Map Source Resource Browser

Open **World ground**, choose a kingdom and **Inspect kingdom**, then **Browse world resources**. Filter by kingdom and geometry or native TIM textures. Metadata shows stable resource identities, native source hashes and spans, geometry bounds, complete source instance membership and material address associations. Expand **Recorded relationships** and select a link to navigate to its owner, texture or consumer.

**Focus representative source instance** re-reads the selected kingdom, verifies the resource source and complete instance membership, enables source model rendering and frames the first canonical source instance on the Retail layer. It does not frame every instance together. The existing field scene remains active. Texture rows have no geometry focus; navigate to a model consumer first.

**Save resource index** downloads the complete metadata graph after a fresh project/source check. It does not extract geometry or image payloads, save project edits or change Undo/Redo.

## SDK Contract and Scope

`POST /api/worldmap-resources` accepts exactly `{source_key}` using the current Edit project's `worldmap_authoring_state_key`. `legaia.worldmap-resources.v1` contains three kingdom roots, model and native TIM records, exact ownership/material relationships, coverage and explicit limitations. It uses a detached project view and checks source identity before and after discovery. Resources carry `scene_id: null`, a separate source kingdom and `runtime_state: not_observed`.

The native input qualified 215 records: three roots, 77 geometry assets (three derived ground surfaces and 74 placed models), 135 TIM textures and 375 relationships. Geometry enumerates verified drawable assets referenced by source walk placements. It does not claim all unplaced TMDs. Ground comes from the MAP/floor heightfield rather than a native primitive pool. Static material/TIM address associations do not establish runtime palette behavior, VRAM residency or gameplay visibility. Native TIM-local pixel inspection is now available through [Native World TIM Pixel Preview](legaia-worldmap-texture.md). Model authoring is not added to this source browser.

This reusable SDK index is connected to **World ground** and the main **Project resources** browser. The placement ownership graph remains a distinct global source graph; the browser combines their records without adding imported field memberships.

## Offline Evidence — 2026-10-09

Three focused Python tests cover metadata-only output, unchanged project state, stale/Live refusal and malformed source spans/ownership/bounds. The Node decoder qualifies the actual native report and exact browser-downloaded report and rejects fifteen forged source/membership/reference variants. Two JavaScript syntax checks, three Python AST checks and whitespace checks passed.

The muted editor browser workflow navigates resources and native TIM consumers in all three kingdoms. Fresh viewport focus verifies models with 126, 138 and 109 source instances respectively, selects their first canonical instance on Retail, and preserves the active field scene. Full downloaded JSON matches the fresh SDK graph exactly. Stale source keys and unexpected scene selectors return HTTP 400. Desktop and 400px layouts were visually inspected; no page errors occurred.

Private evidence is retained under `local-output/sdk-20260909/worldmap-resources-20261009/`: native/downloaded indexes, browser proof, unchanged-project proof and screenshots. All fixture files, imported/authored inputs and history remain unchanged. No Apply, Build, game launch or runtime attachment occurred. Offline checks are not user acceptance or gameplay proof; the full SDK goal remains active.

## Project Resource Integration — 2026-10-09

Choose **Project resources** in **Asset database scope**, then **Global world-map sources** in the source filter. The combined global inventory contains 1,141 identities: 926 placement ownership identities and 215 geometry/TIM/resource-root records. **Models**, **Textures** and **World-map assets** retain their existing category meanings. Search works by stable ID, type, source kingdom and recorded provenance. Imported scene filters and Active scene resources exclude these global records. Discovery requires an available source disc; empty projects expose the 215 geometry/TIM/resource-root records. The additional 926 placement ownership identities require an imported-disc identity.

Geometry cards open World ground directly and focus one freshly qualified Retail source instance. **Details** opens source metadata, resource relationships and **Save world resource index**. Texture cards open Details with **Native TIM pixels** and **Preview native TIM**; their geometry focus is disabled. Follow a consumer link to geometry or an owner link to its resource root. Back retains at most 32 prior resource selections. Field model assignment, donor NPC creation and field editable-instance actions are not offered for global geometry.

The UI qualifies both the navigation-independent Project resources source key and the world geometry source key, which includes active scene context. Discovery withdraws stale combined results, rejects conflicting identities and enforces a combined 32 MiB metadata budget. Viewport handoff re-reads the native kingdom, matches model provenance and complete source membership, and leaves the active imported field scene unchanged. Pending world-map drafts must be resolved before navigation.

Two focused Node suites cover existing project discovery/membership behavior and all 215 native resource adapters, separate source keys, search/filter isolation and nine malformed/stale handoffs. Four JavaScript syntax checks and the server AST check passed. Actual editor workflows cover all three kingdoms, source Details and exact full-index download readback, native TIM consumers, Back and representative viewport focus. Desktop and 400px layouts were inspected with zero page errors. All fixture files, imported/authored inputs and history remain unchanged. Evidence is private under `local-output/sdk-20260909/project-world-resources-20261009/`. No Build, game or runtime attachment occurred; gameplay verification remains deferred.

## Disc-Backed Empty Projects — 2026-10-09

A project with its source disc configured can now use **Project resources**, **Global world-map sources** and **World ground** before importing any field scene. No placeholder scene or actor is created. The imported index has zero scenes, zero records and zero memberships; the source resource index contributes 215 global records. Active scene resources exclude those records and the active field scene/selection remain empty.

The SDK still validates the retail disc through the existing verified import context before publishing the empty imported index, and independently qualifies all three kingdom resource sources. Missing or unsupported inputs refuse discovery. Source keys, detached metadata bounds and stale result withdrawal remain enforced. Project inventory supports zero through 64 imports; the absence of a disc keeps empty-project discovery unavailable.

Placement ownership/authoring, authored comparison and native world GLB exports retain their existing imported-disc identity requirements. Their capabilities remain false on empty projects. The World ground export controls now explicitly require the native export capability, while numeric source inspection and resource metadata downloads remain available.

Sixteen focused Python index/HTTP tests pass, including unchanged empty indexes, no invented memberships, exact dispatch and capability separation. Two Node suites pass, including real 215-resource adapter qualification, mounted empty discovery using exact separate requests, stale world-source withdrawal and the existing populated-project lifecycle/membership workflow. Two JavaScript syntax checks and five Python AST checks pass. A private empty-project editor workflow covers all three kingdoms, search, Details, native TIM consumers, Back, exact full index download and fresh Retail representative focus. Export and authored placement controls remain disabled. Desktop/400px layouts inspected; zero page errors.

Evidence is private under `local-output/sdk-20260909/empty-world-resources-20261009/`. All fixture files, imports, project document, selection and history remain unchanged after inspection. No Apply, Build, game launch or runtime attachment occurred. Gameplay verification remains deferred; the full SDK goal remains active.
