# Saved runtime node review

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
