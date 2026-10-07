# Structured scene hierarchy queries

The hierarchy search supports AND terms, quoted phrases and `-` exclusions. Fields are `name`, `id`, `type`, `component`, `authored` and `visibility`; an unqualified term searches the existing name, stable identity and authored actor-component labels. Examples: `type:actor name:"Actor 0049"`, `type:actor -authored:true`, `component:Transform`, and `type:actor visibility:hidden`. Literal stable-ID URIs remain searchable. Queries are limited to 2048 characters and 32 terms; invalid fields, incomplete phrases and empty terms show an accessible error and disable matching selection.

Types come from existing hierarchy groups: actor, npc-draft, environment, transition, trigger, region, collision and script. Actor component queries use recorded authored component names and their Inspector labels. Actor `authored:true/false` follows the existing authored-state indicator; NPC drafts are authored. Environment and resource authorship is `unknown` in this filter, rather than inferred from shared edits. This is row-local authorship, not dependency-based effective asset use.

For actors, NPC drafts and environment rows, `visibility:shown/hidden` follows the editor's hidden-entity set, including hide/isolation state. It does not assert rendered pixels, loaded geometry, occlusion or gameplay visibility. Resource visibility is `unknown`. Collapsing a hierarchy group does not change visibility. A nonempty search expands matching groups through the existing hierarchy folding/navigation service.

**Select matching actors** replaces the existing actor group with matching imported actors from the current scene. It rechecks the source/result binding and exact eligible identities, limits selection to 128 actors and uses the existing actor group service. Resource rows, NPC drafts and environment rows are excluded from this action. Busy states, held previews/inspections and invalid or empty actor results block it. Selection does not author components or create project history. Existing group tools and named selections remain available afterward.

**Reveal selection** clears the query, expands the selected group and focuses the row through the existing keyboard navigation service. The shared parser now accepts an optional field vocabulary; the Asset Database keeps its original default fields and grammar. `/hierarchy-query.js` is a registered editor module; no new authoring API or runtime behavior is introduced.

Offline checks passed on 2026-10-07: four focused Node suites and three syntax checks passed. A private real Town01 editor verified 52 actors, one-actor quoted selection, 51-actor exclusion selection, authored/component queries, invalid-query blocking, hide-list filtering, refreshed script resources, resource visibility `unknown`, Reveal/focus and wide/400 px layout without page errors or authoring requests. Save/Open preserved document, history, imports, authored state and Build inputs exactly. Search help scrolls within a bounded area so result rows remain accessible. Evidence is in `local-output/sdk-20260909/hierarchy-query-20261007/`; earlier startup busy-control, harness prerequisite and layout failures are retained. No game, native Build, runtime edit, full campaign, installation or disc export ran.

## Select matching scene placements

**Select matching placements** replaces the mixed placement group with eligible
imported actors, NPC drafts and static decorations from the current typed search
results. Collapsed hierarchy folds do not exclude matching rows. Resource rows and
shared scenery geometry without an editable placement identity are excluded.
The existing **Select matching actors** action remains available separately.

The action rechecks the current scene source, exact result IDs and query before
committing local selection. Busy work, held inspection/proposal tools, invalid or
empty queries, unavailable scene previews and non-authored scene representations
block entry. More than 128 matching placements disables the action with a tooltip
asking for a narrower query; results are never silently trimmed. Focus stays on the
active member when it belongs to the result. Otherwise the first matching stable ID
becomes active. Selection creates no project command or history step.

Use **Move scene placement group** for supported mixed-group Review/Apply, **Focus**
to frame the selected group, **Reveal selection** to expand its hierarchy folds, or
**Saved scene selections** to retain the IDs. Actor-only results populate the existing actor group; scenery-only results populate
the existing scenery group. Their dedicated placement tools receive the exact
matching IDs. Mixed results retain the scene-placement group; NPC-only results
retain existing selection behavior without claiming new group authoring support.

Offline checks passed (2026-10-07): two focused Node suites, two JavaScript syntax
checks and actual wide/400 px Town01 checks. Query `id:004` selected exactly 12 actor
and static-scenery placements, then opened the existing mixed-group Review. An
invalid field query disabled the action and retained the previous group. Project
document/history and saved file sizes/timestamps stayed unchanged; no native Build,
game launch or installation occurred. Private evidence:
`local-output/sdk-20260909/hierarchy-matching-placements-20261007/`
(`browser.json`, `readonly.json`, wide/narrow/group-review screenshots). NPC-draft
membership is covered by the source-bound eligibility helper; this actual fixture
contains imported actors and scenery. Gameplay remains deferred.


## Matching Placement Authoring Handoff

**Select matching placements** routes results using the current SDK actor, NPC-draft
and static-decoration identities. Actor-only queries open **Actor group placements**
through **Review group placements**. Scenery-only queries enable **Move scenery
group**. Mixed queries retain **Move scene placement group**. The routing preserves
existing source, edit-mode and proposal guards; it creates no authored command.
Conflicting or foreign identities are refused. Actor and scenery dialog actions
wrap to remain accessible in narrow editor layouts.

Offline checks passed (2026-10-07): the focused selection Node suite, two JavaScript
syntax checks, and actual private Town01 editor checks at 1440 and 400 px. Exact
queries handed 11 actors, five decorations and 12 mixed placements to their existing
Review workflows; each review was cancelled. Project document, Undo/Redo stacks
and saved file sizes/timestamps stayed unchanged. Earlier probe timing and overly
broad fixture-query failures remain alongside the layout evidence. No native Build,
game launch, runtime attachment or installation occurred. Gameplay remains deferred.
Private evidence: `local-output/sdk-20260909/hierarchy-authoring-handoff-20261007/`
(`browser.json`, `readonly.json`, browser logs and wide/narrow review screenshots).
