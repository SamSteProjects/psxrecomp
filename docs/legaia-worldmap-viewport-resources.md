# World Viewport Source Asset Inspection

In **World ground**, select a model instance or ground and choose **Inspect source asset**. The existing World resource browser opens directly on that entity's exact geometry asset. Native source metadata, complete source instance membership and material/TIM relationships stay in the same browser. From there, inspect all source asset instances to return to the viewport, or follow a TIM relationship and preview its native pixels.

The handoff freshly discovers the resource inventory and compares its source key, complete kingdom provenance, selected asset provenance, mesh counts and full instance membership with the loaded viewport. Missing or changed evidence refuses navigation. Changing selection during discovery closes the resource browser rather than selecting the old asset. Closing the browser during discovery cancels navigation without a second error.

This is read-only source inspection and works in disc-backed empty projects. Ground is a derived asset and has no placement owner. Placement editing remains a separate capability-gated action: the shared Inspector binding now checks geometry capability generally, while each placement action independently requires placement capability. Current-layer inspection retains the displayed layer; entering source resources does not author or reset placements. Runtime residency, visibility and per-material runtime palette use remain unverified.

## Offline Checks — 2026-10-10

Nineteen Inspector schema checks preserve read-only source properties and unresolved runtime states. One focused Node suite covers ten forged source/membership/mesh refusal cases and immutable inputs. The helper also binds every rendered native instance to its exact resource asset: 302/273/237 across the three kingdoms, including ground. Two JavaScript syntax checks and the Inspector schema AST check pass.

Actual empty-project browser workflows cover all three kingdoms: selected model → exact asset details → complete instance-group viewport return; selected ground → exact asset → TIM relationship → native pixel preview. No field import, selection, authored edit or history entry is created. Desktop/400px resource layouts were inspected without clipping and zero page errors occurred. Every project file and the complete project document remain unchanged.

An additional imported-project workflow verifies Current-layer resource inspection retaining its layer, the existing complete-owner batch action remaining available, a delayed request refusing changed-selection navigation, and safe close-during-discovery cancellation. Cancellation releases the closing request's busy flag; a completed stale request cannot release another request's flag. Project data remains unchanged. Private evidence: `local-output/sdk-20260909/worldmap-viewport-resources-20261010/`. No Build, game, runtime attachment, installation or disc export ran. Gameplay verification remains deferred; the full SDK goal remains active.
