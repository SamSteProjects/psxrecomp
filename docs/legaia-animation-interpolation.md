# Animation frame-range interpolation

Select an imported actor with a supported rigid animation and open **Author
animation channels**. Copy its retail or effective channel, select another
frame of the same object, and choose **First target frame** and **Last target
frame**. **Review interpolated frame range** shows the proposed six-axis poses.
The copied pose is the first target endpoint; the currently selected effective
pose is the last. The target range need not equal the endpoint source frames.
Review leaves the project unchanged.

**Apply reviewed interpolation** replaces this actor's contributions for the
chosen object and inclusive target frames as one ordinary animation command.
Other frames and objects remain unchanged. Existing shared-clip conflict checks,
source verification, Undo/Redo, Save/Open and Build validation still apply.
Unapplied channel drafts must be applied or discarded first. Changed endpoints,
target ranges, authored state or source context withdraw the review.

Translation uses linear interpolation rounded to signed integer source units.
Each rotation axis follows its shortest circular path modulo4096, rounded to
16-unit PSX increments. Exact half ties round toward the larger integer; an exact
2048-unit half-turn follows the positive direction. This is per-axis pose
interpolation, not quaternion interpolation, retargeting or inferred playback
timing. Endpoints remain exact. Choose at least two target frames; the combined
contributions remain bounded to4096 channels and the existing clip layout.

## Verification — 2026-10-01

The retail Dolk2 actor0001 browser workflow reviewed five target frames without
commands, rejected a changed target range, applied one command and passed
Save/Undo/Redo. Baseline restored, zero page errors, review screenshots inspected.
Independent reopen retained four NPC drafts. A separate integer encoder matched
the complete resulting record, with only record offsets254/334/413/493 changed.
Detached no-draft normal Build matched the full114764-byte animation bank and
preserved all other content payloads. Package SHA256:
`daac46b83e72c2234453c88ab3616c876e91f9b1ce032f98bd0985537be35b48`.

This workflow exposed a normal Build bug: it assumed scene ANM banks always had
a compressed-stream offset. Dolk2 has a raw streaming ANM bank. Normal Build now
uses the shared source-preserving animation patch preparation for both layouts,
including source preimage and physical carrier checks. Raw banks emit a bounded
`.bin` overlay; compressed banks retain `.lzs` output and compression audit.
Raw bank hashes are separate from decoded compression hashes.

Thirteen focused Python checks passed with the private retail disc, including
independent complete-bank readback for town01 compressed and Dolk2 raw normal
Build and existing streaming/draft composition checks. All20 Node test files
and22 editor syntax checks passed. Math checks cover exact endpoints, signed
ties, angle wrapping, half-turn choice, bounds and preservation of other edits.
Private evidence:
`local-output/sdk-20260909/animation-interpolation-20261001/`.

No game launched or disc installed. Normal Build still rejects authored NPC
drafts; verification detached them only in memory. Playback and gameplay remain
deferred. These checks postdate the integrated469-test checkpoint and do not
establish complete SDK or runtime acceptance.


The final source9084e545 browser guard also verified that an observed external
authored-state change blocks both the old Apply and a new review from the stale
channel form. No interpolation command was sent; Undo restored the baseline.
Private evidence: `authored-state-guard.json` in the folder above. The subsequent
integrated offline run on that unchanged source passed475 Python tests with
retail input and no skips,20 Node files and22 editor syntax checks. See the
[current validation checkpoint](TEST_PLAN.md).
