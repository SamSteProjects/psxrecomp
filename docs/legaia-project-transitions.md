# Project transition references

Central transition assets now expose the same decoded instruction identities in
the Asset Browser and shared Inspector, with encoded/static arrival layers and
Active/Project asset references. Authored entry spans are freshly qualified before
annotation; scene annotations have a separate freshness key. See
[transition asset workflow](legaia-transition-assets.md).

Choose **Project transitions** in the Asset Database tool area to inspect decoded
scene-change references from all imported scenes. **Scene transitions** limits
source instructions to the active scene. Discovery verifies retail source evidence
and does not refresh resources, change selection or author values.

The diagram and scene list distinguish imported scenes, named retail destinations
and unresolved destinations. Select a scene with the mouse or Enter/Space, then
choose **Focus direct references** for its incoming/outgoing instructions. This
shows direct encoded references only. **Show all scenes** restores the overview.
Search matches scenes, owners, scripts, instruction IDs and coverage status;
**Imported scenes only** excludes endpoints outside the project. A scene without
a supported script catalog remains available with its source-unavailable reason.

**Fit graph**, plus/minus, wheel zoom and drag pan control the diagram camera.
Arrow badges show the number of independent instructions with the same source
and destination. Select a badge to inspect precisely those instructions. Opposite
directions and self references retain separate identities. Long arrows pass
between other scene boxes; crossings do not connect scenes. Labels and scene
selection remain accessible through the scene list and keyboard.

Every instruction retains source scene, owner script, PC, partition, source
coverage, provenance and encoded destination. Its table separates Retail,
Authored and Effective entry bytes; inherited authored values remain explicit.
The reference list paginates 20 rows. The drawing caps 80 nodes/160 source-target
pairs and reports omissions, while all matching instruction records remain
available below. Search or direct-reference focus brings omitted endpoints into
the drawing. Missing references do not establish that a scene has no exits.

**Inspect source script** opens the imported source scene and selects the exact
instruction in the normal script inspector. **Open imported destination** and
**Open imported scene** are enabled only for scenes already in the project.
Navigation uses ordinary scene selection and does not write an actor or
transition component. Close aborts pending discovery and disposes handlers;
stale source, annotation or project-only state changes block retained actions.
A late error from a closed request cannot replace a newly opened workspace.

## Current visual workspace evidence — 2026-10-02

26 focused retail-enabled Python cases passed with no skips, plus 6 Node suites
and 3 changed-module syntax checks. Thirteen actual browser workflows passed:
real project/active graph discovery, complete reference pagination, keyboard
scene selection/direct focus, eight-reference badge identity, zoom/pan/wheel/Fit,
imported-only filtering and exact ID search, separate entry layers, cross-scene
script/PC navigation, destination navigation, project-only invalidation, stale
response rejection, pending-close/reopen cleanup and old-request isolation and narrow-layout bounds. Zero page or
HTTP errors, zero authoring commands and zero game-launch requests were observed.

The Town01/Dolk2/Town0b/map01 fixture contains 17 nodes, 18 grouped pairs and 35
instructions from 319 scripts (195 partial, zero unavailable). Town01P2 preserves
retail X96 separately from authored/effective X97. Saved project/import hashes
remain unchanged. Full/narrow graph and entry-layer screenshots were inspected.
Private scripts, logs, source responses and captures are retained under
`local-output/sdk-20260909/transition-graph-workspace-20261002/`.
This source-reference workspace needs no manual gameplay acceptance. Wider
runtime, route and story behavior remains deferred; the full SDK is incomplete.

## Limits and evidence

The service accepts no client source bindings and is bounded to 1–64 imported
scenes, 16,384 references and 16,448 nodes. Only supported decoded paths are
covered. Edges have reachability `not_evaluated`: no gameplay route, story flag
condition, complete exit inventory or runtime transition is inferred. Source
inspection uses existing bounded authoring rules separately.

**Earlier list-only checkpoint (2026-09-30):** Five focused Python tests passed.
Retail HTTP/browser checks across town01 and
Dolk2 returned three references to map01 from180 scripts,88 partial and zero
unavailable scripts. Cross-scene source navigation, no authoring commands,
unchanged draft/override state, strict request rejection and zero page errors
passed. Screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-transitions-20260930/`.
This feature postdates the441-test integrated checkpoint; no game was launched.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.
