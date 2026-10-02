# Saved scene placement selections

Choose one imported actor/static decoration, an actor or scenery group, or use
**Select scene placements** for a mixed group. **Saved scene selections** stores
1–128 distinct imported placements under a scene-local name. **Save current
placements** captures source identity and membership. Save the project to retain
it across sessions. NPC drafts, placed scenery and ground are excluded.

The dialog supports **Rename selection**, **Replace with current placements**
and **Delete selection**. Each operation has one Undo/Redo entry and changes
editor metadata only. Names are unique per scene; the library allows 128 sets.
**Recall placements** can switch to the saved imported scene. It verifies fresh
source membership, selects the focused entity and recalls actor-only, scenery-only
or mixed membership into the corresponding existing placement tools. A single
member focuses one placement. Recall does not apply saved transforms or move
objects; edited objects keep their current authored positions.

The library stores imported metadata identity and MAP identity when scenery is
included. Project metadata can reopen without the disc; Create/Replace/Recall
with scenery require the current verified source. Missing/drifted input rejects
recall. Pending Close, changed context and late responses cannot reinstate a
cancelled selection. Changed reimport is blocked while sets or their undo history
still bind the prior source. Rename/Delete remain metadata-only operations.

## Verified offline workflow — 2026-10-01

38 focused Python checks passed in 2.554s; 32 Node files and 33 syntax checks
passed. Actual Town01/Dolk2 browser checks covered Create/Rename/Delete/history,
Save/Open, cross-scene mixed recall, single-decoration replacement/recall/Undo and
pending source/recall cancellation. Zero page errors; screenshot inspected.
A saved project copy retained exact membership; normal Build produced identical
package bytes before and after editor-only selection metadata. Private evidence:
`local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This does not establish runtime visibility, parenting,
instantiation or gameplay position parity.
