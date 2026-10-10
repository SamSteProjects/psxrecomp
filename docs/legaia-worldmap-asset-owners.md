# World Viewport Asset Owner Editing

Inspect a kingdom in **World ground**, select a source model instance, then choose **Edit selected asset owner records…** in its Inspector. This qualifies every source instance of that asset and opens the existing batch placement editor with all its complete native record owners selected. It works from Retail and Current display layers. Ground has no native placement owner and exposes no owner-edit action.

The selection covers the asset's complete source instance group, independently of viewport isolation or hierarchy search. Each selected native record retains every cell it owns. A shared record can affect cells belonging to another asset; the batch editor's owner/cell counts and shared-record consent remain authoritative. This action does not create per-instance authoring for shared records.

The handoff compares kingdom/disc/MAP/floor provenance and source keys, checks entity/record hashes and complete membership, and carries detached Current values and Current MAP identity into the existing fresh batch navigation check. Missing, conflicting, partial or unavailable owners refuse navigation. Limits remain 128 owners and 512 source seeds. Closing World ground during qualification cancels the request and prevents late navigation.

Use the batch editor's existing translation/yaw tools, Current/Proposed preview, Review/Apply, Undo/Redo and Save/Open. Review and shared-record consent are still required. The original **Inspect placement record** action remains available for one owner. Source ownership does not establish runtime visibility or resting positions.

## Offline Checks — 2026-10-10

Nineteen Inspector schema checks preserve read-only source properties and unresolved runtime states while exposing the two capability-gated editor actions. One focused Node suite covers complete scope including an owner shared with another asset, detached targets, fresh handoff refusal and fifteen source/ownership refusal cases. The same helper passes three native report pairs with groups of 126/138/109 instances, respectively 4/4/3 native owners, and complete owned seed equality. Three JavaScript syntax and two SDK Python AST checks pass.

Actual three-kingdom browser workflows select model groups in World ground, open exact complete owner selections, refuse Review without shared-record consent, Review Proposed changes, Apply, Undo/Redo and restore the project. Saved/reopened project data and every fixture file match the original bytes. The active field scene and selection remain unchanged. A further actual workflow verifies Current-layer navigation, original single-record routing and close-during-qualification cancellation. Desktop/400px Inspector and batch Review layouts were inspected; zero page errors occurred.

Private evidence: `local-output/sdk-20260909/worldmap-asset-owners-20261010/`. No Build, game launch, runtime attachment, installation or disc export occurred. Gameplay verification remains deferred and the full SDK goal remains active.
