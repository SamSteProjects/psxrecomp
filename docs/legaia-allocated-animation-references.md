# Retained initial animation references

Actor Asset Details → Inspect recorded references distinguishes the original
imported initial clip from a retained clip assigned through the actor Inspector.
An assigned retained clip replaces the effective inherited animation edge; it
does not erase the original imported animation relationship. Clearing the
assignment restores the inherited effective edge. Undo restores the assignment.

The retained identity is `animation://<scene>/authored-record/<record UUID>`.
The actor-to-clip edge uses the **effective** layer. The clip-to-model relationship
uses the **authored** layer and can be inspected inversely from the model. Active
scene and Project scopes use the same source qualification. If a scene's derived
catalog is unavailable, its retained relationships are not asserted.

Recorded provenance contains the current ledger and retained record hashes,
effective native bank hash, captured model/channel owners, model identity,
frame/channel counts, resolved native record slot and initial selector. The actor
edge additionally binds the exact assignment owner and component hash. Fresh
readonly assignment Review qualifies these against the source and native writer;
the original imported hash and current catalog key qualify the graph request.
Slot positions can change when other retained clips are retired, so the stable
record UUID remains the identity and each request resolves the current selector.

Retained clips now have navigable records when registered in the verified scene
animation catalog. See [retained asset workflow](legaia-retained-animation-assets.md).
Their actor Inspector continues to Manage assignments and edit retained content.
Hash/identity
search and layer filters work normally; expand Recorded provenance to review the
native evidence. These relationships assert project content, not live playback,
residency, scheduling or gameplay acceptance.

Reference queries do not issue authoring commands or change project metadata,
history or authored files. Observation mode uses a separate readonly verification
view without changing the original project's mode.

## Verification - 2026-10-05

All 28 focused/neighboring Python checks and both JavaScript reference suites passed.
Private native fixture checks cover active/Project actor, clip and model HTTP
graphs, native Review selector agreement, Clear/Undo and Save/Open. Readonly
queries in Edit/observation contexts preserve document/history/files. The browser
checks source-layer separation, UUID search, disabled retained navigation and
Recorded provenance with zero page errors or mutation requests; screenshot
inspected. Evidence: `local-output/sdk-20260909/allocated-references-20261005/`.
No game launched; gameplay acceptance remains deferred.
