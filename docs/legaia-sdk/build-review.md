# Reviewing a build

Build opens a report of the changes that actually entered the private package.
The Build report button reopens the latest report for the current editor
session. Opening a different project clears it. Actor placement values use
world units; model and animation changes retain their encoded indexes;
dialogue preserves its padded text; texture replacements show content hashes.
No-op bindings are omitted because they do not modify the package.

The report lists affected scenes, guarded overlay bytes and build-time
validation results. Paths and package hashes remain available under the
provenance disclosure. It does not claim the package was executed or rendered
correctly in the game.

An authored-state digest covers the project name/root, disc path, imports,
actor overrides and texture bindings. Selection, undo history and unused
templates do not affect it. Editing or importing data retains the previous
report and marks it stale; returning to the exact prior inputs restores the
match. This comparison does not reread the disc, replacement files or package
on each state request. A fresh build performs those integrity checks.

The report is a projection of the validated audit, returned after packing.
It adds no payload to the package and changes no serializer or runtime behavior.
The existing deterministic build ID and archive format remain unchanged.
