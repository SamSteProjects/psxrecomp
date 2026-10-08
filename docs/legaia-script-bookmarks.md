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

## Project-wide navigation

Choose **Script bookmarks** beside the project resource tools to browse all saved
locations across imported scenes. Search by name, scene, script owner, hex offset,
mnemonic or original record hash. Multiple search terms must all match; the scene
selector narrows results further. Expand **Original source witness** for the record
and imported-scene hashes. An empty project explains how to save the first bookmark.

**Open bookmarked instruction** changes the active editor scene when necessary,
selects an actor owner when applicable, and opens the actor or partition-two script
workspace. The freshly inspected original record must match the saved owner, hash,
offset and mnemonic before any bookmarked row is focused. The workspace displays a
verified-bookmark label. A changed record produces an inspection error instead of
guessing another offset. A changed project list requires **Refresh bookmark list**.
Finish pending script/world-map edits or active animation preview before navigating.

This route does not author instructions or bookmark metadata. Active scene and
selection follow the existing editor navigation behavior; changing scenes can mark
the retained active-scene setting dirty. A native map01 → town01 actor → town01
partition-two script → map01 roundtrip passed exact selection/focus and preserved
the complete project document, history and Authored files on return. A deliberately
mismatched inspection record rejected before focus. Catalog search, stale/pending
dispatch and detached source snapshots passed focused checks. Screenshots inspected;
no game launched. Evidence: `local-output/sdk-20260909/project-script-bookmarks-20261005/`.

## Script Bookmark Metadata Transfer

In the Script and dialogue inspector, expand **Transfer a script bookmark**. Select a saved bookmark and choose **Export selected script bookmark JSON**. In a project containing the same imported scene and script owner, open that script, choose the JSON file, review its decoded offset and mnemonic, choose a distinct name and select **Import as new script bookmark**. The new bookmark is selected and its verified boundary is focused; Recall, Undo/Redo and project Save/Open use the existing bookmark workflow.

The exact `legaia.script-bookmark-transfer.v1` envelope contains editor metadata only: the original bookmark UUID/name, stable scene/owner identities, import and original-record SHA-256 witnesses, offset and mnemonic. The historical UUID is not reused on import. No script instructions, dialogue payload or runtime state are included. A 64 KiB file limit, exact envelope/source fields, bounded Unicode names, owner/scene/hash equality and a unique decoded Retail boundary are checked before submitting the existing create command. That command independently reimports source evidence and verifies the original record. Imported names must be distinct within the owning script; a Copy name is suggested and adjusted for existing entries. Server validation remains authoritative for duplicate-name case folding and the 256-bookmark limit.

Export requires the current saved row and verified report. Import requires Edit mode, current script context, no pending script drafts and no busy operation. Clear bookmark transfer cancels a pending local file read; disposed inspectors ignore late completions. Live, authored branch execution and unsupported/opaque byte navigation are not established by this metadata workflow. Valid non-BMP names remain supported through the 80-character limit.

Offline checks passed on 2026-10-08: two focused Node suites, five existing Python bookmark persistence cases and changed JavaScript syntax checks passed. The new transfer suite covers source hashes, owner, exact fields, bounds, names, ambiguous boundaries, forged saved rows, detached metadata and the file-size limit. Private native Town01 editor checks passed download/upload, foreign import-hash refusal without a command, pending-read cancellation, a distinct imported UUID, selected new bookmark, Recall, Save, Undo/Redo and restoration of the prepared private project. Wide and 400 px captures were inspected; the transfer controls fit without horizontal overflow and the browser reported no page errors. Independent Open matched saved/restored state; imported evidence, assets, original files and Undo history were restored, with one legitimate private Redo entry. The first browser attempt caught missing module routes in the editor server; those were added before the passing run. Evidence: `local-output/sdk-20260909/script-bookmark-transfer-20261008/`. No native Build, game or runtime attachment ran; full SDK goal active and gameplay deferred.
