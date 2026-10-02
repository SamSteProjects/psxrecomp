# Imported project Asset Database

The Asset Database can list source assets across every imported scene without
changing the active scene. It combines imported scenes, actors and models with
the existing bounded resource catalogs. Each shared stable ID retains a separate
record for each source scene, including that scene's provenance and bindings.
This is a source inventory; it does not establish runtime residency, actor
spawning, playable routes or complete game coverage.

1. Import the scenes needed for the project using the user-owned retail disc.
2. In **Asset database scope**, choose **Imported project resources**, then
   **Refresh project resources**. Discovery verifies the imported sources and
   builds catalogs on detached project views. It does not select a scene, issue
   authoring commands, change Undo/Redo history, save the project or replace the
   active scene's resource caches.
3. Use **Source scene** to show all imported scenes or one scene. The existing
   category and search controls apply to the resulting records. Search accepts
   names and IDs as well as `type:`, `scene:`, `model:`, `confidence:` and
   `provenance:` filters; see [asset search](legaia-asset-search.md).
   Project results use pages of 128 rows. Previous/Next assets retains the full
   filtered inventory; page size does not truncate discovery.
4. Open Asset Details. For a shared ID, **Imported source membership** identifies
   the exact variant being inspected. With all scenes displayed, choose the
   membership to inspect. A single-scene filter fixes the membership to that
   scene. All-scenes scope retains an explicit membership choice; without one,
   it prefers the active scene when it owns a variant, otherwise the first
   source scene in stable order. Records from different scenes are never
   combined into an invented binding.
5. Open the asset's existing inspector or tool. Cross-scene actions navigate to
   the chosen imported source scene and refresh its resources when required.
   Script ownership, instruction PCs and dialogue segment focus remain tied to
   that source. The asset index itself offers no alternative authoring path;
   existing Review/Apply, Undo/Redo, Save and Build workflows remain authoritative.

Choose **Active scene resources** to return to the existing scene workflow.
**Refresh scene resources** loads the active resource catalog. Project discovery
is explicit: changing scope alone does not load every imported scene.

| Records | Existing inspection and navigation |
| --- | --- |
| Scenes, actors and models | Imported source provenance, scene/actor selection and model tools. Imported models retain their source `tmd_model` kind alongside the browser's normalized model category. |
| Textures and animations | Source texture inspection, verified initial MAN animation bindings, and the existing model/clip previews. Shared field clips retain their explicit model and clip IDs; they do not acquire a scene actor assignment. |
| Scripts and dialogue | The source actor or P2 script workspace, with the recorded instruction or dialogue segment focus. Partial decoder coverage stays visible. |
| Flag references and transitions | Existing source-qualified reference inspectors and supported instruction authoring. Encoded selectors and named destinations do not prove runtime flag values or reachable routes. |
| Collision, triggers and regions | Existing field source workspace and outline inspection. Source bounds do not establish floor height, collision behavior or trigger activation. |
| World-map landmarks | Global menu source inspection and the existing landmark authoring workflow. Catalog membership in a scene does not make the global menu a scene-local resource. |

**Imported scene coverage and limits** reports each scene's import digest,
record count, availability and limitations. Available means the bounded source
products were returned. Partial means the returned inventory carries coverage
limits. An unavailable derived catalog can retain imported base records; inspect
its reason before treating missing rows as absence of an asset. Unknown script
instructions, unavailable animation bindings, unsupported formats and unresolved
references remain explicit. Neither record counts nor successful refresh imply
a complete decoder or successful gameplay execution.

**Inspect asset references…** remains the canonical Dependencies/Referenced by
view. Its [project scope](legaia-asset-references.md) preserves source-qualified
edges. [Imported material links](legaia-material-references.md) describe static
texture-address candidates and can include providers outside the navigable TIM
catalog. Such a provider does not become openable merely because another scene
references it. Shared model membership is also distinct from actor usage: the
same global model can have different initial actor references in each scene,
including no recorded actor reference in a scene that catalogs the model.

The read-only endpoint is `POST /api/project-assets` with exactly `{}`. Its
`legaia.project-assets.v1` response includes stable IDs, explicit `scene_ids`,
complete per-scene `variants`, scene coverage and limitations. Each variant binds
its record to the source import digest and, for derived records, its catalog key.
The project freshness key includes the project path, source disc path/stat,
import digests and resource-affecting authored overrides, actor drafts, model
replacements and texture replacements. Active scene, selection, history and
caches do not change this key. Source or authored drift invalidates the project
inventory and requires a new refresh; late responses from invalidated requests
are ignored.

Discovery is bounded to 1–64 imported scenes, 16,384 unique asset IDs, 65,536
scene memberships and 32 MiB of metadata. These are service limits, not promises
that every resource type is supported. An index budget failure disables project
discovery with an explicit reason; existing editor state remains usable.
Catalog metadata contains locators,
hashes, counts and references; source pixels, model payloads, raw script bytes
and dialogue text remain in their existing private source/preview workflows.

Private offline evidence uses Town01, Dolk2 and map01 under
`local-output/sdk-20260909/project-assets-20261002/`. It checks detached discovery
against a saved private project containing an authored placement, selection,
Undo/Redo entries and an existing resource cache. The metadata audit records
per-scene coverage, shared IDs, exact source-scene examples and state/file
preservation. No game launch or manual gameplay verification is part of this
inventory feature's evidence.

Central validation on 2026-10-02 passed 18 selected Python tests, two Node suites
and both changed editor module syntax checks. Retail browser checks covered
discovery without authoring, pagination, all 132 imported actors, shared source
choices, navigation-independent freshness, texture/model/script/dialogue/flag/
transition/field/animation handoffs, P2 owner and PC focus, and source invalidation.
An isolated private placement edit followed by Undo checked invalidation without
saving or building that edit. The 540px controls and source inspector were
reviewed. Browser page/HTTP errors and game-launch requests were zero. The source
audit preserved populated caches and saved files; gameplay remains unverified.
