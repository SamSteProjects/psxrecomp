# Compare saved Build audits

Open **Build history**, select two completed saved Builds in the **Left audit**
and **Right audit** controls, and choose **Verify both and compare**. The editor
verifies both packages through the existing receipt/audit/manifest/payload/ZIP
checks before displaying a comparison. At least two valid completion receipts
are required. Builds without receipts cannot be compared.

The comparison uses the recorded source disc SHA-256 and stable audit identities:
scene, owner, asset, field, scope, and animation frame/object where present. A
different retail disc hash or duplicate identity rejects the comparison. This
operation does not import the source disc, change a project, install a package,
attach a runtime or launch the game.

Each row is a difference between saved audit records:

- A record exists only in the left or right audit.
- Both audits contain the identity, but their records differ.
- Identical records contribute to the unchanged count.

Complete record equality includes bounded payload/vector deltas and contributor
metadata, even when the headline Before/After values match. Expand **Full compared
record** for those details. A missing audit record is displayed as **Not recorded
in this audit**. It does not prove a runtime value, entity deletion, reverted bytes
or complete scene coverage. This is an audit comparison, not a game simulation.

Input identity and package integrity are separate. Comparing two different
packages does not require either to match the current authored inputs. Both must
pass saved-file verification and refer to the same recorded retail disc identity.
The disc itself is not rehashed; source-disc integrity and gameplay remain
unverified. Local receipts are unsigned recorded provenance, not authenticity
certificates. File verification is an observation, not an atomic snapshot against
concurrent external filesystem edits.

`POST /api/builds/compare` accepts `left_id` and `right_id` only. Identical IDs,
stale project context, changed receipts, ambiguous audit identities and comparisons
over eight MiB are rejected. The browser displays the first 256 differences;
counts cover the full bounded comparison. Closing the dialog aborts its request.
A failed recheck clears the prior comparison and withdraws the affected package
rows' previous verification claims.

Validation on 2026-10-01: 15 focused retail-enabled Python checks passed in
10.963 seconds in the final run, including source mismatch, duplicate identity, exact animation
frame/object identity, typed JSON/detail changes, metadata bounds, project/receipt drift,
real baseline/authored packages, corruption and existing Build history/review.
All 25 Node test files and 26 editor module syntax checks passed. A fresh browser
compared real Town01 packages with nine changes each: actor0011 X changed from
2944 to 3008, with one different audit record and eight identical records. Browser
checks blocked identical IDs before dispatch, rejected a corrupted private archive,
cleared the previous report, restored the file and successfully compared again.
Malformed API input was rejected; authored entities, assets and saved metadata
were unchanged, with zero page errors and no authoring/Build/Run request.

The first private fixture attempt used the copied active Dolk2 scene and correctly
hit its unsupported placement-serialization guard. A separate explicit Town01
fixture supplied the evidence above. Port4455 was unavailable; the owned SDK server
used4445 after the failed launch was terminal. The first screenshot exposed tight
columns and stale per-row verification labels; spacing/visible selector labels and
verification status synchronization were corrected, browser checks repeated and
the final screenshot inspected. Owned browser/server stopped.

Private evidence remains under `local-output/sdk-20260909/build-compare-20261001/`
and `build-compare-python-final-20261001.log`. This feature postdates the passing
498-test integrated checkpoint. Broader SDK/runtime/gameplay acceptance remains
open and manual gameplay is deferred.
