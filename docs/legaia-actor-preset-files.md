# Actor preset files

Open **Authored actor templates** and choose a preset's **Export preset JSON**.
The file stores its authored position, initial appearance donor, or both, plus
retail disc/scene/actor provenance and the exact source import SHA256. It includes
no retail geometry, textures, animation bytes, scripts or runtime observations.

In the destination project, import the same retail source scene first. Choose
**Import preset JSON**, select the file and review the proposed name, absolute
coordinates, donor and source provenance. Use a unique name. Changing the name
withdraws the review; **Review preset file** checks it again. **Import reviewed
preset** adds an independent library entry with a new project identity and one
Undo/Redo step. Save/Open retains the library. It changes no actor components;
applying the preset is a separate existing workflow with its normal target
compatibility checks and, for combined presets, scene comparison.

Format: `legaia.actor-preset-file.v1`, UTF-8 JSON up to 8 KiB, exactly one preset.
Supported scopes are authored position, appearance and combined presets. The
source import must match exactly and is freshly verified against the user-owned
disc. Appearance donors are rechecked against compatible initial pairs. Duplicate
JSON keys, extra/payload fields, unsupported scopes, invalid UTF-8/nonfinite
values, duplicate names, missing/changed source imports, stale library reviews
and the 128-preset project limit reject. A changed source scene cannot replace
an import underneath saved actor presets; resolve the library first.

As of 2026-10-02, [initial-animation presets](legaia-animated-actor-presets.md)
use `authored-actor-preset-v2` and `legaia.actor-preset-file.v2`, with an exact
clip witness/hash and optional authored position/appearance. Legacy files keep
the v1 envelope. Version/scope mismatches reject; no animation payload is
included. Frozen witness validation does not reinterpret a preset through the
source actor's mutable appearance. All existing bounds and transfer gates apply.

Coordinates are absolute. Uncaptured axes remain inherited when applied; authored
Y may be project-only. Files do not introduce actor spawning, runtime identity,
script scheduling, collision or gameplay guarantees. Closing a pending file or
review withdraws it. Export and review do not author the project.

## Verification — 2026-09-30

Nineteen focused Python/HTTP checks passed in 1.324 seconds. They cover all three scopes, independent project identity, detached
review, one library history entry, Undo/Redo, Save/Open, stale/forged/source/name/
JSON bounds and saved-library reimport rejection. Real retail-source browser
export/import/name rejection, no-preview writes, unchanged actors, one command,
Undo/Redo, oversized file and closed response withdrawal passed with zero page
errors. The final review screenshot was inspected. An independent retail-source
project imported the combined file, preserved components and source hash, changed
no actors/imports, saved/reopened and freshly re-exported it. All transient
browser library edits were undone; the original saved fixture was unchanged.
Private evidence: `local-output/sdk-20260909/preset-files-20260930/`.
No game launched or runtime attached. This work postdates the 441-test checkpoint.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.

## Portable NPC branch presets v8 - 2026-10-05

NPC presets now freeze independent branch destinations with all six earlier edit
families. Capture, export, import review and new-instance placement qualify the
complete frozen script composition against the retail donor. Metadata-only v8
stores stable branch IDs and typed target PCs; original boundaries, conditions,
selectors and dispatch remain native-qualified. Earlier v1-v7 envelopes and bounds
remain available. Branch-bearing files cannot use an older schema. Import creates
only a library entry; reviewed placement creates an independent undoable NPC.

Validation: 19 focused Python checks with private retail input and both Node
preset suites pass. Coverage includes freezing after source edits, all earlier
families, skipped-body composition, atomic history, Save/Open, invalid/interior
PCs, forged ownership/fields and freshly qualified stored-template placement.
Actual browser capture/download/upload, changed-review withdrawal, library
Undo/Redo, Save/reload, detached scene inspection and new-instance Apply pass.
The 2583-byte v8 file and 540px import review were inspected.

Recipient normal Build `ee559898bc7a73de` independently reopens branch PC14 target11,
flag bit0, facing sector0, wait11, movement X3200/Z5696/MOVE_ID10, appearance105/13
and text `Wait NPC`. Source drafts and recipient imports stay unchanged. Package
SHA256: `3a1ee99cfc40358682941c2afc850393303255f64b6e39f309072d47a0a24f71`.
Evidence: `local-output/sdk-20260909/npc-branches-presets-20261005/proof.json`.

This supersedes the earlier branch-preset capture restriction. No game launch or
full-disc export occurred. Runtime activation, story reachability, scheduling and
termination remain unverified; manual acceptance is deferred and the goal active.
