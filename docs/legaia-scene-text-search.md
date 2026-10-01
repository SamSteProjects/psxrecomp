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

## Project-wide search

**Search project text** uses the same panel across all imported scenes. Search
also matches scene names; each result identifies its owning scene. Discovery
uses detached scene views and leaves the active scene, selection and overrides
unchanged. **Open text editor** switches to the owning imported scene when
needed, then focuses the exact actor or partition-two text field. That explicit
navigation changes the active scene and may mark Active scene as unsaved; it
does not author text or add an Undo entry.

The project snapshot binds imported documents, disc/source identity and all
Dialogue overrides, including those outside the current scene. Changes during
discovery reject the aggregate. Unavailable scene catalogs retain their reasons
and contribute no text; source mismatch and budget failures reject discovery.
Budgets are1-64 imported scenes,32768 total runs and4MiB source glyph capacity.
Per-scene budgets and source guards also remain enforced.

Retail town01/Dolk2 review found645 supported runs across180 scripts (88 partial),
with both catalogs verified. Eleven focused text/project tests passed in0.716s.
The browser passed scene-name/layer filtering, unchanged discovery state,
Dolk2 navigation and return to the saved town01 override, unchanged authored
assets/history, stale project-text navigation, malformed requests and held-response
close/reopen. Screenshot inspected; zero authoring requests/page errors. Private
evidence is in `local-output/sdk-20260909/project-text-search-20260930/`:
`project-text-index.json`, `project-text-browser-check.json`,
`project-text-late-check.json` and `project-text-search.png`. This validation
follows the397-test checkpoint. No game was launched; gameplay remains deferred.

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
