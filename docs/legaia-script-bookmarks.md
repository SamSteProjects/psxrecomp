# Saved script bookmarks

Open an actor's **Script and dialogue** Inspector or the partition-two dialogue
workspace. In **Instruction paths**, select an offset button. Enter a name under
**Saved script bookmarks**, then choose **Save script bookmark**.

The project retains the name, stable bookmark UUID, script owner, original record
hash, imported scene witness, record-relative offset and decoded mnemonic. Names
are unique within each script, limited to 80 characters; a project supports 256
bookmarks. Saving reimports the scene evidence and inspects the original source
record. Only a unique decoded instruction or dialogue boundary can be retained.
Opaque bytes are not accepted as apparent instructions. Navigation uses the
read-only inspector's bounds, rather than requiring serializer write eligibility.

Select a saved entry and choose **Recall script bookmark** to focus its original
decoded row. Recall is read-only and requires the exact record hash, owner, offset
and mnemonic in the newly verified report. It does not follow an authored branch
or prove that the game executes that instruction. Original record offsets remain
separate from runtime addresses, authored operands and proposed flow.

**Rename script bookmark** uses the name field. **Update bookmark offset** binds
the same bookmark to the currently selected original boundary. **Delete script
bookmark** removes the navigation record. These commands use ordinary Undo/Redo,
dirty tracking and Save project. Apply or discard script drafts before changing
bookmarks or using project history. Stale, busy or closed workspaces cannot dispatch
bookmark changes. Source mismatch disables recall; no replacement is inferred.

Save/Open and project copy preserve bookmarks. Opening validates portable metadata
without needing the disc; creating/updating and freshly inspecting the source need
the user-owned disc. Changed scene imports cannot reinterpret bookmarks or their
retained history. Delete the affected navigation records, save and reopen to clear
their history before replacing that scene's imported evidence.

Bookmarks do not change game assets or native Build inputs. Town01 actor 0044
passed create, rename, retarget, recall, delete, Undo/Redo and reopening in the
browser. A partition-two script bookmark passed source qualification and Save/Open.
Project copy retained the records. Paired normal Builds with/without bookmarks
emitted identical native payloads. Imports, overrides and Authored files remained
unchanged. Twenty focused Python tests and JavaScript source/boundary guards passed.
Private evidence: `local-output/sdk-20260909/script-bookmarks-final-20261005/`.
No game was launched; this navigation feature adds no gameplay acceptance gate.
