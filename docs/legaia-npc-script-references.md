# NPC retail script donor navigation

An authored NPC's Asset references now includes **NPC retail script donor**. Open
that dependency to inspect its retail partition-1 script. The script's reverse
references identify each authored NPC using it, including multiple NPCs sharing
one donor. Active-scene and project scopes retain their existing navigation and
coverage rules.

The relationship records the exact donor identity, source script ID, record
SHA-256, byte coordinates, decoder status, reference pin and complete authored
draft digest. It is an authored source relationship. It does not represent the
NPC's generated script or live execution; use its saved Build comparison for
emitted bytes. Missing/unavailable catalog records increase unresolved coverage.
Duplicate records or conflicting source identities are rejected. Decoder stops
remain visible as partial coverage.

Offline acceptance (2026-10-06): 31 focused Python checks passed with the private
retail disc and no skips; the existing reference decoder suite, new strict donor
decoder checks and editor syntax check passed. Fresh Town0b reports verified both
color-edited NPCs reference donor 0037, reverse links list both, and active/project
client qualification passes. A private muted editor browser verified forward and
reverse navigation, wide/400 px layouts, no page errors and no game requests.
Document, history, scene and selection remained unchanged. No new Build or game
verification was needed for this read-only feature.

Evidence: `local-output/sdk-20260909/npc-script-navigation-20261007/`, including
actual reports, browser screenshots, proof metadata and client log. This is a
focused addition; the historical full Python/client campaigns were not rerun.
