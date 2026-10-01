# Repeat an NPC draft

Select an existing NPC draft in its scene and choose **Repeat draft...** in the
Inspector. Enter a name prefix, copy count and X/Z spacing, then choose Preview.
Copy001 is one spacing step from the original, copy002 two steps, and so on.
Each copy retains the original retail donor binding and receives an independent
project UUID. Names end in a three-digit sequence.

Spacing uses integer multiples of64 retail units. Every resulting position must
fit the existing placement bounds. The total project limit is128 NPC drafts.
Zero spacing is allowed; coincident placements remain the author's choice.

**Inspect copies in scene** shows a detached proposal. Use Proposed/Current to
compare while retaining the camera, Return to draft copies to retain the review,
or Restore scene preview to discard the comparison. Inspection changes no
project data. Restore before exporting a scene comparison.

Apply revalidates the source scene, original and full draft collection against
the reviewed snapshot. A stale or invalid last copy rejects the whole command.
All copies enter one Undo/Redo history entry. Save retains them; each copy can
then be renamed, moved, given another donor or deleted independently.

## Build and runtime boundaries

Normal Build rejects projects containing NPC drafts. Experimental export uses the existing donor,
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
