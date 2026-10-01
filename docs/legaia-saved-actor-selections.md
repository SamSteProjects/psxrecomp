# Saved actor selections

Select2–128 imported actors with Ctrl/Command-click, a box or hierarchy range.
Choose **Saved actor selections** beside Box select in the viewport tool row.
Enter a name and **Save current actor group**, then Save the project to retain
it across sessions. Names contain1–80 characters and are unique within one scene;
the project is bounded to128 saved selections.

The dialog lists selections from every imported scene with scene/name/count.
**Recall actor group** navigates to its scene, focuses the first source actor,
and restores the whole group. Placement, appearance and component review tools
then consume that group normally. Recall does not author actor properties or
add an Undo entry; cross-scene navigation changes the ordinary active-scene
project setting. The dialog supports **Rename selection**, **Replace with current
group** (same active scene), and **Delete selection**. Each successful change is
one project Undo/Redo entry. Repeating identical names or membership is a no-op.

These are editor selection metadata, not game parenting, new actor instances,
transform groups or prefabs. NPC drafts, scenery and runtime nodes are excluded.
They do not affect the scene geometry source key, game build input key or emitted
game edits. No game launch is needed to verify selection metadata itself.

## Source and command binding

The optional `actor_selection_sets` project field retains canonical UUID-based
`selection://` IDs, names, scene IDs, imported-document SHA256 and sorted actor
IDs. Legacy projects without it still open. Invalid/unordered/duplicate members,
stale import binding and duplicate scene-local names fail on Open. Import changes
are blocked while a saved selection or referenced command history depends on the
old import. The source is never silently reinterpreted.

`create_actor_selection_set` requires type, scene_id, import_sha256, name and
actor_ids. It only captures imported actors in the active scene. Rename, Update
membership and Delete require type, selection_set_id and review_key, plus name or
actor_ids for the relevant operation. Extra fields reject. Review identity binds
the project root and complete saved selection; commands require Edit mode.

The UI refreshes state before opening and after a rejected reviewed command.
Recall validates current imported scene/hash/membership and rechecks the saved
selection after navigation/focus, preventing a stale group from being installed
in another context. Source/project/mode/inspection changes disable or close the
metadata editor. A failed reviewed command never partially renames/replaces/deletes.

## Evidence - 2026-09-30

Fifteen focused Python tests passed in1.318s, no skips: five new selection tests
plus ten existing placement/layout tests. Coverage includes layers/source/game
input exclusion, dirty-section identity, Save/Open, history/redo/no-op, atomic
stale/name/member/Live/extra-field rejection, malformed saved binding, legacy
opening and changed-import/history guards. Node checks verified scene/hash/member
binding, canonical order, detached recall IDs and rejected invalid proposals.
Editor/module syntax and diff checks passed.

Retail browser town01 actor0011/0012/0013 selection creation, Rename/Undo/Redo,
member replacement/Undo, Delete/Undo and Save/reload passed. Recall from the
imported Dolk2 scene restored town01 and those three IDs, with no game components
or commands changed. Placement review received exactly three checked actors.
An external rename made the earlier rename review stale: rejection retained the
external result and refreshed displayed state; Undo restored the saved name.
Zero page errors. First browser run found a clipped Recall button; the targeted
wrapping dialog fix passed the complete subsequent workflow and screenshot review.

Independent `ProjectService.open` from the saved retail project retained the
name, UUID, members and imported-source digest, with clean dirty state. Comparing
a detached copy without selection metadata proved identical nonnull scene source
keys, build input keys, imports and authored game components. No game launch,
package install or gameplay verification was performed. Owned browsers/server
were closed. Private evidence lives under
`local-output/sdk-20260909/saved-actor-selections-20260930/`, including
`saved-selection-browser-check.json`, `saved-selection-disk-check.json` and
`saved-selection-cross-scene.png`. This addition postdates425 full checkpoint.
