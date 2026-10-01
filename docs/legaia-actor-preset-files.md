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
