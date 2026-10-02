# Asset dependencies and referenced-by navigation

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
use and effective animation donor bindings remain unresolved. The unresolved count describes the assembled graph, not just
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
