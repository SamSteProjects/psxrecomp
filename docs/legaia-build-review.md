# Review normal Build before writing a package

Choose **Review Build…** beside Build. The SDK takes a detached snapshot of
current authored inputs and runs the same source verification, serializers,
overlap checks, compressed-span checks, manifest parsing and existing-file guards
used by normal Build. Review returns audited before/after changes, source/audit/
manifest hashes, overlay counts and explicit blockers. It writes no output files
and does not run the package packer, install overlays or launch a game.

Current v2 review includes source-qualified NPC candidates. Unsupported, stale or
out-of-capacity candidates remain blockers. Package fit does not establish runtime
allocation, spawning, scheduling or opaque script behavior; see
[qualified NPC Build candidates](legaia-npc-build-candidates.md). The current project,
imported facts, authored assets, history and saved metadata remain unchanged. If
serialization fails, the assessment is absent and later changes are not claimed
to have passed.

After review completes, **Save full Build review…** downloads the complete accepted
JSON response, including blockers when Build is unavailable. It retains all change
rows and native/other records even when the dialog displays only a subset. The file
contains source identity, serialization provenance, coverage and limitations; it is
review metadata rather than a package or an authoring import. Export revalidates the
response and current authored-input identity, uses a source-key filename and a 32 MiB
UTF-8 limit, and requires an open, nonbusy dialog. Changed inputs require fresh review.

2026-10-05 download validation: ordinary/NPC Node suites and syntax pass, including
301-row and multibyte-overflow cases. Actual private retail browser downloads at
desktop/540px match the complete accepted response and its 130 coordinate records;
pending disable, mounted UI stale-source guard and unchanged project/history/files
pass without page errors. No package or game was created. Evidence:
`local-output/sdk-20260909/build-review-download-20261005/proof.json`.

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

For model-shape rows with a qualified ledger, open **Native coordinate audit** to
see object/vector/axis, model byte offset and signed before/after values. Coordinates
render lazily in 128-row pages. Other primitive/material/removal/allocation records
remain in the full audit and are counted separately. Existing-layout ledgers survive
model-pack relocation into normal Build metadata. Topology additions without a ledger
show their existing hashes/relocation evidence only. Offsets refer to the recorded
model layout. Source changes require reopening review before paging or building.

2026-10-05 validation: nine focused Python cases, ordinary/NPC Build-review Node
suites and syntax pass. Normal synthetic package readback checks ledger retention.
A private retail Town01 browser review checks all 130 native words across two pages,
source/candidate hashes, paging bounds and 540px layout, without changing project,
history or files. No retail package or game was created/launched for this check.
Evidence: `local-output/sdk-20260909/build-review-model-coordinates-20261005/proof.json`.

Historical v1 validation on 2026-10-01 (draft exclusion is superseded by v2 candidate inclusion): five retail-enabled Python checks passed, including
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
