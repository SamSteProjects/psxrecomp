# NPC Creation from Model Rows

An active-scene model row now offers **Create NPC from model**. It lists the SDK's recorded Retail initial-model owners and requires an explicit donor choice before opening the existing source-qualified NPC candidate editor. Name and X/Z placement remain editable and explicit. Creation uses the existing Project command, history, persistence and native Build pipeline rather than creating a script from model geometry.

Retail ownership is deliberately independent of effective authored appearance. A donor whose authored appearance changed remains associated with its original Retail model for cloning. Authored NPCs, effective-only references and other scenes do not become Retail donors. Duplicate or mismatched source identities refuse; models without a Retail actor owner cannot create an NPC through this action. The SDK records are consumed directly; the asset browser does not parse MAN or scripts.

The chooser binds the exact Project path/copy key, scene/source key, asset row and Retail donor set. The existing candidate editor now also checks Project/source freshness, verifies the requested model against the native candidate's donor dependencies, and disables stale creation and navigation controls. Withdrawal is permanent for that dialog even if the old key reappears. Close aborts requests and disposes timers. Read-only candidate inspection remains available through its existing entry points; creation requires Edit mode. The NPC draft manager now points to Review Build instead of its obsolete blanket claim that playable builds are unavailable.

Four focused Python draft lifecycle cases passed, covering history, independent duplication, persistence, invalid donor/position refusal and Build invalidation. The expanded Node model-user contract passed Retail/effective separation, draft exclusion, detachment, empty owner sets, wrong scene, source mismatch and duplicate refusal. Editor JS syntax passed.

Actual private Town01 editor checks selected model0092 and explicitly chose Retail actor0040. Candidate inspection verified the native model identity, then created a named NPC at X128/Z256. Save and independent Project reopen preserved it; Undo removed only the new draft, Redo restored it, and final Undo/Save restored the original Project. Original actors, other NPCs, imports, Asset Database and undo history were preserved; one legitimate Redo remained. Chooser and candidate stale-key refusals passed. Wide and 400 px captures were inspected without horizontal dialog overflow or page errors; browser/server helpers closed.

Evidence: `local-output/sdk-20260909/asset-npc-creation-20261008/checks.json` and `browser/`. Retail inputs and evidence remain private and untracked. No native Build, game, runtime attachment, recompilation, install or disc export ran for this checkpoint. Source donor inspection is not proof of runtime spawning, scheduling, appearance restaging or gameplay. Those checks remain deferred; the full SDK goal remains active and solo development continues.

The subsequent [NPC Creation Selection Handoff](legaia-npc-creation-selection.md) connects successful creation to hierarchy, camera and Inspector focus, including delayed-preview source guards.

[Scene Ground Placement](legaia-npc-ground-placement.md) now copies qualified native X/Z into the creation form before explicit Create.
