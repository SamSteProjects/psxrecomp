# Saved runtime node review

## Compare files spatially — 2026-10-06

After comparing two saved reviews in the dialog, choose **Show historical comparison positions** while their matching scene is loaded in Edit mode. Use **Historical samples** to show Both files, Baseline (blue) or Comparison (amber). Complete XYZ samples appear independently; skipped counts follow the selected layer. Dashed lines join differing complete samples sharing a declared key. File-only keys are unconnected. Lines do not establish movement paths, actor identity, a common process or capture order. Missing heights remain unknown.

**Frame historical positions** fits the chosen layer while preserving camera angles and scene visibility; an empty layer disables framing. **Return to historical review** reopens the full comparison table and evidence. Clear, source-change withdrawal and the read-only/nonpersistent rules remain unchanged. These are file metadata displays, never accepted Live correlation. Both files must pass the existing scene/epoch/profile comparison guards.

Node guards, a retail-source browser with synthetic files and the existing single-review browser workflow passed. Wide/narrow comparison screenshots were inspected, with no page errors or retained authored changes. Evidence: `local-output/sdk-20260909/historical-runtime-comparison-viewport-20261006/final-pass/proof.json`. No real runtime or gameplay verification occurred. This supersedes the earlier statement that comparison has no camera authority: explicit Frame now affects only the editor camera.


## Historical viewport display — 2026-10-06

Open a saved review while the matching scene is loaded in Edit mode, then choose **Show historical positions**. Complete XYZ samples within the supported display range appear as dashed amber markers. Unknown axes are skipped rather than placed on an invented ground plane. The count includes skipped samples. File-declared scene/epoch and unconfirmed identity remain explicit; schema validation does not authenticate the file or its coordinates. Markers include occluded samples and never select or bind imported actors.

**Frame historical positions** changes only the camera target/distance, retaining camera angles, projection and visibility. **Return to historical review** reopens the detached evidence, and **Clear historical positions** removes the display. Active controls remain visible beside the viewport even with Scene tools collapsed. Display is withdrawn by project/mode/scene/source/representation changes and is not restored by Undo or retained in saved views/projects. This supersedes the original camera/framing exclusion below; all Live authority and identity exclusions remain.

Focused Node guards and a fresh browser with synthetic files over a retail-imported scene passed, including wide/narrow framing, return, clear, source-change withdrawal and foreign-scene rejection. Authored state remained unchanged after the verification transform was undone. No real runtime capture or gameplay check occurred. Proof and inspected screenshots: `local-output/sdk-20260909/historical-runtime-viewport-20261006/final-pass/`.


The editor's **Observed nodes** panel can download decoded metadata from an
accepted actor observation. The download is a detached historical review, not
an executable snapshot, savestate, reusable observation token or authored edit.
Raw node prefixes and guard tokens are excluded.

When gameplay verification resumes, enter Live mode, observe actors, open
**Observed nodes**, and select **Download captured node metadata**. The action
rechecks the scene/project/observation context before exporting. It records node
IDs, scene/epoch/profile identifiers, position capture frames, decoded fields,
uncertainty/evidence and unconfirmed candidate IDs. Export time is labelled
separately from capture frames.

To review later without a running game, open **Observed nodes** in Edit mode and
choose the JSON under **Open saved runtime node review**. Expand a node to inspect
positions, captured fields, confidence, applicability and evidence. Search filters
the saved metadata. Re-exporting retains the same historical values.

Saved files cannot establish Live state, restore correlation, select candidates,
frame runtime nodes, submit edits or change the camera/project. Returning to the
current observed list uses its normal observation guards. Closing or replacing
the panel while a file read is pending withdraws that read.

Format: `legaia.runtime-node-review.v1`, explicitly historical and read only.
Limits: 1 MiB including the formatted download, 128 nodes, 64 fields per node,
bounded candidate IDs, text and decoded metadata depth. Invalid epochs,
duplicates, nonfinite positions, reversed capture frames, authority claims and
unknown file fields reject. A valid file is still user-supplied historical data;
schema validation does not authenticate its source or confirm any actor identity.
Keep real runtime captures in private ignored output.

## Validation on September 30

Serializer checks cover detached roundtrip, heading interpretation, payload/token
redaction, epoch/identity/type/depth/size rejection. Synthetic data passed the
actual browser download/reopen/filter workflow, stale download rejection,
malformed/oversized files and closed-read withdrawal. Project, camera, service
and Live state remained unchanged; zero authoring requests or page errors.
The actual revisioned field profile decoded a synthetic156-byte prefix into17
fields, all accepted with pointer/uncertainty metadata preserved. The historical
viewer screenshot was inspected.

Private evidence: `local-output/sdk-20260909/runtime-node-review-20260930/`.
No real runtime observation or game launch occurred. Real capture acceptance,
runtime actor identity and gameplay/lifecycle verification remain deferred.

## Compare two saved reviews

Open a saved review, then choose **Compare another saved review with this
baseline**. Both files must declare the same scene, epoch and profile (including
an unknown profile). The table shows each matching node key's coordinates,
capture frames, candidate IDs and binding reason. Coordinate differences are
comparison minus baseline. Missing coordinates and overflow remain unknown.
Filter by changed/unchanged samples or keys present in only one file; text search
also covers decoded fields and evidence. Expand changed fields or full metadata
to retain confidence, applicability, unresolved interpretations and source notes.
Return to either review, or download `legaia.runtime-node-comparison.v1` metadata.
Comparison downloads are reports, not input review files.

Matching declared keys do not confirm the same actor, allocation or process.
The v1 input format has no process/executable identity; matching epochs alone
cannot prove a common session. Baseline/comparison describe file selection order,
not chronological capture order. Export timestamps are not capture timestamps.
File-only keys do not establish spawning or removal. Comparison has no camera,
project, authoring, attachment or Live-state authority.

Node checks cover context rejection, detached evidence, null/overflow axes,
changed field metadata, file-only keys and semantic object-key ordering.
Synthetic browser checks passed comparison/filter/download/return, mismatched
context and closed pending-read withdrawal. Project, camera and runtime state
were unchanged; zero authoring requests and page errors. Final screenshot
inspected. Private evidence:
`local-output/sdk-20260909/runtime-comparison-20260930/`.
No real runtime sample or gameplay acceptance is claimed.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.
