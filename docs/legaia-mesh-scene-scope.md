# Inspect imported mesh geometry in one or all scene instances

Status: **qualified offline editor workflow**, 2026-10-07. The existing single-donor and mapped-section mesh dialogs now expose **Scene inspection scope** from the loaded Current authored scene. Choose one supported model instance or all supported instances, then inspect the reviewed mesh before Apply. Static imports and explicitly sampled animation poses share this workflow.

The choice only controls scene inspection. Native Apply still changes the shared model asset. Retail provenance, scene placement, model-to-scene matrices and existing native pose ownership remain separate from the external mesh pose baked into proposed geometry. This does not create native animation or retargeting.

## Workflow

Load the authored scene with Models enabled, open its model and choose **Import GLB mesh**. Choose and qualify the source GLB/pose, then Review. The scope selector lists supported scene instances by their SDK labels. Inspect one instance or all supported instances in the assembled viewport. Switch **Inspection layer** between Current and Proposed, then **Return to mesh import** to keep the reviewed draft. Changing the inspection scope does not change the native recipe or invalidate native Review.

**Map section donors** carries the chosen view scope into the mapped draft. The scope is temporary inspection state, not authored placement or a persisted import recipe field. Recovery from retained GLB/settings continues to require fresh Review and defaults to all supported instances. A missing chosen instance stays unavailable instead of silently switching to another instance; unavailable inventories and pending/stale contexts disable scene inspection.

Both dialog paths pass exact `entity_id` and `all_instances` to the existing source-qualified SDK proposal route. The central scene callback checks current renderable model ownership, the held native Review/candidate identity and response scope. Single-instance responses use the existing isolated scene proposal path rather than assuming an all-instance array. All-instance responses preserve existing per-pose geometry grouping and unavailable-instance metadata. Return and stale-response ownership remain guarded by current scene/source and the chosen view scope.

## Focused acceptance

Five Python cases passed with zero skips: the new sampled-pose one/all inspection case, three existing mesh-scene cases and an existing mapped-object scene case. The complete native candidate matched an independently declared static pose before scene composition. A fixture with two raw instances, a distinct posed instance and an unavailable instance matched complete expected single/all previews and existing pose ownership. Changed time, unavailable/wrong entity, nonboolean scope and changed candidate hash refused without mutation.

Three Node suites passed: the new scope-choice suite and existing actual single/batch pose DTO suites. Empty/missing, duplicate and over-budget instance inventories refuse a target; exact one/all choices retain their declared identities. Five affected JS files passed syntax checks and two Python files passed AST checks.

The actual production editor module and scene callback were exercised against a fresh private town01 project. Model0009 exposes **one supported Current scene instance** in this project. Single/all scene inspection, sampled clip zero at 0.5 seconds, Current/Proposed switching, Return retaining Review, transfer into mapped-section inspection and 400 px layout passed. Actual retail multi-instance rendering is not claimed; that scope is qualified by the explicit fixture. Complete out-of-scope entity data, Current geometry retained in the proposal and the base scene stayed exact. The successful probe observed zero page errors or Run requests.

The whole project document, native model bytes and authored files stayed exact with empty Undo/Redo history. Save/Open matched. No new native Build was necessary for this read-only UI workflow; native single/batch pose Build acceptance remains the preceding checkpoints. No runtime code changed, no game was launched or attached, and no installation or full-disc export ran.

Private evidence: `local-output/sdk-20260909/mesh-scene-scope-20261007/` contains fresh fixtures, browser and saved proofs and screenshots. Initial helper setup used a nonexistent display variable, then attempted scene refresh before enabling Models. The helper was corrected to use the existing Models UI and await the actual scene. The first helper server closed with exact project state; subsequent probes used the same second server. A bounded text replacement initially matched another callback and then encountered label encoding; the production edit was restricted to the mesh callback using ASCII identity fields. Production validation was not relaxed.

The full SDK goal remains active. Native skeletal/morph animation, retargeting and manual gameplay acceptance remain unfinished; development continues solo.
