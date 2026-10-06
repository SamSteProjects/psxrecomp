# Repeat an NPC draft

Select an existing NPC draft in its scene and choose **Repeat draft...** in the
Inspector. Enter a name prefix, copy count and X/Z spacing, then choose Preview.
In **Line**, copy001 is one spacing step from the original, copy002 two steps, and so on.
Each copy retains the original retail script donor and supported own appearance,
dialogue, waits and script movement. It receives an independent
project UUID. Names end in a three-digit sequence.

Spacing uses integer multiples of64 retail units. Every resulting position must
fit the existing placement bounds. The total project limit is128 NPC drafts.
In Line, zero spacing is allowed; coincident placements remain the author's choice.

**Inspect copies in scene** shows a detached proposal. Use Proposed/Current to
compare while retaining the camera, Return to draft copies to retain the review,
or Restore scene preview to discard the comparison. Inspection changes no
project data. Restore before exporting a scene comparison.

Apply revalidates the source scene, original and full draft collection against
the reviewed snapshot. A stale or invalid last copy rejects the whole command.
All copies enter one Undo/Redo history entry. Save retains them; each copy can
then be renamed, moved, given another donor or deleted independently.


## Rectangular grid

Choose **Rectangular grid**, then enter **Grid columns, including original**.
The original occupies the first cell; copy count counts only new drafts. Copies
fill across X columns, then continue in Z rows. X step is column spacing and Z
step is row spacing; both can be negative within placement bounds.

For five copies and three columns, cell order is:

| Cell | X offset | Z offset |
| --- | --- | --- |
| Original | 0 | 0 |
| Copy001 | X step | 0 |
| Copy002 | 2 × X step | 0 |
| Copy003 | 0 | Z step |
| Copy004 | X step | Z step |
| Copy005 | 2 × X step | Z step |

Columns must be an integer from2 through copy count plus1. X spacing must be
nonzero. Z spacing must be nonzero when copies reach another row; a single row
can use zero Z spacing. Every resulting X/Z must still fit64..16384 on the retail
grid. Pattern, columns and spacing changes clear the accepted preview.
Fresh line/grid reviews use `draft-repeat.v2` / `draft-repeat-grid.v2`, binding
the complete project source key. Existing saved NPC identities remain unchanged.
The same detached scene inspection, atomic Undo/Redo and Save/Open workflow applies.

Offline 2026-10-05 evidence: 12 focused Python cases and expanded Node checks pass.
Private actual browser grid/line/invalid review, scene positions, Apply/Undo/Redo/
Save/reload and disk reopen pass. Prepared native PROT readback matches all six
draft positions and MAN hash, with59 partition-one records and one growth sector.
The 540px controls are inspected. Evidence:
`local-output/sdk-20260909/npc-grid-repetition-20261005/{proof,native-proof}.json`.
This establishes authored placement/serialization; gameplay remains deferred.

Copies can subsequently be moved together with [NPC draft group movement](legaia-npc-draft-groups.md).

## Build and runtime boundaries

Normal Build includes source-qualified compressed and raw streaming MAN candidates.
Compressed candidates can use fixed-span overlays or qualified capacity-growth
relocation; raw candidates use qualified relocation. Source identity, allocation,
composition and actor-pool checks still apply. Use **Review Build** to assess all
current authored inputs; a repetition preview is not Build readiness. See
[candidate boundaries](legaia-npc-build-candidates.md).
Experimental export uses the existing donor,
MAN append, script-reference and archive checks. Repetition adds no new spawn or
scheduling semantics. Copied source scripts can retain story-specific behavior;
partial decoder coverage, runtime initialization, visibility and collision remain
unverified. A correct editor scene or archive does not establish playable NPCs.

## Offline evidence — 2026-09-30

Eleven focused Python tests and Node scene binding checks passed. A retail-source
browser review made three copies of a town01 draft at X2944/3008/3072, Z5440,
verified unchanged existing scene/assets and no preview writes, camera retention,
Return, atomic Apply/Undo/Redo, Save/reload, bounds/stale rejection and zero page
errors. Screenshot inspected. Independent disk reopen retained four drafts.
Independent prepared PROT reopen decoded the final MAN: appended records53–56
retained exact positions, model105, animation13 and script bytes equal to donor
record0011. The donor's script inspection remains partial.

Private evidence lives in `local-output/sdk-20260909/draft-repeat-20260930/`.
Archive SHA256: `b386fb186853a10e445030c3b7f3dc09d2dde1d3faa817acdc6fb6b7f711b262`.
No output disc was written or installed and no game was launched. This feature
postdates the441-test integrated checkpoint.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.

## Current SDK scope notes — 2026-10-05

After **Preview draft copies**, the review displays the SDK's complete bounded
scope notes below the copy table. Repetition and experimental archive review
share the normal-NPC-builder's delivery scope message. These notes do not grant
readiness or gameplay acceptance. Malformed/unbounded scope notes reject the
repetition report and leave Apply disabled. Scope text is rendered as text.

Experimental NPC output review reports `normal_build_assessment: not_assessed_here`.
Its legacy `normal_build_ready: false` remains for compatibility and grants no
readiness claim; **Review Build** performs the separate normal-package assessment.
Existing repetition identities, positions, review keys, commands and history are
unchanged. Runtime spawning/scheduling, opaque scripts, collision and safe total
actor-pool headroom remain deferred. The fixed-span-only descriptions in the
2026-10-01 raw-MAN milestone are historical, not current capability limits.

## Retained own script edits

Copies freeze the source NPC's supported own appearance, dialogue, waits and
movement. Review and Apply freshly requalify their retail source bindings. The
browser accepts only the exact complete copied metadata. Spacing changes instance
placement; it never adds spacing offsets to movement instructions. Later edits
to a copy remain independent, while shared model/animation assets remain shared.

A library or other project change invalidates the source-bound review. Preview
and scene inspection change no authored state. All applied copies still use one
Undo/Redo step and persist with Save/Open. Four-family editor and emitted-record
evidence is in `local-output/sdk-20260909/npc-owned-repetition-20261005/proof.json`.
Runtime spawning, script scheduling and selector behavior require later gameplay
verification.
