# Hierarchy Keyboard Browsing

## Type to Focus — 2026-10-07

With keyboard focus in the hierarchy, type unmodified letters or numbers to
focus the next visible name with that prefix. Consecutive characters within
one second extend the prefix; repeating a single character cycles matching
rows and wraps at the end. The prefix resets after inactivity, hierarchy
rebuilding, project/scene changes or an arrow/Home/End navigation key.

Group headings participate. Actor names use their displayed name rather than
their icon or authored badge. Hidden and disabled rows are excluded. Modifiers,
composition input and typing in search fields retain their normal behavior.
Enter/Space still activate the existing selection action. Typing changes focus
only and does not select entities or edit the project.

Two focused Node suites and JavaScript syntax/whitespace checks passed. Actual
private Town01 browser checks passed repeated-character cycling, multi-character
prefixes, modifier isolation, collapsed-child exclusion, search reset and the
400 px Hierarchy & assets tab. Selection, authored data, history and dirty state
stayed unchanged; navigation issued no API writes. Complete document/history/
file snapshots stayed unchanged, there were no page errors, the screenshot was
inspected and owned helpers terminated. No native Build or game ran.

Private evidence:
`local-output/sdk-20260909/hierarchy-type-focus-20261007/qualified/`.
Earlier harness failures are retained: one expected Environment rows before
catalog loading; another overlooked matching script rows after actor folding.
The passing harness uses the populated visible row order. Gameplay remains
deferred and the full SDK goal remains active.

Tab enters the scene hierarchy at its remembered focused row, selected row, or first available row. **Arrow Up/Down** browse rows; **Home/End** focus the first/last row. Browsing moves focus only. **Enter/Space** activate the existing button action to select an actor, draft, environment object or source resource. Existing pointer and modifier selection actions remain available. Group headers participate in focus browsing. Right expands a collapsed header, then enters its first available child on the next press. Left from a child returns to its header; Left on the header collapses the group. Search temporarily expands groups and disables their headers, so Left from a search result retains focus on that row.

The shared navigation controller tracks stable SDK row IDs. Before each hierarchy rebuild it captures whether focus was inside the tree and the project/scene scope. Afterward it restores the same row when available, otherwise an available selected/first row. Search retains its own focus. An empty hierarchy provides a focusable container. Context changes reset the entry point without focusing an old scene's matching ID. Arrow navigation ignores modifiers and does not intercept Enter/Space; hidden/disabled rows are excluded.

Focused Node checks cover one Tab entry, boundary keys, modifiers/native activation, same-scene redraw, filtering, empty results, external focus and changed scope. Seven actual private-retail browser checks pass on Town01: arrows traverse actor/environment rows without API requests or selection changes; Enter selects through the existing selection endpoint and the reconstructed row retains focus. Search and empty-result handling stay focused on search. Complete project file hashes and history remain exact, with no authoring, Build or game request.

The540px Scene tab hides the hierarchy sidebar. Select **Hierarchy & assets** to browse it with the keyboard; this existing tab workflow is verified by the later [scene-tools browser proof](legaia-scene-tool-drawer.md). Returning to desktop also restores reachable keyboard browsing. Desktop screenshot was visually inspected. Proof: `local-output/sdk-20260909/hierarchy-keyboard-20261003/parent/`. Owned browser/server handles are terminal. This navigation feature requires no immediate gameplay verification.

## Hierarchy parent and child keyboard focus - 2026-10-04

Right expands a collapsed group while keeping focus on the header; pressing Right
again enters its first available child. Left on a child returns focus to its group;
Left on the header collapses it. These keys only browse the hierarchy. Disabled
search headers, hidden/disabled children and modifier keys are respected.

Focused Node checks and a real Town01 browser workflow passed across Actors,
Environment and Scripts, including a later child, one Tab entry and filtered-parent
handling. SDK selection, authored data, history, dirty state and imports stayed
unchanged; no navigation API writes or page errors occurred. Screenshot inspected.
Private evidence: `local-output/sdk-20260909/hierarchy-parent-child-20261004/parent/proof.json`.
No game launched; this feature requires no immediate gameplay verification.
