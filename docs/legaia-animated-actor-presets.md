# Reusable initial-animation actor presets — 2026-10-02

In Edit mode, select an imported actor with a non-null authored initial-animation
assignment. Open **Authored actor templates** and enter a unique name.
**Capture authored initial animation** saves only that assignment.
**Capture animation with authored position and appearance** also saves whatever
authored position axes and appearance donor are present. Inherited settings,
scripts, channel edits and other components are not captured.

These presets use `authored-actor-preset-v2`. The required `ActorAnimation` stores
its exact imported witness, stable scene clip identity and record SHA-256.
`Transform` and `ActorAppearance` are optional. Existing position, appearance
and combined v1 scopes retain their component sets and behavior.

## Review and apply

Choose a compatible existing actor, then review the preset. Review separates
imported position/clip evidence, current authored settings, the proposed
appearance's inherited clip and the proposed initial clip. It identifies the
qualified immutable witness, model source and animation record digest.
Application verifies the complete proposed component set in a detached view;
appearance and animation never apply as intermediate commands.

Omitted components remain unchanged. A captured clip matching the proposed
appearance's inherited clip removes a conflicting target animation override.
A qualified captured witness for another clip stays exact. Legacy presets that
omit animation retain the target assignment and reject incompatible appearance
changes. Channel edits remain attached to their original imported shared clip.

Single-target Apply creates one normal Undo entry. Group presets review all
2–128 distinct active-scene actors before one atomic Apply/Undo entry. Failure
at the final target leaves every actor and the history unchanged. No-op Apply
preserves Undo and Redo. Save/Open retains the library and authored components.

**Inspect actor preset in scene** and the group equivalent display the exact
verified witness pose at the target's proposed position. Proposed/Current,
Return and Restore preserve the existing review lifecycle. Inspection changes
no authored state. Source, template, target, selection and scene changes
withdraw stale comparisons. The proposed witness is independent of the
appearance donor, and unchanged owners and geometry are checked.

## Transfer and Build

Exported v2 presets use `legaia.actor-preset-file.v2`; v1 presets keep the v1
envelope. Version/scope mismatches reject. Files remain metadata-only UTF-8 JSON,
up to 8 KiB, with duplicate-key/nonfinite/payload rejection, exact source-import
hash and fresh user-owned-disc proof. Import reviews a unique name and adds one
independent UUID library entry without changing actors.

Frozen template evidence does not depend on the source actor's current authored
appearance. With captured appearance, the frozen appearance/clip are validated
together. With animation alone, the imported witness proves its model and clip;
each target's final model compatibility is checked separately.

The existing normal and experimental draft writers serialize the resulting
component and compose one final MAN model/animation header. There is no new
serializer, retargeter, global clip pairing, actor spawning or runtime write.
Only the existing local, nonzero, full same-model bindings accepted by the
source-qualified MAN writer are supported. Scripts can replace this initial
clip; cadence, suitability, visibility, collision and story behavior remain on
the deferred gameplay checklist.

Private evidence is under
`local-output/sdk-20260909/animated-presets-20261002/`. Imported retail payloads,
source screenshots and generated packages stay local and untracked.

## Verification

The final focused retail-enabled pass completed47 Python tests in57.695s with
no skips, plus8 HTTP/project compatibility tests in1.293s. All37 Node test files
and37 module syntax checks passed. The actual browser workflow covered capture,
v2 file export/import, independent library identity, single/group scene review,
Proposed/Current/Return, Apply, inheritance, Undo/Redo and Save. It reported zero
page errors and zero unexpected HTTP errors; final screenshots were inspected.
A browser-discovered empty-override inheritance bug is fixed and covered by a
regression proving no history/Redo/import/persistence changes on untouched actors.

Independent Town0b transfer/Build readback changes only decoded MAN offset9471,
14→13, with exact source ANM record12 digest; inherited output reproduces baseline
package bytes and imported channel ownership. The combined private fixture
changes only offsets19122 (animation13→14) and19123 (X byte119→150), giving
actor0049 X2944/Z1472/model0102 and exact record13 digest
`5f8e8175544512db45f3ec37a9be33ddf414ee0b5a2ddf079ac195b6d5bdd09e`.
Reopening the saved browser project reproduces package SHA256
`2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389`.
Build leaves imports and saved project bytes unchanged. The untouched baseline
has no overlays; no synthetic retail MAN payload is invented for that archive.
No game was launched or package installed. Gameplay acceptance remains deferred.
