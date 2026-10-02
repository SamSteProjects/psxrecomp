# Asset dependencies and referenced-by navigation

Gate-1 field triggers now expose `field_trigger_script_reference` edges to a
unique bounded P2 record. Both source hashes, primary/fallback table identity,
row/P2 indexes and gate1 qualify the relationship in Active/Project scopes.
Shared script targets do not merge source trigger rows. Gate0, unknown gates,
missing and aliased targets remain unresolved; malformed provenance rejects.
These edges establish source references, without asserting runtime activation.
See [field source workspace](legaia-field-source-workspace.md).

Transition assets now expose `script_transition_reference` and named
`transition_destination_source` relationships with exact source record/PC proof.
Active/Project scopes navigate to the source script and imported destination;
unknown labels remain unresolved. Legacy direct scene-change edges are retained.
See [central transition assets](legaia-transition-assets.md).

Flag assets now expose one `script_flag_reference` dependency per decoded PC,
with the inverse source-script relationship under Referenced by. Both Active
and Project scopes retain script/context/bank/retail-index identities and
source-import/catalog provenance. Authored effective selectors stay separate
from retail graph grouping; no runtime variable or story reachability is
asserted. See [central flag assets](legaia-flag-assets.md).

Shared field clips now expose `reference_pinned_model_clip` dependencies to
their global models. Model Referenced by lists the inverse relationships. The
eight supported pairs are party idle/walk for global slots 00f0–00f2 and the
reference loops for 00f3–00f4; the auxiliary model's role remains unresolved.
Each edge retains `reference_clip_evidence`: the pinned reference commit,
model ID, clip ID, record index, frame/channel counts and complete disc/PROT/LZS
source locator. Exact stable IDs, pinned model source, record mapping and
bounded source/count metadata are validated before rendering. Missing imported
models increase unresolved coverage without inventing a target. Actor initial
assignment, effective donor playback and live timing are never inferred from
these model associations. The label reads "actor playback unknown."

These edges use the existing Active/Project response versions and navigation.
Fresh three-scene discovery checked 8 clips/24 scene-qualified edges and exact
source/edge hashes while preserving the whole project and caches. 31 focused
Python checks, 33 Node files and 34 syntax checks passed; actual browser party
and auxiliary navigation, three-scene scope and saved/history preservation
passed with zero errors. Evidence:
`local-output/sdk-20260909/shared-clip-references-20261001/`.
No game launched or new gameplay gate introduced.

**Reference scope** selects Active scene or Project. Active scene retains the
original response and refresh behavior below. Project verifies every imported
scene before decoding existing resource/material relationships in detached
views. It preserves the project's active scene, selection, authored data,
history, dirty state and Asset Database caches. Choosing a reference explicitly
navigates to its supported source scene. Non-active derived assets can open
Project scope directly from Asset Details.

Shared stable IDs retain both `scene_ids` (recorded source memberships) and
`navigable_scene_ids` (catalogs which can open the asset). Navigation uses the
edge's source scene when navigable, otherwise the deterministic primary catalog.
An external material provider does not become navigable just because another
scene records a reference to it. Each scene reports its verified import hash,
resource key, availability and limitations. Available means a catalog was
returned; unsupported resource kinds and unresolved relationships remain
explicit. Material diagnostic details select the first source scene in stable
order; individual material edges retain their own scene and source evidence.

The project response uses `legaia.project-asset-references.v1`. Request body:
`{"asset_id":"stable ID","scope":"project"}`. Omit scope or use `active` for
existing `legaia.asset-references.v1`. Unknown fields/scopes reject. Bounds remain
1–64 imports,16384 nodes,32768 edges and4096 neighborhood edges, with8MiB per-scene
assembled graphs and responses,32MiB accumulated decoded metadata/merged graph,
and bounded coverage/limitations. Source identity includes the disc path; drift
rejects discovery. Changing scope or closing aborts pending requests and ignores
late responses. Project queries issue no authoring commands and do not save.

Verification:20 focused retail-enabled Python checks/13.948s,33 Node files and34
syntax checks. Fresh Town01/Dolk2/map01 graph checks preserve complete project and
caches, independently match source hashes and12 shared material edges, and check
script/dialogue/animation/landmark references. Browser Active/Project discovery,
cross-scene navigation, pending Close/stale-source rejection and unchanged saved
bytes passed with zero errors; screenshot inspected. Private evidence is in
`local-output/sdk-20260909/project-asset-references-20261001/`. No game launched.
The following active-scope details and historical evidence remain applicable:


Asset Details → **Inspect asset references…** opens a read-only neighborhood of
recorded relationships. Dependencies follows outgoing references; Referenced by
follows incoming references. Selecting an available neighbor opens its Asset
Details, switching to its imported source scene and refreshing the resource
catalog when required. Unimported encoded scene destinations remain visible with
navigation disabled.

The SDK verifies every imported scene against the user-owned disc and refreshes
the active scene resource catalog before returning the view. Imported scene,
actor and model membership plus initial/effective model assignments cover the
project. Script ownership, dialogue segments, initial animation bindings,
recorded clip/model bindings, trigger/region collision-table sources and world
map destination labels cover the active resource scene. Draft donor relationships
are authored references. Each edge includes source import identity, evidence
layer and, for decoded references, the resource catalog key. Instruction PCs are
included when recorded.

These edges do not prove runtime residency, scheduling, actor spawning or
gameplay reachability. Script model-pool selectors and trigger dispatch remain
unresolved. Imported static material source candidates are now supplied through
the [material reference service](legaia-material-references.md); runtime material
use remains unresolved. [Effective initial donor animation relationships](legaia-effective-animation-references.md)
now retain their own evidence layer. The unresolved count describes the assembled graph, not just
the selected neighborhood. Missing edges therefore do not prove absence of use.

Queries change only derived caches. They do not issue authoring commands, mutate
imports, save changes or access guest RAM. Project/source changes invalidate an
open view; closed dialogs abort their pending requests. Server bounds are 64
imported scenes, 16,384 nodes, 32,768 edges and 4,096 neighborhood edges. The
browser validates the bounded schema and source identity before rendering.

Validation on 2026-10-01: three focused Python tests passed, including a fresh
town01 retail-source query and imported/authored/history preservation. Eleven
workflow/schema regression tests, all 22 Node test files and 24 module syntax
checks passed. Browser verified actor/script and cross-scene navigation, stale
view rejection, pending-request close, unchanged authored content/history and
zero errors or authoring commands; screenshot inspected. Evidence is private under
`local-output/sdk-20260909/asset-references-20261001/`. No game is launched for
this feature. These checks postdate the integrated 475-test checkpoint; they do
not establish complete SDK or runtime acceptance.
