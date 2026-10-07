# Select Texture Placement Matches

Open a texture from the Asset Database, choose **Inspect scene texture uses**, then
**Select matched placements (N)**. The action selects all eligible placements in
qualified decoded `address_match` groups for that texture source. Matches may refer
to image or CLUT contributors. They do not prove final visible pixels, upload order,
palette animation or runtime use.

Hidden placements participate when their geometry has a qualified decoded match.
Partial candidate groups, unavailable geometry, ground and nonplacement resources
are excluded. Search and pagination filter the displayed list only; this action
selects all qualified matches. More than 128 placements refuse selection instead
of trimming. Missing, conflicting or mismatched scene/geometry/model identities
also refuse selection.

Only Edit mode and the current Authored scene support this selection action. The
texture session, both inspection dialogs, scene source/object and current matched
IDs must remain bound through dispatch. Busy/held proposals and Retail comparison
refuse it. Success closes both texture dialogs, clears hierarchy search, reveals
the selection and retains the focused member when possible. Existing actor,
scenery and mixed placement tools receive the group; their own authoring bounds
and native Review/Apply qualification remain required. Selection creates no
project command or history step.

Offline checks passed (2026-10-07): the texture-usage and placement-selection Node
suites cover image/CLUT matches, actor/NPC/scenery membership, partial/unavailable/
ground exclusion, canonical IDs, duplicate geometry/scene identities, wrong model
bindings and 128-member/overflow boundaries. Actual private Town01 checks passed
at 1440 and 400 px for `texture://town01/5/raw/6`: six actor/NPC matches, including a
hidden member, reached the exact existing mixed Review and Cancel. An empty display
query did not trim selection. Retail mode refused the action. Wide/narrow screenshots
were inspected. The separate Asset Details/model viewport regression passed all
actor, scenery and mixed cases at both widths after extracting the common handoff.
Prepared project documents, Undo/Redo history and saved file sizes/timestamps stayed
unchanged. No native Build, game launch, runtime attachment or installation occurred;
the fixture NPC was not spawned. Gameplay stays deferred.

Private evidence: `local-output/sdk-20260909/texture-match-placement-selection-20261007/`
(`oracle.json`, `browser.json`, `readonly.json`, fixture receipt, browser logs,
wide/narrow usage/Review screenshots and `model-regression/`). These are focused
editor checks, not complete SDK or gameplay acceptance.
