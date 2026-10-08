# Inspect Stored Animation Channel Contributions

Open a native scene animation's Asset Details and choose **Inspect stored channel
contributions…**. The read-only inspector lists exact stored frame, object,
translation/rotation axis, value and contributing actor. Pages contain at most
128 contributions. **Inspect contributor** routes the selected owner through
normal scene selection and closes the owned inspectors after a fresh handoff.

This is separate from current initial animation users: channel contributions
remain attached to the actor's imported shared clip even when its initial
appearance or animation assignment changes. NPC drafts and allocated retained
record editing are not imported shared-channel owners.

The inspector requires a native clip in the active scene, its source-record hash,
frame/object counts and matching imported owner identity. It rejects duplicate
owner/channel records, mismatched hashes, invalid axes and unrepresentable
values. Translation is signed 12-bit (-2048–2047); PSX rotation is 0–4080 in
steps of 16. Stored lists are bounded to 4096 edits per owner and 65536 total
axis contributions.

Equal stored values share an axis. Different stored values are marked as a
metadata conflict. Normal native authoring already rejects contradictory writes;
this inspector neither applies them nor relaxes that gate. Stored values are
not a native byte audit, runtime assignment or gameplay report. Exact native
Retail/Effective values remain available in the existing channel editor.

Project/scene/source and complete contribution snapshots guard navigation.
Changed sources withdraw controls. Close, Escape, parent disposal and reopening
withdraw old ownership; a dialog generation prevents late navigation from closing
a newer inspector. Contributor navigation uses existing authored-scene geometry
and placement-selection gates. Inspection itself creates no overrides.

## Offline Checks Passed — 2026-10-07

Two focused Node suites passed contribution/animation-user contracts. The new
cases cover deterministic per-axis owners, equal values, synthetic contradictory
metadata, immutable sources, source/count/encoding bounds and malformed refusal.
Two JavaScript syntax checks, server AST and whitespace checks passed.

A private Town01 copy prepared identical channel edits on two imported owners
through normal native commands, then saved before the verification snapshot.
Fresh native channel inspection confirmed the composed value and both axis
contributors. Actual wide/400 px browser checks displayed that exact stored
value and ownership and navigated to the second contributor. The screenshot
was inspected. Additional browser checks passed 129-entry pagination, stale
withdrawal, disposal and closing/reopening while navigation was pending; a late
completion preserved the newer inspector. Complete project documents, history
and files and authored/dirty state remained unchanged during inspection.

No page errors or authoring/Build/Run requests occurred; owned helpers terminated.
Private evidence: `local-output/sdk-20260909/animation-contributions-20261007/final/`.
No native Build, game, attachment, installation or disc export occurred. Runtime
playback and gameplay remain deferred; the full SDK goal remains active.
