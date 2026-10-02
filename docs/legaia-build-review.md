# Review normal Build before writing a package

Choose **Review Build…** beside Build. The SDK takes a detached snapshot of
current authored inputs and runs the same source verification, serializers,
overlap checks, compressed-span checks, manifest parsing and existing-file guards
used by normal Build. Review returns audited before/after changes, source/audit/
manifest hashes, overlay counts and explicit blockers. It writes no output files
and does not run the package packer, install overlays or launch a game.

NPC drafts remain normal-Build blockers. Review lists each retained draft and
assesses existing overrides with drafts explicitly excluded in the detached
snapshot. The current project, its imported facts, authored assets, history and
saved metadata are not changed. This partial assessment cannot enable Build while
draft blockers remain. If serialization fails, the assessment is absent and later
changes are not claimed to have passed.

A ready review exposes **Build reviewed inputs** in Edit mode. It passes the
reviewed authored-input identity to normal Build; both the browser and server
reject changed inputs. Actual Build revalidates sources and performs packaging.
The editor then opens the ordinary built-package report. Existing direct Build
remains available. Review keys cover project/root/source/imports, authored
overrides, drafts and model/texture replacement bindings.

Passing review establishes supported serialization, not a completed archive or
interactive acceptance. Packing, filesystem write permissions/capacity,
installation, script behavior, live identities, collision and animation suitability
remain separate checks. Gameplay verification stays deferred. Review metadata
is bounded to eight MiB; the UI shows the first 256 change rows with an explicit
total when larger. Full serializer coverage is represented by the audited report
count and hash, rather than by the displayed row count.

Validation on 2026-10-01: five retail-enabled Python checks passed, including
no-write/no-packer review, retained draft blockers, source drift/stale dispatch,
audit/manifest/report equality with actual Build, and unchanged raw/compressed
animation Build behavior. All 23 Node test files and 25 module syntax checks
passed. Browser showed four retained draft blockers and nine audited existing
changes, with no Build files created. A separate no-draft fixture rejected an
outdated review after rename, restored its name with Undo, then produced a matching
package from a fresh review. Both fixtures preserved saved metadata and authored
content, with zero page errors and no Run request. Screenshots inspected.

Private evidence: `local-output/sdk-20260909/build-review-20261001/`.
These checks postdate integrated475; full SDK/runtime acceptance is incomplete.
