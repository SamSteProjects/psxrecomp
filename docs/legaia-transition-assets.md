# Transition assets and source inspection

Refresh scene resources, choose **Transitions** in the Asset Browser and use
ordinary typed search, for example `type:transition scene:town01`. Each resource
is one decoded SCENE_CHANGE instruction, retained by its source scene, partition,
record and PC. The source catalog remains metadata only.

The info button opens the shared Inspector. **Inspect transition entry and
source** opens a focused view of encoded imported/authored/effective X, Z and
direction bytes, plus imported/effective static arrival X/Z and facing. The
arrival coordinates belong to the destination scene. Source trigger location,
player height, route reachability, current story state and runtime arrival remain
unknown; no source trigger marker or collider is created from arrival bytes.

**Inspect parent script** and **Inspect transition 0x....** open the original
P1 actor or P2 script; the latter focuses its exact instruction. Existing source
forms provide bounded entry-byte and exact arrival-grid edits, Undo/Redo and
Save/Open. Destination names and instruction sizes stay immutable. A partial
catalog may include unvisited prefix/tail bytes with zero decoder stops: that
coverage label alone does not prohibit an entry qualified by the serializer.
Unknown/conflicting path stops, unsupported names and aliased source records
remain subject to the existing fail-closed source rules.

**Open imported destination** uses ordinary project scene navigation. It is
disabled for unresolved names and sources not imported into the project.
Navigation does not apply an edit or alter the arrival. Dialog actions reject
changed context, busy/pending operations and closed views. Scene or transition
annotation changes close stale dialogs; the transition-state key is independent
of the geometry key, so an operand edit does not require mesh reconstruction.

## Recorded dependencies

**Inspect asset references** supports Active and Project scopes. A script has a
`script_transition_reference` relationship to each transition. Named references
have a `transition_destination_source` relationship to their encoded scene.
The legacy direct `encoded_scene_change` relationship remains available.
Unknown names retain their source instruction and unresolved coverage without
inventing a destination scene. Dependency and Referenced by actions navigate
using the verified source scene; unimported targets remain unavailable.

Each new relationship retains the source import/catalog keys, instruction PC,
authoring operand ID, script record SHA256, encoded destination/name digest,
dispatch context and `not_evaluated` reachability. The graph requires one exact
source script and compares its owner, record extent/hash, status, stop count and
reference against the asset. These records establish source relationships,
without asserting execution or runtime residency.

Stable resource IDs are `transition://<scene>/<actors/man-p1|scripts/man-p2>/<record>/<pc>`.
Authoring IDs stay `script://<scene>/<owner-path>/<record>/transition/<pc>`.
Discovery is bounded to 4,096 transition assets,16,384 decoded references and
64 imported scene identities; the combined scene resource budget remains4,096.
The adapter neither decodes additional bytes nor reads a second source format.
Resource callers verify fresh imports and authored spans before annotation.

## Verification on 2026-10-02

55 focused retail-enabled Python tests passed with no skips;39 Node files and
38 module syntax checks passed. The four-scene private probe found35 transitions
among4,399 resource records: Town01=1, Dolk2=2, map01=31, Town0b=1. Actual browser
checks covered the shared Inspector, source PC0x16, qualified partial-script
arrival editing, encoded/static layers, Undo/Redo/Save, stale-view closure,
Active/Project references, source navigation, imported map01 navigation and the
disabled unimported town0c destination. No page or unexpected HTTP errors occurred.
Final Inspector/reference screenshots were reviewed for readable tables/actions.

The saved Town01 fixture edits P2[0], PC0x16: X12352 to128 and facing2048 to1024;
Z3264 stays unchanged. Independent decompression of its package MAN differs only
at28574 (96 to128) and28576 (4 to2). Save/Open reproduces package SHA256
`7277e4d50b88a668386beab8f707f6616be894a2b4e11e7a52b9591100a27a46`.
Imported metadata and saved bytes remain unchanged by discovery and Build.
Private evidence is under `local-output/sdk-20260909/transition-assets-20261002/`.
No game launch, package installation, runtime patch or live write occurred.

The full SDK objective remains incomplete. Gameplay acceptance still needs an
identified source trigger, actual destination arrival/facing and scene/script
continuity; it remains in the [deferred queue](legaia-gameplay-verification-queue.md).
