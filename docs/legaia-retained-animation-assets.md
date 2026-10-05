# Retained animation assets

Refresh scene resources now registers saved retained clips in the Asset Database.
They appear in Animations and Authored assets, with an Authored badge and the stable
`animation://<scene>/authored-record/<UUID>` identity. Project resource discovery
includes their source-scene membership too. No extracted animation bytes are
stored in the metadata catalog or committed with this feature.

Open a retained asset to inspect its active/retired status, frame/channel counts,
authored initial-assignment count and source witnesses. Retired clips remain
inspectable; they are absent from the generated native bank. Inspect captured
model opens the recorded model asset. Select capture actor navigates to the actor
that supplied the saved capture. Neither action changes the animation assignment.

Preview retained clip verifies the current project source and reconstructs the
saved native record using the existing retained-pose decoder. It opens the normal
model viewer with the saved frames and Current model geometry. Preview works for
assigned, unassigned and retired clips without applying edits or reactivating
anything. Timing, looping, live playback and runtime assignment remain unresolved.

Asset Details → Inspect recorded references supports navigation to registered
retained clips. Each clip has an authored **retained model capture** relationship,
qualified by ledger/record/original donor hashes, captured model/channel owners,
counts and active status. This source relationship assigns no native slot. An
active authored initial assignment separately retains its existing verified
native selector/bank relationship and actor edge. These represent distinct
provenance layers. Unavailable scene resource catalogs remain explicitly partial.

Discovery and preview are readonly in Edit and observation contexts. A separate
verification view satisfies the existing saved-record decoder's Edit prerequisite;
it does not change the original mode. Exact asset identity and current source key
qualify preview requests. Changed source, wrong model/record, malformed metadata
or extra HTTP fields reject. Closing a pending inspector aborts its request.

## Verification - 2026-10-05

Validation: 42 focused/neighboring Python checks, four JavaScript workflow/contract
suites and three syntax checks passed. Native HTTP discovery, actor/clip/model
references, all three clip previews, Project membership, malformed/stale requests
and readonly observation mode passed. The actual browser verified animation/authored
categories, all three inspectors and model viewers, captured-model navigation,
actor reference -> registered clip metadata navigation and stale-source rejection.
Complete document/history/files/mode/scene were unchanged. Zero page errors or
authoring/Build/Save/game requests; screenshots inspected. Private evidence:
`local-output/sdk-20260909/retained-assets-20261005/proof.json`. Initial browser
harness assumptions about responsive-only tabs, total authored counts and collapsed
provenance text were corrected; prior attempts are preserved. No game launched.
