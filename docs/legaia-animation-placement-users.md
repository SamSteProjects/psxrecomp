# Select Current Animation Users from Asset Details

Open an animation asset's **Details** button in the Asset database, then choose
**Select current scene actors (N)**. The action selects imported actors whose
effective initial animation assignment matches that exact SDK asset identity.
It preserves an active matching actor as the focus, otherwise choosing the first
stable member. The hierarchy search clears, selected groups are revealed and
the shared placement selection flows into existing inspector/group tools.

The action requires the current authored scene, fresh source-bound geometry and
Asset Details ownership. Retail comparison, missing context and unused clips
disable it. Eligibility comes from the shared scene selection service; qualified
hidden actors participate. Duplicate, foreign or missing actor/assignment
identities and selections above 128 refuse rather than guessing.

Current initial assignments are distinct from imported usage, inherited
appearance-donor bindings and shared animation-channel contributors. Effective
identities include explicit observed initial-clip assignments and retained
allocated clips. The action does not claim runtime script-selected clips or
playback behavior, and does not include NPC drafts. It changes transient editor
selection only, without creating authored overrides.

The model and animation actions share pending/source/disposal ownership. Changing
the scene, document or matching membership invalidates an in-flight handoff;
reopening/closing Asset Details disposes its previous action. The parent rechecks
the complete current membership before publishing the group after normal
selection navigation. Existing model-selection defaults remain unchanged.

## Offline Checks Passed — 2026-10-07

Three Node suites passed animation/model user selection and shared placement
contracts. The new cases qualify effective-versus-imported identity, allocated
clips, eligibility, duplicates/foreign sources, bounds, immutability and pending/
stale/disposed ownership. Three JavaScript syntax checks, server AST and
whitespace validation passed.

Actual private Town01 browser checks selected all seven users of
`animation://town01/scene-anm/0017`, revealed the exact hierarchy membership and
qualified Retail refusal. The 400 px dialog fits; visual inspection found and
corrected overflow in existing Used by labels by wrapping long actor IDs.
Selection uses the normal selection endpoint; no command, Build or Run occurred.
Project document/history/files and authored/dirty state stayed unchanged; no page
errors occurred and owned helpers terminated.

Private evidence:
`local-output/sdk-20260909/animation-asset-users-20261007/complete/`.
Earlier attempts retain a main-card-versus-Details harness mistake, the label
overflow evidence, and a harness wait for an authoring control intentionally
disabled in Retail mode. The passing check waits for the Retail preview response.

No game, runtime attachment, installation or disc export occurred. Gameplay
remains deferred and the full SDK goal remains active.
