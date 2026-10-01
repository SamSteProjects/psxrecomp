# Scene text search

With an imported scene and its retail disc available, choose **Search scene text**
beside the resource controls. Search by text, source owner, stable run ID or kind.
Choose Retail, Effective, Authored overrides or All text layers. Authored mode
includes only runs with saved project overrides. Results show the three layers
separately and retain source capacity and instruction PC. Pages contain25 runs.

**Open text editor** opens the actor or partition-two script Inspector, focuses
the exact source-bound text field and scrolls it into view. Existing Apply,
Discard, Undo/Redo, Save and Build workflows own all changes. Search sends no
authoring commands and does not change the camera or project.

Discovery uses a freshly verified imported scene and one bounded dialogue source
snapshot. It enumerates cataloged script owners and only offers runs accepted by
the existing authoring decoder. Unknown/unvisited bytes, unsupported ordinary
dialogue and controller records are excluded. Partial scripts may still offer
decoded menu labels. Separate runs are source spans, not reconstructed sentences,
boxes, current story dialogue or proof of gameplay reachability.

Coverage lists inspected, partial and unavailable scripts; Coverage and limits
also lists owner restrictions and unresolved overrides. Legacy invalid text has
an unavailable effective layer and retains its validation reason. Retail text
is returned only in this private inspection response, never stored in the
metadata-only Asset Database or tracked in Git.

Source identity and text override identity are checked independently. Changes
during discovery reject the result. Closing aborts the request; old responses
cannot replace a reopened panel. Source or text changes withdraw navigation.
Budgets are1024 script owners,8192 runs and1MiB of source glyph capacity.

## Validation - 2026-09-30

Nine focused Python tests passed in0.712s, including source/text changes during
discovery, budgets, legacy invalid edits, exclusions and unchanged project state.
Editor syntax passed. The retail town01 browser found267 supported runs across91
scripts (60 partial, zero catalog-unavailable); eight runs belonged to partition
two. Three existing overrides remained separate from retail text. Filtering,
disjoint pages, empty results, exact actor/P2 field navigation, text-state stale
navigation, malformed requests and held-response close/reopen passed. State
remained unchanged, with zero authoring requests and page errors. The search
screenshot was visually inspected.

Private evidence: `local-output/sdk-20260909/text-json-project-20260930/`
contains `scene-text-index.json`, `text-search-browser-check.json`,
`text-search-late-check.json` and `text-search.png`. These retain private source
text and are ignored. The397-test checkpoint predates this feature. No game was
launched; gameplay acceptance remains deferred.
